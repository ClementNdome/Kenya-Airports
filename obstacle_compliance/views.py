# obstacle_compliance/views.py - Updated views

import csv
import json
import logging
import io
import hashlib
from datetime import datetime
from urllib.parse import quote

import requests
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count, Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.urls import reverse, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Aerodrome, AerodromeBuffer, UserProfile, Property, ComplianceCheck, Notification, ComplianceApplication, BulkUploadJob
from .utils import ComplianceCalculator, DEMService, ApplicationWorkflow
from obstacle_compliance import models

logger = logging.getLogger(__name__)
calculator = ComplianceCalculator()

# ============================================
# MAIN DASHBOARD VIEWS
# ============================================

class ObstacleComplianceDashboard(TemplateView):
    """
    Main dashboard view for the Obstacle Compliance tool
    """
    template_name = 'obstacle_compliance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics for the dashboard
        context['total_airports'] = Aerodrome.objects.count()
        
        # Get buffer stats with counts
        buffer_stats = {
            '3km': AerodromeBuffer.objects.filter(radius_km=3).count(),
            '5km': AerodromeBuffer.objects.filter(radius_km=5).count(),
            '10km': AerodromeBuffer.objects.filter(radius_km=10).count(),
            '15km': AerodromeBuffer.objects.filter(radius_km=15).count(),
        }
        context['buffer_stats'] = buffer_stats
        
        # Get recent airports with prefetch for efficiency
        context['recent_airports'] = Aerodrome.objects.all()[:5].select_related().prefetch_related('buffers')
        
        # Map configuration
        context['map_config'] = {
            'center': [-1.2864, 36.8172],  # Nairobi center
            'zoom': 7,  # Slightly zoomed out to show more of Kenya
            'max_zoom': 18,
            'min_zoom': 6,
            'default_radius': 15,
        }
        
        # Available basemap options
        context['basemaps'] = [
            {
                'id': 'osm',
                'name': 'OpenStreetMap',
                'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                'thumbnail': 'https://a.tile.openstreetmap.org/0/0/0.png'
            },
            {
                'id': 'satellite',
                'name': 'Satellite',
                'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attribution': '&copy; <a href="https://www.esri.com/">Esri</a>',
                'thumbnail': 'https://www.esri.com/content/dam/esrisites/en-us/home/imagery/imagery-world-imagery.jpg'
            },
            {
                'id': 'terrain',
                'name': 'Terrain',
                'url': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                'attribution': '&copy; <a href="https://opentopomap.org/">OpenTopoMap</a>',
                'thumbnail': 'https://opentopomap.org/resources/img/logo.png'
            },
            {
                'id': 'carto-light',
                'name': 'Carto Light',
                'url': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                'attribution': '&copy; <a href="https://www.carto.com/">CartoDB</a>',
                'thumbnail': 'https://carto.com/favicon.ico'
            },
            {
                'id': 'carto-dark',
                'name': 'Carto Dark',
                'url': 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                'attribution': '&copy; <a href="https://www.carto.com/">CartoDB</a>',
                'thumbnail': 'https://carto.com/favicon.ico'
            }
        ]
        
        return context

class AirportListView(ListView):
    """
    List all airports with filtering and search
    """
    model = Aerodrome
    template_name = 'obstacle_compliance/airport_list.html'
    context_object_name = 'airports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Aerodrome.objects.all().order_by('name')
        
        # Search functionality
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(icao_code__icontains=search) |
                Q(admin_company__icontains=search) |
                Q(type__icontains=search)
            )
        
        # Filter by type
        airport_type = self.request.GET.get('type', '')
        if airport_type:
            queryset = queryset.filter(type__icontains=airport_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        # context['airport_type'] = self.request.GET.get('type', '')
        # context['airport_types'] = Aerodrome.objects.values_list('type', flat=True).distinct().order_by('type')
        return context


class AirportDetailView(DetailView):
    """
    Detailed view for a single airport with buffer visualization
    """
    model = Aerodrome
    template_name = 'obstacle_compliance/airport_detail.html'
    context_object_name = 'airport'
    slug_field = 'icao_code'
    slug_url_kwarg = 'icao'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        airport = self.get_object()
        
        # Get all buffers for this airport
        buffers = AerodromeBuffer.objects.filter(aerodrome=airport).order_by('radius_km')
        context['buffers'] = buffers
        
        # Get buffer at specific radius if requested
        radius = self.request.GET.get('radius', 15)
        try:
            context['selected_buffer'] = buffers.get(radius_km=int(radius))
        except (AerodromeBuffer.DoesNotExist, ValueError):
            context['selected_buffer'] = buffers.filter(radius_km=15).first()
        
        # Count overlapping airports
        if context['selected_buffer']:
            overlapping = AerodromeBuffer.objects.filter(
                radius_km=15,
                geom__overlaps=context['selected_buffer'].geom
            ).exclude(aerodrome=airport).select_related('aerodrome')
            context['overlapping_airports'] = overlapping[:10]
            context['overlapping_count'] = overlapping.count()
        
        # Airport statistics
        context.update(self._get_airport_stats(airport))
        
        return context
    
    def _get_airport_stats(self, airport):
        """Calculate statistics for the airport"""
        # Get all properties in buffer (placeholder - will be implemented with property model later)
        return {
            'estimated_properties': 15000,  # Placeholder
            'counties_affected': self._get_counties_affected(airport),
            'runways': self._get_runway_info(airport),
        }
    # ================================================================================
    #to implement later when we have spatial data for counties and runways
    # ================================================================================

    
    # def _get_counties_affected(self, airport):
    #     """Get counties affected by this airport's 15km buffer"""
    #     # This would ideally come from spatial intersection with county boundaries
    #     # For now, return hardcoded based on airport location
    #     airport_counties = {
    #         'HKJK': ['Nairobi', 'Kajiado', 'Kiambu', 'Machakos'],
    #         'HKNW': ['Nairobi', 'Kajiado', 'Kiambu'],
    #         'HKMO': ['Mombasa', 'Kilifi', 'Kwale'],
    #         'HKKI': ['Kisumu', 'Vihiga', 'Kericho'],
    #         'HKEL': ['Uasin Gishu', 'Trans Nzoia', 'Nandi'],
    #     }
    #     return airport_counties.get(airport.icao_code, ['Nairobi County'])
    
    # def _get_runway_info(self, airport):
    #     """Get runway information (placeholder)"""
    #     # This would come from a Runway model in the future
    #     runways = {
    #         'HKJK': ['06/24 (4,117m)', '15/33 (4,267m)'],
    #         'HKNW': ['07/25 (1,459m)', '14/32 (1,126m)'],
    #         'HKMO': ['03/21 (3,350m)', '15/33 (1,463m)'],
    #     }
    #     return runways.get(airport.icao_code, ['Runway info not available'])


# ============================================
# PROPERTY COMPLIANCE VIEWS
# ============================================

class PropertyComplianceView(TemplateView):
    """
    View for checking property compliance
    """
    template_name = 'obstacle_compliance/property_check.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['default_height'] = 30
        context['map_config'] = {
            'center': [-1.2864, 36.8172],
            'zoom': 12,
        }
        return context


# obstacle_compliance/views.py - Enhanced Property Compliance API

class PropertyComplianceAPI(View):
    """
    Enhanced API endpoint for property compliance checks using DEM service
    """
    
    def get(self, request):
        """Handle GET request with query parameters"""
        try:
            # Get parameters
            lat = request.GET.get('lat')
            lon = request.GET.get('lon')
            height = request.GET.get('height', 30)
            
            if not lat or not lon:
                return JsonResponse({
                    'status': 'ERROR',
                    'message': 'Latitude and longitude are required'
                }, status=400)
            
            # Create point
            try:
                point = Point(float(lon), float(lat), srid=4326)
                height = float(height)
            except (ValueError, TypeError) as e:
                return JsonResponse({
                    'status': 'ERROR',
                    'message': f'Invalid coordinates or height: {str(e)}'
                }, status=400)
            
            # Optional parcel ring: "lat1,lon1|lat2,lon2|..." (closed polygon)
            parcel_str = request.GET.get('parcel')
            parcel_ring = None
            if parcel_str:
                try:
                    parcel_ring = [tuple(float(v) for v in pair.split(',')) for pair in parcel_str.split('|')]
                    if len(parcel_ring) < 3:
                        parcel_ring = None
                except (ValueError, TypeError):
                    parcel_ring = None

            # Check cache (parcel-aware so a point check never satisfies a
            # parcel check or vice versa)
            key_suffix = hashlib.md5((parcel_str or '').encode()).hexdigest()[:10] if parcel_str else 'point'
            cache_key = f"compliance_api_{lat}_{lon}_{height}_{key_suffix}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return JsonResponse(cached_result)
            
            # Evaluate compliance with full DEM context
            if parcel_ring:
                result = self._parcel_compliance_check(parcel_ring, height, point)
            else:
                result = self._enhanced_compliance_check(point, height)
            
            # Cache result
            cache.set(cache_key, result, 300)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in PropertyComplianceAPI: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'ERROR',
                'message': f'System error: {str(e)}'
            }, status=500)
    
    def _parcel_compliance_check(self, parcel_ring, height, centroid):
        """Evaluate a parcel polygon: densify the ring, check every vertex,
        aggregate the worst result across the whole parcel."""
        from .utils import densify_ring
        pts = densify_ring(list(parcel_ring), 50.0)
        if not pts:
            return self._enhanced_compliance_check(centroid, height)
        
        results = []
        for lat, lon in pts:
            p = Point(lon, lat, srid=4326)
            r = calculator.evaluate_property_all_airports(p, height)
            if r and r.get('status') not in (None, 'ERROR'):
                r['_point'] = [round(lat, 6), round(lon, 6)]
                results.append(r)
        
        if not results:
            return self._enhanced_compliance_check(centroid, height)
        
        status_priority = {'RED': 0, 'YELLOW': 1, 'GREEN': 2, 'WARNING': 3, 'ERROR': 4}
        worst = min(results, key=lambda r: status_priority.get(r.get('status'), 4))
        
        combined = {
            'status': worst.get('status'),
            'status_code': worst.get('status_code'),
            'message': worst.get('message'),
            'compliance_score': worst.get('compliance_score'),
            'is_hazard': worst.get('is_hazard'),
            'requires_lighting': any(r.get('requires_lighting') for r in results),
            'airports_affected': worst.get('airports_affected', []),
            'primary_airport': worst.get('primary_airport'),
            'primary_result': worst.get('primary_result'),
            'parcel_points_checked': len(results),
            'parcel_worst_point': worst.get('_point'),
            'parcel_mode': True,
            'dem_context': self._get_dem_context(centroid),
            'terrain_profile': self._get_terrain_profile(centroid),
            'visualization': self._generate_visualization_data(centroid, height, worst),
        }
        return combined
    
    def _enhanced_compliance_check(self, point, height):
        """Enhanced compliance check with full DEM context"""
        
        # Get base compliance result
        base_result = calculator.evaluate_property_all_airports(point, height)
        
        # Get detailed DEM information
        dem_info = self._get_dem_context(point)
        
        # Enhance the result with DEM context
        enhanced_result = {
            **base_result,
            'dem_context': dem_info,
            'terrain_profile': self._get_terrain_profile(point),
            'visualization': self._generate_visualization_data(point, height, base_result)
        }
        
        return enhanced_result
    
    def _get_dem_context(self, point):
        """Get detailed DEM context for a point"""
        
        # Get elevation with multiple samples for confidence
        elevations = []
        offsets = [(0,0), (0.001,0), (0,0.001), (-0.001,0), (0,-0.001)]
        
        for lon_off, lat_off in offsets:
            sample_point = Point(point.x + lon_off, point.y + lat_off, srid=4326)
            try:
                elev = calculator.dem.get_elevation(sample_point)
                if elev and elev > -500 and elev < 10000:  # Valid range
                    elevations.append(elev)
            except:
                continue
        
        if not elevations:
            return {
                'elevation': None,
                'confidence': 0,
                'source': 'No valid DEM data',
                'interpolation': 'Failed'
            }
        
        # Calculate statistics
        mean_elev = sum(elevations) / len(elevations)
        std_dev = (sum((e - mean_elev) ** 2 for e in elevations) / len(elevations)) ** 0.5
        
        # Determine confidence based on variance
        if std_dev < 1:
            confidence = 95  # High confidence
            quality = 'Excellent'
        elif std_dev < 3:
            confidence = 85  # Good confidence
            quality = 'Good'
        elif std_dev < 10:
            confidence = 70  # Moderate confidence
            quality = 'Fair'
        else:
            confidence = 50  # Low confidence
            quality = 'Poor - High terrain variability'
        
        return {
            'elevation': round(mean_elev, 1),
            'samples_taken': len(elevations),
            'std_deviation': round(std_dev, 2),
            'confidence': confidence,
            'quality': quality,
            'source': 'SRTM 30m DEM',
            'interpolation': 'Bilinear' if len(elevations) > 1 else 'Nearest neighbor',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_terrain_profile(self, point, distance=5000, directions=8):
        """
        Get terrain profile in multiple directions
        Useful for visualizing approach paths
        """
        profiles = []
        
        # Sample in multiple directions
        for angle in range(0, 360, 45):  # 8 directions
            import math
            rad = math.radians(angle)
            profile = []
            
            for dist in range(0, distance + 1, 100):  # Sample every 100m
                dx = dist * math.sin(rad) / 111000  # Approximate degree to meters
                dy = dist * math.cos(rad) / 111000
                
                sample_point = Point(point.x + dx, point.y + dy, srid=4326)
                elev = calculator.dem.get_elevation(sample_point)
                
                profile.append({
                    'distance': dist,
                    'elevation': elev,
                    'point': [sample_point.y, sample_point.x]
                })
            
            profiles.append({
                'direction': angle,
                'bearing': self._bearing_to_cardinal(angle),
                'profile': profile
            })
        
        return profiles
    
    def _bearing_to_cardinal(self, bearing):
        """Convert bearing to cardinal direction"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = round(bearing / 45) % 8
        return directions[index]
    
    def _generate_visualization_data(self, point, height, result):
        """Generate data for 3D visualization"""
        
        viz_data = {
            'point': [point.y, point.x],
            'ground_elevation': result.get('primary_result', {}).get('ground_elevation'),
            'building_top': result.get('primary_result', {}).get('building_top_amsl'),
            'affected_airports': []
        }
        
        # For each affected airport, generate OLS surface points
        for airport in result.get('airports_affected', []):
            # Get airport geometry
            try:
                airport_obj = Aerodrome.objects.get(icao_code=airport['icao'])
                
                # Generate OLS profile from airport to property
                profile = self._generate_ols_profile(airport_obj, point)
                
                viz_data['affected_airports'].append({
                    'icao': airport['icao'],
                    'name': airport['name'],
                    'profile': profile
                })
            except Aerodrome.DoesNotExist:
                continue
        
        return viz_data
    
    def _generate_ols_profile(self, airport, property_point):
        """Generate OLS surface profile between airport and property.
        Runway-aware: when the aerodrome has declared runway geometry the
        Annex 14 approach/strip/transitional ceilings replace the centroid
        approximation along the line."""
        
        # Calculate distance and bearing
        from geopy.distance import geodesic
        from .models import AerodromeRunway
        airport_point = airport.geom
        airport_elev = float(airport.elevation_m or 0)
        airport_coords = (airport_point.y, airport_point.x)
        property_coords = (property_point.y, property_point.x)
        
        total_distance = geodesic(airport_coords, property_coords).meters
        try:
            runway = AerodromeRunway.objects.filter(icao_code=airport.icao_code).first()
        except Exception:
            runway = None
        
        # Generate profile points
        profile = []
        for dist in range(0, int(total_distance) + 1, 100):
            # Calculate OLS ceiling at this distance
            ols_ceiling = calculator.calculate_ols_ceiling(airport_elev, dist)
            
            # Calculate point along line (simplified - would need proper interpolation)
            ratio = dist / total_distance
            lat = airport_point.y + (property_point.y - airport_point.y) * ratio
            lon = airport_point.x + (property_point.x - airport_point.x) * ratio
            
            # Get ground elevation at this point
            sample_point = Point(lon, lat, srid=4326)
            ground_elev = calculator.dem.get_elevation(sample_point)
            
            # Runway-based surfaces bind when they are lower than the centroid ceiling
            if runway is not None:
                try:
                    rc = calculator.calculate_runway_ceiling(sample_point, airport)
                except Exception:
                    rc = None
                if rc and rc.get('ceiling_amsl') is not None and (ols_ceiling is None or rc['ceiling_amsl'] < ols_ceiling):
                    ols_ceiling = rc['ceiling_amsl']
            
            profile.append({
                'distance': dist,
                'ols_ceiling': ols_ceiling,
                'ground_elevation': ground_elev,
                'clearance': ols_ceiling - ground_elev if ols_ceiling else None,
                'point': [lat, lon]
            })
        
        return profile

class BatchComplianceView(View):
    """
    View for batch compliance checking (multiple properties)
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            properties = data.get('properties', [])
            
            if not properties:
                return JsonResponse({
                    'status': 'ERROR',
                    'message': 'No properties provided'
                }, status=400)
            
            results = []
            for prop in properties[:100]:  # Limit to 100 properties
                try:
                    point = Point(float(prop['lon']), float(prop['lat']), srid=4326)
                    height = float(prop.get('height', 30))
                    
                    result = calculator.evaluate_property_all_airports(point, height)
                    result['id'] = prop.get('id', str(hash(f"{prop['lat']}{prop['lon']}")))
                    results.append(result)
                    
                except Exception as e:
                    results.append({
                        'id': prop.get('id', 'unknown'),
                        'status': 'ERROR',
                        'message': str(e)
                    })
            
            return JsonResponse({
                'status': 'SUCCESS',
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error in BatchComplianceView: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'ERROR',
                'message': str(e)
            }, status=500)


# ============================================
# MAP AND VISUALIZATION VIEWS
# ============================================

# obstacle_compliance/views.py - Update MapView class

# obstacle_compliance/views.py - Updated MapView class

class MapView(TemplateView):
    """
    Interactive map view with full capabilities:
    - Buffer visualization (3km, 5km, 10km, 15km)
    - Airport locations with details
    - Property compliance checking
    - Elevation data from DEM
    - Drawing tools for custom areas
    """
    template_name = 'obstacle_compliance/map_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active airport if specified
        icao = self.request.GET.get('airport')
        active_airport = None
        map_center = [-1.2864, 36.8172]  # Default: Nairobi
        map_zoom = 7
        
        if icao:
            try:
                active_airport = Aerodrome.objects.get(icao_code=icao.upper())
                map_center = [active_airport.geom.y, active_airport.geom.x]
                map_zoom = 12
                context['active_airport'] = active_airport
            except Aerodrome.DoesNotExist:
                logger.warning(f"Airport with ICAO code {icao} not found")
        
        # Get coordinates from query params (for property check)
        lat = self.request.GET.get('lat')
        lon = self.request.GET.get('lon')
        if lat and lon:
            try:
                context['initial_lat'] = float(lat)
                context['initial_lon'] = float(lon)
                map_center = [float(lat), float(lon)]
                map_zoom = 15
            except ValueError:
                pass
        
        context['map_config'] = {
            'center': map_center,
            'zoom': map_zoom,
            'max_zoom': 18,
            'min_zoom': 6,
            'default_radius': int(self.request.GET.get('radius', 15)),
        }
        
        # Get all airports for the airports list sidebar
        context['airports'] = Aerodrome.objects.all().order_by('name')[:50]
        context['total_airports'] = Aerodrome.objects.count()
        
        # Buffer statistics
        context['buffer_stats'] = {
            '3km': AerodromeBuffer.objects.filter(radius_km=3).count(),
            '5km': AerodromeBuffer.objects.filter(radius_km=5).count(),
            '10km': AerodromeBuffer.objects.filter(radius_km=10).count(),
            '15km': AerodromeBuffer.objects.filter(radius_km=15).count(),
        }
        
        # Available basemaps
        context['basemaps'] = [
            {
                'id': 'carto-light',
                'name': 'Carto Light',
                'url': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>, &copy; CartoDB',
                'thumbnail': '/static/obstacle_compliance/images/basemaps/carto-light.jpg'
            },
            {
                'id': 'satellite',
                'name': 'Satellite',
                'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attribution': '&copy; <a href="https://www.esri.com/">Esri</a>',
                'thumbnail': '/static/obstacle_compliance/images/basemaps/satellite.jpg'
            },
            {
                'id': 'terrain',
                'name': 'Terrain',
                'url': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                'attribution': '&copy; <a href="https://opentopomap.org/">OpenTopoMap</a>',
                'thumbnail': '/static/obstacle_compliance/images/basemaps/terrain.jpg'
            },
            {
                'id': 'osm',
                'name': 'OpenStreetMap',
                'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                'thumbnail': '/static/obstacle_compliance/images/basemaps/osm.jpg'
            }
        ]
        
        return context


from django.contrib.gis.db.models.functions import Transform
# from django.contrib.gis.db.models.functions import Buffer as GISBuffer

from django.contrib.gis.db.models.functions import GeoFunc

GISBuffer = GeoFunc

# Or try:
# from django.contrib.gis.db.models.functions import Transform
# from django.contrib.gis.db.models.functions import GeomFunc
# from .models import Aerodrome, AerodromeBuffer
import json

class BufferGeoJSONView(View):
    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        try:
            radius_str = request.GET.get('radius', '15')
            radius = int(float(radius_str))  # supports 7 or 7.5 (floors safely)
            if radius < 1:
                radius = 1
            if radius > 100:
                radius = 100

            icao = request.GET.get('icao')

            # === ENSURE BUFFERS EXIST (only creates missing ones, once ever) ===
            if icao:
                try:
                    ad = Aerodrome.objects.get(icao_code=icao.upper())
                    ad.get_or_create_buffer(radius)
                except Aerodrome.DoesNotExist:
                    pass
            else:
                # Bulk-create only what's missing (extremely fast after first time)
                missing = Aerodrome.objects.exclude(buffers__radius_km=radius)
                for ad in missing:
                    ad.get_or_create_buffer(radius)

            # === NOW JUST QUERY THE DB (always fast) ===
            buffers_qs = AerodromeBuffer.objects.filter(
                radius_km=radius
            ).select_related('aerodrome')

            if icao:
                buffers_qs = buffers_qs.filter(aerodrome__icao_code=icao.upper())

            features = []
            for buf in buffers_qs[:100]:
                features.append(self._format_feature(
                    buf.geom.geojson,
                    buf.aerodrome,
                    buf.radius_km,
                    buf.area_km2,
                    buf.id
                ))

            return JsonResponse({
                'type': 'FeatureCollection',
                'features': features,
                'metadata': {
                    'count': len(features),
                    'radius': radius,
                    'icao_filter': icao
                }
            })

        except Exception as e:
            logger.error(f"BufferGeoJSONView error: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)

    def _format_feature(self, geom_json, aerodrome, radius, area, feature_id):
        """Unchanged - exactly as you had it"""
        color = self._get_color_for_radius(radius)
        return {
            'type': 'Feature',
            'geometry': json.loads(geom_json),
            'properties': {
                'id': feature_id,
                'airport_icao': aerodrome.icao_code,
                'airport_name': aerodrome.name or aerodrome.admin_company,
                'radius_km': radius,
                'area_km2': round(area, 2) if area else None,
                'stroke': color,
                'fill': color,
                'fill-opacity': 0.15,
            }
        }

    def _get_color_for_radius(self, radius):
        colors = {3: '#FF6B6B', 5: '#FFA500', 10: '#2196F3', 15: '#4CAF50'}
        return colors.get(radius, '#9C27B0')  # purple for any custom radius

# obstacle_compliance/views.py - Update AirportGeoJSONView

class AirportGeoJSONView(View):
    """
    Return airport points as GeoJSON for mapping with enhanced properties
    """
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request):
        try:
            # Get optional filter
            icao = request.GET.get('icao')
            
            airports = Aerodrome.objects.all()
            if icao:
                airports = airports.filter(icao_code=icao.upper())
            
            features = []
            for airport in airports:
                try:
                    if not airport.geom:
                        continue
                        
                    geom_json = json.loads(airport.geom.geojson)
                    
                    # Parse elevation display
                    if airport.elevation_m:
                        elevation_display = f"{airport.elevation_m:.0f}m"
                    elif airport.elevation_m_ft:
                        elevation_display = airport.elevation_m_ft
                    else:
                        elevation_display = "N/A"
                    
                    feature = {
                        'type': 'Feature',
                        'geometry': geom_json,
                        'properties': {
                            'id': airport.fid,
                            'icao': airport.icao_code,
                            'name': airport.name or airport.admin_company or airport.icao_code,
                            'type': airport.type or 'Unknown',
                            'elevation': airport.elevation_m,
                            'elevation_display': elevation_display,
                            'admin_company': airport.admin_company,
                            'traffic_permitted': airport.traffic_permitted or 'Unknown',
                            'has_buffer_3km': airport.buffers.filter(radius_km=3).exists(),
                            'has_buffer_5km': airport.buffers.filter(radius_km=5).exists(),
                            'has_buffer_10km': airport.buffers.filter(radius_km=10).exists(),
                            'has_buffer_15km': airport.buffers.filter(radius_km=15).exists(),
                            'marker_color': self._get_marker_color(airport.type),
                            'marker_size': 'medium',
                            'marker_symbol': 'airport',
                        }
                    }
                    features.append(feature)
                    
                except Exception as e:
                    logger.error(f"Error processing airport {airport.icao_code}: {e}")
                    continue
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features,
                'metadata': {
                    'count': len(features),
                    'icao_filter': icao
                }
            }
            
            return JsonResponse(geojson)
            
        except Exception as e:
            logger.error(f"Error in AirportGeoJSONView: {str(e)}", exc_info=True)
            return JsonResponse({
                'type': 'FeatureCollection',
                'features': []
            })
    
    def _get_marker_color(self, airport_type):
        """Get marker color based on airport type"""
        airport_type = (airport_type or '').lower()
        
        if 'international' in airport_type:
            return '#dc3545'  # Red for international
        elif 'domestic' in airport_type or 'national' in airport_type:
            return '#0d6efd'  # Blue for domestic
        elif 'military' in airport_type or 'air force' in airport_type:
            return '#198754'  # Green for military
        elif 'airstrip' in airport_type or 'private' in airport_type:
            return '#ffc107'  # Yellow for small airstrips
        else:
            return '#6c757d'  # Gray for unknown# ============================================
# SEARCH AND AUTOCOMPLETE VIEWS
# ============================================

class SearchView(View):
    """
    Search for airports, locations, or properties
    """
    def get(self, request):
        query = request.GET.get('q', '')
        search_type = request.GET.get('type', 'all')
        
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        results = []
        
        # Search airports
        if search_type in ['all', 'airports']:
            airports = Aerodrome.objects.filter(
                Q(name__icontains=query) |
                Q(icao_code__icontains=query) |
                Q(admin_company__icontains=query)
            )[:10]
            
            for airport in airports:
                results.append({
                    'id': f"airport_{airport.icao_code}",
                    'type': 'airport',
                    'text': f"{airport.name or airport.admin_company} ({airport.icao_code})",
                    'url': reverse('obstacle_compliance:airport_detail', args=[airport.icao_code]),
                    'coordinates': [airport.geom.y, airport.geom.x]
                })
        
        # TODO: Add location search using geocoding service
        
        return JsonResponse({'results': results})


class GeocodeView(View):
    """
    Geocode an address to lat/lon using the Mapbox Geocoding API,
    falling back to OpenStreetMap Nominatim when Mapbox is unavailable.
    GET /api/geocode/?address=Nairobi
    """
    MAPBOX_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json'
    MAPBOX_TYPES = 'address,place,locality,neighborhood,district,region,poi'
    NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
    USER_AGENT = 'KCAAObstacleCompliance/1.0'
    CACHE_DURATION = 86400
    EMPTY_CACHE_DURATION = 3600
    KENYA_BBOX = '33.9,-4.7,41.9,5.5'  # lon_min,lat_min,lon_max,lat_max

    def get(self, request):
        address = request.GET.get('address', '').strip()
        if not address:
            return JsonResponse({'error': 'Address parameter is required'}, status=400)

        cache_key = f'geocode_{hashlib.md5(address.lower().encode()).hexdigest()}'
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse(cached)

        # Query both providers and merge: Nominatim is strong on Kenyan POIs
        # (Wilson, JKIA, ...), Mapbox fills in towns, estates and addresses.
        nominatim_results = self._geocode_nominatim(address)
        mapbox_results = self._geocode_mapbox(address)

        if nominatim_results is None and mapbox_results is None:
            return JsonResponse({'error': 'Geocoding service unavailable'}, status=503)

        suggestions = self._merge_results(nominatim_results, mapbox_results)
        source = ','.join(name for name, lst in (('nominatim', nominatim_results), ('mapbox', mapbox_results)) if lst)

        response_data = {'results': suggestions, 'source': source}
        if suggestions:
            cache.set(cache_key, response_data, self.CACHE_DURATION)
        else:
            cache.set(cache_key, response_data, self.EMPTY_CACHE_DURATION)
        return JsonResponse(response_data)

    def _geocode_mapbox(self, address):
        """Geocode using Mapbox. Returns a normalized list or None on failure."""
        token = getattr(settings, 'MAPBOX_ACCESS_TOKEN', '')
        if not token:
            return None

        try:
            resp = requests.get(
                self.MAPBOX_URL.format(query=quote(address)),
                params={
                    'access_token': token,
                    'country': 'ke',
                    'autocomplete': 'true',
                    'limit': 10,
                    'types': self.MAPBOX_TYPES,
                    'language': 'en',
                },
                timeout=10,
            )
            resp.raise_for_status()
            features = resp.json().get('features', [])

            suggestions = []
            for f in features:
                center = f.get('center') or [0, 0]
                suggestions.append({
                    'lat': float(center[1]),
                    'lon': float(center[0]),
                    'display_name': f.get('place_name', ''),
                    'text': f.get('text', ''),
                    'type': (f.get('place_type') or ['place'])[0],
                })
            return suggestions

        except requests.RequestException as e:
            logger.error(f"Mapbox geocoding error: {e}")
            return None

    def _geocode_nominatim(self, address):
        """Geocode using OpenStreetMap Nominatim. Returns a normalized list or None on failure."""
        params = {
            'q': address,
            'format': 'json',
            'limit': 10,
            'addressdetails': 1,
            'countrycodes': 'ke',
            'viewbox': self.KENYA_BBOX,
            'bounded': 1,
        }
        headers = {'User-Agent': self.USER_AGENT}

        try:
            resp = requests.get(self.NOMINATIM_URL, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            results = resp.json()

            suggestions = []
            for r in results:
                display = self._compact_nominatim_name(r)
                suggestions.append({
                    'lat': float(r['lat']),
                    'lon': float(r['lon']),
                    'display_name': display,
                    'text': display,
                    'type': r.get('type', ''),
                })
            return suggestions

        except requests.RequestException as e:
            logger.error(f"Geocoding error: {e}")
            return None

    @staticmethod
    def _compact_nominatim_name(r):
        """Build a short readable label: POI/building name, then admin area."""
        ad = r.get('address') or {}

        def first(*keys):
            for k in keys:
                if ad.get(k):
                    return ad[k]
            return None

        name = r.get('name') or first(
            'aerodrome', 'attraction', 'building', 'hotel', 'road',
            'suburb', 'city', 'town', 'village', 'county', 'state', 'region', 'country')
        region = first('county', 'state', 'region')
        country = ad.get('country')
        parts = [p for p in (name, region, country) if p]
        seen = []
        out = []
        for p in parts:
            if p.lower() in seen:
                continue
            seen.append(p.lower())
            out.append(p)
        return ', '.join(out)

    @staticmethod
    def _merge_results(*lists):
        """Merge provider results, deduplicating by rounded coordinates."""
        seen = set()
        merged = []
        for results in lists:
            if not results:
                continue
            for r in results:
                key = (round(r['lat'], 3), round(r['lon'], 3))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(r)
                if len(merged) >= 10:
                    break
            if len(merged) >= 10:
                break
        return merged


class ReverseGeocodeView(View):
    """
    Reverse geocode lat/lon to address using the Mapbox Geocoding API,
    falling back to OpenStreetMap Nominatim when Mapbox is unavailable.
    GET /api/reverse-geocode/?lat=-1.2864&lon=36.8172
    """
    MAPBOX_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json'
    NOMINATIM_URL = 'https://nominatim.openstreetmap.org/reverse'
    USER_AGENT = 'KCAAObstacleCompliance/1.0'
    CACHE_DURATION = 86400

    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Valid lat and lon parameters required'}, status=400)

        cache_key = f'revgeo_{lat:.4f}_{lon:.4f}'
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        result = self._reverse_mapbox(lat, lon)
        if result is None:
            result = self._reverse_nominatim(lat, lon)

        if result is None:
            return JsonResponse({'error': 'Geocoding service unavailable'}, status=503)

        cache.set(cache_key, result, self.CACHE_DURATION)
        return JsonResponse(result)

    def _reverse_mapbox(self, lat, lon):
        """Reverse geocode using Mapbox. Returns a normalized dict or None on failure."""
        token = getattr(settings, 'MAPBOX_ACCESS_TOKEN', '')
        if not token:
            return None

        try:
            resp = requests.get(
                self.MAPBOX_URL.format(lon=lon, lat=lat),
                params={'access_token': token, 'language': 'en', 'limit': 1},
                timeout=10,
            )
            resp.raise_for_status()
            features = resp.json().get('features', [])
            if not features:
                return {'display_name': '', 'address': {}, 'lat': lat, 'lon': lon}

            f = features[0]
            address = {}
            for ctx in f.get('context', []):
                cid = ctx.get('id', '')
                key = cid.split('.')[0] if '.' in cid else 'context'
                address[key] = ctx.get('text', '')

            return {
                'display_name': f.get('place_name', ''),
                'address': address,
                'lat': lat,
                'lon': lon,
            }

        except requests.RequestException as e:
            logger.error(f"Mapbox reverse geocoding error: {e}")
            return None

    def _reverse_nominatim(self, lat, lon):
        """Reverse geocode using OpenStreetMap Nominatim. Returns a normalized dict or None on failure."""
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
        }
        headers = {'User-Agent': self.USER_AGENT}

        try:
            resp = requests.get(self.NOMINATIM_URL, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            return {
                'display_name': data.get('display_name', ''),
                'address': data.get('address', {}),
                'lat': float(data['lat']),
                'lon': float(data['lon']),
            }

        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f"Reverse geocoding error: {e}")
            return None


# ============================================
# PORTED AIRPORTS_STRIPS VIEWS (Data Unification)
# ============================================

from django.contrib.gis.db.models.functions import Distance
from geopy.distance import geodesic


class AirportsNearEquatorAPI(View):
    """Airports within ~50km of the equator."""
    def get(self, request):
        airports = Aerodrome.objects.filter(
            geom__y__gte=-0.45, geom__y__lte=0.45
        ).values('icao_code', 'name', 'geom')
        data = []
        for a in airports:
            data.append({
                'icao_code': a['icao_code'],
                'name': a['name'],
                'latitude': a['geom'].y if a['geom'] else None,
                'longitude': a['geom'].x if a['geom'] else None,
            })
        return JsonResponse({'airports': data, 'count': len(data)})


class AirportsWithinRadiusAPI(View):
    """Airports within a given radius of a point. GET /api/airports/within-radius/?lat=...&lon=...&radius=50000"""
    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
            radius_m = float(request.GET.get('radius', 50000))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Valid lat, lon, and optional radius required'}, status=400)

        point = Point(lon, lat, srid=4326)
        airports = Aerodrome.objects.annotate(
            dist=Distance('geom', point)
        ).filter(dist__lte=radius_m).order_by('dist')

        data = [{
            'icao_code': a.icao_code,
            'name': a.name,
            'distance_m': round(a.dist.m, 1),
            'distance_km': round(a.dist.m / 1000, 2),
        } for a in airports]
        return JsonResponse({'airports': data, 'count': len(data)})


class NearestAirportAPI(View):
    """Nearest aerodrome to a point. GET /api/airports/nearest/?lat=...&lon=..."""
    def get(self, request):
        try:
            lat = float(request.GET.get('lat'))
            lon = float(request.GET.get('lon'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Valid lat and lon required'}, status=400)

        point = Point(lon, lat, srid=4326)
        nearest = Aerodrome.objects.annotate(
            dist=Distance('geom', point)
        ).order_by('dist').first()

        if not nearest:
            return JsonResponse({'error': 'No airports found'}, status=404)

        dist_km = geodesic((lat, lon), (nearest.geom.y, nearest.geom.x)).kilometers
        return JsonResponse({
            'icao_code': nearest.icao_code,
            'name': nearest.name,
            'distance_km': round(dist_km, 2),
            'latitude': nearest.geom.y,
            'longitude': nearest.geom.x,
        })


class DistanceBetweenAirportsAPI(View):
    """Distance between two aerodromes by ICAO."""
    def get(self, request):
        icao1 = request.GET.get('airport1', '').upper()
        icao2 = request.GET.get('airport2', '').upper()
        if not icao1 or not icao2:
            return JsonResponse({'error': 'airport1 and airport2 ICAO codes required'}, status=400)

        try:
            a1 = Aerodrome.objects.get(icao_code=icao1)
            a2 = Aerodrome.objects.get(icao_code=icao2)
        except Aerodrome.DoesNotExist:
            return JsonResponse({'error': 'One or both airports not found'}, status=404)

        if not a1.geom or not a2.geom:
            return JsonResponse({'error': 'Coordinate data missing for one or both airports'}, status=400)

        dist_km = geodesic((a1.geom.y, a1.geom.x), (a2.geom.y, a2.geom.x)).kilometers
        return JsonResponse({
            'airport1': {'icao_code': a1.icao_code, 'name': a1.name},
            'airport2': {'icao_code': a2.icao_code, 'name': a2.name},
            'distance_km': round(dist_km, 2),
        })


# ============================================
# AUTHENTICATION VIEWS (Feature 1)
# ============================================

class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('obstacle_compliance:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Account'
        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'registration/profile.html'
    fields = ['company', 'phone', 'organization_type']
    success_url = reverse_lazy('obstacle_compliance:profile')

    def get_object(self, queryset=None):
        return self.request.user.profile


# ============================================
# PROPERTY PORTFOLIO VIEWS (Feature 1)
# ============================================

class PropertyListView(LoginRequiredMixin, ListView):
    model = Property
    template_name = 'obstacle_compliance/property_list.html'
    context_object_name = 'properties'
    paginate_by = 20

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user, is_active=True)


class PropertyCreateView(LoginRequiredMixin, CreateView):
    model = Property
    template_name = 'obstacle_compliance/property_form.html'
    fields = ['name', 'address', 'latitude', 'longitude', 'height_m', 'notes']
    success_url = reverse_lazy('obstacle_compliance:property_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PropertyDetailView(LoginRequiredMixin, DetailView):
    model = Property
    template_name = 'obstacle_compliance/property_detail.html'

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_checks'] = self.object.checks.all()[:10]
        return context


class PropertyUpdateView(LoginRequiredMixin, UpdateView):
    model = Property
    template_name = 'obstacle_compliance/property_form.html'
    fields = ['name', 'address', 'latitude', 'longitude', 'height_m', 'notes']
    success_url = reverse_lazy('obstacle_compliance:property_list')

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user)


class PropertyDeleteView(LoginRequiredMixin, DeleteView):
    model = Property
    template_name = 'obstacle_compliance/property_confirm_delete.html'
    success_url = reverse_lazy('obstacle_compliance:property_list')

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user)


class PropertyCheckView(LoginRequiredMixin, View):
    """Run compliance check on a saved property."""

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk, user=request.user)
        check = prop.run_compliance_check()

        return JsonResponse({
            'status': check.status,
            'score': check.score,
            'checked_at': check.checked_at.isoformat(),
            'detail_url': reverse('obstacle_compliance:property_detail', args=[prop.pk]),
        })


class SavePropertyFromCheckView(LoginRequiredMixin, View):
    """Save from quick-check form results."""

    def post(self, request):
        try:
            from django.contrib.gis.geos import MultiPolygon, Polygon
            data = json.loads(request.body)
            lat = float(data['lat'])
            lon = float(data['lon'])
            # Optional parcel ring: [[lat, lon], [lat, lon], ...]
            parcel_geom = None
            parcel_ring = data.get('parcel') or []
            if isinstance(parcel_ring, list) and len(parcel_ring) >= 3:
                ring = [(float(p[1]), float(p[0])) for p in parcel_ring]
                if ring[0] != ring[-1]:
                    ring.append(ring[0])
                if len(ring) >= 4:
                    try:
                        parcel_geom = MultiPolygon([Polygon(ring)])
                    except Exception:
                        parcel_geom = None
            prop = Property.objects.create(
                user=request.user,
                name=data.get('name', f"Property @ {lat:.4f}, {lon:.4f}"),
                latitude=lat,
                longitude=lon,
                geom=Point(lon, lat, srid=4326),
                parcel_boundary=parcel_geom,
                height_m=float(data.get('height', 30)),
                address=data.get('address', ''),
            )
            return JsonResponse({'id': prop.pk, 'name': prop.name, 'status': 'created', 'has_parcel': parcel_geom is not None})
        except (KeyError, ValueError, TypeError) as e:
            return JsonResponse({'error': str(e)}, status=400)


# ============================================
# PUBLIC PROPERTY QUERY TOOL
# ============================================

class PropertyQueryPageView(TemplateView):
    """Public read-only browser for saved compliance checks."""

    template_name = 'obstacle_compliance/property_query.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['aerodromes'] = Aerodrome.objects.filter(
            icao_code__isnull=False
        ).exclude(icao_code='').order_by('icao_code')[:200]
        ctx['status_choices'] = ['GREEN', 'YELLOW', 'RED']
        ctx['total_properties'] = Property.objects.filter(is_active=True).count()
        return ctx


class PropertyQueryAPI(View):
    """Public read-only spatial query over saved properties.
    Filters: icao + radius_km around ARP (or lat/lon center),
    min/max height, last status. Sorted by height desc."""

    def get(self, request):
        try:
            qs = Property.objects.filter(is_active=True).select_related('user')
            
            icao = (request.GET.get('icao') or '').strip().upper()
            center = None
            if icao:
                ad = Aerodrome.objects.filter(icao_code=icao).first()
                if ad is None or ad.geom is None:
                    return JsonResponse({'error': 'Aerodrome not found'}, status=404)
                center = Point(ad.geom.x, ad.geom.y, srid=4326)
            else:
                try:
                    lat = float(request.GET.get('lat') or '')
                    lon = float(request.GET.get('lon') or '')
                    center = Point(lon, lat, srid=4326)
                except (TypeError, ValueError):
                    pass
            
            try:
                radius_km = float(request.GET.get('radius_km') or 50)
            except (TypeError, ValueError):
                radius_km = 50.0
            radius_km = max(1.0, min(radius_km, 200.0))
            
            if center is not None and qs.exists():
                qs = qs.filter(geom__distance_lte=(center, D(km=radius_km)))
            
            min_h = request.GET.get('min_height')
            if min_h:
                try:
                    qs = qs.filter(height_m__gte=float(min_h))
                except (TypeError, ValueError):
                    pass
            max_h = request.GET.get('max_height')
            if max_h:
                try:
                    qs = qs.filter(height_m__lte=float(max_h))
                except (TypeError, ValueError):
                    pass
            
            status = (request.GET.get('status') or '').strip().upper()
            if status in ('GREEN', 'YELLOW', 'RED'):
                qs = qs.filter(last_status=status)
            
            try:
                limit = min(max(int(request.GET.get('limit') or 500), 1), 1000)
            except (TypeError, ValueError):
                limit = 500
            
            results = []
            for p in qs.order_by('-height_m')[:limit]:
                dist_km = None
                if center is not None and p.geom is not None:
                    try:
                        dist_km = round(calculator.calculate_distance(center, p.geom) / 1000.0, 2)
                    except Exception:
                        dist_km = None
                results.append({
                    'id': p.pk,
                    'name': p.name,
                    'address': p.address or '',
                    'user': p.user.username if p.user else None,
                    'lat': p.latitude,
                    'lon': p.longitude,
                    'height_m': p.height_m,
                    'status': p.last_status,
                    'score': p.last_score,
                    'checked_at': p.last_checked.isoformat() if p.last_checked else None,
                    'distance_km': dist_km,
                })
            
            return JsonResponse({
                'count': len(results),
                'icao': icao or None,
                'center': [center.y, center.x] if center is not None else None,
                'radius_km': radius_km,
                'results': results,
            })
        except Exception as e:
            logger.error(f"PropertyQueryAPI error: {e}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# ============================================
# REPORT AND EXPORT VIEWS
# ============================================

@method_decorator(csrf_exempt, name='dispatch')
class ComplianceReportView(View):
    """
    Generate a professional PDF report for a property compliance check
    """
    def post(self, request):
        try:
            data = json.loads(request.body)
            lat = data.get('lat')
            lon = data.get('lon')
            height = data.get('height', 30)

            if not lat or not lon:
                return JsonResponse({'error': 'Coordinates required'}, status=400)

            # 1. Calculate Compliance Data
            point = Point(float(lon), float(lat), srid=4326)
            result = calculator.evaluate_property_all_airports(point, float(height))

            # 2. Prepare Template Context
            context = {
                'generated_at': datetime.now(),
                'property': {
                    'latitude': lat,
                    'longitude': lon,
                    'height': height,
                },
                'compliance': result,
                'status_color': {'RED': '#dc3545', 'YELLOW': '#ffc107', 'GREEN': '#28a745'}.get(result.get('status'), '#28a745'),
                'disclaimer': 'This report is generated for informational purposes only. '
                              'Official approval must be obtained from KCAA before construction.'
            }

            # 3. Render HTML to String
            html_string = render_to_string('obstacle_compliance/pdf_report_template.html', context) # the html file is to be created in the templates/obstacle_compliance/ directory with appropriate styling for PDF output
            
            # 4. Create PDF
            result_file = io.BytesIO()
            pisa_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=result_file)

            if pisa_status.err:
                return JsonResponse({'error': 'PDF generation failed'}, status=500)

            # 5. Return PDF as Downloadable Response
            result_file.seek(0)
            response = HttpResponse(result_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="KCAA_Compliance_{lat}_{lon}.pdf"'
            return response

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# ============================================
# STATISTICS AND ANALYTICS VIEWS
# ============================================

class StatisticsView(View):
    """
    Get system statistics and analytics
    """
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def get(self, request):
        try:
            stats = {
                'airports': {
                    'total': Aerodrome.objects.count(),
                    'by_type': dict(Aerodrome.objects.values_list('type').annotate(count=Count('type'))),
                },
                'buffers': {
                    'total': AerodromeBuffer.objects.count(),
                    'by_radius': dict(AerodromeBuffer.objects.values_list('radius_km').annotate(count=Count('id'))),
                },
                'coverage': {
                    'total_area_km2': round(sum(AerodromeBuffer.objects.filter(
                        radius_km=15
                    ).values_list('area_km2', flat=True)), 2),
                }
            }
            
            return JsonResponse(stats)
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


# ============================================
# ERROR HANDLING VIEWS
# ============================================

def handler404(request, exception):
    """Custom 404 handler"""
    return render(request, 'obstacle_compliance/404.html', status=404)


def handler500(request):
    """Custom 500 handler"""
    return render(request, 'obstacle_compliance/500.html', status=500)


# Add this temporarily for debugging
from django.http import HttpResponse

def debug_geojson(request):
    """Debug endpoint to check GeoJSON data"""
    try:
        airports_count = Aerodrome.objects.count()
        buffers_count = AerodromeBuffer.objects.count()
        
        sample_airport = Aerodrome.objects.first()
        sample_buffer = AerodromeBuffer.objects.first()
        
        return HttpResponse(f"""
            <h1>GeoJSON Debug Info</h1>
            <ul>
                <li>Airports: {airports_count}</li>
                <li>Buffers: {buffers_count}</li>
                <li>Sample Airport: {sample_airport.icao_code if sample_airport else 'None'}</li>
                <li>Sample Buffer: {sample_buffer.id if sample_buffer else 'None'}</li>
            </ul>
            <h2>Test Links:</h2>
            <ul>
                <li><a href="/obstacle-compliance/api/airports.geojson">Airports GeoJSON</a></li>
                <li><a href="/obstacle-compliance/api/buffers.geojson?radius=15">Buffers GeoJSON (15km)</a></li>
            </ul>
        """)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")


# ============================================
# NOTIFICATION VIEWS (Feature 7)
# ============================================

@method_decorator(login_required, name='dispatch')
class NotificationListView(ListView):
    model = Notification
    template_name = 'obstacle_compliance/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class NotificationMarkReadView(View):
    def post(self, request):
        ids = request.POST.getlist('ids')
        Notification.objects.filter(pk__in=ids, user=request.user).update(is_read=True)
        return JsonResponse({'ok': True})

    def get(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return redirect('obstacle_compliance:notification_list')


@method_decorator(login_required, name='dispatch')
class UnreadCountView(View):
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'count': count})


# ============================================
# COMPLIANCE APPLICATION VIEWS (Feature 2)
# ============================================

@method_decorator(login_required, name='dispatch')
class ApplicationListView(ListView):
    model = ComplianceApplication
    template_name = 'obstacle_compliance/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        qs = ComplianceApplication.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


@method_decorator(login_required, name='dispatch')
class ApplicationCreateView(CreateView):
    model = ComplianceApplication
    template_name = 'obstacle_compliance/application_form.html'
    fields = ['property', 'fee_paid']

    def get_form(self):
        form = super().get_form()
        form.fields['property'].queryset = Property.objects.filter(user=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        Notification.objects.create(
            user=self.request.user,
            notification_type='application_update',
            title='Application created',
            message=f'Compliance application #{self.object.pk} has been created.',
            link=reverse('obstacle_compliance:application_detail', args=[self.object.pk]),
        )
        return response

    def get_success_url(self):
        return reverse('obstacle_compliance:application_detail', args=[self.object.pk])


@method_decorator(login_required, name='dispatch')
class ApplicationDetailView(DetailView):
    model = ComplianceApplication
    template_name = 'obstacle_compliance/application_detail.html'
    context_object_name = 'application'

    def get_queryset(self):
        return ComplianceApplication.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class ApplicationSubmitView(View):
    def post(self, request, pk):
        app = get_object_or_404(ComplianceApplication, pk=pk, user=request.user)
        try:
            ApplicationWorkflow.transition(app, 'submitted')
            messages.success(request, f'Application #{app.pk} submitted for review.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('obstacle_compliance:application_detail', pk=pk)


# ============================================
# BULK UPLOAD VIEWS (Feature 3)
# ============================================

@method_decorator(login_required, name='dispatch')
class BulkUploadListView(ListView):
    model = BulkUploadJob
    template_name = 'obstacle_compliance/bulk_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        return BulkUploadJob.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class BulkUploadCreateView(CreateView):
    model = BulkUploadJob
    template_name = 'obstacle_compliance/bulk_form.html'
    fields = ['csv_file']

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Bulk upload job queued. Processing will begin shortly.')
        return response

    def get_success_url(self):
        return reverse('obstacle_compliance:bulk_list')


@method_decorator(login_required, name='dispatch')
class BulkUploadDetailView(DetailView):
    model = BulkUploadJob
    template_name = 'obstacle_compliance/bulk_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return BulkUploadJob.objects.filter(user=self.request.user)


# ============================================
# ANALYTICS DASHBOARD (Feature 5)
# ============================================

@method_decorator(login_required, name='dispatch')
class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'obstacle_compliance/analytics.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        total_properties = Property.objects.filter(user=user).count()
        recent_checks = ComplianceCheck.objects.filter(property__user=user)[:5]
        status_counts = ComplianceCheck.objects.filter(property__user=user)\
            .values('status').annotate(count=Count('id'))
        app_counts = ComplianceApplication.objects.filter(user=user)\
            .values('status').annotate(count=Count('id'))
        total_applications = ComplianceApplication.objects.filter(user=user).count()

        aerodromes_total = Aerodrome.objects.count()
        aerodromes_by_type = Aerodrome.objects.values('type').annotate(count=Count('id'))

        ctx.update({
            'total_properties': total_properties,
            'recent_checks': recent_checks,
            'status_counts': list(status_counts),
            'app_counts': list(app_counts),
            'total_applications': total_applications,
            'aerodromes_total': aerodromes_total,
            'aerodromes_by_type': list(aerodromes_by_type),
        })
        return ctx


# ============================================
# PERSONALIZED USER DASHBOARD (overrides generic)
# ============================================

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'obstacle_compliance/user_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        properties = Property.objects.filter(user=user, is_active=True)
        total_props = properties.count()
        safe_props = properties.filter(last_status='GREEN').count()
        warning_props = properties.filter(last_status='YELLOW').count()
        hazard_props = properties.filter(last_status='RED').count()

        recent_checks = ComplianceCheck.objects.filter(property__user=user).order_by('-checked_at')[:10]
        unread_notifications = Notification.objects.filter(user=user, is_read=False)[:5]
        recent_apps = ComplianceApplication.objects.filter(user=user)[:5]
        pending_apps = ComplianceApplication.objects.filter(user=user, status__in=['submitted', 'under_review']).count()

        # QS for status counts chart
        status_qs = ComplianceCheck.objects.filter(property__user=user).values('status').annotate(count=Count('id'))
        status_labels = [s['status'] for s in status_qs]
        status_data = [s['count'] for s in status_qs]

        ctx.update({
            'total_properties': total_props,
            'safe_properties': safe_props,
            'warning_properties': warning_props,
            'hazard_properties': hazard_props,
            'recent_checks': recent_checks,
            'unread_notifications': unread_notifications,
            'recent_apps': recent_apps,
            'pending_apps': pending_apps,
            'properties': properties[:5],
            'status_labels': status_labels,
            'status_data': status_data,
        })
        return ctx


# ============================================
# KCAA ADMIN REVIEW DASHBOARD (Feature 2 gap)
# ============================================

@method_decorator(login_required, name='dispatch')
class AdminApplicationListView(ListView):
    model = ComplianceApplication
    template_name = 'obstacle_compliance/admin_application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def get_queryset(self):
        qs = ComplianceApplication.objects.all().select_related('property', 'user', 'reviewed_by')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        labels = dict(ComplianceApplication.APP_STATUS_CHOICES)
        ctx['counts'] = {
            labels[s]: ComplianceApplication.objects.filter(status=s).count()
            for s, _ in ComplianceApplication.APP_STATUS_CHOICES
        }
        return ctx


@method_decorator(login_required, name='dispatch')
class AdminApplicationDetailView(DetailView):
    model = ComplianceApplication
    template_name = 'obstacle_compliance/admin_application_detail.html'
    context_object_name = 'application'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['transitions'] = ApplicationWorkflow.TRANSITIONS.get(self.object.status, [])
        return ctx


@method_decorator(login_required, name='dispatch')
class AdminApplicationActionView(View):
    def post(self, request, pk, action):
        app = get_object_or_404(ComplianceApplication, pk=pk)
        approved = action == 'approve'
        to_status = 'approved' if approved else 'rejected'
        notes = request.POST.get('notes', '')

        try:
            ApplicationWorkflow.transition(app, to_status, user=request.user, notes=notes)
            from .utils import generate_certificate_pdf
            if approved:
                try:
                    generate_certificate_pdf(app)
                    from datetime import date, timedelta
                    app.valid_until = date.today() + timedelta(days=365)
                    app.save(update_fields=['valid_until'])
                except Exception as e:
                    messages.error(request, f'PDF generation failed: {e}')

            Notification.objects.create(
                user=app.user,
                notification_type='application_update',
                title=f'Application #{app.pk} {approved and "approved" or "rejected"}',
                message=notes or f'Your application has been {approved and "approved" or "rejected"}.',
                link=reverse('obstacle_compliance:application_detail', args=[app.pk]),
            )

            from .utils import send_notification_email
            try:
                send_notification_email(Notification.objects.filter(user=app.user).latest('created_at'))
            except Exception:
                pass

            messages.success(request, f'Application #{app.pk} {approved and "approved" or "rejected"}.')
        except ValueError as e:
            messages.error(request, str(e))

        return redirect('obstacle_compliance:admin_application_detail', pk=pk)


# ============================================
# PUBLIC QUICK CHECK (no login required)
# ============================================

class QuickCheckView(TemplateView):
    template_name = 'obstacle_compliance/quick_check.html'


class QuickCheckAPI(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            lat = float(data.get('latitude'))
            lon = float(data.get('longitude'))
            height = float(data.get('height', 30))
            point = Point(lon, lat, srid=4326)
            result = ComplianceCalculator().evaluate_property_all_airports(point, height)
            result['can_save'] = request.user.is_authenticated
            return JsonResponse(result)
        except (ValueError, TypeError, KeyError) as e:
            return JsonResponse({'error': str(e)}, status=400)


# ============================================
# PROPERTIES GEOJSON (for map overlay)
# ============================================

class PropertiesGeoJSONView(LoginRequiredMixin, View):
    def get(self, request):
        properties = Property.objects.filter(user=request.user, is_active=True)
        features = []
        for p in properties:
            status_color = {'GREEN': '#198754', 'YELLOW': '#ffc107', 'RED': '#dc3545'}.get(p.last_status, '#0d6efd')
            features.append({
                'type': 'Feature',
                'geometry': {'type': 'Point', 'coordinates': [p.longitude, p.latitude]},
                'properties': {
                    'id': p.pk,
                    'name': p.name,
                    'status': p.last_status or 'UNCHECKED',
                    'score': p.last_score,
                    'height': p.height_m,
                    'color': status_color,
                    'last_checked': p.last_checked.isoformat() if p.last_checked else None,
                    'url': reverse('obstacle_compliance:property_detail', args=[p.pk]),
                }
            })
        return JsonResponse({'type': 'FeatureCollection', 'features': features})


# ============================================
# PROPERTIES CSV EXPORT
# ============================================

class PropertiesExportView(LoginRequiredMixin, View):
    def get(self, request):
        properties = Property.objects.filter(user=request.user, is_active=True)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(['Name', 'Latitude', 'Longitude', 'Height (m)', 'Status', 'Score', 'Last Checked'])
        for p in properties:
            writer.writerow([
                p.name, p.latitude, p.longitude, p.height_m,
                p.last_status or 'UNCHECKED', p.last_score or '',
                p.last_checked.isoformat() if p.last_checked else '',
            ])
        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="my_properties.csv"'
        return response


# ============================================
# BULK UPLOAD PROCESS (trigger from UI)
# ============================================

@method_decorator(login_required, name='dispatch')
class BulkUploadProcessView(View):
    def post(self, request, pk):
        job = get_object_or_404(BulkUploadJob, pk=pk, user=request.user)
        if job.status != 'pending':
            messages.error(request, f'Job {job.pk} is already {job.status}.')
        else:
            from .utils import process_bulk_upload
            try:
                process_bulk_upload(job)
                messages.success(request, f'Bulk upload #{pk} processed: {job.success_count}/{job.total_rows} succeeded.')
            except Exception as e:
                messages.error(request, f'Processing failed: {e}')
        return redirect('obstacle_compliance:bulk_detail', pk=pk)