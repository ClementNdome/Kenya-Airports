# Architecture

## Overview

Three Django packages make up the codebase:

| Package | Role |
|---|---|
| `airports_kenya` | Project configuration: `settings.py`, root `urls.py`, WSGI/ASGI |
| `airports_strips` | **Legacy** GIS demo app (airport visualisation + basic spatial queries). Its data was merged into the main app via `merge_airports_data` |
| `obstacle_compliance` | The **core KCAA compliance system**: 11 models, 45+ views, 36 templates, 12 migrations, 12 management commands, DRF API, OLS engine |

## URL Layout

- `/` and `/obstacle-compliance/` → `obstacle_compliance` (namespaces `obstacle_compliance` / `obstacle_compliance_v2`)
- `/airports-strips/` → legacy app
- `/admin` → Jazzmin admin
- `/api/v1/` → DRF API (`obstacle_compliance.api_urls`)
- `/api-auth/` → DRF auth
- `/api/schema/`, `/api/docs/swagger/`, `/api/docs/redoc/` → drf-spectacular OpenAPI docs
- `/service-worker.js` → PWA service worker (static)

## Core Engine Modules

| Module | Responsibility |
|---|---|
| `obstacle_compliance/ols_surfaces.py` | `RunwayOLS` / `AirportOLS` — full ICAO Annex 14 surface geometry: `ceiling_at()` queries, GeoJSON footprints, 3D surface slices; `reference_code()` from declared length |
| `obstacle_compliance/utils.py` | `DEMService` (remote COG elevation sampling via rasterio/GDAL `/vsicurl/`), `ComplianceCalculator` (per-airport + all-airport evaluation, terrain-breach grid, lighting rules, 0–100 score), `ApplicationWorkflow` (state machine), `process_bulk_upload`, `generate_certificate_pdf` |
| `obstacle_compliance/projection.py` | UTM zone selection (EPSG 32636/32637/32736/32737) + true-metric buffer/distance/area helpers |
| `obstacle_compliance/api.py` / `serializers.py` | DRF v1 ViewSets and compliance-check endpoints |
| `obstacle_compliance/signals.py` | `post_save` notifications + emails on status change |

## Data Flow

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

## Key Architectural Decisions

1. **Geodetic vs projected work is explicit.** True-metric buffers use the local UTM zone via `projection.py`; proximity lookups use a degree-bbox prefilter + exact pyproj WGS84 geodesic (`utils.get_airports_in_radius`). No planar-degree distance math remains in the buffer/proximity paths. See [ADRs](ADRs) → `ADR-projection-buffer-types`.
2. **OLS ceilings are surface-minima.** At any point, the controlling ceiling = minimum of all applicable Annex 14 surfaces (most restrictive wins), each computed from real runway geometry (thresholds, bearings, elevations) rather than centroid approximations — with a hybrid fallback for aerodromes without runway rows.
3. **Caching is multi-level.** DEM samples: Python LRU + Django cache (1 h TTL). GeoJSON views: cache_page TTLs (5–30 min). Geocode: 24 h (1 h for empty results), parcel-aware keys.
4. **Dual namespaces.** The app is served at `/` and `/obstacle-compliance/` — intentional, but pick a canonical URL for production SEO/canonicalisation.
5. **Unmanaged runway tables.** `AerodromeRunway` → `public."aerodrome-runways"`, `DeclaredDistance` → `public."runways-declared_distances"` (managed = False); declared distances joined on `(icao_code, TRIM(runway_pair))` — the pair column is whitespace-padded in the legacy data.

## Settings Highlights (`airports_kenya/settings.py`)

- `INSTALLED_APPS`: jazzmin, `django.contrib.gis`, `airports_strips`, `leaflet`, `obstacle_compliance`, `rest_framework` (+authtoken), `drf_spectacular`, `django_filters`
- Database: PostgreSQL + **PostGIS** engine
- Middleware includes **Whitenoise** (production static)
- Leaflet default view: Kenya centre (−0.0236, 37.9062), zoom 6, min 3, max 18
- DRF: Token + Session auth, default `IsAuthenticated`, throttle 100 req/h/user, page size 50
- Jazzmin admin: dark theme, "kenya airports Admin"
- **Not configured (installed but unused):** `django-cors-headers`, `django-debug-toolbar`, `django-environ`, `django-extensions`, Redis caching (falls back to LocMemCache)
- **Missing:** `MEDIA_URL`/`MEDIA_ROOT` (latent `AttributeError` risk in DEBUG static serving)
