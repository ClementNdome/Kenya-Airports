import os
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource

from airports_strips.models import Airports

# Auto-generated `LayerMapping` dictionary for Airports model
airports_mapping = {
    "type": "Type",
    "name": "Name",
    "iata": "IATA",
    "icao": "ICAO",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "runway_len": "Runway_Len",
    "elevation_field": "Elevation_",
    "nearest_to": "Nearest_To",
    "airlines": "Airlines",
    "geom": "MULTIPOINT",
}


def import_data(verbose=True):
    file = os.getcwd() + "/data/airports.gpkg"
    data_source = DataSource(file)
    airports_layer = data_source[0].name

    airports_layer_mapping = LayerMapping(
        Airports, file, airports_mapping, layer=airports_layer
    )

    airports_layer_mapping.save(verbose=verbose)
