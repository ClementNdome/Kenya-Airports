from django.urls import path
from .views import *


urlpatterns = [
    path('', AirportMapView.as_view()),
    path('map/', AirportMapView.as_view(), name='airport_map'),
    path('long-runway/', LongRunwayAirportsView.as_view(), name='long_runway_airports'),
    # path('equator/', NearEquatorAirportsView.as_view(), name='near_equator_airports'),
    path('closest-airport/', ClosestAirportView.as_view(), name='closest_airport'),
     path('near-equator/', airports_near_equator, name='near_equator'),
    path('within-radius/', airports_within_radius, name='within_radius'),
    path('distance-between/', distance_between_airports, name='distance_between'),
    path('api/airports/', airport_search, name='airport_search'),
]