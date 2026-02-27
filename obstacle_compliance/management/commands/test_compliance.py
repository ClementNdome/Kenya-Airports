# management/commands/test_compliance.py

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from obstacle_compliance.utils import ComplianceCalculator
from obstacle_compliance.models import Aerodrome

class Command(BaseCommand):
    help = 'Test compliance calculator with sample properties'

    def add_arguments(self, parser):
        parser.add_argument('--lat', type=float, help='Latitude for custom test')
        parser.add_argument('--lon', type=float, help='Longitude for custom test')
        parser.add_argument('--height', type=float, default=30, help='Height in meters')

    def handle(self, *args, **options):
        calculator = ComplianceCalculator()
        
        # Test locations
        test_points = [
            {
                'name': 'JKIA Terminal',
                'point': Point(36.9278, -1.3192, srid=4326),
                'height': 25,
                'description': 'Near JKIA'
            },
            {
                'name': 'Wilson Area',
                'point': Point(36.8150, -1.3186, srid=4326),
                'height': 45,
                'description': 'Near Wilson Airport'
            },
            {
                'name': 'Mombasa CBD',
                'point': Point(39.6685, -4.0435, srid=4326),
                'height': 50,
                'description': 'Near Moi International'
            },
            {
                'name': 'Kisumu CBD',
                'point': Point(34.7487, -0.1022, srid=4326),
                'height': 35,
                'description': 'Near Kisumu Airport'
            }
        ]
        
        # Add custom test if provided
        if options['lat'] and options['lon']:
            test_points.append({
                'name': 'Custom Location',
                'point': Point(options['lon'], options['lat'], srid=4326),
                'height': options['height'],
                'description': f'Custom test at {options["lat"]}, {options["lon"]}'
            })
        
        for test in test_points:
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.MIGRATE_HEADING(
                f"📍 {test['name']} - {test['description']}"
            ))
            self.stdout.write("="*70)
            
            result = calculator.evaluate_property_all_airports(
                test['point'], 
                test['height']
            )
            
            # Status with color
            status = result['status']
            if status == 'GREEN':
                status_display = self.style.SUCCESS(f"● {status}")
            elif status == 'YELLOW':
                status_display = self.style.WARNING(f"● {status}")
            elif status == 'RED':
                status_display = self.style.ERROR(f"● {status}")
            else:
                status_display = self.style.NOTICE(f"● {status}")
            
            self.stdout.write(f"Status: {status_display} (Score: {result.get('compliance_score', 'N/A')})")
            self.stdout.write(f"Message: {result.get('message', 'N/A')}")
            
            if result.get('primary_airport'):
                pa = result['primary_airport']
                self.stdout.write(self.style.MIGRATE_LABEL(
                    f"\nPrimary Airport: {pa['name']} ({pa['icao_code']})"
                ))
                self.stdout.write(f"  Distance: {pa['distance_km']}km")
                self.stdout.write(f"  Type: {pa.get('type', 'N/A')}")
            
            # Show detailed primary result
            if result.get('primary_result'):
                pr = result['primary_result']
                self.stdout.write("\n📊 Detailed Analysis:")
                self.stdout.write(f"  Ground Elevation: {pr.get('ground_elevation', 'N/A')}m AMSL")
                self.stdout.write(f"  Building Top: {pr.get('building_top_amsl', 'N/A')}m AMSL")
                if pr.get('max_allowed_agl'):
                    self.stdout.write(f"  Max Allowed AGL: {pr['max_allowed_agl']}m")
                if pr.get('headroom') is not None:
                    headroom = pr['headroom']
                    if headroom < 0:
                        hr_style = self.style.ERROR
                    elif headroom < 5:
                        hr_style = self.style.WARNING
                    else:
                        hr_style = self.style.SUCCESS
                    self.stdout.write(f"  Headroom: {hr_style(f'{headroom}m')}")
            
            # Show affected airports
            if result.get('airports_affected'):
                self.stdout.write(self.style.MIGRATE_LABEL("\n🛩️ Affected Airports:"))
                for apt in result['airports_affected']:
                    apt_status = apt['status']
                    if apt_status == 'GREEN':
                        apt_display = self.style.SUCCESS(f"{apt_status}")
                    elif apt_status == 'YELLOW':
                        apt_display = self.style.WARNING(f"{apt_status}")
                    elif apt_status == 'RED':
                        apt_display = self.style.ERROR(f"{apt_status}")
                    else:
                        apt_display = apt_status
                    
                    self.stdout.write(
                        f"  • {apt['name']} ({apt['icao']}): "
                        f"{apt['distance_km']}km "
                        f"[{apt_display}]"
                    )
            
            # Show requirements
            requirements = []
            if result.get('requires_lighting'):
                requirements.append(self.style.WARNING("⚠ Lighting Required"))
            if result.get('is_hazard'):
                requirements.append(self.style.ERROR("⛔ HAZARD DETECTED"))
            
            if requirements:
                self.stdout.write("\n" + "\n".join(requirements))
            
            # Show zone info
            if result.get('primary_result'):
                pr = result['primary_result']
                zones = []
                if pr.get('within_ihs_zone'):
                    zones.append("Inner Horizontal Surface (0-4km)")
                if pr.get('within_conical_zone') and not pr.get('within_ihs_zone'):
                    zones.append("Conical Surface (4-6km)")
                if pr.get('within_15km_zone') and not pr.get('within_conical_zone'):
                    zones.append("15km Regulatory Zone (6-15km)")
                
                if zones:
                    self.stdout.write("\n📍 Zones:")
                    for zone in zones:
                        self.stdout.write(f"  • {zone}")
            
            # Show compliance score breakdown if available
            if result.get('compliance_score') is not None:
                score = result['compliance_score']
                if score >= 80:
                    score_style = self.style.SUCCESS
                elif score >= 50:
                    score_style = self.style.WARNING
                else:
                    score_style = self.style.ERROR
                
                self.stdout.write(f"\n📈 Compliance Score: {score_style(f'{score}/100')}")