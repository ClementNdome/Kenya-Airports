# Roadmap

## Deferred ADR Work

Tracked in detail in [ADRs](ADRs); the deferred items:

1. **Per-surface OLS layer independence** — each Annex 14 surface individually toggleable with distinct colours/legend; friendly popup names; revisit the 15 km ring for the Nairobi cluster (HKJK/HKNW/HKRE/HKFP).
2. **Layer-checker card on `/map/`** — 2D layer toggles restyled like the 3D legend card, with per-surface OLS sub-toggles below the basemap switcher.
3. **Leaflet → Mapbox GL JS / MapLibre migration** — decision gate: prototype OLS 3D extrusion + terrain in a standalone page first; keep Leaflet as fallback.
4. **Merge property-query into property-check** — embed the query experience as a tab/section (API already public and reusable).
5. **Minimal property-check card on `/map/`** — collapsible lat/lon/height card on the map page; complex flows stay on `/property-check/`.
6. **Property-check proximity visuals** — show client/server-side buffer or proximity line on the check map after geocoding, so the map communicates distance to aerodromes/runways/restricted areas.
7. **3D snapshot in PDF reports** — capture the 3D map scene and attach it to generated PDF reports (exploration area — must not overload the system).
8. **Full 3D OLS (SFCGAL)** — PostGIS `ST_3DIntersects`-grade true 3D surfaces; currently Phase 2.5 delivers true Annex 14 surface *math* with 2D footprints + per-vertex heights for client-side 3D rendering.
9. **Persistent buffer layers** — user-saved named layers with visibility toggles (post-auth hardening).
10. **Client-side turf.js OLS fallback** — complex OLS on the client for offline/resilient operation.
11. **Property query user-scoping** — restrict `PropertyQueryAPI` to `request.user.properties` when auth matures (verified emails, ownership); per-user saved queries; `is_public` opt-out flag.

## Engineering Backlog / Known Items

- Update GitHub Actions matrix to Python 3.11/3.12 + add a PostGIS service (current 3.7–3.9 matrix is incompatible with Django 5.1).
- Add `MEDIA_URL`/`MEDIA_ROOT` (DEBUG static serving in `urls.py` references them; latent `AttributeError`).
- Configure Redis `CACHES` (installed but unused — currently LocMemCache).
- Remove or configure unused deps: `django-cors-headers`, `django-debug-toolbar`, `django-environ`, `django-extensions`.
- `load_aerodromes` references `latitude_decimal` fields that exist on `AerodromeBuffer` but not `Aerodrome` — verify before use.

## Product Directions (TO ADD.MD backlog)

| # | Area | Ideas |
|---|---|---|
| 1 | Flight planning & operations | Route optimization (range, no-fly zones, weather), alternate-airport suggestions, fuel planning |
| 2 | Safety & emergency response | SAR (hospitals within radius), emergency landing sites, incident command centers |
| 3 | Infrastructure planning | Capacity analysis, maintenance scheduling, development impact assessment, budget allocation |
| 4 | Economic & tourism | Tourism corridor mapping, cargo/logistics optimization, regional economic impact heatmaps |
| 5 | Regulatory | Airspace management, noise/emissions monitoring, permit processing tool |
| 6 | Pilot training | Virtual navigation, emergency procedure simulation, airport familiarization |
| 7 | Weather integration | Real-time overlays, predictive analytics, divert alerts |
| 8 | Disaster management | Post-disaster operational airports, humanitarian aid routing, evacuation planning |
