from django.urls import path
from .views import *

urlpatterns = [
    path('', AirportMapView.as_view()),
    path('map/', AirportMapView.as_view(), name='airport_map'),
    path('near-equator/', airports_near_equator, name='near_equator'),
    path('within-radius/', airports_within_radius, name='within_radius'),
    path('distance-between/', distance_between_airports, name='distance_between'),
    path('api/airports/', airport_search, name='airport_search'),
    path('long-runway/', airports_long_runway, name='long-runway'),
    path('index/', index, name='index'),
    path('closest-airports/', closest_airports, name='closest_airports'),
    path('nearest-airport/', nearest_airport, name='nearest_airport'),
     path('explore/', ExploreView.as_view(), name='explore'),  # New Explore Route
]