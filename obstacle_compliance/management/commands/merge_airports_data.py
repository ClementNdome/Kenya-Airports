from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from obstacle_compliance.models import Aerodrome


class Command(BaseCommand):
    help = 'Merge airports_strips.Airports data into obstacle_compliance.Aerodrome'

    def handle(self, *args, **options):
        try:
            from airports_strips.models import Airports
        except ImportError:
            self.stdout.write(self.style.ERROR('airports_strips app not available'))
            return

        matched = 0
        created = 0
        errors = 0

        for ap in Airports.objects.all():
            try:
                aero = Aerodrome.objects.get(icao_code=ap.icao.upper())
                aero.iata_code = ap.iata or aero.iata_code
                aero.runway_length_m = ap.runway_len or aero.runway_length_m
                aero.nearest_city = ap.nearest_to or aero.nearest_city
                aero.airlines = ap.airlines or aero.airlines
                aero.source = 'merged'
                aero.last_synced = datetime.now()
                aero.save()
                matched += 1
            except Aerodrome.DoesNotExist:
                try:
                    Aerodrome.objects.create(
                        icao_code=ap.icao.upper(),
                        name=ap.name,
                        type=ap.type or 'unknown',
                        latitude=str(ap.latitude) if ap.latitude else '',
                        longitude=str(ap.longitude) if ap.longitude else '',
                        geom=Point(ap.longitude, ap.latitude, srid=4326) if ap.latitude and ap.longitude else None,
                        elevation_m=float(ap.elevation_field) if ap.elevation_field else None,
                        elevation_m_ft=str(ap.elevation_field) if ap.elevation_field else '',
                        iata_code=ap.iata,
                        runway_length_m=ap.runway_len,
                        nearest_city=ap.nearest_to,
                        airlines=ap.airlines,
                        source='geopackage',
                    )
                    created += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating {ap.icao}: {e}"))
                    errors += 1

        self.stdout.write(self.style.SUCCESS(
            f'Matched: {matched}, Created: {created}, Errors: {errors}'
        ))
