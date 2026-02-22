# obstacle_compliance/urls.py
from django.urls import path
from . import views

app_name = 'obstacle_compliance'

urlpatterns = [
    # Main dashboard
    path('', views.ObstacleDashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/buffer-data/', views.get_buffer_data, name='api_buffer_data'),
    path('api/check-property/', views.check_property, name='api_check_property'),
    path('api/search-properties/', views.search_properties, name='api_search_properties'),
    
    # Airport detail
    path('airport/<int:airport_id>/', views.airport_detail, name='airport_detail'),
]