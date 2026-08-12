# Features

## 🔍 Compliance Checking
- Enter coordinates + building height → instant **GREEN** (compliant) / **YELLOW** (caution) / **RED** (hazard) status with a 0–100 compliance score
- Full **ICAO Annex 14 OLS evaluation**: approach, inner approach, transitional, inner transitional, balked-landing, take-off-climb (per runway, per end) plus ARP-centred Inner Horizontal, Conical and Outer Horizontal surfaces
- **SRTM 30 m DEM integration** — Cloud Optimized GeoTIFF on Cloudflare R2, streamed via rasterio/GDAL `/vsicurl/`, multi-level cached (LRU + Django cache)
- **Terrain breach detection** — grid-samples the DEM against the controlling OLS ceiling and flags natural terrain penetrating surfaces
- **Batch check** — up to 100 properties in one request
- **Public quick check** — no login required
- **Public property query** — read-only browser of checked properties (filter by aerodrome + radius, height range, or status)

## 🗺️ Interactive GIS Map
- Leaflet 2D with basemap switcher (Carto Light/Dark, OSM, Satellite, Terrain)
- **Mapbox GL JS 3D viewer** — satellite terrain, fill-extrusion buildings, stepped OLS surface slices with legend
- Toggleable layers: aerodromes, buffers, runways, OLS footprints, terrain breaches, flyover, skyline, user layers, saved properties
- **4D flyover simulation** — approach-path playback, clear/warn/breach colour-coding vs OLS ceilings
- **Skyline layer** — grid of max allowed AGL height (OLS ceiling − terrain)
- **Buffer builder** — radius presets 3/5/10 km + custom (1–50), **Runway/Point type toggle** (capsule vs ARP circle), default 10 km
- **User layers** — persistent, toggleable custom geometries
- Airport popups with buffer flags, drawing tools (Leaflet-Draw)

## 👤 Accounts & Property Portfolio
- Registration, login, logout, password reset
- Profile: company, phone, organization type (developer/architect/agent/public/kcaa/other)
- Properties CRUD (name, coords, height AGL, optional parcel polygon), check history, CSV export

## 📋 Compliance Certificate Workflow
- 6-state machine: **Draft → Submitted → Under Review → Approved / Rejected / Revoked**
- KCAA admin review dashboard (`/admin-review/`) with reviewer notes + auto OLS re-check on action
- Auto certificate numbers `KCAA-YYYYMMDD-0000N`, **PDF certificates** (xhtml2pdf)
- Certificate shows OLS verdict snapshot: status, score, ceiling AMSL, headroom, last-checked date
- Rejected applications can be resubmitted

## 📦 Bulk Upload
- CSV upload (name, latitude, longitude, height) → auto property creation + compliance checks
- Success/warning/error counts + downloadable error log

## 🔌 REST API
- Token-authenticated `/api/v1/`: aerodromes, buffers, properties (user-scoped), check-compliance, batch-check
- GeoJSON endpoints: airports, buffers, runways, OLS, terrain breaches, flyover, skyline, my properties, user layers
- Swagger (`/api/docs/swagger/`) + ReDoc (`/api/docs/redoc/`)
- Throttled (100 req/h), paginated (50/page)

## 📊 Analytics
- Chart.js: compliance status distribution, aerodrome types, recent activity
- Personalized user dashboard
- Downloadable **PDF compliance reports**

## 🔔 Notifications
- `post_save` signal detection of status changes
- In-app center (15 s polling) + email; unread badge in navbar

## 🌐 Geocoding & Spatial Queries
- **Mapbox + Nominatim fallback** geocoding (Kenya-bounded, merged/deduped, 24 h cache, airport-name blending)
- Reverse geocoding
- Nearest airport, airports within radius, near-equator, distance between airports

## 🗃️ Admin (Jazzmin)
- Dark-themed admin with LeafletGeoAdmin map widgets
- Aerodrome, buffer, property, compliance check, notification, application, user-layer, runway, declared-distance registrations
- `ComplianceApplication.save_model` triggers an automatic OLS re-check with admin feedback
