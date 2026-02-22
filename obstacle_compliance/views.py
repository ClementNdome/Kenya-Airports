# obstacle_compliance/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET
from airports_strips.models import Airports
from .models import AerodromeBuffer, Property, Building, ComplianceCheck
from .utils import check_building_compliance, calculate_max_allowed_height
import json

class ObstacleDashboardView(TemplateView):
    """Main dashboard for obstacle limitation"""
    template_name = 'obstacle_compliance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all airports for selector
        context['airports'] = Airports.objects.all().order_by('name')
        
        # Default to first airport or specified one
        airport_id = self.request.GET.get('airport')
        if airport_id:
            context['selected_airport'] = get_object_or_404(Airports, id=airport_id)
        else:
            context['selected_airport'] = Airports.objects.first()
        
        # Default radius
        context['default_radius'] = int(self.request.GET.get('radius', 15))
        
        # Available radii presets
        context['radii_presets'] = [3, 5, 8, 10, 15, 20, 30, 50]
        
        return context

@require_GET
def get_buffer_data(request):
    """API endpoint for buffer data"""
    airport_id = request.GET.get('airport_id')
    radius = int(request.GET.get('radius', 15))
    
    try:
        airport = Airports.objects.get(id=airport_id)
        
        # Get or generate buffer
        buffer, created = AerodromeBuffer.objects.get_or_create(
            airport=airport,
            radius_km=radius,
            defaults={
                'geometry': Point(airport.longitude, airport.latitude, srid=4326).buffer(radius * 1000),
                'area_sqkm': 3.14159 * (radius ** 2)
            }
        )
        
        # Get gazetted areas within buffer (mock for now)
        # In production, you'd query actual data
        gazetted_areas = [
            "Nairobi West", "Madaraka", "South B", "South C", "Lang'ata",
            "Karen", "Ongata Rongai", "Kibera", "Highrise"
        ][:5]  # Limit for demo
        
        response = {
            'success': True,
            'airport': {
                'id': airport.id,
                'name': airport.name,
                'code': airport.iata or airport.icao,
                'latitude': airport.latitude,
                'longitude': airport.longitude,
                'elevation': airport.elevation_field
            },
            'buffer': {
                'radius_km': radius,
                'area_sqkm': round(buffer.area_sqkm, 2),
                'geometry': json.loads(buffer.geometry.geojson)
            },
            'stats': {
                'area_sqkm': round(buffer.area_sqkm, 2),
                'estimated_properties': radius * 15000,  # Mock calculation
                'estimated_population': radius * 75000,  # Mock calculation
                'gazetted_areas_count': len(gazetted_areas),
                'gazetted_areas': gazetted_areas
            }
        }
        
        return JsonResponse(response)
        
    except Airports.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Airport not found'}, status=404)

@require_GET
def check_property(request):
    """Check property compliance"""
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    address = request.GET.get('address')
    height = request.GET.get('height', 0)
    
    try:
        lat = float(lat)
        lon = float(lon)
        height = float(height)
        
        point = Point(lon, lat, srid=4326)
        
        # Find nearest airport
        nearest = Airports.objects.annotate(
            distance=Distance('geom', point)
        ).order_by('distance').first()
        
        if not nearest:
            return JsonResponse({'success': False, 'error': 'No airports found'})
        
        distance_km = nearest.distance.km
        distance_m = distance_km * 1000
        
        # Calculate max allowed height
        max_height = calculate_max_allowed_height(
            nearest.elevation_field or 0,
            distance_m,
            nearest
        )
        
        # Determine compliance
        height_compliant = height <= max_height
        lights_required = height > 30 and distance_m <= 15000
        
        # Find if property exists or create mock
        property_data = {
            'address': address or f"Point at {lat:.4f}, {lon:.4f}",
            'coordinates': {'lat': lat, 'lon': lon}
        }
        
        response = {
            'success': True,
            'property': property_data,
            'nearest_airport': {
                'id': nearest.id,
                'name': nearest.name,
                'code': nearest.iata or nearest.icao,
                'distance_km': round(distance_km, 2),
                'elevation': nearest.elevation_field
            },
            'compliance': {
                'max_allowed_height_m': round(max_height, 1),
                'current_height_m': height,
                'height_compliant': height_compliant,
                'lights_required': lights_required,
                'status': 'compliant' if (height_compliant and not lights_required) else 'non_compliant',
                'message': self._get_compliance_message(height_compliant, lights_required)
            }
        }
        
        return JsonResponse(response)
        
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid parameters'}, status=400)

def _get_compliance_message(height_compliant, lights_required):
    if height_compliant and not lights_required:
        return "✅ Property complies with all regulations"
    elif not height_compliant and lights_required:
        return "❌ Height violation AND obstacle lights required"
    elif not height_compliant:
        return "❌ Height exceeds maximum allowed"
    elif lights_required:
        return "⚠️ Obstacle lights required"
    return "Compliance status unknown"

@require_GET
def search_properties(request):
    """Search properties by address or coordinates"""
    query = request.GET.get('q', '')
    
    # Mock response for now - in production, query actual property database
    mock_results = [
        {
            'id': 1,
            'address': 'Nairobi West, Next to St Mary\'s School',
            'coordinates': {'lat': -1.3105, 'lon': 36.8152},
            'type': 'residential'
        },
        {
            'id': 2,
            'address': 'Karen, Lang\'ata Road',
            'coordinates': {'lat': -1.3196, 'lon': 36.7082},
            'type': 'commercial'
        },
        {
            'id': 3,
            'address': 'South B, Opposite Shell',
            'coordinates': {'lat': -1.3056, 'lon': 36.8250},
            'type': 'residential'
        }
    ]
    
    # Filter based on query
    if query:
        mock_results = [r for r in mock_results if query.lower() in r['address'].lower()]
    
    return JsonResponse({'results': mock_results[:10]})

def airport_detail(request, airport_id):
    """Detailed view for a single airport"""
    airport = get_object_or_404(Airports, id=airport_id)
    
    context = {
        'airport': airport,
        'default_radius': 15,
        'radii_presets': [3, 5, 8, 10, 15, 20, 30, 50],
        'gazetted_areas': [
            "Nairobi West", "Madaraka", "South B", "South C", 
            "Lang'ata", "Karen", "Ongata Rongai"
        ]  # Mock data
    }
    
    return render(request, 'obstacle_compliance/airport_detail.html', context)