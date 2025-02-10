from django.contrib.gis.db import models


# Create your models here.
class Airports(models.Model):
    type = models.CharField(max_length=254)
    name = models.CharField(max_length=254)
    iata = models.CharField(max_length=254)
    icao = models.CharField(max_length=254)
    latitude = models.FloatField()
    longitude = models.FloatField()
    runway_len = models.BigIntegerField()
    elevation_field = models.BigIntegerField()
    nearest_to = models.CharField(max_length=254)
    airlines = models.CharField(max_length=254)
    geom = models.PointField(srid=4326)
