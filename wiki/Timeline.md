# Project Timeline

Reconstructed from the git history (first commit **2025-02-11**, latest **2026-08-12**), the ADRs, and the documentation. All work by Clement Ndome.

## Phase Overview

| Phase | Period | Theme |
|---|---|---|
| [0. Legacy Airport GIS App](#phase-0--legacy-airport-gis-app-feb--mar-2025) | Feb 11 – Mar 19, 2025 | Repo init, PostGIS, legacy `airports_strips` app, deployment prep |
| [1. Data & Database Evolution](#phase-1--data--database-evolution-aug--oct-2025) | Aug 24 – Oct 9, 2025 | Aiven Postgres, dataset imports, packaging fixes |
| [2. Obstacle Compliance App Created](#phase-2--obstacle-compliance-app-created-feb-2026) | Feb 22 – 27, 2026 | New `obstacle_compliance` app, switchable settings, model enhancements |
| [3. Deployment Hardening](#phase-3--deployment-hardening-apr--jul-2026) | Apr 27 – Jul 4, 2026 | Docker, GitLab CI, gunicorn, URL/routing fixes, report downloads |
| [4. Core Compliance + OLS Engine](#phase-4--core-compliance--ols-engine-aug-2026) | Aug 11 – 12, 2026 | Compliance core, true Annex 14 OLS engine, 3D map, GeoJSON, ADRs, tests |

---

## Phase 0 — Legacy Airport GIS App (Feb–Mar 2025)

Initial repository: a GeoDjango demo app for Kenyan airports with spatial queries.

- **2025-02-11** — repo init; settings configured; PostGIS database configured; spatial data loader for PostgreSQL (`load_aerodromes`)
- **2025-02-12** — UI updates, GIS analysis functions (near-equator, within-radius, distance), endpoints added, deployment prep, requirements
- **2025-02-13** — deployment status checks
- **2025-02-15** — UI and function updates
- **2025-03-12/13** — README; GitHub Actions CI (`django.yml`) added
- **2025-03-19** — Jazzmin admin added; Render database renewed; merges

**Deliverables:** `airports_strips` legacy app (map, explore, spatial query endpoints), PostGIS setup, CI.

---

## Phase 1 — Data & Database Evolution (Aug–Oct 2025)

- **2025-08-24/25** — database moved to **Aiven** (Postgres); dataset commits
- **2025-10-09** — requirements updated to binary `psycopg2`; static files handling; `build.sh`; settings for deployment; explore page improved; static files removed from tracking

**Deliverables:** managed cloud database, deployment scripting, data refresh.

---

## Phase 2 — Obstacle Compliance App Created (Feb 2026)

- **2026-02-22** — `obstacle_compliance` app created; configs set for local ↔ production switching; enhanced aerodrome/airport models; dashboard testing; static files from previous code kept out of the new app; guides for the compliance app
- **2026-02-27** — "Newapp" merge (`#4`)

**Deliverables:** the compliance app skeleton with dashboard, models, settings switching.

---

## Phase 3 — Deployment Hardening (Apr–Jul 2026)

- **2026-04-27** — GitLab CI/CD config + Dockerfile added
- **2026-07-04** — Dockerfile made usable; WSGI path fix; GDAL library path update + default DB config; base URL switched to the compliance app; URL patterns improved + service worker; PDF report generation with download + error handling; dependencies cleanup (toml removed, pyproj fix, psycopg2 removal); settings fixes

**Deliverables:** containerised deployment, gunicorn config, service worker, report downloads.

---

## Phase 4 — Core Compliance + OLS Engine (Aug 2026)

### 2026-08-11 — Core system
- Core obstacle compliance system: property portfolio management, application workflows, bulk processing, analytics dashboard
- Geocoding widget + compliance app settings
- ADR docs added (`ADR-property-query-public` created)
- DB inspection code; data verified: **23 runways / 19 aerodromes** in `aerodrome-runways`, all declared distances join cleanly

### 2026-08-12 — OLS engine & advanced map features
- **OLS calculation engine** — `ols_surfaces.py` (true Annex 14 surfaces) + evaluation classes
- Runway + OLS **GeoJSON views**
- OLS refactor to ARP-based dimensions; improved runway handling
- **Terrain breach detection** + application OLS re-check
- `add_threshold_buffers` backfill command (runway-capsule buffers)
- `approach_category` migration for `aerodrome-runways`
- `ComplianceApplication` OLS snapshot fields + `UserLayer` model (+ admin)
- Flyover, Skyline, Terrain-Breach GeoJSON views; user-layer management
- Runway/OLS layer toggles on the map with loading functionality
- **UTM projection + buffer-type ADR implemented** (`projection.py`, `regenerate_buffers` command)
- 15 km preset dropped; default radius 10 km (ADR-map-layer-checker)
- KCAA docs added (Annex 14 PDF, AC AGA005C, AC AGA032A); `OLS_VERIFICATION_MATRIX.md`
- Geocode enrichment (Mapbox + Nominatim merge); static files collected
- Deferred roadmaps recorded (map-visualization-upgrade, per-surface OLS independence, layer checker)

**Deliverables:** production-grade OLS engine with 32 passing tests, 3D map experience, GeoJSON API surface, ADR trail, certificate workflow with OLS verdicts.

---

## ADR Timeline

| Date | ADR | Status |
|---|---|---|
| 2026-07-30 | `ADR-buffer_OLS_NA_OA.md` — future implementation tracker | Partially implemented (2026-08-12) |
| 2026-08-11 | `ADR-property-query-public.md` — public read-only query tool | Accepted (Phase 1) |
| 2026-08-12 | `ADR-projection-buffer-types.md` — UTM projection + buffer types | Implemented |
| 2026-08-12 | `ADR-map-layer-checker-15km-buffer.md` — layer checker card, drop 15 km, AC refs | Partially implemented |
| 2026-08-12 | `ADR-map-visualization-upgrade.md` — map/visualization roadmap | Accepted (deferred) |
| 2026-08-12 (04:35) | `ADR-per_service-OLS-layer-independence.md` — per-surface OLS layers | Accepted (deferred) |
| n/a | `3Dvisuilization-and-OLS.md`, `OLS & buffering.md` — wish/educational notes | Notes |

See [ADRs](ADRs) for summaries.
