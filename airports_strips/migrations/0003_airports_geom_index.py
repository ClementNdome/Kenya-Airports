# Generated by Django 5.1.6 on 2025-02-10 22:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("airports_strips", "0002_alter_airports_geom"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="airports",
            index=models.Index(fields=["geom"], name="geom_index"),
        ),
    ]
