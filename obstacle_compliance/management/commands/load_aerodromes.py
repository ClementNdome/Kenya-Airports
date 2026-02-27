import re
from django.core.management.base import BaseCommand
from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.geos import Point
from obstacle_compliance.models import Aerodrome

def dms_to_decimal(dms_str):
    """Convert DMS string to decimal degrees"""
    if not dms_str:
        return None
    
    # Pattern: DDDMMSS.SS followed by N/S/E/W
    match = re.match(r'(\d{3})(\d{2})(\d{2}\.\d+)([NSEW])', dms_str)
    if not match:
        # Try alternative format without leading zeros
        match = re.match(r'(\d{1,3})(\d{2})(\d{2}\.\d+)([NSEW])', dms_str)
    
    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        direction = match.group(4)
        
        decimal = degrees + (minutes / 60) + (seconds / 3600)
        
        # Make negative for South or West
        if direction in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    return None

class Command(BaseCommand):
    help = 'Load aerodromes from GeoJSON file'
    
    def handle(self, *args, **options):
        file_path = 'obstacle_compliance/newdata/aerodromes-ke.geojson'
        
        # Load the data source
        from django.contrib.gis.gdal import DataSource
        ds = DataSource(file_path)
        layer = ds[0]
        
        for feature in layer:
            # Get the DMS strings
            lat_dms = feature['Latitude'].value
            lon_dms = feature['Longitude'].value
            
            # Convert to decimal degrees
            lat_decimal = dms_to_decimal(lat_dms)
            lon_decimal = dms_to_decimal(lon_dms)
            
            # Create point geometry
            point = Point(lon_decimal, lat_decimal, srid=4326) if lat_decimal and lon_decimal else None
            
            # Create or update aerodrome
            aerodrome, created = Aerodrome.objects.update_or_create(
                icao_code=feature['ICAO_Code'].value,
                defaults={
                    'fid': feature['fid'].value,
                    'type': feature['Type'].value,
                    'latitude': lat_dms,  # Keep original for reference
                    'longitude': lon_dms,  # Keep original for reference
                    # 'latitude_decimal': lat_decimal,  # Add new field
                    # 'longitude_decimal': lon_decimal,  # Add new field
                    'elevation_m_ft': feature['Elevation_m_ft'].value,
                    'geoid_undulation_m': feature['Geoid_Undulation_m'].value,
                    'remarks_spatial': feature['Remarks_Spatial'].value,
                    'admin_company': feature['Admin_Company'].value,
                    'admin_address': feature['Admin_Address'].value,
                    'admin_telephone': feature['Admin_Telephone'].value,
                    'admin_afs': feature['Admin_AFS'].value,
                    'admin_email': feature['Admin_Email'].value,
                    'traffic_permitted': feature['Traffic_Permitted'].value,
                    'magnetic_variation': feature['Magnetic_Variation'].value,
                    'annual_change': feature['Annual_Change'].value,
                    'remarks_nonspatial': feature['Remarks_NonSpatial'].value,
                    'admin_website': feature['Admin_Website'].value,
                    'geom': point,  # Store as geometry
                }
            )
            
            self.stdout.write(f"{'Created' if created else 'Updated'}: {aerodrome.icao_code}")