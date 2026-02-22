from django.contrib.gis.db import models

# models.py - Enhanced models
class Dataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=[
        ('aviation', 'Aviation'),
        ('economic', 'Economic'),
        ('demographic', 'Demographic'),
        ('environmental', 'Environmental'),
        ('infrastructure', 'Infrastructure')
    ])
    source = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now=True)
    is_spatial = models.BooleanField(default=False)
    
class DataImport(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    csv_file = models.FileField(upload_to='data_imports/')
    import_config = models.JSONField()  # Field mapping, transformations
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
#existing models
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
    geom = models.MultiPointField(srid=4326)

    class Meta:
        indexes=[
            models.Index(fields=["geom"], name="geom_index")
        ]

    def __str__(self):
        return self.name
    
    # def __str__
    

