# obstacle_compliance/utils.py
import csv
import io
import logging
import math
import os
import re
from datetime import datetime
from io import BytesIO

import rasterio
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.template.loader import render_to_string
from django.urls import reverse
from functools import lru_cache
from geopy.distance import geodesic
from xhtml2pdf import pisa

from .models import Aerodrome, AerodromeBuffer, AerodromeRunway
# from dotenv import load_dotenv
import os
from decouple import config
# load_dotenv()
logger = logging.getLogger(__name__)

# Constants from KCAA/ICAO
IHS_RADIUS = 4000  # 4km Inner Horizontal Surface
IHS_HEIGHT = 45    # 45m above aerodrome elevation
CONICAL_SLOPE = 0.05  # 5% (1:20) rise
CONICAL_END = 6000    # Conical zone ends at 6km
KCAA_ZONE = 15000     # 15km regulatory zone
LIGHTING_THRESHOLD = 30  # Lighting required for structures >30m within 15km
HIGH_RISE_THRESHOLD = 90  # Additional lighting threshold for very tall structures

def initial_bearing_rad(lat1, lon1, lat2, lon2):
    """Initial bearing in radians (clockwise from north) between two points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return math.atan2(x, y)


def destination_point_rad(lat, lon, bearing_rad, distance_m):
    """Destination coordinates given start point, bearing (radians), distance (m)."""
    R = 6371000.0
    delta = distance_m / R
    phi1 = math.radians(lat)
    lam1 = math.radians(lon)
    phi2 = math.asin(math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(bearing_rad))
    lam2 = lam1 + math.atan2(math.sin(bearing_rad) * math.sin(delta) * math.cos(phi1),
                             math.cos(delta) - math.sin(phi1) * math.sin(phi2))
    return math.degrees(phi2), math.degrees(lam2)


def along_perp_dist(thr_lat, thr_lon, bearing_rad, lat, lon):
    """Project a point onto a runway centerline (threshold + bearing).

    Returns (d_along_m, d_perp_m): metres along the centerline (0 at the
    threshold, positive outward) and signed lateral offset (positive right
    of the direction of travel). Local planar approximation - accurate for
    OLS-sized distances (<= ~4km).
    """
    distance = geodesic((thr_lat, thr_lon), (lat, lon)).meters
    p_bearing = initial_bearing_rad(thr_lat, thr_lon, lat, lon)
    delta = (p_bearing - bearing_rad + math.pi) % (2 * math.pi) - math.pi
    return distance * math.cos(delta), distance * math.sin(delta)


def densify_ring(ring, step_m=50.0):
    """Densify a polygon ring [(lat, lon), ...] so no segment exceeds step_m.

    Returns a closed ring of interpolated points (used for parcel checks).
    """
    if not ring or len(ring) < 3:
        return []
    pts = []
    n = len(ring)
    for i in range(n):
        lat1, lon1 = ring[i]
        lat2, lon2 = ring[(i + 1) % n]
        seg = geodesic((lat1, lon1), (lat2, lon2)).meters
        if seg <= 0:
            continue
        steps = max(1, int(seg / step_m))
        brg = initial_bearing_rad(lat1, lon1, lat2, lon2)
        for k in range(steps):
            f = k / steps
            pt = destination_point_rad(lat1, lon1, brg, seg * f)
            pts.append(pt)
    return pts


class DEMService:
    """Handles Digital Elevation Model queries with caching"""
    
    def __init__(self, dem_path=None):
        # Use Environment Variable in production, fallback to local for dev
        # self.dem_path = dem_path or config('', default='obstacle_compliance/newdata/kenya_srtm_30.tif')
        self.dem_path = dem_path or config('DEM_URL')

        self._dataset = None
        self._nodata_value = None
    
    def _get_dataset(self):
        """Lazy load the DEM dataset with support for remote COGs"""
        if self._dataset is None:
            try:
                # If the path is a URL, prefix it for rasterio/GDAL
                path = self.dem_path
                if path.startswith('http'):
                    path = f"/vsicurl/{path}"
                
                # Rasterio uses GDAL's virtual file system to stream only needed bytes
                self._dataset = rasterio.open(path)
                self._nodata_value = self._dataset.nodata
                logger.info(f"DEM loaded from: {path}")
            except Exception as e:
                logger.error(f"Failed to load DEM: {e}")
                raise
        return self._dataset
    
    def _is_valid_elevation(self, value):
        """Check if elevation value is valid (not nodata and within reasonable range)"""
        if value is None:
            return False
        
        # Check for nodata value
        if self._nodata_value is not None and abs(value - self._nodata_value) < 0.1:
            return False
        
        # Check for other common nodata indicators
        if value > 10000 or value < -500:  # Impossible elevations in Kenya
            return False
            
        # Check for exact 32767 (common nodata)
        if abs(value - 32767) < 0.1 or abs(value - -32767) < 0.1:
            return False
            
        return True
    
    @lru_cache(maxsize=1000)
    def get_elevation(self, point):
        """
        Get ground elevation at given point
        point: GEOS Point object with SRID 4326
        """
        if not point:
            return 0.0
            
        # Extract coordinates
        lon, lat = point.x, point.y
        
        cache_key = f"elev_{lat:.4f}_{lon:.4f}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            ds = self._get_dataset()
            # rasterio uses (lon, lat) order
            values = list(ds.sample([(lon, lat)]))
            
            if values and len(values[0]) > 0:
                elevation = float(values[0][0])  # Get first band value
                
                # Validate the elevation
                if self._is_valid_elevation(elevation):
                    # Cache for 1 hour (3600 seconds)
                    cache.set(cache_key, elevation, 3600)
                    return elevation
                else:
                    logger.warning(f"Invalid elevation value {elevation} at ({lat}, {lon})")
                    
                    # Try to get nearest valid elevation
                    return self._get_nearest_valid_elevation(lon, lat)
            
        except Exception as e:
            logger.warning(f"Error sampling DEM at ({lat}, {lon}): {e}")
        
        return 0.0
    
    def _get_nearest_valid_elevation(self, lon, lat, max_offset=0.01):
        """
        Try to find nearest valid elevation by sampling around the point
        max_offset: approximately 1km in degrees
        """
        ds = self._get_dataset()
        
        # Try small offsets in cardinal directions
        offsets = [
            (0, 0),  # Original point
            (0.001, 0), (0, 0.001), (-0.001, 0), (0, -0.001),  # ~100m offsets
            (0.002, 0), (0, 0.002), (-0.002, 0), (0, -0.002),  # ~200m offsets
        ]
        
        valid_elevations = []
        
        for lon_offset, lat_offset in offsets:
            try:
                sample_lon = lon + lon_offset
                sample_lat = lat + lat_offset
                values = list(ds.sample([(sample_lon, sample_lat)]))
                
                if values and len(values[0]) > 0:
                    elev = float(values[0][0])
                    if self._is_valid_elevation(elev):
                        valid_elevations.append(elev)
                        
                        # If we found a valid one close by, return it
                        if lon_offset == 0 and lat_offset == 0:
                            return elev
            except:
                continue
        
        if valid_elevations:
            # Return average of valid elevations found
            return sum(valid_elevations) / len(valid_elevations)
        
        return 0.0
    
    def batch_get_elevation(self, points):
        """Get elevations for multiple points efficiently"""
        ds = self._get_dataset()
        samples = [(p.x, p.y) for p in points if p]
        
        if not samples:
            return []
        
        results = []
        for vals in ds.sample(samples):
            if vals and len(vals) > 0:
                elev = float(vals[0])
                if self._is_valid_elevation(elev):
                    results.append(elev)
                else:
                    results.append(0.0)
            else:
                results.append(0.0)
        
        return results
    
    def get_dem_info(self):
        """Get information about the DEM file"""
        ds = self._get_dataset()
        return {
            'bounds': ds.bounds,
            'crs': str(ds.crs),
            'width': ds.width,
            'height': ds.height,
            'nodata': ds.nodata,
            'band_count': ds.count
        }
    


class ComplianceCalculator:
    """Main compliance calculation engine with caching and error handling"""
    
    def __init__(self):
        self.dem = DEMService()  # Assuming DEMService is defined elsewhere
        self._cache_timeout = 3600  # 1 hour cache for calculations

    def calculate_ols_ceiling(self, airport_elevation, distance_m):
        """
        Calculate Obstacle Limitation Surface ceiling at given distance
        Based on KCAA/ICAO conical surface formula
        
        Args:
            airport_elevation: Airport elevation in meters AMSL
            distance_m: Distance from airport reference point in meters
        
        Returns:
            float: Maximum allowed height in meters AMSL, or None if beyond conical zone
        """
        if distance_m < 0:
            logger.warning(f"Negative distance provided: {distance_m}m")
            return None
            
        if distance_m <= IHS_RADIUS:
            # Inner Horizontal Surface - constant height
            return airport_elevation + IHS_HEIGHT
            
        elif distance_m <= CONICAL_END:
            # Conical surface - rises at 5% from IHS edge
            extra_height = (distance_m - IHS_RADIUS) * CONICAL_SLOPE
            return airport_elevation + IHS_HEIGHT + extra_height
        else:
            # Beyond conical zone (>6km), no OLS restriction
            # But still within 15km regulatory zone for lighting requirements
            return None

    def calculate_distance(self, point1, point2, method='geodesic'):
        """
        Calculate distance between two points with multiple methods
        
        Args:
            point1: First GEOS Point (SRID 4326)
            point2: Second GEOS Point (SRID 4326)
            method: 'geodesic' (accurate) or 'projected' (fast)
        
        Returns:
            float: Distance in meters
        """
        if not point1 or not point2:
            return None
            
        if method == 'geodesic':
            # Most accurate - uses WGS84 ellipsoid
            coords1 = (point1.y, point1.x)
            coords2 = (point2.y, point2.x)
            return geodesic(coords1, coords2).meters
        else:
            # Faster but less accurate - Web Mercator projection
            # Suitable for rough calculations or when performance is critical
            point1_3857 = point1.transform(3857, clone=True)
            point2_3857 = point2.transform(3857, clone=True)
            return point1_3857.distance(point2_3857)

    # =========================================================
    # RUNWAY-BASED OLS (Annex 14) - declared runway geometry when
    # available, else falls back to the centroid approximation.
    # =========================================================
    APPROACH_SLOPE = 0.02            # 2% (1:50) approach surface
    APPROACH_LENGTH_M = 3000.0       # approach surface length (code 3/4)
    APPROACH_DIVERGENCE = 0.15       # 15% lateral divergence
    TRANSITIONAL_SLOPE = 1.0 / 7.0   # 1:7 transitional surface

    @staticmethod
    def _strip_half_width(runway):
        """Strip half-width in metres per side (best effort)."""
        hw = 75.0
        if runway.length_declared_m and runway.length_declared_m >= 1800:
            hw = 150.0
        raw = runway.strip_dimensions or runway.strip_dimensions_m
        if raw:
            m = re.search(r'(\d+(?:\.\d+)?)\s*m', str(raw))
            if m:
                val = float(m.group(1))
                if val >= 60:
                    hw = val
        return hw

    def _runway_geometry(self, runway):
        """Extract threshold coordinates/bearings from a runway LineString."""
        if runway.geom is None or runway.geom.geom_type != 'LineString' or runway.geom.num_coords < 2:
            return None
        coords = list(runway.geom.coords)  # [(lon, lat), (lon, lat), ...]
        t1 = (coords[0][1], coords[0][0])  # (lat, lon)
        t2 = (coords[-1][1], coords[-1][0])
        length = geodesic(t1, t2).meters or 1.0
        bearing = initial_bearing_rad(t1[0], t1[1], t2[0], t2[1])  # t1 -> t2
        elev1 = runway.thr_elevation_1_m
        elev2 = runway.thr_elevation_2_m
        if elev1 is None and runway.aerodrome and runway.aerodrome.elevation_m:
            elev1 = float(runway.aerodrome.elevation_m)
        if elev2 is None and runway.aerodrome and runway.aerodrome.elevation_m:
            elev2 = float(runway.aerodrome.elevation_m)
        return {
            't1': t1,
            't2': t2,
            'length_m': length,
            'bearing_rad': bearing,
            'elev1_m': float(elev1 or 0.0),
            'elev2_m': float(elev2 or 0.0),
            'designator1': (runway.rwy_designator_1 or '').strip() or 'end1',
            'designator2': (runway.rwy_designator_2 or '').strip() or 'end2',
        }

    def calculate_runway_ceiling(self, prop_point, airport):
        """Annex 14 OLS ceiling at a point using declared runway geometry.

        Evaluates approach surfaces (2% from each threshold), transitional
        surfaces (1:7 from strip edge) plus the universal Inner Horizontal
        Surface (flat 45m within 4km) and conical surface (5% 4-6km) measured
        from the aerodrome reference point. The controlling ceiling is the
        minimum across every applicable surface.

        Returns dict with 'ceiling_amsl', 'surfaces', 'distance_m' or None
        when no runway data applies at this point.
        """
        try:
            runways = list(AerodromeRunway.objects.filter(icao_code=airport.icao_code))
        except Exception:
            runways = []
        if not runways:
            return None

        lat, lon = prop_point.y, prop_point.x
        ceilings = []  # [(ceiling_amsl, surface_label)]

        for rwy in runways:
            g = self._runway_geometry(rwy)
            if not g:
                continue
            hw = self._strip_half_width(rwy)
            length_m = g['length_m']
            ends = [
                (g['t1'], g['elev1_m'], g['bearing_rad'], g['designator1']),
                (g['t2'], g['elev2_m'], (g['bearing_rad'] + math.pi) % (2 * math.pi) - math.pi, g['designator2']),
            ]
            for (thr, elev, bearing, label) in ends:
                d_along, d_perp = along_perp_dist(thr[0], thr[1], bearing, lat, lon)
                # Approach surface: 2% rising from threshold, diverging 15%
                if 0.0 <= d_along <= self.APPROACH_LENGTH_M:
                    half_w = hw + self.APPROACH_DIVERGENCE * d_along
                    if abs(d_perp) <= half_w:
                        ceilings.append((elev + self.APPROACH_SLOPE * d_along, 'approach_%s' % label))
                # Transitional surface: 1:7 upward from strip edge, along the strip
                if 0.0 <= d_along <= length_m and abs(d_perp) > hw:
                    ceilings.append((elev + (abs(d_perp) - hw) * self.TRANSITIONAL_SLOPE, 'transitional_%s' % label))

        # Universal IHS + conical from ARP
        distance_m = self.calculate_distance(prop_point, airport.geom, method='geodesic')
        airport_elev = float(airport.elevation_m or 0)
        if distance_m is not None:
            if distance_m <= IHS_RADIUS:
                ceilings.append((airport_elev + IHS_HEIGHT, 'horizontal'))
            elif distance_m <= CONICAL_END:
                ceilings.append((airport_elev + IHS_HEIGHT + (distance_m - IHS_RADIUS) * CONICAL_SLOPE, 'conical'))

        if not ceilings:
            return None
        ceilings.sort(key=lambda x: x[0])
        min_ceiling = ceilings[0][0]
        surfaces = sorted(set(name for c, name in ceilings if abs(c - min_ceiling) < 0.5))
        return {
            'ceiling_amsl': min_ceiling,
            'surfaces': surfaces,
            'distance_m': distance_m,
            'runway_count': len(runways),
        }

    def evaluate_property(self, prop_point, prop_height_agl, airport, use_cache=True):
        """
        Evaluate compliance for a single property against an airport
        
        Args:
            prop_point: GEOS Point of property (SRID 4326)
            prop_height_agl: Height above ground in meters
            airport: Aerodrome instance
            use_cache: Whether to cache results
        
        Returns:
            Dictionary with compliance results or None if error
        """
        # Input validation
        if not prop_point or not airport or not airport.geom:
            logger.error(f"Invalid inputs: prop_point={bool(prop_point)}, airport={bool(airport)}")
            return None
            
        if prop_height_agl < 0:
            logger.warning(f"Negative height provided: {prop_height_agl}m")
            prop_height_agl = 0
            
        # Check cache if enabled
        # Check cache if enabled - FIXED CACHE KEY
        if use_cache:
        # Create a safe cache key by sanitizing the WKT string
            import hashlib
        
            # Option 1: Use hashed version (most reliable)
            point_str = f"{prop_point.x:.6f}_{prop_point.y:.6f}"
            key_base = f"compliance_{airport.icao_code}_{point_str}_{prop_height_agl}"
            cache_key = hashlib.md5(key_base.encode()).hexdigest()
            cache_key = f"comp_{cache_key}"  # Add prefix for readability
        
            # Alternative Option 2: Clean the WKT (if you prefer readable keys)
            # clean_wkt = prop_point.wkt.replace(' ', '_').replace('(', '').replace(')', '').replace('.', 'p')
            # cache_key = f"compliance_{airport.icao_code}_{clean_wkt}_{prop_height_agl}"
            # cache_key = cache_key[:250]  # Memcached key limit is 250 chars
            
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
        
        try:
            # Calculate distance using geodesic method for accuracy
            distance_m = self.calculate_distance(prop_point, airport.geom, method='geodesic')
            distance_km = distance_m / 1000
            
            # Get ground elevation at property from DEM
            ground_amsl = self.dem.get_elevation(prop_point)
            
            # Handle DEM errors gracefully
            if ground_amsl is None:
                logger.warning(f"DEM returned None for point {prop_point.wkt}, using airport elevation")
                ground_amsl = airport.elevation_m
            elif ground_amsl > 10000:  # Invalid DEM value (NoData)
                logger.warning(f"DEM returned invalid value {ground_amsl}m for {prop_point.wkt}, using airport elevation")
                ground_amsl = airport.elevation_m
            
            building_top_amsl = ground_amsl + prop_height_agl
            airport_elev = airport.elevation_m or 0
            
            # Calculate OLS ceiling - runway-based Annex 14 surfaces when
            # declared runway data exists, otherwise centroid approximation
            runway_ols = self.calculate_runway_ceiling(prop_point, airport)
            if runway_ols:
                ols_ceiling = runway_ols['ceiling_amsl']
                surfaces_checked = runway_ols['surfaces']
            else:
                ols_ceiling = self.calculate_ols_ceiling(airport_elev, distance_m)
                if ols_ceiling is not None:
                    surfaces_checked = ['horizontal'] if distance_m <= IHS_RADIUS else ['conical']
                else:
                    surfaces_checked = []
            
            # Determine hazard status and restrictions
            is_hazard = False
            max_allowed = None
            headroom = None
            
            if ols_ceiling is not None:
                max_allowed_amsl = ols_ceiling
                max_allowed_agl = max(0, max_allowed_amsl - ground_amsl)  # Can't be negative
                max_allowed = round(max_allowed_agl, 1)
                headroom = round(max_allowed_agl - prop_height_agl, 1)
                is_hazard = building_top_amsl > ols_ceiling
            else:
                max_allowed = None  # No OLS restriction beyond conical zone
            
            # Determine lighting requirements (per KCAA circular)
            requires_lighting = False
            lighting_reason = None
            
            if distance_km <= (KCAA_ZONE / 1000):
                if prop_height_agl >= HIGH_RISE_THRESHOLD:
                    requires_lighting = True
                    lighting_reason = f"High-rise structure ({prop_height_agl}m) requires lighting per KCAA circular"
                elif prop_height_agl >= LIGHTING_THRESHOLD:
                    requires_lighting = True
                    lighting_reason = f"Structure height ({prop_height_agl}m) exceeds {LIGHTING_THRESHOLD}m within 15km zone"
            
            # Determine status color and message
            if is_hazard:
                status = "RED"
                status_message = "HAZARD - Structure exceeds obstacle limitation surface"
            elif distance_km <= (KCAA_ZONE / 1000):
                status = "YELLOW"
                status_message = "CAUTION - Within 15km regulatory zone"
            else:
                status = "GREEN"
                status_message = "CLEAR - Outside all restriction zones"
            
            # Build result dictionary
            result = {
                "is_hazard": is_hazard,
                "requires_lighting": requires_lighting,
                "lighting_reason": lighting_reason,
                "distance_km": round(distance_km, 2),
                "distance_m": round(distance_m, 1),
                "status": status,
                "status_message": status_message,
                "max_allowed_agl": max_allowed,
                "headroom": headroom,
                "ground_elevation": round(ground_amsl, 1),
                "building_top_amsl": round(building_top_amsl, 1),
                "airport_elevation": round(airport_elev, 1),
                "ols_ceiling_amsl": round(ols_ceiling, 1) if ols_ceiling is not None else None,
                "surfaces_checked": surfaces_checked,
                "within_15km_zone": distance_km <= (KCAA_ZONE / 1000),
                "within_conical_zone": distance_m <= CONICAL_END,
                "within_ihs_zone": distance_m <= IHS_RADIUS
            }
            
            # Cache the result
            if use_cache:
                cache.set(cache_key, result, self._cache_timeout)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating property against {airport.icao_code}: {str(e)}", exc_info=True)
            return {
                "error": True,
                "message": f"Evaluation error: {str(e)}",
                "status": "ERROR",
                "airport": airport.icao_code
            }

    def evaluate_property_all_airports(self, prop_point, prop_height_agl, max_airports=5):
        """
        Evaluate property against all nearby airports within 15km
        Returns the most restrictive result with detailed information
        
        Args:
            prop_point: GEOS Point of property (SRID 4326)
            prop_height_agl: Height above ground in meters
            max_airports: Maximum number of airports to return in affected list
        
        Returns:
            Dictionary with comprehensive compliance results
        """
        # Input validation
        if not prop_point:
            return {
                "status": "ERROR",
                "status_code": "INVALID_POINT",
                "message": "Invalid property point coordinates",
                "airports_affected": [],
                "compliance_score": 0
            }
        
        if prop_height_agl < 0:
            return {
                "status": "ERROR",
                "status_code": "INVALID_HEIGHT",
                "message": "Height cannot be negative",
                "airports_affected": [],
                "compliance_score": 0
            }
        
        try:
            # Find all airports whose 15km buffer contains this point
            # Using spatial index for fast lookup
            containing_buffers = AerodromeBuffer.objects.filter(
                radius_km=15,
                geom__contains=prop_point
            ).select_related('aerodrome')[:10]  # Limit to 10 for performance
            
            buffer_count = containing_buffers.count()
            
            # Distance-based fallback: a missing prebuilt buffer must never
            # produce a silent false GREEN.
            if buffer_count == 0:
                nearby = list(self.get_airports_in_radius(prop_point, KCAA_ZONE / 1000.0)[:10])
                if not nearby:
                    return {
                        "status": "GREEN",
                        "status_code": "OUTSIDE_ALL_ZONES",
                        "message": "Property is outside all 15km airport regulatory zones",
                        "airports_affected": [],
                        "compliance_score": 100,
                        "requires_lighting": False,
                        "is_hazard": False
                    }
                airports_qs = nearby
            else:
                airports_qs = [buffer.aerodrome for buffer in containing_buffers]
            
            # Evaluate against each airport
            results = []
            for airport in airports_qs:
                result = self.evaluate_property(prop_point, prop_height_agl, airport, use_cache=True)
                
                if result and not result.get('error'):
                    # Add airport info to result
                    result['airport'] = {
                        'icao_code': airport.icao_code,
                        'name': airport.name or airport.admin_company or airport.icao_code,
                        'type': airport.type,
                        'distance_km': result['distance_km'],
                        'elevation_m': airport.elevation_m
                    }
                    results.append(result)
            
            if not results:
                return {
                    "status": "WARNING",
                    "status_code": "NO_VALID_EVALUATIONS",
                    "message": "Could not evaluate against any airports",
                    "airports_affected": [],
                    "compliance_score": 0
                }
            
            # Sort by restrictiveness: RED > YELLOW > GREEN, then by distance
            status_priority = {'RED': 0, 'YELLOW': 1, 'GREEN': 2, 'ERROR': 3}
            results.sort(key=lambda x: (
                status_priority.get(x['status'], 3), 
                x.get('distance_km', float('inf'))
            ))
            
            most_restrictive = results[0]
            
            # Calculate compliance score (0-100)
            compliance_score = self._calculate_compliance_score(results, most_restrictive)
            
            # Prepare affected airports list (limited to max_airports)
            airports_affected = [
                {
                    'icao': r['airport']['icao_code'],
                    'name': r['airport']['name'],
                    'distance_km': r['distance_km'],
                    'status': r['status'],
                    'requires_lighting': r['requires_lighting'],
                    'is_hazard': r['is_hazard']
                } for r in results[:max_airports]
            ]
            
            return {
                "status": most_restrictive['status'],
                "status_code": most_restrictive.get('status_code', 'EVALUATED'),
                "message": most_restrictive.get('status_message', f"Property evaluated against {buffer_count} airport(s)"),
                "compliance_score": compliance_score,
                "airports_affected_count": len(results),
                "airports_affected": airports_affected,
                "primary_airport": most_restrictive['airport'],
                "primary_result": {k: v for k, v in most_restrictive.items() if k != 'airport'},
                "requires_lighting": any(r['requires_lighting'] for r in results),
                "is_hazard": any(r['is_hazard'] for r in results),
                "evaluation_timestamp": __import__('datetime').datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in evaluate_property_all_airports: {str(e)}", exc_info=True)
            return {
                "status": "ERROR",
                "status_code": "SYSTEM_ERROR",
                "message": f"System error during evaluation: {str(e)}",
                "airports_affected": [],
                "compliance_score": 0
            }
    
    def _calculate_compliance_score(self, results, most_restrictive):
        """
        Calculate a compliance score (0-100) based on evaluation results
        
        Args:
            results: List of evaluation results
            most_restrictive: The most restrictive result
        
        Returns:
            int: Compliance score (0-100)
        """
        if not results:
            return 0
            
        # Base score depends on status
        status_scores = {
            'GREEN': 100,
            'YELLOW': 70,
            'RED': 30,
            'ERROR': 0
        }
        
        base_score = status_scores.get(most_restrictive['status'], 50)
        
        # Adjust based on various factors
        adjustments = 0
        
        # If within multiple zones, reduce score
        if len(results) > 1:
            adjustments -= 5 * min(len(results) - 1, 3)
        
        # If requires lighting but not installed, reduce score
        if most_restrictive.get('requires_lighting'):
            adjustments -= 10
        
        # If near the limit (low headroom), adjust
        headroom = most_restrictive.get('headroom')
        if headroom is not None and headroom < 5:
            adjustments -= 15
        elif headroom is not None and headroom < 10:
            adjustments -= 5
        
        # Calculate final score (ensure within 0-100)
        final_score = max(0, min(100, base_score + adjustments))
        return round(final_score)

    def get_airports_in_radius(self, prop_point, radius_km=15):
        """
        Get all airports within a given radius of a point
        
        Args:
            prop_point: GEOS Point (SRID 4326)
            radius_km: Radius in kilometers
        
        Returns:
            QuerySet of Aerodrome objects
        """
        if not prop_point:
            return Aerodrome.objects.none()
        
        # Use spatial distance lookup (Django >= 2.0 API)
        from django.contrib.gis.measure import D
        from django.contrib.gis.db.models.functions import Distance
        return Aerodrome.objects.filter(
            geom__distance_lte=(prop_point, D(km=radius_km))
        ).annotate(
            _dist=Distance('geom', prop_point)
        ).order_by('_dist')
class ApplicationWorkflow:
    TRANSITIONS = {
        'draft': ['submitted'],
        'submitted': ['under_review'],
        'under_review': ['approved', 'rejected'],
        'approved': ['revoked'],
        'rejected': ['submitted'],
        'revoked': [],
    }

    @classmethod
    def can_transition(cls, from_status, to_status):
        return to_status in cls.TRANSITIONS.get(from_status, [])

    @classmethod
    def transition(cls, application, to_status, user=None, notes=''):
        if not cls.can_transition(application.status, to_status):
            raise ValueError(f"Cannot transition from {application.status} to {to_status}")
        from datetime import datetime
        application.status = to_status
        if to_status == 'submitted':
            application.submitted_at = datetime.now()
        elif to_status in ('approved', 'rejected'):
            application.reviewed_by = user
            application.reviewed_at = datetime.now()
            application.reviewer_notes = notes
            if to_status == 'approved':
                application.certificate_number = f"KCAA-{datetime.now():%Y%m%d}-{application.id:05d}"
        application.save()


def process_bulk_upload(job):
    """
    Process a BulkUploadJob: read CSV, run compliance checks on each row.
    Expected CSV columns: name, latitude, longitude, height_m
    """
    from .models import Property, ComplianceCheck, Notification

    job.status = 'processing'
    job.save(update_fields=['status'])

    from django.contrib.gis.geos import Point

    calculator = ComplianceCalculator()
    errors = []
    success_count = 0
    warning_count = 0
    total_rows = 0

    try:
        csv_file = job.csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(csv_file))

        for row in reader:
            total_rows += 1
            try:
                name = row.get('name', '').strip()
                lat = float(row.get('latitude', 0))
                lon = float(row.get('longitude', 0))
                height = float(row.get('height_m', 30))

                if not name:
                    warning_count += 1
                    errors.append(f"Row {total_rows}: missing name, skipped")
                    continue

                point = Point(lon, lat, srid=4326)
                result = calculator.evaluate_property_all_airports(point, height)

                prop, created = Property.objects.get_or_create(
                    user=job.user, name=name,
                    defaults={'latitude': lat, 'longitude': lon, 'height_m': height}
                )
                if not created:
                    prop.latitude = lat
                    prop.longitude = lon
                    prop.height_m = height
                    prop.save(update_fields=['latitude', 'longitude', 'height_m'])

                ComplianceCheck.objects.create(
                    property=prop,
                    result_json=result,
                    status=result.get('status', 'UNKNOWN'),
                    score=result.get('compliance_score', 0),
                    primary_airport_icao=result.get('primary_airport', {}).get('icao', ''),
                    airports_affected=result.get('airports_affected_count', 0),
                    requires_lighting=result.get('requires_lighting', False),
                    is_hazard=result.get('is_hazard', False),
                    trigger='bulk',
                )
                success_count += 1

            except (ValueError, KeyError) as e:
                errors.append(f"Row {total_rows}: {str(e)}")
                warning_count += 1

        job.total_rows = total_rows
        job.processed_rows = total_rows
        job.success_count = success_count
        job.warning_count = warning_count
        job.error_count = len(errors) - warning_count
        job.error_log = '\n'.join(errors[-50:]) if errors else ''
        job.status = 'completed'
        job.completed_at = datetime.now()
        job.save()

        Notification.objects.create(
            user=job.user,
            notification_type='bulk_complete',
            title='Bulk upload complete',
            message=f'Processed {success_count}/{total_rows} properties successfully.',
            link='/bulk-upload/',
        )

    except Exception as e:
        job.status = 'failed'
        job.error_log = str(e)
        job.completed_at = datetime.now()
        job.save()


def generate_certificate_pdf(application):
    """Generate a PDF certificate for an approved ComplianceApplication."""
    html = render_to_string('obstacle_compliance/certificate_pdf.html', {
        'app': application,
        'property': application.property,
        'site_url': settings.SITE_URL,
    })
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('UTF-8')), dest=buffer)
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed: {pisa_status.err}")

    filename = f"certificate_{application.certificate_number}.pdf"
    from django.core.files.base import ContentFile
    application.certificate_pdf.save(filename, ContentFile(buffer.getvalue()))
    application.save(update_fields=['certificate_pdf'])
    return application.certificate_pdf.url if application.certificate_pdf else None


def send_notification_email(notification):
    """Send an email for a Notification if not already sent."""
    if notification.email_sent:
        return

    subject = f"KCAA OCS: {notification.title}"
    profile_url = f"{settings.SITE_URL}{reverse('obstacle_compliance:notification_list')}"
    message = f"{notification.message}\n\nView: {profile_url}"

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.user.email],
            fail_silently=True,
        )
        notification.email_sent = True
        notification.save(update_fields=['email_sent'])
    except Exception:
        pass
