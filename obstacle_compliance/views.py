# obstacle_compliance/views.py

import json
import logging
import io
from datetime import datetime
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q, Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.urls import reverse

from .models import Aerodrome, AerodromeBuffer
from .utils import ComplianceCalculator, DEMService

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
        context['international_airports'] = Aerodrome.objects.filter(
            Q(name__icontains='international') | Q(type__icontains='international')
        ).count()
        
        # Get buffer stats
        context['buffer_stats'] = {
            '3km': AerodromeBuffer.objects.filter(radius_km=3).count(),
            '5km': AerodromeBuffer.objects.filter(radius_km=5).count(),
            '10km': AerodromeBuffer.objects.filter(radius_km=10).count(),
            '15km': AerodromeBuffer.objects.filter(radius_km=15).count(),
        }
        
        # Get recent airports (for quick access)
        context['recent_airports'] = Aerodrome.objects.all()[:5]
        
        # Map configuration
        context['map_config'] = {
            'center': [-1.2864, 36.8172],  # Nairobi center
            'zoom': 10,
            'max_zoom': 18,
            'min_zoom': 6,
        }
        
        # Default buffer radius
        context['default_radius'] = 15
        
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
        context['airport_type'] = self.request.GET.get('type', '')
        context['airport_types'] = Aerodrome.objects.values_list('type', flat=True).distinct().order_by('type')
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


class PropertyComplianceAPI(View):
    """
    API endpoint for property compliance checks
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
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
            
            # Check cache
            cache_key = f"compliance_api_{lat}_{lon}_{height}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return JsonResponse(cached_result)
            
            # Evaluate compliance
            result = calculator.evaluate_property_all_airports(point, height)
            
            # Cache result (5 minutes for API)
            cache.set(cache_key, result, 300)
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in PropertyComplianceAPI GET: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'ERROR',
                'message': f'System error: {str(e)}'
            }, status=500)
    
    def post(self, request):
        """Handle POST request with JSON body"""
        try:
            data = json.loads(request.body)
            
            lat = data.get('lat')
            lon = data.get('lon')
            height = data.get('height', 30)
            
            if not lat or not lon:
                return JsonResponse({
                    'status': 'ERROR',
                    'message': 'Latitude and longitude are required'
                }, status=400)
            
            point = Point(float(lon), float(lat), srid=4326)
            height = float(height)
            
            result = calculator.evaluate_property_all_airports(point, height)
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'ERROR',
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Error in PropertyComplianceAPI POST: {str(e)}", exc_info=True)
            return JsonResponse({
                'status': 'ERROR',
                'message': f'System error: {str(e)}'
            }, status=500)


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

class MapView(TemplateView):
    """
    Interactive map view with buffer visualization
    """
    template_name = 'obstacle_compliance/map_view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active airport if specified
        icao = self.request.GET.get('airport')
        active_airport = None
        
        if icao:
            try:
                active_airport = Aerodrome.objects.get(icao_code=icao.upper())
                context['active_airport'] = active_airport
                context['map_center'] = [active_airport.geom.y, active_airport.geom.x]
                context['map_zoom'] = 12
            except Aerodrome.DoesNotExist:
                # Log the error but don't break the page
                logger.warning(f"Airport with ICAO code {icao} not found")
                context['map_center'] = [-1.2864, 36.8172]  # Nairobi center
                context['map_zoom'] = 8
        else:
            context['map_center'] = [-1.2864, 36.8172]  # Nairobi center
            context['map_zoom'] = 8
        
        # Default radius - ensure it's an integer
        try:
            context['default_radius'] = int(self.request.GET.get('radius', 15))
        except ValueError:
            context['default_radius'] = 15
        
        # Layer visibility - ensure boolean values
        context['show_buffers'] = self.request.GET.get('buffers', 'true').lower() == 'true'
        context['show_airports'] = self.request.GET.get('airports', 'true').lower() == 'true'
        
        return context


class BufferGeoJSONView(View):
    """
    Return buffer geometries as GeoJSON for mapping
    """
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        try:
            # Get parameters
            radius = request.GET.get('radius', 15)
            icao = request.GET.get('icao')
            
            # Build query
            buffers = AerodromeBuffer.objects.filter(radius_km=radius)
            
            if icao:
                buffers = buffers.filter(aerodrome__icao_code=icao)
            
            # Limit for performance
            buffers = buffers.select_related('aerodrome')[:50]
            
            # Build GeoJSON
            features = []
            for buffer in buffers:
                try:
                    # Transform to GeoJSON format
                    geom_json = json.loads(buffer.geom.geojson)
                    
                    feature = {
                        'type': 'Feature',
                        'geometry': geom_json,
                        'properties': {
                            'id': buffer.id,
                            'airport_icao': buffer.aerodrome.icao_code,
                            'airport_name': buffer.aerodrome.name or buffer.aerodrome.admin_company,
                            'radius_km': buffer.radius_km,
                            'area_km2': round(buffer.area_km2, 2) if buffer.area_km2 else None,
                            'stroke': self._get_color_for_radius(buffer.radius_km),
                            'stroke-width': 2,
                            'stroke-opacity': 0.8,
                            'fill': self._get_color_for_radius(buffer.radius_km),
                            'fill-opacity': 0.15,
                        }
                    }
                    features.append(feature)
                    
                except Exception as e:
                    logger.error(f"Error processing buffer {buffer.id}: {e}")
                    continue
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features,
                'metadata': {
                    'count': len(features),
                    'radius': radius,
                    'icao_filter': icao
                }
            }
            
            return JsonResponse(geojson)
            
        except Exception as e:
            logger.error(f"Error in BufferGeoJSONView: {str(e)}", exc_info=True)
            return JsonResponse({
                'type': 'FeatureCollection',
                'features': [],
                'error': str(e)
            }, status=500)
    
    def _get_color_for_radius(self, radius):
        """Get color based on buffer radius"""
        colors = {
            3: '#FF6B6B',   # Red for inner zone
            5: '#FFA500',   # Orange for middle zone
            10: '#2196F3',  # Blue for outer zone
            15: '#4CAF50',  # Green for regulatory zone
        }
        return colors.get(radius, '#666666')


# obstacle_compliance/views.py - Update AirportGeoJSONView

class AirportGeoJSONView(View):
    """
    Return airport points as GeoJSON for mapping
    """
    def get(self, request):
        try:
            airports = Aerodrome.objects.all()
            
            features = []
            for airport in airports:
                try:
                    if not airport.geom:
                        continue
                        
                    geom_json = json.loads(airport.geom.geojson)
                    
                    feature = {
                        'type': 'Feature',
                        'geometry': geom_json,
                        'properties': {
                            'id': airport.fid,
                            'icao': airport.icao_code,
                            'name': airport.name or airport.admin_company or airport.icao_code,
                            'type': airport.type or 'Unknown',
                            'elevation': airport.elevation_m,
                            'runway_info': f"Elevation: {airport.elevation_m}m",
                        }
                    }
                    features.append(feature)
                    
                except Exception as e:
                    logger.error(f"Error processing airport {airport.icao_code}: {e}")
                    continue
            
            geojson = {
                'type': 'FeatureCollection',
                'features': features
            }
            
            return JsonResponse(geojson)
            
        except Exception as e:
            logger.error(f"Error in AirportGeoJSONView: {str(e)}", exc_info=True)
            return JsonResponse({
                'type': 'FeatureCollection',
                'features': []
            })
# ============================================
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
    Geocode an address to coordinates (placeholder - integrate with real geocoder)
    """
    def get(self, request):
        address = request.GET.get('address', '')
        
        if not address:
            return JsonResponse({'error': 'Address required'}, status=400)
        
        # Placeholder - in production, use Google Maps API, Mapbox, or OpenStreetMap
        # For now, return Nairobi center for any address
        return JsonResponse({
            'lat': -1.2864,
            'lon': 36.8172,
            'display_name': f"Nairobi, Kenya ({address})",
            'place_id': 'placeholder'
        })


# ============================================
# REPORT AND EXPORT VIEWS
# ============================================

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
                'status_color': '#dc3545' if result['status'] == 'HAZARD' else '#28a745',
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