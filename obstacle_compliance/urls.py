# obstacle_compliance/urls.py

from django.urls import path
from . import views

app_name = 'obstacle_compliance'

urlpatterns = [
    # Main dashboard
    path('', views.ObstacleComplianceDashboard.as_view(), name='dashboard'),
    
    # Airport views
    path('airports/', views.AirportListView.as_view(), name='airport_list'),
    path('airports/<str:icao>/', views.AirportDetailView.as_view(), name='airport_detail'),
    
    # Property compliance
    path('property-check/', views.PropertyComplianceView.as_view(), name='property_check'),
    path('api/check-compliance/', views.PropertyComplianceAPI.as_view(), name='api_check_compliance'),
    path('api/batch-check/', views.BatchComplianceView.as_view(), name='api_batch_check'),
    
    # Map views
    path('map/', views.MapView.as_view(), name='map_view'),
    path('api/buffers.geojson', views.BufferGeoJSONView.as_view(), name='api_buffers'),
    path('api/airports.geojson', views.AirportGeoJSONView.as_view(), name='api_airports'),
    
    # Search
    path('api/search/', views.SearchView.as_view(), name='api_search'),
    path('api/geocode/', views.GeocodeView.as_view(), name='api_geocode'),
    
    # Reports
    path('api/generate-report/', views.ComplianceReportView.as_view(), name='api_generate_report'),
    
    # Statistics
    path('api/stats/', views.StatisticsView.as_view(), name='api_stats'),

    path('api/airport-points.geojson', views.AerodromePointsGeoJSONView.as_view(), name='airport_points_geojson'),

        # In obstacle_compliance/urls.py - add temporarily
    path('debug/', views.debug_geojson, name='debug'),
]