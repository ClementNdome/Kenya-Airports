# KCAA Obstacle Compliance & Airport GIS System (Kenya)

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://kenya-airports.onrender.com/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.1-green)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

A Web GIS application built with **Django + GeoDjango** for the **Kenya Civil Aviation Authority (KCAA)** to regulate **Obstacle Limitation Surfaces (OLS)** around Kenyan aerodromes. Property developers, real estate agents, KCAA regulators, and the public can check whether a building or structure complies with KCAA regulations — and obtain official compliance certificates through an approval workflow.

> **Live Demo:** [kenya-airports.onrender.com](https://kenya-airports.onrender.com/)

---

## Screenshots

<!-- ![Dashboard Map](screenshots/dashboard.png) -->
<!-- ![Compliance Check](screenshots/compliance-check.png) -->
<!-- ![Analytics Dashboard](screenshots/analytics.png) -->
<!-- ![Certificate PDF](screenshots/certificate.png) -->

---

## Key Features

### 🔍 Compliance Checking
- Enter coordinates and building height to get instant **GREEN** (compliant), **YELLOW** (caution), or **RED** (hazard) status
- Uses real **KCAA/ICAO Obstacle Limitation Surface (OLS)** formulas — Inner Horizontal Surface (flat 45m up to 4 km), Conical Surface (5% slope from 4–6 km), and a 15 km regulatory zone
- Integrates **SRTM 30m Digital Elevation Model (DEM)** — served as a Cloud Optimized GeoTIFF via Cloudflare R2 / Spationex — for ground elevation at any point in Kenya
- **Batch check** up to 100 properties at once
- **Public quick check** (no login required)

### 🗺️ Interactive GIS Map
- Leaflet-based map with multiple basemaps (Carto Light/Dark, OSM, Satellite, Terrain)
- Toggleable aerodrome markers and pre-computed buffer zones (3, 5, 10, 15 km)
- Custom radius search, airport detail popups, drawing tools

### 👤 User Accounts & Property Portfolio
- Registration, login, and password reset flow
- Save properties (name, coordinates, height) with full CRUD
- Run and re-run compliance checks, track check history over time

### 📋 Compliance Certificate Workflow
- 6-state state machine: **Draft → Submitted → Under Review → Approved / Rejected / Revoked**
- KCAA admin review dashboard with transition controls and reviewer notes
- Auto-generated **KCAA certificate numbers** (e.g. `KCAA-20260708-00001`) and **PDF certificates** via xhtml2pdf
- Rejected applications can be resubmitted

### 📦 Bulk Upload
- Upload a CSV of properties (name, latitude, longitude, height)
- Automatic property creation + compliance checking in the background
- Detailed results with success/warning/error counts

### 🔌 REST API
- Token-authenticated **Django REST Framework** API
- Endpoints: aerodromes, buffers, properties, compliance checks, batch checks
- Interactive documentation: **Swagger UI** (`/api/docs/`) and **ReDoc** (`/api/redoc/`)
- Rate limited (100 requests/hour), pagination (50/page)

### 📊 Analytics Dashboard
- Chart.js visualizations: compliance status distribution, aerodrome type breakdown, recent check activity
- Personalized user dashboard with property stats and pending applications
- Downloadable **PDF compliance reports**

### 🔔 Notifications
- Real-time compliance status change detection via `post_save` signal
- In-app notification center (polled every 15 seconds) + email notifications
- Unread count badge in the navbar

### 🌐 Geocoding & Spatial Queries
- Address-to-coordinates via OpenStreetMap Nominatim (Kenya-focused, 24-hour cache)
- Reverse geocoding (coordinates to address)
- Find nearest airport, airports within a radius, airports near the equator, distance between two airports

---

## Tech Stack

| Category | Technologies |
|---|---|
| **Backend** | Python 3.12, Django 5.1, GeoDjango, Django REST Framework 3.15 |
| **Database** | PostgreSQL + PostGIS |
| **GIS & Spatial** | GDAL, Rasterio 1.4, Leaflet.js 1.9 + Leaflet Draw, django-leaflet, geopy, pyproj, numpy |
| **Frontend** | Bootstrap 5.3, Font Awesome 6, Chart.js 4.4, jQuery 3.6, Select2, Animate.css |
| **Admin** | django-jazzmin (dark theme) |
| **PDF** | xhtml2pdf, reportlab |
| **Caching** | Redis 7 (via hiredis) |
| **Storage** | Cloudflare R2 (S3-compatible), Whitenoise |
| **CI/CD** | GitHub Actions, GitLab CI, Docker |
| **Deployment** | Render (Docker), Heroku-ready |

---

## Architecture Overview

The project contains two Django apps:

- **`airports_strips`** — Legacy GIS demo app for airport visualization and basic spatial queries. Its data has been merged into the main app.
- **`obstacle_compliance`** — The core KCAA compliance system. Contains 8 models, 30+ views, a DRF API, 20+ templates, and the compliance calculation engine.

### Core Engine

The **`ComplianceCalculator`** (in `obstacle_compliance/utils.py`) implements KCAA/ICAO OLS formulas:

| Surface | Distance from Airport | Max Height Above Airport |
|---|---|---|
| Inner Horizontal (IHS) | 0–4 km | 45 m |
| Conical Surface | 4–6 km | 45 m + 5% gradient |
| Beyond OLS | >6 km | No restriction |
| Lighting Required | 0–15 km | If height > 30 m |
| High-Rise Notification | Any | If height > 90 m |

The **`DEMService`** loads a remote Cloud Optimized GeoTIFF via GDAL's `/vsicurl/` virtual filesystem, streaming only the bytes needed for each query. Results are cached at multiple levels (Python LRU cache + Django Redis cache).

<!-- ![Architecture Diagram](screenshots/architecture.png) -->

---

## Installation & Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ with PostGIS extension
- GDAL (system package on Linux, OSGeo4W on Windows)

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

# 4. Configure environment variables
# Copy the following into a .env file:
#   DATABASE_URL=postgres://user:pass@localhost:5432/kenya_airports
#   SECRET_KEY=your-django-secret-key
#   DEM_URL=https://your-bucket.r2.cloudflarestorage.com/dem.tif
#   AWS_ACCESS_KEY_ID=your-r2-key
#   AWS_SECRET_ACCESS_KEY=your-r2-secret
#   DEBUG=True

# 5. Create the database and enable PostGIS
psql -U postgres -c "CREATE DATABASE kenya_airports;"
psql -U postgres -d kenya_airports -c "CREATE EXTENSION postgis;"

# 6. Run migrations
python manage.py migrate

# 7. Load spatial data
python manage.py load_aerodromes
python manage.py load_buffers

# 8. Start the development server
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Usage

| Page | URL | Description |
|---|---|---|
| Dashboard & Map | `/` | Interactive map with airports, buffers, and compliance tools |
| Quick Check | `/quick-check/` | Public compliance check (no login) |
| Property Check | `/property-check/` | Full compliance check with DEM context |
| Property Portfolio | `/my-properties/` | Saved properties with check history |
| Applications | `/applications/` | Submit and track compliance certificates |
| Bulk Upload | `/bulk-upload/` | CSV batch compliance checking |
| Analytics | `/analytics/` | Charts and statistics dashboard |
| Admin Review | `/admin-review/` | KCAA admin application review |
| API Docs | `/api/docs/` | Swagger UI documentation |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/aerodromes/` | List/search aerodromes |
| `GET` | `/api/v1/buffers/` | List/filter buffer zones |
| `GET/POST/PUT/DELETE` | `/api/v1/properties/` | User property CRUD |
| `POST` | `/api/v1/check-compliance/` | Single compliance check |
| `POST` | `/api/v1/batch-check/` | Batch compliance check (max 100) |
| `GET` | `/api/airports.geojson` | All airports as GeoJSON |
| `GET` | `/api/buffers.geojson` | Buffer zones as GeoJSON |
| `GET` | `/api/geocode/?q=...` | Address-to-coordinates |
| `GET` | `/api/stats/` | System statistics |

API documentation is available at `/api/docs/` (Swagger) and `/api/redoc/` (ReDoc).

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
