from django.core.management.base import BaseCommand
from obstacle_compliance.models import Aerodrome

class Command(BaseCommand):
    help = 'Test elevation parsing for all aerodromes'

    def handle(self, *args, **options):
        airports = Aerodrome.objects.all().order_by('icao_code')
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write(f"{'ICAO':8} {'Raw Elevation':25} {'Parsed Meters':15} {'Status'}")
        self.stdout.write("="*80)
        
        for airport in airports:
            raw = airport.elevation_m_ft or "NULL"
            parsed = airport.elevation_m
            
            # Determine if parsing was successful
            if parsed > 0:
                status = self.style.SUCCESS("✓")
            else:
                status = self.style.WARNING("⚠")
            
            self.stdout.write(
                f"{airport.icao_code:8} {raw[:25]:25} {parsed:>15.1f} {status}"
            )
        
        self.stdout.write("="*80)
        
        # Summary statistics
        total = airports.count()
        successful = sum(1 for a in airports if a.elevation_m > 0)
        self.stdout.write(self.style.SUCCESS(
            f"\nSuccessfully parsed: {successful}/{total} airports"
        ))