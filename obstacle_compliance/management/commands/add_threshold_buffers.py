# obstacle_compliance/management/commands/add_threshold_buffers.py
from django.core.management.base import BaseCommand

from obstacle_compliance.models import Aerodrome, AerodromeRunway


class Command(BaseCommand):
    help = ('Backfill 3/5/10 km runway-threshold buffers (HKNL 03/21): '
            'stadium-shaped buffers around runway centreline(s), replacing '
            'the ARP-circle buffers for aerodromes with runway geometry.')

    def add_arguments(self, parser):
        parser.add_argument('--radii', default='3,5,10',
                            help='Comma-separated radii in km (default 3,5,10)')
        parser.add_argument('--icao', default=None,
                            help='Only process this aerodrome')

    def handle(self, *args, **options):
        radii = [int(r.strip()) for r in options['radii'].split(',') if r.strip()]
        qs = Aerodrome.objects.all()
        if options['icao']:
            qs = qs.filter(icao_code=options['icao'].upper())

        with_runways = []
        without_runways = []
        for ad in qs:
            has = AerodromeRunway.objects.filter(icao_code=ad.icao_code, geom__isnull=False).exists()
            (with_runways if has else without_runways).append(ad)

        self.stdout.write(self.style.NOTICE(
            f'{len(with_runways)} aerodrome(s) with runway geometry, '
            f'{len(without_runways)} without (kept as ARP circles)'))

        created = 0
        skipped = 0
        for ad in with_runways:
            for radius in radii:
                buf = ad.get_or_create_runway_threshold_buffer(radius)
                if buf is not None:
                    created += 1
                    self.stdout.write(f'  {ad.icao_code}: {radius} km runway capsule ready')
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done: {created} runway-threshold buffer(s) in place, {skipped} skipped.'))