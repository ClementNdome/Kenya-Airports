import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airports_kenya.settings')
sys.path.insert(0, '.')
django.setup()
from django.db import connection
cursor = connection.cursor()

schemas = {

    'public': ['aerodrome-runways','runways-declared_distances']
}

for schema, tables in schemas.items():
    for table in tables:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, [schema, table])
        cols = cursor.fetchall()
        print(f'\n--- {schema}.{table} ---')
        for c in cols:
            print(f'  {c[0]} | {c[1]} | nullable={c[2]}')




