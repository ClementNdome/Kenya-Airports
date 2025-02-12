from django.shortcuts import render
from django.views.generic import TemplateView
from .models import Airports

class AirportMapView(TemplateView):
    template_name = 'airports/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['airports'] = Airports.objects.all()
        return context
    
class LongRunwayAirportsView(TemplateView):
    template_name = 'airports/long_runway.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['airports'] = Airports.objects.filter(runway_len__gt=1500)
        return context
    
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point

class NearEquatorAirportsView(TemplateView):
    template_name = 'airports/near_equator.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equator = Point(0, 0, srid=4326)  # Equator line (latitude = 0)
        context['airports'] = Airports.objects.annotate(
            distance=Distance('geom', equator)
        ).filter(distance__lte=50000)  # 50 km
        return context
#more in equator
from django.http import JsonResponse
from .models import Airports

def airports_near_equator(request):
    airports = Airports.objects.filter(latitude__gte=-0.45, latitude__lte=0.45)
    data = [{"name": airport.name, "latitude": airport.latitude, "longitude": airport.longitude} for airport in airports]
    return JsonResponse({"airports": data})


class ClosestAirportView(TemplateView):
    template_name = 'airports/closest_airport.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kakamega = Point(34.7519, 0.2827, srid=4326)
        nairobi = Point(36.8172, -1.2864, srid=4326)

        # Find closest airport to Kakamega
        context['closest_to_kakamega'] = Airports.objects.annotate(
            distance=Distance('geom', kakamega)).order_by('distance').first()

        # Find closest airport to Nairobi
        context['closest_to_nairobi'] = Airports.objects.annotate(
            distance=Distance('geom', nairobi)).order_by('distance').first()
        return context
    
#new radius
def airports_within_radius(request):
    lat = float(request.GET.get('lat'))
    lon = float(request.GET.get('lon'))
    radius = float(request.GET.get('radius'))  # in meters

    point = Point(lon, lat, srid=4326)
    airports = Airports.objects.annotate(distance=Distance('geom', point)).filter(distance__lte=radius)
    data = [{"name": airport.name, "distance": airport.distance.m} for airport in airports]
    return JsonResponse({"airports": data})

# new distance1!!
def distance_between_airports(request):
    airport1_id = request.GET.get('airport1')
    airport2_id = request.GET.get('airport2')

    airport1 = Airports.objects.get(id=airport1_id)
    airport2 = Airports.objects.get(id=airport2_id)

    distance = airport1.geom.distance(airport2.geom) * 100  # Convert to kilometers
    return JsonResponse({"distance": distance})

from django.http import JsonResponse
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from .models import Airports

def airports_long_runway(request):
    airports = Airports.objects.filter(runway_len__gt=1500)
    data = [{"name": a.name, "latitude": a.latitude, "longitude": a.longitude} for a in airports]
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
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    radius = request.GET.get('radius')

    if not (lat and lon and radius):
        return JsonResponse({"error": "Missing parameters"}, status=400)

    point = Point(float(lon), float(lat), srid=4326)
    airports = Airports.objects.annotate(distance=Distance('geom', point)).filter(distance__lte=float(radius))
    data = [{"name": a.name, "latitude": a.latitude, "longitude": a.longitude} for a in airports]
    return JsonResponse({"airports": data})

def distance_between_airports(request):
    airport1_id = request.GET.get('airport1')
    airport2_id = request.GET.get('airport2')

    if not (airport1_id and airport2_id):
        return JsonResponse({"error": "Missing airport IDs"}, status=400)

    airport1 = Airports.objects.get(id=airport1_id)
    airport2 = Airports.objects.get(id=airport2_id)

    distance_km = airport1.geom.distance(airport2.geom) * 100  # Convert to km
    data = {
        "airport1": {"name": airport1.name, "latitude": airport1.latitude, "longitude": airport1.longitude},
        "airport2": {"name": airport2.name, "latitude": airport2.latitude, "longitude": airport2.longitude},
        "distance_km": distance_km
    }
    return JsonResponse(data)

    # views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
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
    return Response({"results": data})