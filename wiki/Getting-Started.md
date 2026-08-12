# Getting Started

## Prerequisites

- Python 3.11+ (3.12 recommended)
- PostgreSQL 14+ with the **PostGIS** extension
- GDAL / GEOS / PROJ
  - Linux: system packages (`libgdal-dev`, `libgeos-dev`, `libproj-dev`, ...)
  - Windows: [OSGeo4W](https://trac.osgeo.org/osgeo4w/) — `settings.py` auto-configures the GDAL library path on `nt`
- (Optional for maps) a [Mapbox](https://www.mapbox.com/) account for the GL JS 3D viewer and geocoding

## Environment Variables

All configuration is read from a `.env` file at the project root via `python-decouple`. The keys actually used:

| Variable | Required | Purpose |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No (default `False`) | Debug mode |
| `ALLOWED_HOSTS` | No (default `*`) | Comma-separated allowed hosts |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Yes | PostGIS connection |
| `DB_SSLMODE` | No | SSL mode for managed databases (e.g. Aiven/Render) |
| `DATABASE_URL` | Optional | Alternative `postgres://...` URL (parse branch is commented out in settings) |
| `DEM_URL` | Yes (for DEM features) | Cloud Optimized GeoTIFF URL of the SRTM 30 m DEM (Cloudflare R2) |
| `DEM_BUCKET_NAME`, `DEM_OBJECT_NAME` | No | R2 bucket/object (used by the demo CDN pattern) |
| `ACCESS_KEY`, `SECRET_KEY` (R2) | No | Cloudflare R2 credentials (media storage pattern) |
| `ENDPOINT_URL` | No | R2 S3 endpoint |
| `MAPBOX_ACCESS_TOKEN` | Yes (for maps) | Server-side Mapbox token (`sk.`) |
| `MAPBOX_PUBLIC_ACCESS_TOKEN` | Yes (for maps) | Client-side Mapbox token (`pk.`) |

> **Note:** `MEDIA_URL`/`MEDIA_ROOT` are not defined in `settings.py`; avoid file-upload flows in `DEBUG=True` until added.

## Setup Steps

```sh
# 1. Clone
git clone https://github.com/ClementNdome/Kenya-Airports.git
cd Kenya-Airports

# 2. Virtual environment
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Create the database with PostGIS
psql -U postgres -c "CREATE DATABASE kenya_airports;"
psql -U postgres -d kenya_airports -c "CREATE EXTENSION postgis;"

# 5. Write your .env (see table above)

# 6. Migrations
python manage.py migrate

# 7. Load spatial data
python manage.py load_aerodromes            # KCAA aerodrome GeoJSON
python manage.py load_buffers               # precomputed 3/5/10/15 km buffers
python manage.py merge_airports_data        # merge legacy airports_strips data
# (optional) regenerate buffers in true local UTM:
python manage.py regenerate_buffers --radii 3 5 10 --type both

# 8. Run
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## First-Run Sanity Checks

```sh
python manage.py check
python manage.py verify_data          # counts, buffer completeness, spatial sanity
python manage.py test_compliance      # sample checks: JKIA/Wilson/Mombasa/Kisumu
python manage.py test obstacle_compliance
```

## Notes

- The app is served at **both** `/` and `/obstacle-compliance/` (same routes, two URL namespaces) — either works locally and in production.
- DEM queries require `DEM_URL`; without it the map/compliance pages still work but elevation-aware features (terrain breaches, skyline) will fail.
- The runways data (`aerodrome-runways` + `runways-declared_distances` tables) is loaded externally; the Django models are unmanaged (`managed = False`).
