from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from .models import Aerodrome, AerodromeBuffer, Property, ComplianceCheck
from .serializers import (
    AerodromeSerializer, AerodromeBufferSerializer,
    PropertySerializer, ComplianceCheckSerializer,
    ComplianceCheckInputSerializer, BatchCheckInputSerializer,
)
from .utils import ComplianceCalculator


class AerodromeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Aerodrome.objects.all()
    serializer_class = AerodromeSerializer
    search_fields = ['name', 'icao_code', 'nearest_city', 'iata_code']
    filterset_fields = ['type']


class AerodromeBufferViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AerodromeBuffer.objects.all()
    serializer_class = AerodromeBufferSerializer
    filterset_fields = ['radius_km', 'aerodrome__icao_code']


class PropertyViewSet(viewsets.ModelViewSet):
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ComplianceCheckView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceCheckInputSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lat = serializer.validated_data['latitude']
        lon = serializer.validated_data['longitude']
        height = serializer.validated_data['height']

        point = Point(lon, lat, srid=4326)
        result = ComplianceCalculator().evaluate_property_all_airports(point, height)

        property_id = request.data.get('property_id')
        if property_id:
            try:
                prop = Property.objects.get(pk=property_id, user=request.user)
                ComplianceCheck.objects.create(
                    property=prop, result_json=result,
                    status=result.get('status', 'UNKNOWN'),
                    score=result.get('compliance_score', 0),
                    primary_airport_icao=result.get('primary_airport', {}).get('icao', ''),
                    airports_affected=result.get('airports_affected_count', 0),
                    requires_lighting=result.get('requires_lighting', False),
                    is_hazard=result.get('is_hazard', False),
                    trigger='api',
                )
            except Property.DoesNotExist:
                pass

        return Response(result)


class BatchComplianceCheckView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BatchCheckInputSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        calculator = ComplianceCalculator()
        results = []
        for item in serializer.validated_data['properties']:
            point = Point(item['longitude'], item['latitude'], srid=4326)
            result = calculator.evaluate_property_all_airports(point, item['height'])
            results.append(result)

        return Response({'results': results, 'count': len(results)})
