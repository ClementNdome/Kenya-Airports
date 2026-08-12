# KCAA Obstacle Compliance & Airport GIS System (Kenya)

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://kenya-airports.onrender.com/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.1-green)](https://www.djangoproject.com/)
[![PostGIS](https://img.shields.io/badge/PostGIS-required-336791)](https://postgis.net/)
[![DRF](https://img.shields.io/badge/DRF-3.15-purple)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

A Web GIS application built with **Django + GeoDjango** for the **Kenya Civil Aviation Authority (KCAA)** to regulate **Obstacle Limitation Surfaces (OLS)** around Kenyan aerodromes. Property developers, real estate agents, KCAA regulators, and the public can check whether a building or structure complies with KCAA regulations — and obtain official compliance certificates through an approval workflow.

The OLS engine implements the full **ICAO Annex 14 Vol I (8th ed.)** surface geometry — approach, inner approach, transitional, balked-landing and take-off-climb surfaces plus the ARP-centred Inner Horizontal, Conical and Outer Horizontal surfaces — in accordance with **KCAA Advisory Circular AC-AGA005C** (June 2024) and obstacle lighting per **AC-AGA032A** (Feb 2026).

> **Live Demo:** [kenya-airports.onrender.com](https://kenya-airports.onrender.com/)

---

## Screenshots

<!-- ![Dashboard Map](screenshots/dashboard.png) -->
<!-- ![3D OLS Viewer](screenshots/3d-ols.png) -->
<!-- ![Compliance Check](screenshots/compliance-check.png) -->
<!-- ![Analytics Dashboard](screenshots/analytics.png) -->
<!-- ![Certificate PDF](screenshots/certificate.png) -->

---

## Key Features

### 🔍 Compliance Checking
- Enter coordinates and building height to get instant **GREEN** (compliant), **YELLOW** (caution), or **RED** (hazard) status, with a 0–100 compliance score
- Full **ICAO Annex 14 OLS evaluation**: approach/inner-approach/transitional/balked-landing/take-off-climb surfaces (per runway, per end) plus ARP-centred IHS, Conical and Outer Horizontal surfaces
- **SRTM 30 m Digital Elevation Model (DEM)** integration — served as a Cloud Optimized GeoTIFF via Cloudflare R2 and streamed through rasterio/GDAL (`/vsicurl/`), multi-level cached
- **Terrain breach detection** — samples the DEM against the controlling OLS ceiling and flags natural terrain that penetrates surfaces
- **Batch check** up to 100 properties at once
- **Public quick check** (no login required)
- **Public property query** — read-only browser of previously checked properties (filter by aerodrome + radius, height, or status)

### 🗺️ Interactive GIS Map
- Leaflet-based 2D map with multiple basemaps (Carto Light/Dark, OSM, Satellite, Terrain) and a **Mapbox GL JS 3D OLS viewer** (satellite terrain + fill-extrusion buildings and stepped OLS surface slices)
- Toggleable layers: aerodromes, pre-computed buffers (ARP circles vs runway-threshold capsules, 3/5/10 km presets + custom radius), runways, OLS footprints, terrain breaches, flyover simulation, skyline, user layers, and your saved properties
- **4D flyover simulation** — flight-path playback along the approach with clear/warn/breach colour-coding against OLS ceilings
- **Skyline layer** — grid heatmap of maximum allowed AGL height (OLS ceiling minus terrain)
- **Custom radius builder** and buffer-type toggle (ARP point vs runway capsule), true-metric geometry via local UTM projection
- **User layers** — save persistent, toggleable custom geometries
- Airport detail popups and drawing tools (Leaflet-Draw)

### 👤 User Accounts & Property Portfolio
- Registration, login, and password reset flow; company/phone/organization-type profile
- Save properties (name, coordinates, height, optional parcel polygon) with full CRUD
- Run and re-run compliance checks, track check history over time, export portfolio to CSV

### 📋 Compliance Certificate Workflow
- 6-state state machine: **Draft → Submitted → Under Review → Approved / Rejected / Revoked**
- KCAA admin review dashboard with transition controls, reviewer notes, and automatic OLS re-check on action
- Auto-generated **KCAA certificate numbers** (e.g. `KCAA-20260708-00001`) and **PDF certificates** via xhtml2pdf
- Certificate carries the OLS verdict snapshot (status, score, ceiling AMSL, headroom) and last-checked date
- Rejected applications can be resubmitted

### 📦 Bulk Upload
- Upload a CSV of properties (name, latitude, longitude, height)
- Automatic property creation + compliance checking
- Detailed results with success/warning/error counts and downloadable error log

### 🔌 REST API
- Token-authenticated **Django REST Framework** API (`/api/v1/`)
- Endpoints: aerodromes, buffers, properties (user-scoped CRUD), single & batch compliance checks
- GeoJSON endpoints for airports, buffers, runways, OLS footprints, terrain breaches, flyover, skyline, my properties, and user layers
- Interactive documentation: **Swagger UI** (`/api/docs/swagger/`) and **ReDoc** (`/api/docs/redoc/`)
- Rate limited (100 requests/hour), pagination (50/page)

### 📊 Analytics Dashboard
- Chart.js visualizations: compliance status distribution, aerodrome type breakdown, recent check activity
- Personalized user dashboard with property stats and pending applications
- Downloadable **PDF compliance reports**

### 🔔 Notifications
- Compliance status-change detection via `post_save` signals
- In-app notification center (polled every 15 seconds) + email notifications
- Unread count badge in the navbar

### 🌐 Geocoding & Spatial Queries
- Address-to-coordinates via **Mapbox with OpenStreetMap Nominatim fallback** (Kenya-bounded, merged/deduped, 24-hour cache, airport-name blending)
- Reverse geocoding (coordinates to address)
- Find nearest airport, airports within a radius, airports near the equator, distance between two airports

---

## OLS Model

The controlling OLS ceiling at any point is the **minimum** of all applicable surfaces (most restrictive):

| Surface | Extent | Max Height Above Airport / Slope |
|---|---|---|
| Inner Horizontal (IHS) | 0–4 km from ARP | 45 m flat (radius 2–4 km by category/code) |
| Conical Surface | 4–6 km from ARP | 5% gradient (up to 35–100 m) |
| Outer Horizontal | 15 km radius (codes 3–4, KCAA AC AGA005C §4.2.1.3) | 150 m flat |
| Approach (per end, by category) | from threshold to 15 km | stepped (e.g. 2% + 2.5% slopes) |
| Inner Approach / Transitional / Inner Transitional | strip area | 20% / 40% slopes |
| Balked Landing / Take-off Climb | over the runway | 3.33% / 2.5% (Table 4-2) |
| Obstacle Lighting | > 30 m AGL and > 150 m above aerodrome elevation within 15 km | light levels = ⌈height / 45 m⌉ (AC AGA032A) |

Buffers are computed as **true-metric geometries** in the local UTM zone (EPSG 32636/32637/32736/32737) — ARP-circle buffers, or runway "capsule" (stadium) buffers around the runway centerline — never planar degree math.

---

## Tech Stack

| Category | Technologies |
|---|---|
| **Backend** | Python 3.12, Django 5.1.6, GeoDjango, Django REST Framework 3.15.2 |
| **Database** | PostgreSQL + PostGIS |
| **GIS & Spatial** | GDAL, Rasterio 1.4, Shapely, pyproj 3.7, geopy, numpy, django-leaflet, Leaflet.js 1.9 + Leaflet-Draw, Mapbox GL JS (3D) |
| **Frontend** | Bootstrap 5.3, Font Awesome 6, Chart.js 4.4, jQuery, Select2 |
| **Admin** | django-jazzmin (dark theme) + LeafletGeoAdmin |
| **PDF** | xhtml2pdf, reportlab |
| **Caching** | Django cache framework (Redis-ready via `hiredis`/`redis`) |
| **Storage** | Cloudflare R2 (S3-compatible COGs), Whitenoise static |
| **CI/CD** | GitHub Actions, GitLab CI (Auto-DevOps + PostGIS service) |
| **Deployment** | Docker, gunicorn, Render, Heroku-ready (Procfile) |

---

## Architecture Overview

Three Django packages:

- **`airports_kenya`** — project configuration package (settings, root URLs, WSGI/ASGI).
- **`airports_strips`** — legacy GIS demo app (airport visualization and basic spatial queries). Its data has been merged into the main app via `merge_airports_data`.
- **`obstacle_compliance`** — the core KCAA compliance system: **11 models**, **45+ views**, **12 migrations**, **12 management commands**, **36 templates**, a DRF API, and the OLS calculation engine.

### Core Engine

| Module | Responsibility |
|---|---|
| `ols_surfaces.py` | `RunwayOLS` / `AirportOLS` — Annex 14 surface geometry, `ceiling_at()` queries, GeoJSON footprints, 3D surface slices; `reference_code()` from declared length |
| `utils.py` | `DEMService` (remote COG elevation sampling), `ComplianceCalculator` (per-airport and all-airport evaluation, terrain breach grid, lighting rules, 0–100 score), `ApplicationWorkflow` (state machine), `process_bulk_upload`, `generate_certificate_pdf` |
| `projection.py` | UTM zone selection and true-metric projection helpers (buffers, distances, areas) |
| `api.py` / `serializers.py` | DRF v1 ViewSets and compliance-check endpoints |

The **`DEMService`** loads a remote Cloud Optimized GeoTIFF via GDAL's `/vsicurl/` virtual filesystem, streaming only the bytes needed per query; results are cached at multiple levels (Python LRU + Django cache with 1-hour TTL).

```
┌─────────────┐   ┌──────────────────┐   ┌─────────────────┐   ┌───────────────┐
│ Browser/Map │──▶│ Django Views     │──▶│ ComplianceCalc. │──▶│ AirportOLS /  │
│ (Leaflet +  │   │ (web + GeoJSON)  │   │ DEMService      │   │ RunwayOLS     │
│  Mapbox GL) │   └──────────────────┘   └─────────────────┘   └───────────────┘
└─────────────┘          │                       │                      │
              ┌──────────┴─────────┐    ┌─────────┴────────┐   ┌────────┴────────┐
              │ DRF API (/api/v1/) │    │ PostGIS database │   │ Cloudflare R2   │
              │ Swagger / ReDoc    │    │ (GeoDjango)      │   │ DEM COG + media │
              └────────────────────┘    └──────────────────┘   └─────────────────┘
```

The app is served at both `/` and `/obstacle-compliance/` (the same routes under two namespaces).

---

## Installation & Setup

### Prerequisites

- Python 3.11+ (3.12 recommended)
- PostgreSQL 14+ with the PostGIS extension
- GDAL / GEOS / PROJ (system packages on Linux; OSGeo4W on Windows — `settings.py` auto-configures GDAL on Windows)

### Steps

```sh
# 1. Clone the repository
git clone https://github.com/ClementNdome/Kenya-Airports.git
cd Kenya-Airports

# 2. Create and activate a virtual environment
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables in a .env file
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=kenya_airports
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
# Remote DEM (Cloud Optimized GeoTIFF)
DEM_URL=https://your-bucket.r2.cloudflarestorage.com/dem.tif
# Mapbox (server + public client tokens)
MAPBOX_ACCESS_TOKEN=sk.your-server-token
MAPBOX_PUBLIC_ACCESS_TOKEN=pk.your-public-token

# 5. Create the database and enable PostGIS
psql -U postgres -c "CREATE DATABASE kenya_airports;"
psql -U postgres -d kenya_airports -c "CREATE EXTENSION postgis;"

# 6. Run migrations
python manage.py migrate

# 7. Load spatial data
python manage.py load_aerodromes            # KCAA aerodrome GeoJSON
python manage.py load_buffers               # precomputed 3/5/10/15 km buffers
python manage.py merge_airports_data        # merge legacy airports_strips data
# (optional) regenerate buffers in local UTM:
python manage.py regenerate_buffers --radii 3 5 10 --type both

# 8. Start the development server
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Usage

| Page | URL | Description |
|---|---|---|
| Dashboard & Map | `/` | Overview map with airports, buffers, and quick stats |
| Interactive Map | `/map/` | Full map: OLS 3D viewer, flyover, skyline, terrain breaches, user layers |
| Property Check | `/property-check/` | Full compliance check with DEM context, parcel drawing, 3D scene, PDF report |
| Quick Check | `/quick-check/` | Public compliance check (no login) |
| Property Query | `/property-query/` | Public read-only browser of checked properties |
| Airport Directory | `/airports/` | Searchable list + detail pages per ICAO code |
| Property Portfolio | `/my-properties/` | Saved properties with check history and CSV export |
| Applications | `/applications/` | Submit and track compliance certificates |
| Admin Review | `/admin-review/` | KCAA admin application review with approve/reject |
| Bulk Upload | `/bulk-upload/` | CSV batch compliance checking |
| Analytics | `/analytics/` | Charts and statistics dashboard |
| Notifications | `/notifications/` | In-app notification center |
| API Docs | `/api/docs/swagger/` | Swagger UI (ReDoc at `/api/docs/redoc/`) |

---

## API Endpoints

### REST API v1 (`/api/v1/`, token-authenticated)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/aerodromes/` | List/search aerodromes |
| `GET` | `/api/v1/buffers/` | List/filter buffer zones |
| `GET/POST/PUT/DELETE` | `/api/v1/properties/` | User property CRUD (user-scoped) |
| `POST` | `/api/v1/check-compliance/` | Single compliance check |
| `POST` | `/api/v1/batch-check/` | Batch compliance check (max 100) |

### GeoJSON & Utility Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/airports.geojson` | All aerodromes as points with elevation/buffer flags |
| `GET` | `/api/buffers.geojson?radius=&icao=&type=` | Buffer zones (auto-creates missing; `type=arp`/`runway`) |
| `GET` | `/api/runways.geojson` | Runway centerlines, strips, thresholds, declared distances |
| `GET` | `/api/ols.geojson` | Annex 14 OLS surface footprints with 3D heights |
| `GET` | `/api/terrain-breaches.geojson` | DEM terrain penetrations of the controlling OLS |
| `GET` | `/api/flyover.geojson?icao=&step=` | 4D flyover path simulation with clear/warn/breach segments |
| `GET` | `/api/skyline.geojson?icao=&step=` | Max allowed AGL height grid (OLS − terrain) |
| `GET` | `/api/my-properties.geojson` | Logged-in user's saved properties |
| `GET` | `/api/user-layers.geojson` | User's custom layers (save/delete via `/api/user-layers/...`) |
| `GET` | `/api/check-compliance/?lat=&lon=&height=` | Compliance check (public) |
| `POST` | `/api/batch-check/` | Batch check (public) |
| `GET` | `/api/search/?q=` | Airport autocomplete |
| `GET` | `/api/geocode/?q=` | Address-to-coordinates (Mapbox + Nominatim, Kenya-bounded) |
| `GET` | `/api/reverse-geocode/` | Coordinates-to-address |
| `GET` | `/api/airports/nearest/` | Nearest airport to a point |
| `GET` | `/api/airports/within-radius/` | Airports within a radius |
| `GET` | `/api/airports/near-equator/` | Airports near the equator |
| `GET` | `/api/airports/distance-between/` | Geodesic distance between two airports |
| `GET` | `/api/stats/` | System statistics |
| `POST` | `/api/generate-report/` | PDF compliance report |

API documentation is available at `/api/docs/swagger/` (Swagger) and `/api/docs/redoc/` (ReDoc).

---

## Management Commands

| Command | Purpose |
|---|---|
| `load_aerodromes` | Load KCAA aerodrome GeoJSON (DMS → decimal conversion) |
| `load_buffers` | Load precomputed buffers from GeoJSON via LayerMapping |
| `merge_airports_data` | Merge `airports_strips.Airports` data into `Aerodrome` |
| `add_threshold_buffers` | Backfill runway-threshold (capsule) buffers (`--icao`, `--radii`) |
| `regenerate_buffers` | Regenerate all buffers in local UTM (`--radii`, `--type`, `--icao`) |
| `verify_data` | Data sanity audit: counts, buffer completeness, spatial checks |
| `process_bulk_upload` | Process pending `BulkUploadJob`s (`--job`) |
| `send_notifications` | Notification utility (unread counts per user) |
| `test_compliance` | Sample compliance checks (JKIA/Wilson/Mombasa/Kisumu/custom) |
| `test_elevation` | Elevation-parsing audit table |
| `test_dem` / `test_dem_detailed` | DEM sampling diagnostics |

---

## Testing

```sh
python manage.py test obstacle_compliance
```

**32 tests** covering reference-code thresholds, Annex 14 approach/inner-approach/transitional/balked-landing/take-off-climb surfaces, conical/outer-horizontal/IHS ceilings, footprint generation, 3D surface slices, and UTM projection (zone selection, true-metric buffers, geodesic distances). All are `SimpleTestCase` — no database required. A hand-computed verification matrix against the Annex 14 tables lives in [`docs/OLS_VERIFICATION_MATRIX.md`](docs/OLS_VERIFICATION_MATRIX.md).

---

## Documentation

| Resource | Description |
|---|---|
| [`docs/ADRs/`](docs/ADRs/) | Architecture Decision Records — implemented: UTM projection & buffer types, property-query-public; tracked/deferred: 3D OLS, map-layer checker, per-surface OLS layer independence |
| [`docs/an14_v1.pdf`](docs/an14_v1.pdf) | ICAO Annex 14 Vol I (regulatory reference) |
| [`docs/CAA-AC-AGA005C CONTROL OF OBSTACLES.pdf`](docs/CAA-AC-AGA005C%20CONTROL%20OF%20OBSTACLES.pdf) | KCAA AC AGA005C (June 2024) — obstacle control |
| [`docs/CAA-AC-AGA032A Lighting and Marking of Obstacles.pdf`](docs/CAA-AC-AGA032A%20Lighting%20and%20Marking%20of%20Obstacles.pdf) | KCAA AC AGA032A (Feb 2026) — obstacle lighting |
| [`docs/OLS_VERIFICATION_MATRIX.md`](docs/OLS_VERIFICATION_MATRIX.md) | Hand-computed OLS engine verification vs Annex 14 |
| [`docs/specific use case.md`](docs/specific%20use%20case.md) | Full product specification, methodology, and phasing |

---

## Deployment

- **Docker**: `Dockerfile` (python:3.12-slim + GDAL/GEOS/PROJ system libs, `collectstatic`, gunicorn on :8080)
- **Gunicorn**: `gunicorn.conf.py` (3 workers, timeouts, `max_requests`), `Procfile` for Render/Heroku
- **Static files**: Whitenoise serving `staticfiles/` (collectstatic output)
- **CI**: `.github/workflows/django.yml` (Django CI) and `.gitlab-ci.yml` (Auto-DevOps + `postgis/postgis:15-3.3` service)
- Requires a **remote PostGIS** database and the Cloudflare R2 DEM bucket in production

---

## Roadmap & Backlog

Deferred items tracked in `docs/ADRs/`:

- Per-surface OLS layer independence with distinct colours/legend (ADR)
- Leaflet → Mapbox/MapLibre full migration (decision gate = 3D prototype)
- Merge property-query into property-check; minimal property-check card on `/map/`
- 3D snapshot embedded in PDF reports
- Full SFCGAL 3D OLS surfaces
- Layer-checker card with per-surface OLS toggles

Future product directions (see `TO ADD.MD`): flight planning & operations, safety/emergency response (SAR, emergency landing sites), infrastructure capacity analysis, economic/tourism corridor mapping, regulatory airspace/noise monitoring, pilot training tools, weather integration, and disaster management routing.

---

## Live Demo

The application is hosted on Render:

[**kenya-airports.onrender.com**](https://kenya-airports.onrender.com/)

---

## Repository

Source code on GitHub:

[github.com/ClementNdome/Kenya-Airports](https://github.com/ClementNdome/Kenya-Airports)

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Contact

For issues, feature requests, or questions, please use the [GitHub Issues](https://github.com/ClementNdome/Kenya-Airports/issues) page.
