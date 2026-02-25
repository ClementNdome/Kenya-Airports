# management/commands/test_dem.py
from django.core.management.base import BaseCommand
from obstacle_compliance.utils import DEMService
from django.contrib.gis.geos import Point

class Command(BaseCommand):
    def handle(self, *args, **options):
        dem = DEMService()
        # Test with JKIA coordinates
        test_point = Point(36.9278, -1.3192, srid=4326)
        elevation = dem.get_elevation(test_point)
        self.stdout.write(f"DEM Test - Elevation at JKIA: {elevation}m")