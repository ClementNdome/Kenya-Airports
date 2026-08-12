# API Reference

All web routes are served at both `/` and `/obstacle-compliance/`. API docs (OpenAPI) are generated with drf-spectacular at `/api/schema/`, Swagger at `/api/docs/swagger/`, ReDoc at `/api/docs/redoc/`.

## REST API v1 — `/api/v1/` (token-authenticated)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/aerodromes/` | List/search aerodromes (search + type filter) |
| `GET` | `/api/v1/buffers/` | List/filter buffers (radius, icao) |
| `GET/POST/PUT/DELETE` | `/api/v1/properties/` | User property CRUD (user-scoped) |
| `POST` | `/api/v1/check-compliance/` | Single compliance check (lat/lon/height) |
| `POST` | `/api/v1/batch-check/` | Batch compliance check (max 100) |

- Auth: `Authorization: Token <token>` (DRF TokenAuth) or session
- Rate limit: 100 requests/hour/user; pagination 50/page
- Default permission class: `IsAuthenticated`

## GeoJSON Endpoints

| Endpoint | Params | Description |
|---|---|---|
| `/api/airports.geojson` | — | Aerodrome points with elevation + buffer flags, marker colours by type (30 min cache) |
| `/api/buffers.geojson` | `radius`, `icao`, `type=arp\|runway` | Buffer polygons; auto-creates missing buffers on first request; coloured by radius (15 min cache) |
| `/api/runways.geojson` | `icao` | Runway centreline + strip polygon + threshold points per end with declared TORA/TODA/ASDA/LDA |
| `/api/ols.geojson` | `icao` | Annex 14 surface footprints; per-surface features with `surface` property + 3D heights |
| `/api/terrain-breaches.geojson` | `icao` | DEM terrain penetrations of the controlling OLS |
| `/api/flyover.geojson` | `icao`, `step` | 4D flyover path simulation along the longest runway's approach; clear/warn/breach segments vs ceilings, per-vertex AGLs |
| `/api/skyline.geojson` | `icao`, `step` | Max allowed AGL height grid (OLS ceiling − terrain), 9 km half-extent |
| `/api/my-properties.geojson` | — | Logged-in user's saved properties (with parcels) |
| `/api/user-layers.geojson` | — | User's custom layers |
| `/api/user-layers/save/` | `POST` | Save a user layer (name, type, geometry, properties) |
| `/api/user-layers/<pk>/delete/` | `DELETE` | Delete a user layer |

## Utility & Query Endpoints

| Method | Endpoint | Params | Description |
|---|---|---|---|
| `GET` | `/api/check-compliance/` | `lat`, `lon`, `height`, optional `parcel` (JSON ring) | Full compliance check — DEM context (multi-sample stats), terrain profile (8-direction × 100 m), visualisation data; 5 min cache |
| `POST` | `/api/batch-check/` | JSON array ≤100 | Batch compliance check |
| `GET` | `/api/quick-check/` | `lat`, `lon`, `height` | Public quick check (no login) |
| `GET` | `/api/properties/query/` | `icao`, `radius` (or `lat`/`lon` centre), `min_height`, `max_height`, `status`, `limit` | Public read-only property browser; sorted by height desc; limit ≤1000 |
| `GET` | `/api/search/?q=` | query | Airport autocomplete |
| `GET` | `/api/geocode/?q=` | query | Address→coordinates: Mapbox + Nominatim fallback, Kenya-bounded, merged/deduped, airport-name blending, 24 h cache |
| `GET` | `/api/reverse-geocode/` | `lat`, `lon` | Coordinates→address |
| `GET` | `/api/airports/nearest/` | `lat`, `lon` | Nearest airport |
| `GET` | `/api/airports/within-radius/` | `lat`, `lon`, `radius` | Airports within radius (Distance annotation) |
| `GET` | `/api/airports/near-equator/` | — | Airports near the equator |
| `GET` | `/api/airports/distance-between/` | `icao1`, `icao2` | Geodesic distance (km) |
| `GET` | `/api/stats/` | — | System statistics |
| `POST` | `/api/generate-report/` | `property_id` (etc.) | PDF compliance report (xhtml2pdf) |
| `GET` | `/api/save-property/` | `POST` | Save property from a check result (point + optional parcel) |
| `GET` | `/api/my-properties/export/` | — | CSV export of portfolio |

## Auth & Account URLs

| Endpoint | Description |
|---|---|
| `/accounts/register/` | Registration |
| `/accounts/login/`, `/accounts/logout/` | Django auth |
| `/accounts/profile/` | Profile (company, phone, org type) |
| `/accounts/password-reset/` (+ done/confirm/complete) | Password reset flow |
| `/api/auth/` | DRF auth endpoints (`rest_framework.urls`) |

## Application / Workflow URLs

| Endpoint | Description |
|---|---|
| `/applications/` | List my applications |
| `/applications/add/` | Create application |
| `/applications/<pk>/` | Detail (with OLS verdict snapshot) |
| `/applications/<pk>/submit/` | Submit (transition + auto OLS re-check + breach alert) |
| `/admin-review/` | KCAA admin review list |
| `/admin-review/<pk>/` | Review detail |
| `/admin-review/<pk>/<action>/` | approve / reject / revoke (+ certificate PDF + email) |

## Notifications

| Endpoint | Description |
|---|---|
| `/notifications/` | In-app notification list |
| `/notifications/mark-read/` | Mark as read |
| `/notifications/unread-count/` | Unread badge count |
