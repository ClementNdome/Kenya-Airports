# Create a management command: obstacle_compliance/management/commands/verify_data.py
from django.core.management.base import BaseCommand
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from obstacle_compliance.models import Aerodrome, AerodromeBuffer

class Command(BaseCommand):
    help = 'Verify aerodrome and buffer data integrity'
    
    def handle(self, *args, **options):
        # 1. Check aerodrome counts
        aero_count = Aerodrome.objects.count()
        self.stdout.write(f"Total aerodromes: {aero_count}")
        
        # 2. Check buffer counts per radius
        for radius in [3,5,10,15]:
            count = AerodromeBuffer.objects.filter(radius_km=radius).count()
            self.stdout.write(f"Buffers ({radius}km): {count}")
        
        # 3. Verify each aerodrome has all buffers
        missing_buffers = []
        for aero in Aerodrome.objects.all():
            existing_radii = set(aero.buffers.values_list('radius_km', flat=True))
            expected_radii = {3,5,10,15}
            missing = expected_radii - existing_radii
            if missing:
                missing_buffers.append(f"{aero.icao_code}: missing {missing}")
        
        if missing_buffers:
            self.stdout.write(self.style.WARNING("Missing buffers found:"))
            for msg in missing_buffers:
                self.stdout.write(f"  {msg}")
        else:
            self.stdout.write(self.style.SUCCESS("✓ All aerodromes have complete buffer sets"))
        
        # 4. Test spatial relationship using geom field
        for aero in Aerodrome.objects.filter(geom__isnull=False)[:5]:
            buffer_15 = aero.buffers.get(radius_km=15)
            if buffer_15.geom.contains(aero.geom):
                self.stdout.write(self.style.SUCCESS(f"✓ {aero.icao_code} point inside 15km buffer"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ {aero.icao_code} point NOT inside 15km buffer"))
                
        missing_geom = Aerodrome.objects.filter(geom__isnull=True).count()
        if missing_geom:
            self.stdout.write(self.style.WARNING(f"⚠ {missing_geom} aerodromes missing geometry"))