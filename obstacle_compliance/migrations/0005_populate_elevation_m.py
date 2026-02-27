from django.db import migrations

def parse_elevation_value(elev_str):
    """Copy of your parsing logic here (since model methods aren't available in migrations)"""
    if not elev_str:
        return None
    
    elev_str = str(elev_str).strip()
    import re
    
    # Pattern 1: "6945 FT (2117 M)" or "18 FT (5 M)"
    m_pattern = r'\((\d+(?:\.\d+)?)\s*M\)'
    match = re.search(m_pattern, elev_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Pattern 2: "1690 / 5546"
    if '/' in elev_str and 'FT' not in elev_str.upper():
        parts = elev_str.split('/')
        if parts:
            try:
                return float(parts[0].strip())
            except ValueError:
                pass
    
    # Pattern 3: Just a number
    try:
        return float(elev_str)
    except ValueError:
        pass
    
    # Pattern 4: Number followed by M
    m_alt_pattern = r'(\d+(?:\.\d+)?)\s*M(?!\()'
    match = re.search(m_alt_pattern, elev_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Pattern 5: Feet conversion
    ft_pattern = r'(\d+(?:\.\d+)?)\s*FT'
    match = re.search(ft_pattern, elev_str, re.IGNORECASE)
    if match:
        try:
            feet = float(match.group(1))
            return round(feet * 0.3048, 1)
        except ValueError:
            pass
    
    return None

def populate_elevation_m(apps, schema_editor):
    Aerodrome = apps.get_model('obstacle_compliance', 'Aerodrome')
    for airport in Aerodrome.objects.all():
        if airport.elevation_m_ft and airport.elevation_m is None:
            parsed_value = parse_elevation_value(airport.elevation_m_ft)
            if parsed_value is not None:
                airport.elevation_m = parsed_value
                airport.save()

class Migration(migrations.Migration):
    dependencies = [
        ('obstacle_compliance', '0004_add_elevation_m_field'),
    ]

    operations = [
        migrations.RunPython(populate_elevation_m),
    ]