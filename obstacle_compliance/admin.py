from django.contrib import admin

# from django.contrib.gis.db import admin
from leaflet.admin import LeafletGeoAdmin


# Register your models here.
from .models import Aerodrome #GazettedEstate


class Aerodromes(LeafletGeoAdmin):
    list_display = (
        "name",
        "icao_code",
        "fid",
        "type",
        "admin_company",
    )


# admin.site.register(Aerodromes)
admin.site.register(Aerodrome, Aerodromes)
# admin.site.register(GazettedEstate)
