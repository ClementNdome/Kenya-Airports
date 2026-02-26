from django.contrib import admin

# from django.contrib.gis.db import admin
from leaflet.admin import LeafletGeoAdmin


# Register your models here.
from .models import Aerodrome, AerodromeBuffer
 #GazettedEstate


class Aerodromes(LeafletGeoAdmin):
    list_display = (
        "name",
        "icao_code",
        "fid",
        "type",
        "admin_company",
    )
    

class AerodromeBuffers(LeafletGeoAdmin):
    list_display = (
        "aerodrome",
        "radius_km",
        "fid",
    )
    

# admin.site.register(Aerodromes)
admin.site.register(Aerodrome, Aerodromes)
# admin.site.register(GazettedEstate)
admin.site.register(AerodromeBuffer, AerodromeBuffers)