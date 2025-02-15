from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from .models import Airports
from django.db.models import Avg, Max 
from geopy.distance import geodesic
from django.db.models import Count

class AirportMapView(TemplateView):
    template_name = 'airports/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['airports'] = Airports.objects.all()
        return context

#more iews explore 


    # long runway
def airports_long_runway(request):
    airports = Airports.objects.filter(runway_len__gt=1500)
    data = [{"name": a.name, "latitude": a.latitude, "longitude": a.longitude, "runway_len": a.runway_len} for a in airports]
    return JsonResponse({"airports": data})

def airports_near_equator(request):
    airports = Airports.objects.filter(latitude__gte=-0.45, latitude__lte=0.45)
    data = [{"name": a.name, "latitude": a.latitude, "longitude": a.longitude} for a in airports]
    return JsonResponse({"airports": data})

def closest_airports(request):
    kakamega = Point(34.7519, 0.2827, srid=4326)
    nairobi = Point(36.8172, -1.2864, srid=4326)

    closest_to_kakamega = Airports.objects.annotate(distance=Distance('geom', kakamega)).order_by('distance').first()
    closest_to_nairobi = Airports.objects.annotate(distance=Distance('geom', nairobi)).order_by('distance').first()

    data = {
        "closest_to_kakamega": {
            "name": closest_to_kakamega.name,
            "latitude": closest_to_kakamega.latitude,
            "longitude": closest_to_kakamega.longitude,
            "distance": closest_to_kakamega.distance.m
        },
        "closest_to_nairobi": {
            "name": closest_to_nairobi.name,
            "latitude": closest_to_nairobi.latitude,
            "longitude": closest_to_nairobi.longitude,
            "distance": closest_to_nairobi.distance.m
        }
    }
    return JsonResponse(data)

def airports_within_radius(request):
    lat = float(request.GET.get('lat'))
    lon = float(request.GET.get('lon'))
    radius = float(request.GET.get('radius'))  # in meters

    point = Point(lon, lat, srid=4326)
    airports = Airports.objects.annotate(distance=Distance('geom', point)).filter(distance__lte=radius)
    data = [{"name": airport.name, "latitude": airport.latitude, "longitude": airport.longitude, "distance": airport.distance.m} for airport in airports]
    return JsonResponse({"airports": data})

def distance_between_airports(request):
    airport1_id = request.GET.get('airport1')
    airport2_id = request.GET.get('airport2')

    if not (airport1_id and airport2_id):
        return JsonResponse({"error": "Missing airport IDs"}, status=400)

    airport1 = Airports.objects.get(id=airport1_id)
    airport2 = Airports.objects.get(id=airport2_id)

    # Calculate distance using geopy
    coords_1 = (airport1.latitude, airport1.longitude)
    coords_2 = (airport2.latitude, airport2.longitude)
    distance_km = geodesic(coords_1, coords_2).kilometers

    data = {
        "airport1": {"name": airport1.name, "latitude": airport1.latitude, "longitude": airport1.longitude},
        "airport2": {"name": airport2.name, "latitude": airport2.latitude, "longitude": airport2.longitude},
        "distance_km": round(distance_km, 2)  # Round to 2 decimal places
    }
    return JsonResponse(data)

def nearest_airport(request):
    lat = float(request.GET.get('lat'))
    lon = float(request.GET.get('lon'))
    point = Point(lon, lat, srid=4326)

    nearest_airport = Airports.objects.annotate(distance=Distance('geom', point)).order_by('distance').first()
    coords_1 = (lat, lon)
    coords_2 = (nearest_airport.latitude, nearest_airport.longitude)
    distance_km = geodesic(coords_1, coords_2).kilometers

    data = {
        "name": nearest_airport.name,
        "latitude": nearest_airport.latitude,
        "longitude": nearest_airport.longitude,
        "distance": distance_km
    }
    return JsonResponse(data)

def airport_search(request):
    query = request.GET.get('search', '')
    airports = Airports.objects.filter(name__icontains=query)[:10]
    data = [{
        "id": a.id,
        "name": a.name,
        "iata": a.iata,
        "latitude": a.latitude,
        "longitude": a.longitude,
        "runway_len": a.runway_len
    } for a in airports]
    return JsonResponse({"results": data})

def index(request):
    stations = list(Airports.objects.values('latitude', 'longitude'))
    context = {'stations': stations}
    return render(request, 'index.html', context)


# from django.views.generic import TemplateView
# from django.db.models import Avg, Max, Count
# from .models import Airports

class ExploreView(TemplateView):
    template_name = 'airports/explore.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        airports = Airports.objects.all()
        
        # Calculate statistics
        context['airports'] = airports
        context['avg_runway_length'] = airports.aggregate(avg_runway=Avg('runway_len'))['avg_runway']
        context['max_elevation'] = airports.aggregate(max_elevation=Max('elevation_field'))['max_elevation']
        
        # Calculate runway length distribution
        context['short_runways'] = airports.filter(runway_len__lt=1000).count()
        context['medium_runways'] = airports.filter(runway_len__gte=1000, runway_len__lte=2000).count()
        context['long_runways'] = airports.filter(runway_len__gt=2000).count()
        
        # Calculate airport type distribution
        context['airport_types'] = airports.values('type').annotate(count=Count('type')).order_by('-count')
        
        # Calculate elevation distribution
        elevation_data = airports.values_list('elevation_field', flat=True)
        context['elevation_data'] = sorted(elevation_data)  # Sort elevation data for line chart
        
        # Calculate number of airports per region
        context['airports_per_region'] = airports.values('nearest_to').annotate(count=Count('nearest_to')).order_by('-count')
        
        # Calculate airlines operating at each airport
        context['airlines_data'] = airports.values('name', 'airlines')
        
        return context