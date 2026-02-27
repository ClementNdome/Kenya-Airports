# obstacle_compliance/management/commands/update_aerodrome_names.py

from django.core.management.base import BaseCommand
from obstacle_compliance.models import Aerodrome

# Mapping of ICAO codes to names (without the code)
AERODROME_NAMES = {
    'HKEL': 'ELDORET INTL',
    'HKEM': 'EMBU',
    'HKFP': 'NORTHLANDS',
    'HKIS': 'ISIOLO',
    'HKJK': 'NAIROBI JOMO KENYATTA INTL',
    'HKKG': 'KAKAMEGA',
    'HKKI': 'KISUMU',
    'HKKT': 'KITALE AIRSTRIP',
    'HKLK': 'LOKICHOGGIO',
    'HKLU': 'LAMU MANDA',
    'HKMJ': 'MIGORI',
    'HKML': 'MALINDI',
    'HKMO': 'MOMBASA MOI INTL',
    'HKNL': 'NANYUKI CIVIL',
    'HKNW': 'NAIROBI WILSON',
    'HKOK': 'OLKIOMBO',
    'HKRE': 'NAIROBI EASTLEIGH',
    'HKUK': 'DIANI',
    'HKWJ': 'WAJIR',
}

class Command(BaseCommand):
    help = 'Update aerodrome names based on ICAO code mapping'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )
        parser.add_argument(
            '--icao',
            type=str,
            help='Update only a specific ICAO code (optional)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_icao = options.get('icao')
        
        # Filter queryset based on arguments
        if specific_icao:
            queryset = Aerodrome.objects.filter(icao_code=specific_icao)
            if not queryset.exists():
                self.stdout.write(
                    self.style.ERROR(f"No aerodrome found with ICAO code: {specific_icao}")
                )
                return
        else:
            queryset = Aerodrome.objects.filter(icao_code__in=AERODROME_NAMES.keys())
        
        updated_count = 0
        not_found_count = 0
        
        self.stdout.write(self.style.NOTICE("Starting aerodrome name update..."))
        
        for aerodrome in queryset:
            icao = aerodrome.icao_code
            
            if icao in AERODROME_NAMES:
                new_name = AERODROME_NAMES[icao]
                
                # Check if name needs updating (avoid unnecessary updates)
                if aerodrome.name != new_name:
                    old_name = aerodrome.name
                    
                    if dry_run:
                        self.stdout.write(
                            f"[DRY RUN] Would update {icao}: "
                            f"'{old_name}' -> '{new_name}'"
                        )
                    else:
                        aerodrome.name = new_name
                        aerodrome.save(update_fields=['name'])  # Only save the name field
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Updated {icao}: '{old_name}' -> '{new_name}'")
                        )
                    
                    updated_count += 1
                else:
                    self.stdout.write(f"✓ {icao} already has correct name: '{new_name}'")
            else:
                # This shouldn't happen with our filtered queryset, but just in case
                self.stdout.write(
                    self.style.WARNING(f"⚠ No name mapping found for {icao}")
                )
                not_found_count += 1
        
        # Summary
        self.stdout.write("=" * 50)
        if dry_run:
            self.stdout.write(
                self.style.NOTICE(f"DRY RUN SUMMARY: Would update {updated_count} aerodromes")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"COMPLETED: Updated {updated_count} aerodromes")
            )
        
        if specific_icao:
            self.stdout.write(f"Targeted ICAO: {specific_icao}")
        else:
            total_expected = len(AERODROME_NAMES)
            self.stdout.write(f"Expected: {total_expected} aerodromes")
            self.stdout.write(f"Updated: {updated_count}")
            self.stdout.write(f"Not found in mapping: {not_found_count}")
        
        # Optional: Check for aerodromes in mapping that weren't found in database
        if not specific_icao and not dry_run:
            db_icaos = set(queryset.values_list('icao_code', flat=True))
            mapped_icaos = set(AERODROME_NAMES.keys())
            missing_from_db = mapped_icaos - db_icaos
            
            if missing_from_db:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nWarning: These ICAO codes from mapping were not found in database: "
                        f"{', '.join(sorted(missing_from_db))}"
                    )
                )