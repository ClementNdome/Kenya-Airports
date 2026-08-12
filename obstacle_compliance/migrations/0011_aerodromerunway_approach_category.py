from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("obstacle_compliance", "0010_aerodromerunway_declareddistance"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                (
                    'ALTER TABLE "aerodrome-runways" ADD COLUMN IF NOT EXISTS '
                    "approach_category varchar(20) NULL"
                ),
                (
                    "UPDATE \"aerodrome-runways\" r SET approach_category ="
                    " CASE"
                    "   WHEN r.ofz IS NOT NULL AND UPPER(r.ofz) LIKE '%YES%' THEN 'precision_i'"
                    "   WHEN a.type ILIKE '%airstrip%' OR a.type ILIKE '%strip%' THEN 'non_instrument'"
                    "   ELSE 'non_precision'"
                    " END"
                    " FROM obstacle_compliance_aerodrome a"
                    " WHERE a.icao_code = r.icao_code"
                    "   AND r.approach_category IS NULL"
                ),
                (
                    "UPDATE \"aerodrome-runways\" SET approach_category = 'non_precision'"
                    " WHERE approach_category IS NULL"
                ),
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
