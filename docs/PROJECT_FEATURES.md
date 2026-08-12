# Kenya-Airports — Project Features & Implementation Overview

> Single reference of **everything that has been built** in this application.
> Last updated: 2026-08-12. Companion docs: `README.md` (runbook), `docs/ADRs/`
> (decision log), `docs/OLS_VERIFICATION_MATRIX.md` (engine verification),
> `docs/specific use case.md` (product narrative).

---

## 1. Overview

A Web GIS application built with **Django + GeoDjango** for the **Kenya Civil
Aviation Authority (KCAA)** to regulate **Obstacle Limitation Surfaces (OLS)**
around Kenyan aerodromes. Property developers, real estate agents, KCAA
regulators and the public can check whether a building/structure complies with
KCAA regulations — and obtain official compliance certificates through an
approval workflow.

- **Live demo:** https://kenya-airports.onrender.com
- **Repository:** https://github.com/ClementNdome/Kenya-Airports
- **License:** MIT

The OLS engine implements the full **ICAO Annex 14 Vol I (8th ed., 2018)**
surface geometry (Tables 4-1, 4-2, 3-1, 1-1), mirrored by the KCAA Civil
Aviation (Aerodromes Design and Operations) Regulations 2018, in accordance
with **KCAA AC AGA005C — Control of Obstacles (June 2024)** and obstacle
lighting per **AC AGA032A — Lighting and Marking of Obstacles (Feb 2026)**.
Source PDFs are kept in `docs/`.

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1.6, GeoDjango, Python 3.12 |
| Database | PostgreSQL + **PostGIS** (external tables for runways/declared distances) |
| API | Django REST Framework 3.15.2, djangorestframework-gis, drf-spectacular (Swagger/ReDoc) |
| Mapping (2D) | django-leaflet 0.31, Leaflet 1.9.4, Leaflet-Draw 1.0.4 |
| Mapping (3D) | Mapbox GL JS (fill-extrusion terrain + OLS surfaces) |
| Geospatial engine | rasterio 1.4 + GDAL (`/vsicurl/` COG streaming), pyproj, geopy |
| Documents | xhtml2pdf 0.2.17 (certificates + compliance reports) |
| Admin | django-jazzmin (dark theme) + LeafletGeoAdmin |
| Frontend | Bootstrap 5.3.0-alpha1, FontAwesome 6, jQuery 3.6, Chart.js 4.4.0, animate.css |
| Infra | Redis/hiredis (cache), boto3 + Cloudflare R2 (media/DEM), Whitenoise (static), Render (deploy) |

## 3. Architecture

```
Kenya-Airports/
├── airports_kenya/            # Project settings, URLs, WSGI/ASGI
├── obstacle_compliance/       # CORE app: OLS engine, compliance, workflow, GIS
├── airports_strips/           # LEGACY app: OurAirports dataset + exploratory pages
├── data/                      # Import scripts + source datasets (GPKG, GeoJSON, CSV)
├── docs/                      # Regulatory PDFs, ADRs, verification matrix
├── static/                    # geocode-widget.js/.css, service-worker.js
└── templates (per-app)        # 36+ templates
```

- The core app is mounted at **both** `/` and `/obstacle-compliance/`
  (URL namespaces `obstacle_compliance` and `obstacle_compliance_v2`).
- Legacy app under `airports-strips/` (kept; its map shows a migration banner
  pointing to the Unified Map).
- `api/v1/` — DRF token API; `api/schema/`, `api/docs/swagger/`,
  `api/docs/redoc/` — OpenAPI docs.

## 4. Data Model (11 models, migrations 0001–0012)

| Model | Purpose / key fields |
|---|---|
| `Aerodrome` | KCAA aerodrome point: `icao_code`, `name`, `type`, DMS lat/lon, `elevation_m_ft` auto-parsed to `elevation_m` (5-pattern parser), `geoid_undulation_m`, admin contacts, `traffic_permitted`, `geom` (Point 4326). Data-unification: `iata_code`, `runway_length_m`, `nearest_city`, `airlines`, `source` (geojson/geopackage/merged), `last_synced`. Buffer builders: `get_or_create_buffer`, `runway_capsule`, `get_or_create_any_buffer` (arp/runway). |
| `AerodromeBuffer` | Precomputed zones: `radius_km` (3/5/10/15), `area_km2`, `layer` (`<r>km_buffer` / `<r>km_runway_capsule`), `geom` MultiPolygon 4326 with GiST index, unique (aerodrome, radius_km). |
| `AerodromeRunway` | Unmanaged table `aerodrome-runways` (23 runways / 19 aerodromes): centreline LineString, designators, threshold elevations/bearings, declared dimensions, strip/OFZ/RESA, `approach_category` (non_instrument/non_precision/precision_i/precision_ii_iii) — drives Table 4-1 OLS dimensions. `.declared` joins DeclaredDistance. |
| `DeclaredDistance` | Unmanaged `runways-declared_distances`: TORA/TODA/ASDA/LDA per end (`parse()` handles padded runway_pair). |
| `UserProfile` | OneToOne→User: company, phone, organization_type (developer/architect/agent/public/kcaa/other); auto-created via signal. |
| `Property` | User portfolio: name, address, lat/lon, `height_m` (AGL), `geom` auto-set, `parcel_boundary`, cached `last_status/score/checked`, `run_compliance_check()`. |
| `ComplianceCheck` | Verdict history: `result_json` (full payload), status, score, primary airport, `requires_lighting`, `is_hazard`, `trigger` (manual/auto/bulk/api). |
| `Notification` | 5 types (status_change/regulation_update/application_update/reassessment/bulk_complete), `is_read`, `email_sent`. |
| `ComplianceApplication` | 6-state certificate workflow + `certificate_number` (KCAA-YYYYMMDD-#####), `certificate_pdf`, `valid_until`, `fee_paid`, OLS verdict snapshot (`last_status/score/ceiling_amsl/headroom_m/checked`). |
| `UserLayer` | Persistent user geometry layers: type (buffer/check_result/parcel/custom), GeometryField, JSON properties. |
| `BulkUploadJob` | CSV job lifecycle: pending/processing/completed/failed, per-row counts, `error_log`, `results_file`. |

**Migration timeline:** 0001 initial → 0002 buffers → 0003 decimal coords →
0004/0005 elevation_m (data migration) → 0006 aerodrome data unification →
0007 Property/ComplianceCheck/UserProfile → 0008 applications/notifications/
bulk upload → 0009 notification email flag → 0010 runways + declared distances →
0011 approach_category backfill → 0012 application OLS snapshot + UserLayer.

## 5. OLS Compliance Engine

### 5.1 Regulatory basis
- ICAO Annex 14 Vol I (8th ed. 2018) Tables 4-1 (approach runways), 4-2
  (take-off climb), 3-1 (strip), 1-1 (reference code).
- KCAA AC **AGA005C** (June 2024) — outer-horizontal significance rule
  (§4.2.1.3) and control of obstacles.
- KCAA AC **AGA032A** (Feb 2026) — obstacle lighting: ~1 light level per 45 m
  of structure height.

### 5.2 Surfaces implemented (`obstacle_compliance/ols_surfaces.py`)
Per-runway (both ends) via `RunwayOLS`:
- **Approach** — inner-edge half-width (30/40/75/75, 70/70/140/140 m),
  distance from threshold (30 m code-1 non-instrument, else 60 m), divergence
  10%/15%, stepped slopes (5%→2%) incl. 12 000 m/3% precision codes 1-2 and
  8 400 m horizontal plateau, total 15 000 m.
- **Inner approach** (precision) — 900 m rectangle @ 2–2.5%, half-width
  45/60 m.
- **Transitional** — 20% (codes 1-2), 1:7 (codes 3-4), along the strip AND
  alongside the approach surface.
- **Inner transitional** (precision) — 40% (codes 1-2), 1:3 (codes 3-4).
- **Balked landing** (precision) — 4% (codes 1-2, from strip end) / 1:30
  (codes 3-4, 1 800 m after threshold), ends at the inner horizontal surface.
- **Take-off climb** (Table 4-2) — 5%/4%/2% slopes, 10%/10%/12.5% divergence
  to a constant final half-width (190/290/600 m), 15 000 m max.
- **Strip** — half-widths 30/40/75/75 m.

ARP-centred via `AirportOLS`:
- **Inner horizontal** — 45 m above the aerodrome datum; radius 2 000–4 000 m
  by category/code.
- **Conical** — 5% rising from the IHS edge; heights 35–100 m.
- **Outer horizontal** — 150 m / 15 000 m radius, **codes 3/4 only**
  (AC AGA005C §4.2.1.3 significance rule, not a hard restriction).

**Convention notes:** Tables 4-1/4-2 give full cross-runway lengths; the
engine stores **half-widths** (verified against strip widths §3.4.9, OFZ
§3.4.7 and Table 4-2 final-width arithmetic). The controlling ceiling at any
point is the **minimum** across all applicable surfaces.

### 5.3 Verdict logic (`obstacle_compliance/utils.py`)
- Ground elevation from the SRTM 30 m DEM (COG streamed via `/vsicurl/`,
  multi-level cache, nodata fallback).
- Ceiling from the full runway-based surface set when declared runway data
  exists, else an ARP-based IHS/conical approximation.
- **RED** hazard when building top > controlling ceiling (except a purely
  outer-horizontal penetration, which is downgraded to YELLOW +
  lighting per AC AGA005C — significance, not prohibition).
- **YELLOW** inside the 15 km significance zone (codes 3/4 only).
- **GREEN** outside all zones.
- **Lighting required** when: hazard, OR structure >30 m AGL AND >150 m above
  aerodrome elevation within 15 km (codes 3/4). Light levels =
  `ceil(height / 45)` per AC AGA032A.
- **Compliance score** 0–100: base by status (100/70/30/0) minus penalties
  for zone overlap, lighting and low headroom.
- 1-hour result caching with hashed keys; `evaluate_property_all_airports`
  uses the 15 km buffer spatial index with a geodesic fallback so missing
  buffers never silently produce GREEN.

## 6. Feature Catalog

### 6.1 Compliance checking
- Single property check (coordinates + height) with DEM context, 8-direction
  terrain profiles and runway-aware OLS profile.
- **Batch check** up to 100 properties (POST).
- **Public quick check** (no login) and **public property query** (read-only,
  filter by aerodrome/radius/height/status).
- **Terrain breach detection** — DEM grid sampled against the controlling
  ceiling; GeoJSON of natural-terrain penetrations.
- **Skyline layer** — grid heatmap of max allowed AGL height (ceiling − terrain).
- Saved-property re-checks with check history and CSV export.

### 6.2 Mapping & visualization
- **2D Leaflet map**: 5 basemaps (Carto Light/Dark, OSM, Satellite, Terrain),
  layers for aerodromes, buffers, runways, OLS, terrain breaches, flyover,
  skyline, user layers, saved properties; Leaflet-Draw for parcels.
- **Buffers**: ARP circles vs **runway "capsule" (stadium) buffers**, radius
  presets 3/5/10 km + custom input (1–100), **10 km default**, `?type=arp|runway`
  toggle; true-metric geometry via local UTM projection (`projection.py`,
  zones 36/37, 326xx/327xx). Missing buffers auto-created on request.
- **Runways layer**: centreline + strip rectangle + thresholds with declared
  TORA/TODA/ASDA/LDA.
- **3D Mapbox GL viewer**: satellite terrain + fill-extrusion with
  **per-surface OLS toggles** (approach, take-off, inner approach, balked
  landing, inner horizontal, conical, outer horizontal, strip) and
  per-slice stepped heights from `surface_slices()`.
- **4D flyover simulation** — approach playback along the glide slope
  (16 km behind threshold) with clear/warn/breach colour-coding.
- **Geocoding**: Mapbox primary + Nominatim fallback (Kenya-bounded), merged
  and deduped, 24 h cache; reverse geocoding; airport-name blending.
- **Spatial APIs**: airports near equator, within radius, nearest, distance
  between two aerodromes.
- **User layers**: save/load/delete persistent custom geometries (login required).

### 6.3 Accounts, portfolio & notifications
- Registration, login, password reset, profile (company/phone/organization type).
- Property portfolio CRUD (name, coordinates, height, optional parcel polygon).
- In-app notification centre (polled every 15 s), unread badge in navbar,
  email delivery; status-change and verdict-change alerts via
  `post_save` signals (`signals.py`).

### 6.4 Applications & certificates
- 6-state workflow: **draft → submitted → under_review → approved / rejected /
  revoked** (rejected can be resubmitted) via `ApplicationWorkflow`.
- Submit triggers an automatic OLS re-check and stamps the verdict snapshot;
  KCAA admin review dashboard with transitions, reviewer notes, automatic
  re-check on every admin action.
- Approval generates a unique **KCAA certificate number** and a **PDF
  certificate** (xhtml2pdf) carrying the OLS verdict snapshot, with
  `valid_until` +365 days; emails/notifications on every change.

### 6.5 Bulk upload
- CSV upload (`name, latitude, longitude, height_m`), synchronous per-row
  checking, property upsert, `ComplianceCheck(trigger='bulk')`, success/
  warning/error counts and a downloadable error log; completion notification.

### 6.6 Analytics & reports
- Admin analytics: compliance status distribution, aerodrome type breakdown,
  recent check activity (Chart.js).
- Per-user dashboard: safe/warning/hazard counts, recent checks, pending apps.
- Downloadable PDF compliance reports (`api/generate-report/`).

### 6.7 REST API v1 (`api/v1/`, DRF)
- `AerodromeViewSet`, `AerodromeBufferViewSet` (read-only), `PropertyViewSet`
  (user-scoped CRUD), `ComplianceCheckView` (`POST /api/v1/check-compliance/`),
  `BatchComplianceCheckView`.
- Token + Session auth, `IsAuthenticated` default, 100 req/hour throttle,
  50/page pagination, Swagger/ReDoc docs.

### 6.8 GeoJSON endpoints (GET)
`/api/airports.geojson`, `/api/buffers.geojson`, `/api/runways.geojson`,
`/api/ols.geojson`, `/api/terrain-breaches.geojson`, `/api/flyover.geojson`,
`/api/skyline.geojson`, `/api/my-properties.geojson`, `/api/user-layers.geojson`.

### 6.9 Admin & data pipeline
- Jazzmin admin with LeafletGeoAdmin for spatial models; `ComplianceApplication`
  admin re-checks OLS and notifies on change.
- 12 management commands: `load_aerodromes`, `load_buffers`,
  `regenerate_buffers`, `add_threshold_buffers`, `merge_airports_data`,
  `process_bulk_upload`, `send_notifications`, `test_compliance`,
  `test_dem(_detailed)`, `verify_data`, `test_elevation`.
- Data sources: KCAA GeoJSON (`aerodromes-ke.geojson`), OurAirports GPKG
  (`airports.gpkg`), `ke-runways.geojson` + declared-distances CSV (external
  PostGIS tables), SRTM 30 m DEM COG on Cloudflare R2 (`DEM_URL`).

## 7. URL / Endpoint Map (core app)

| Area | Routes |
|---|---|
| Pages | `/` (dashboard), `airports/`, `airports/<icao>/`, `map/`, `property-check/`, `property-query/`, `quick-check/`, `dashboard/` (user), `analytics/` |
| Portfolio | `my-properties/` (list/add/detail/edit/delete/check/export) |
| Applications | `applications/` (list/create/detail/submit), `admin-review/` (list/detail/actions) |
| Bulk upload | `bulk-upload/` (list/create/detail/process) |
| Notifications | `notifications/` (list/mark-read/unread-count) |
| GeoJSON | `api/buffers.geojson`, `api/airports.geojson`, `api/runways.geojson`, `api/ols.geojson`, `api/terrain-breaches.geojson`, `api/flyover.geojson`, `api/skyline.geojson`, `api/my-properties.geojson`, `api/user-layers.geojson` |
| Compliance API | `api/check-compliance/`, `api/batch-check/`, `api/quick-check/`, `api/save-property/`, `api/generate-report/`, `api/properties/query/` |
| Geo/Search API | `api/search/`, `api/geocode/`, `api/reverse-geocode/`, `api/airports/near-equator/`, `api/airports/within-radius/`, `api/airports/nearest/`, `api/airports/distance-between/`, `api/stats/` |
| DRF v1 | `api/v1/` (aerodromes, buffers, properties, check-compliance, batch-check, auth) |
| Auth | `accounts/login`, `accounts/register`, `accounts/profile`, password reset |
| Other | `/admin/`, `api/schema/`, `api/docs/swagger/`, `api/docs/redoc/`, `airports-strips/`, `service-worker.js`, `debug/` |

## 8. Auth & Permissions Matrix

| Area | Public | Logged-in | Notes |
|---|---|---|---|
| Dashboard, map, airports, property check/query/quick-check | ✅ | ✅ | |
| GeoJSON + geo/search APIs | ✅ | ✅ | Cached 15–30 min |
| Portfolio, applications, bulk upload, notifications, user layers, exports | ❌ | ✅ | `LoginRequiredMixin` |
| Analytics, user dashboard | ❌ | ✅ | |
| Admin review (`/admin-review/`) | ❌ | ✅ | **Gap:** not role-gated (any logged-in user) |
| DRF v1 | ❌ | ✅ | Token/Session, 100 req/h |
| Django admin (`/admin/`) | ❌ | ✅ staff | Jazzmin |

## 9. Testing & Verification

- **32 tests** (`obstacle_compliance/tests.py`, all `SimpleTestCase`, no DB):
  `ReferenceCodeTests`, `RunwayOLSTests` (all 8 surfaces, half-width
  regression tests, footprints/slices), `NonPrecisionRunwayTests`,
  `NonInstrumentCode1Tests`, `SurfaceSliceTests` (3D slice heights),
  `OuterHorizontalSignificanceTests`, `ProjectionTests` (UTM/buffers).
- `docs/OLS_VERIFICATION_MATRIX.md` — every engine value hand-recomputed from
  Annex 14 Tables and confirmed against live engine output (2026-08-12).
- Commands: `manage.py check` clean; `manage.py test_compliance` smoke run.

## 10. Deployment & Ops

- Render (live demo) + Dockerfile + gunicorn.conf.py + Procfile; GitHub
  Actions + GitLab CI; Whitenoise static serving.
- Env vars: `SECRET_KEY`, `DEBUG` (default False), `ALLOWED_HOSTS`, `DEM_URL`
  (R2 COG), `DEM_BUCKET_NAME`/`DEM_OBJECT_NAME`, `MAPBOX_*` tokens,
  `SITE_URL`, DB/Redis/R2 credentials; console email backend in dev.

## 11. Known Gaps & Deferred Roadmap

Deferred per ADRs (see `docs/ADRs/`):
- **2D per-surface OLS layer-checker card** on `/map/` (backend already serves
  per-surface features; only the UI card is missing).
- **Leaflet → MapLibre migration** for the 2D viewer.
- **SFCGAL true 3D OLS surfaces** (currently sampled/stepped extrusions).
- **3D OLS snapshot inside PDF reports/certificates**.
- **Property query user-scoping** (Phase 2: user-only vs public results).
- **Admin-review role enforcement** (`is_staff`/group check) — hardening gap.
- **Service worker** is a placeholder (no offline caching).
- Legacy `airports_strips` app pages (migration banner → Unified Map).

Future product directions (see `TO ADD.MD`): flight planning & operations,
safety/emergency response (SAR), infrastructure capacity planning, economic
corridors, airspace management, pilot training, weather integration.

## 12. Document Index

| Document | Purpose |
|---|---|
| `README.md` | Runbook: setup, commands, deploy |
| `docs/PROJECT_FEATURES.md` | **This file** — what has been built |
| `docs/OLS_VERIFICATION_MATRIX.md` | Engine values vs Annex 14 tables |
| `docs/specific use case.md` | Product narrative / use case |
| `docs/control-obs.md`, `docs/light-obs.md` | PDF extraction logs (AGA005C/AGA032A) |
| `docs/an14_v1.pdf` | ICAO Annex 14 Vol I (8th ed. 2018) |
| `docs/CAA-AC-AGA005C CONTROL OF OBSTACLES.pdf` | KCAA AC (June 2024) |
| `docs/CAA-AC-AGA032A Lighting and Marking of Obstacles.pdf` | KCAA AC (Feb 2026) |
| `docs/ADRs/*` | Decision log (7 ADRs): buffers/OLS, projection+buffer types, per-surface OLS independence, map visualization upgrade, 15 km buffer/layer checker, property-query public, OLS & buffering |
