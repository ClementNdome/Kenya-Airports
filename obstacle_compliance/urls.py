# obstacle_compliance/urls.py

from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from . import views
from .forms import VerificationAwareAuthenticationForm as UserVerificationAuthenticationForm

app_name = 'obstacle_compliance'

urlpatterns = [
    # Main dashboard
    path('', views.ObstacleComplianceDashboard.as_view(), name='dashboard'),
    
    # Airport views
    path('airports/', views.AirportListView.as_view(), name='airport_list'),
    path('airports/<str:icao>/', views.AirportDetailView.as_view(), name='airport_detail'),
    
    # Property compliance
    path('property-check/', views.PropertyComplianceView.as_view(), name='property_check'),
    path('property-query/', views.PropertyQueryPageView.as_view(), name='property_query'),
    path('api/properties/query/', views.PropertyQueryAPI.as_view(), name='api_property_query'),
    path('api/check-compliance/', views.PropertyComplianceAPI.as_view(), name='api_check_compliance'),
    path('api/batch-check/', views.BatchComplianceView.as_view(), name='api_batch_check'),
    
    # Map views
    path('map/', views.MapView.as_view(), name='map_view'),
    path('api/buffers.geojson', views.BufferGeoJSONView.as_view(), name='api_buffers'),
    path('api/airports.geojson', views.AirportGeoJSONView.as_view(), name='api_airports'),
    path('api/runways.geojson', views.RunwaysGeoJSONView.as_view(), name='api_runways'),
    path('api/ols.geojson', views.OLSGeoJSONView.as_view(), name='api_ols'),
    path('api/terrain-breaches.geojson', views.TerrainBreachesGeoJSONView.as_view(), name='api_terrain_breaches'),
    path('api/flyover.geojson', views.FlyoverGeoJSONView.as_view(), name='api_flyover'),
    path('api/skyline.geojson', views.SkylineGeoJSONView.as_view(), name='api_skyline'),
    
    # Search & Geocoding
    path('api/search/', views.SearchView.as_view(), name='api_search'),
    path('api/geocode/', views.GeocodeView.as_view(), name='api_geocode'),
    path('api/reverse-geocode/', views.ReverseGeocodeView.as_view(), name='api_reverse_geocode'),

    # Ported airports_strips spatial queries
    path('api/airports/near-equator/', views.AirportsNearEquatorAPI.as_view(), name='api_airports_near_equator'),
    path('api/airports/within-radius/', views.AirportsWithinRadiusAPI.as_view(), name='api_airports_within_radius'),
    path('api/airports/nearest/', views.NearestAirportAPI.as_view(), name='api_airports_nearest'),
    path('api/airports/distance-between/', views.DistanceBetweenAirportsAPI.as_view(), name='api_airports_distance'),
    
    # Reports
    path('api/generate-report/', views.ComplianceReportView.as_view(), name='api_generate_report'),
    
    # Statistics
    path('api/stats/', views.StatisticsView.as_view(), name='api_stats'),

    # ============ AUTHENTICATION (Feature 1) ============
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/login/', auth_views.LoginView.as_view(
        authentication_form=UserVerificationAuthenticationForm,
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/profile/', views.ProfileView.as_view(), name='profile'),
    path('accounts/verify-email/<str:uidb64>/<str:token>/', views.ActivateAccountView.as_view(), name='verify_email'),
    path('accounts/verify-email/sent/', TemplateView.as_view(template_name='registration/verification_sent.html'), name='verification_sent'),
    path('accounts/verify-email/resend/', views.ResendVerificationView.as_view(), name='resend_verification'),

    # ============ PROPERTY PORTFOLIO (Feature 1) ============
    path('my-properties/', views.PropertyListView.as_view(), name='property_list'),
    path('my-properties/add/', views.PropertyCreateView.as_view(), name='property_add'),
    path('my-properties/<int:pk>/', views.PropertyDetailView.as_view(), name='property_detail'),
    path('my-properties/<int:pk>/edit/', views.PropertyUpdateView.as_view(), name='property_edit'),
    path('my-properties/<int:pk>/delete/', views.PropertyDeleteView.as_view(), name='property_delete'),
    path('my-properties/<int:pk>/check/', views.PropertyCheckView.as_view(), name='property_check'),
    path('api/save-property/', views.SavePropertyFromCheckView.as_view(), name='api_save_property'),

    # ============ DEVELOPER API (Feature 8) ============
    path('api/v1/', include('obstacle_compliance.api_urls')),

    # ============ NOTIFICATIONS (Feature 7) ============
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/mark-read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/unread-count/', views.UnreadCountView.as_view(), name='notification_unread_count'),

    # ============ COMPLIANCE APPLICATIONS (Feature 2) ============
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/add/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/submit/', views.ApplicationSubmitView.as_view(), name='application_submit'),

    # ============ BULK UPLOAD (Feature 3) ============
    path('bulk-upload/', views.BulkUploadListView.as_view(), name='bulk_list'),
    path('bulk-upload/add/', views.BulkUploadCreateView.as_view(), name='bulk_create'),
    path('bulk-upload/<int:pk>/', views.BulkUploadDetailView.as_view(), name='bulk_detail'),

    # ============ ANALYTICS DASHBOARD (Feature 5) ============
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics'),

    # ============ USER DASHBOARD (personalized) ============
    path('dashboard/', views.UserDashboardView.as_view(), name='user_dashboard'),

    # ============ PUBLIC QUICK CHECK ============
    path('quick-check/', views.QuickCheckView.as_view(), name='quick_check'),
    path('api/quick-check/', views.QuickCheckAPI.as_view(), name='api_quick_check'),

    # ============ MY PROPERTIES ON MAP & EXPORT ============
    path('api/my-properties.geojson', views.PropertiesGeoJSONView.as_view(), name='api_my_properties_geojson'),

    # ============ USER LAYERS (persistent toggleable layers) ============
    path('api/user-layers.geojson', views.UserLayersGeoJSONView.as_view(), name='api_user_layers'),
    path('api/user-layers/save/', views.UserLayerSaveView.as_view(), name='api_user_layer_save'),
    path('api/user-layers/<int:pk>/delete/', views.UserLayerDeleteView.as_view(), name='api_user_layer_delete'),
    path('my-properties/export/', views.PropertiesExportView.as_view(), name='property_export'),

    # ============ BULK UPLOAD PROCESS ============
    path('bulk-upload/<int:pk>/process/', views.BulkUploadProcessView.as_view(), name='bulk_process'),

    # ============ KCAA ADMIN REVIEW ============
    path('admin-review/', views.AdminApplicationListView.as_view(), name='admin_application_list'),
    path('admin-review/<int:pk>/', views.AdminApplicationDetailView.as_view(), name='admin_application_detail'),
    path('admin-review/<int:pk>/<slug:action>/', views.AdminApplicationActionView.as_view(), name='admin_application_action'),

    # ============ PASSWORD RESET ============
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/obstacle-compliance/accounts/password-reset/done/',
    ), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/obstacle-compliance/accounts/reset/done/',
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),

    path('debug/', views.debug_geojson, name='debug'),
]