from django.contrib import admin

# from django.contrib.gis.db import admin
from leaflet.admin import LeafletGeoAdmin

# Register your models here.
from .models import Airports


class AirportsAdmin(LeafletGeoAdmin):
    list_display = ("name", "icao", "iata", "nearest_to", "runway_len", "airlines")


admin.site.register(Airports, AirportsAdmin)
