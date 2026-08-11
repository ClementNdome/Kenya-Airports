from rest_framework import serializers
from .models import Aerodrome, AerodromeBuffer, Property, ComplianceCheck


class AerodromeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aerodrome
        fields = ['icao_code', 'name', 'type', 'latitude', 'longitude',
                   'elevation_m', 'iata_code', 'runway_length_m',
                   'nearest_city', 'airlines', 'admin_company', 'admin_email']


class AerodromeBufferSerializer(serializers.ModelSerializer):
    aerodrome_icao = serializers.CharField(source='aerodrome.icao_code', read_only=True)

    class Meta:
        model = AerodromeBuffer
        fields = ['aerodrome_icao', 'radius_km', 'area_km2', 'layer', 'geom']


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['id', 'name', 'latitude', 'longitude', 'height_m',
                   'last_status', 'last_score', 'last_checked', 'created_at']
        read_only_fields = ['user', 'last_status', 'last_score', 'last_checked']


class ComplianceCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceCheck
        fields = '__all__'
        read_only_fields = ['checked_at']


class ComplianceCheckInputSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    height = serializers.FloatField(default=30)


class BatchCheckInputSerializer(serializers.Serializer):
    properties = serializers.ListField(
        child=ComplianceCheckInputSerializer(),
        max_length=100,
    )
