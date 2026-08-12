# Data Model

All models are GeoDjango models (SRID 4326 unless noted). 12 migrations (`0001_initial` → `0012`).

## Managed Models

### `Aerodrome`
KCAA GeoJSON data + unified OurAirports data.

| Field | Notes |
|---|---|
| `fid` | PK |
| `icao_code` | Unique, e.g. `HKJK` |
| `name`, `type` | e.g. international, military, private |
| `latitude` / `longitude` | String DMS |
| `elevation_m_ft` / `elevation_m` | Mixed-format string + parsed float (5 regex patterns in `save()`) |
| `geoid_undulation_m` | |
| `geom` | `PointField` 4326 |
| `iata_code`, `runway_length_m`, `nearest_city`, `airlines` | From `merge_airports_data` |
| `source` | geojson / geopackage / merged |
| `last_synced` | |

Methods: `get_or_create_buffer(radius_km)` (true-metric ARP circle via UTM), `runway_capsule(radius_km)` (stadium buffer), `get_or_create_runway_threshold_buffer`, `get_or_create_any_buffer(radius, type)`.

### `AerodromeBuffer`
Precomputed buffers. Unique `(aerodrome, radius_km)`, GiST spatial index.

| Field | Notes |
|---|---|
| `radius_km` | 3/5/10/15 (or custom) |
| `type` | `'arp'` circle vs `'runway'` capsule |
| `latitude_decimal` / `longitude_decimal` | |
| `area_km2` | Planimetric (UTM) |
| `layer`, `geom` | `MultiPolygonField` |

### `AerodromeRunway` *(unmanaged — `db_table='aerodrome-runways'`)*
23 runways / 19 aerodromes (2026-08-11). Centerline `LineString`, threshold DMS + decimal coords/elevations, true/mag bearings, declared dimensions, SWY/CWY/strip/OFZ/RESA dims, `approach_category` (non_instrument / non_precision / precision_i / precision_ii_iii). `aerodrome` property resolves via ICAO.

### `DeclaredDistance` *(unmanaged — `db_table='runways-declared_distances'`)*
TORA/TODA/ASDA/LDA per runway end + remarks. `parse()` converts to float.

> **⚠ Whitespace gotcha:** `runway_pair` is whitespace-padded in the legacy data (e.g. `' 08/26      '`). Joins MUST use `(icao_code, TRIM(runway_pair))` — verified 23/23 rows join cleanly (ADR-property-query-public).

### `UserProfile`
OneToOne `user` + `company`, `phone`, `organization_type` (developer/architect/agent/public/kcaa/other), `email_verified`. Auto-created by `post_save` signal.

### `Property`
User property portfolio.

| Field | Notes |
|---|---|
| `user`, `name`, `address` | |
| `latitude` / `longitude` / `height_m` | Height AGL |
| `geom` | Point, auto-set on save |
| `parcel_boundary` | MultiPolygon (drawn parcel) |
| `last_status` / `last_score` / `last_checked` | GREEN/YELLOW/RED/UNKNOWN |

`run_compliance_check()` runs the ComplianceCalculator and stores a `ComplianceCheck`.

### `ComplianceCheck`
Check history. `result_json` (JSON), `status`, `score`, `primary_airport_icao`, `airports_affected`, `requires_lighting`, `is_hazard`, `checked_at`, `trigger` (manual/auto/bulk/api).

### `Notification`
`notification_type` (status_change / regulation_update / application_update / reassessment / bulk_complete), `title`, `message`, `link`, `is_read`, `email_sent`, `created_at`.

### `ComplianceApplication`
Certificate workflow. `status` (draft → submitted → under_review → approved / rejected / revoked), `certificate_number` (unique, `KCAA-YYYYMMDD-0000N`), `certificate_pdf` (FileField), `valid_until`, `fee_paid`, `reviewed_by/at`, `reviewer_notes`, **OLS snapshot**: `last_status`, `last_score`, `last_ceiling_amsl`, `last_headroom_m`, `last_checked`.

### `UserLayer`
Persisted map layers. `name`, `layer_type` (buffer / check_result / parcel / custom), `geometry` (GeometryField), `properties` (JSON), `created_at`.

### `BulkUploadJob`
CSV batch processing. `csv_file`, `status` (pending/processing/completed/failed), counts, `results_file`, `error_log`.

## Data Flow Notes

- **Loaders:** `load_aerodromes` (GeoJSON), `load_buffers` (LayerMapping), `merge_airports_data` (legacy app merge), `add_threshold_buffers` / `regenerate_buffers` (UTM capsule/circle generation).
- **Spatial indexes:** GiST on `Aerodrome.geom`, `AerodromeBuffer.geom`, runways.
- **Unmanaged tables** are read-only from Django's perspective; schema is owned externally (KCAA dataset load).
