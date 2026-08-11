from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api

router = DefaultRouter()
router.register(r'aerodromes', api.AerodromeViewSet)
router.register(r'buffers', api.AerodromeBufferViewSet)
router.register(r'properties', api.PropertyViewSet, basename='property')

urlpatterns = [
    path('', include(router.urls)),
    path('check-compliance/', api.ComplianceCheckView.as_view(), name='api_v1_check'),
    path('batch-check/', api.BatchComplianceCheckView.as_view(), name='api_v1_batch_check'),
    path('auth/', include('rest_framework.urls')),
]
