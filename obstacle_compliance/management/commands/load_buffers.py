import os
from django.core.management.base import BaseCommand
from django.contrib.gis.utils import LayerMapping
from obstacle_compliance.models import Aerodrome, AerodromeBuffer

# Common mapping from your ogrinspect (identical for all)
BUFFER_MAPPING = {
    'fid': 'fid',
    'type': 'Type',
    'latitude': 'Latitude',
    'longitude': 'Longitude',
    'elevation_m_ft': 'Elevation_m_ft',
    'geoid_undulation_m': 'Geoid_Undulation_m',
    'remarks_spatial': 'Remarks_Spatial',
    'admin_company': 'Admin_Company',
    'admin_address': 'Admin_Address',
    'admin_telephone': 'Admin_Telephone',
    'admin_afs': 'Admin_AFS',
    'admin_email': 'Admin_Email',
    'traffic_permitted': 'Traffic_Permitted',
    'magnetic_variation': 'Magnetic_Variation',
    'annual_change': 'Annual_Change',
    'remarks_nonspatial': 'Remarks_NonSpatial',
    'admin_website': 'Admin_Website',
    'area_km2': 'area_km2',
    'layer': 'layer',
    'geom': 'MULTIPOLYGON',
}

class Command(BaseCommand):
    help = 'Load precomputed aerodrome buffers from GeoJSON files'

    def handle(self, *args, **options):
        base_dir = 'obstacle_compliance/newdata/final_buffered/'  # Adjust if path differs
        files = [
            '3km_buffer-wgs84.geojson',
            '5km_buffer-wgs84.geojson',
            '10km_buffer-wgs84.geojson',
            '15km_buffer-wgs84.geojson',
        ]

        for file_name in files:
            file_path = os.path.join(base_dir, file_name)
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
                continue

            # Extract radius from filename (e.g., '3km' → 3)
            radius_str = file_name.split('km_buffer')[0]  # '3' or '15'
            radius_km = int(radius_str)

            self.stdout.write(self.style.NOTICE(f"Loading {file_name} for {radius_km}km..."))

            lm = LayerMapping(
                AerodromeBuffer,  # Unified model
                file_path,
                BUFFER_MAPPING,
                transform=False,  # Already in SRID=4326
                encoding='utf-8',
            )

            # Save features, but set aerodrome and radius_km (not in mapping)
            for feature in lm.layer:
                icao_code = feature['ICAO_Code'].value  # From GeoJSON
                try:
                    aerodrome = Aerodrome.objects.get(icao_code=icao_code)
                except Aerodrome.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Aerodrome {icao_code} not found; skipping feature {feature.fid}"))
                    continue

                # Create instance manually to set extra fields
                buffer_obj = AerodromeBuffer(
                    aerodrome=aerodrome,
                    radius_km=radius_km,
                    fid=feature['fid'].value,
                    type=feature['Type'].value,
                    latitude=feature['Latitude'].value,
                    longitude=feature['Longitude'].value,
                    elevation_m_ft=feature['Elevation_m_ft'].value,
                    geoid_undulation_m=feature['Geoid_Undulation_m'].value,
                    remarks_spatial=feature['Remarks_Spatial'].value,
                    admin_company=feature['Admin_Company'].value,
                    admin_address=feature['Admin_Address'].value,
                    admin_telephone=feature['Admin_Telephone'].value,
                    admin_afs=feature['Admin_AFS'].value,
                    admin_email=feature['Admin_Email'].value,
                    traffic_permitted=feature['Traffic_Permitted'].value,
                    magnetic_variation=feature['Magnetic_Variation'].value,
                    annual_change=feature['Annual_Change'].value,
                    remarks_nonspatial=feature['Remarks_NonSpatial'].value,
                    admin_website=feature['Admin_Website'].value,
                    area_km2=feature['area_km2'].value,
                    layer=feature['layer'].value,
                    geom=feature.geom.geos,  # GEOS geometry
                )
                buffer_obj.save()  # Saves if not duplicate (due to unique_together)

            self.stdout.write(self.style.SUCCESS(f"Loaded {file_name} successfully"))
