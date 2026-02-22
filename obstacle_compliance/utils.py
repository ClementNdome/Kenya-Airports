# obstacle_compliance/utils.py
import math
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db.models.functions import Distance
from airports_strips.models import Airports
from .models import AerodromeBuffer, Building

def calculate_max_allowed_height(airport_elevation, distance_m, airport=None):
    """
    Calculate maximum allowed height based on ICAO Annex 14
    Returns height in meters above ground level (AGL)
    """
    # Distance in kilometers
    distance_km = distance_m / 1000
    
    if distance_km <= 4:
        # Approach surface: 2% slope (1:50) from runway end
        # Simplified: 20m height increase per km from airport
        return 20 * distance_km
    elif distance_km <= 15:
        # Conical surface: 5% slope (1:20) beyond 4km
        # Start from 80m at 4km (20*4) + (distance-4)*50
        base_height = 80  # 20 * 4
        additional = (distance_km - 4) * 50  # 5% = 50m per km
        return base_height + additional
    else:
        # Outer horizontal surface: capped at 150m above airport
        return 150

def check_building_compliance(building_id):
    """Run compliance check for a specific building"""
    try:
        building = Building.objects.select_related('property').get(id=building_id)
        
        # Find nearest airport
        nearest_airport = Airports.objects.annotate(
            distance=Distance('geom', building.property.coordinates)
        ).order_by('distance').first()
        
        if not nearest_airport:
            return None
        
        distance_m = nearest_airport.distance.m
        max_height = calculate_max_allowed_height(
            nearest_airport.elevation_field or 0, 
            distance_m,
            nearest_airport
        )
        
        # Determine compliance status
        if building.height_m <= max_height:
            height_compliant = True
        else:
            height_compliant = False
        
        lights_required = building.height_m > 30 and distance_m <= 15000
        lights_compliant = building.lights_installed if lights_required else True
        
        if height_compliant and lights_compliant:
            status = 'compliant'
        elif not height_compliant and not lights_compliant:
            status = 'both_violation'
        elif not height_compliant:
            status = 'height_violation'
        else:
            status = 'lights_violation'
        
        # Save compliance check
        from .models import ComplianceCheck
        check = ComplianceCheck.objects.create(
            building=building,
            airport=nearest_airport,
            distance_m=distance_m,
            max_allowed_height_m=max_height,
            status=status
        )
        
        # Update building status
        building.compliance_status = status
        building.save()
        
        return {
            'building_id': building.id,
            'airport': nearest_airport.name,
            'distance_km': round(distance_m / 1000, 2),
            'max_height': round(max_height, 1),
            'current_height': building.height_m,
            'compliant': height_compliant,
            'lights_required': lights_required,
            'lights_installed': building.lights_installed,
            'status': status
        }
        
    except Building.DoesNotExist:
        return None

def generate_airport_buffers(airport_id, radii=[3, 5, 8, 10, 15, 20, 30, 50]):
    """Pre-generate buffer zones for an airport"""
    from airports_strips.models import Airports
    
    try:
        airport = Airports.objects.get(id=airport_id)
        point = Point(airport.longitude, airport.latitude, srid=4326)
        
        results = []
        for radius in radii:
            # Create buffer in meters (radius * 1000)
            buffer_geom = point.buffer(radius * 1000)
            
            # Calculate approximate area
            area_sqkm = math.pi * (radius ** 2)
            
            # Create or update buffer record
            buffer, created = AerodromeBuffer.objects.update_or_create(
                airport=airport,
                radius_km=radius,
                defaults={
                    'geometry': buffer_geom,
                    'area_sqkm': area_sqkm
                }
            )
            
            results.append({
                'radius': radius,
                'area_sqkm': area_sqkm,
                'created': created
            })
        
        return results
        
    except Airports.DoesNotExist:
        return None

def get_estates_within_buffer(airport_id, radius_km):
    """Get list of estates/areas within buffer zone (from gazette)"""
    from .models import GazettedArea
    
    try:
        airport = Airports.objects.get(id=airport_id)
        buffer = AerodromeBuffer.objects.get(airport=airport, radius_km=radius_km)
        
        # Find gazetted areas that intersect with buffer
        areas = GazettedArea.objects.filter(
            airport=airport,
            geometry__intersects=buffer.geometry
        ).values_list('name', flat=True)
        
        return list(areas)
        
    except (Airports.DoesNotExist, AerodromeBuffer.DoesNotExist):
        return []