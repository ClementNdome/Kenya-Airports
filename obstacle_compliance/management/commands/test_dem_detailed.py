# management/commands/test_dem_detailed.py
from django.core.management.base import BaseCommand
from obstacle_compliance.utils import DEMService
from django.contrib.gis.geos import Point
import logging

class Command(BaseCommand):
    help = 'Test DEM with detailed diagnostics'

    def add_arguments(self, parser):
        parser.add_argument('--lon', type=float, default=36.9278, help='Longitude')
        parser.add_argument('--lat', type=float, default=-1.3192, help='Latitude')

    def handle(self, *args, **options):
        # Set up logging to see details
        logging.basicConfig(level=logging.INFO)
        
        dem = DEMService()
        
        # Get DEM info
        info = dem.get_dem_info()
        self.stdout.write("DEM Information:")
        self.stdout.write(f"  Bounds: {info['bounds']}")
        self.stdout.write(f"  CRS: {info['crs']}")
        self.stdout.write(f"  NODATA value: {info['nodata']}")
        self.stdout.write(f"  Size: {info['width']}x{info['height']}")
        
        # Test points
        test_points = [
            ("JKIA", 36.9278, -1.3192),
            ("Wilson Airport", 36.8150, -1.3186),
            ("Mombasa Moi International", 39.5942, -4.0348),
            ("Kisumu Airport", 34.7286, -0.0861),
            ("Eldoret Airport", 35.2389, 0.4044),
        ]
        
        self.stdout.write("\nElevation Tests:")
        for name, lon, lat in test_points:
            point = Point(lon, lat, srid=4326)
            elev = dem.get_elevation(point)
            self.stdout.write(f"  {name}: {elev:.1f}m at ({lat:.4f}, {lon:.4f})")
        
        # Test with small offset to see if we get valid data nearby
        if options['lon'] and options['lat']:
            self.stdout.write("\nNeighbor Sampling Test:")
            for offset in [0, 0.001, 0.002, 0.005, 0.01]:
                test_lon = options['lon'] + offset
                test_lat = options['lat'] + offset
                point = Point(test_lon, test_lat, srid=4326)
                elev = dem.get_elevation(point)
                self.stdout.write(f"  Offset {offset:.3f}°: {elev:.1f}m")