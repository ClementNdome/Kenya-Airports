# obstacle_compliance/management/commands/regenerate_buffers.py
from django.core.management.base import BaseCommand

from obstacle_compliance.models import Aerodrome, AerodromeRunway


class Command(BaseCommand):
    help = ('Regenerate AerodromeBuffer geometries in the local UTM zone '
            '(EPSG 32636/32637/32736/32737) instead of Web Mercator. '
            'Any radius works with either buffer type: runway capsules '
            'around the runway centreline(s) or ARP circles.')

    def add_arguments(self, parser):
        parser.add_argument('--radii', default='3,5,10',
                            help='Comma-separated radii in km (default 3,5,10)')
        parser.add_argument('--type', default='both', choices=['arp', 'runway', 'both'],
                            help="'runway': capsule (ARP circle fallback for "
                                 "aerodromes without runways); 'arp': circle; "
                                 "'both': capsule where runways exist, else circle")
        parser.add_argument('--icao', default=None,
                            help='Only process this aerodrome')

    def handle(self, *args, **options):
        radii = [int(r.strip()) for r in options['radii'].split(',') if r.strip()]
        buffer_type = options['type']
        qs = Aerodrome.objects.all()
        if options['icao']:
            qs = qs.filter(icao_code=options['icao'].upper())

        has_rw = set(AerodromeRunway.objects.filter(
            geom__isnull=False).values_list('icao_code', flat=True))

        created = 0
        skipped = 0
        for ad in qs:
            for radius in radii:
                if buffer_type == 'runway' or (buffer_type == 'both' and ad.icao_code in has_rw):
                    buf = ad.get_or_create_any_buffer(radius, 'runway')
                else:
                    buf = ad.get_or_create_any_buffer(radius, 'arp')
                if buf is not None:
                    created += 1
                    self.stdout.write(
                        f'  {ad.icao_code}: {radius} km {buf.type or "arp"} buffer regenerated '
                        f'(area {buf.area_km2} km²)')
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done: {created} buffer(s) regenerated, {skipped} skipped.'))
