# ADR: UTM projection + buffer type selection — implemented

Status: **Accepted (implemented)** · Date: 2026-08-12 · Applies to: `obstacle_compliance` (Kenya-Airports)

## Context

Two accuracy problems surfaced in the buffer/OLS audit:

1. **Buffer shapes were ambiguous.** Radii 3/5/10 km produced stadium-shaped *runway capsules* (around the runway centreline, per HKNL 03/21 threshold-buffer practice) while every other radius — including any custom value — silently produced a *circle around the ARP point* (`runway_radii = (3, 5, 10)` was hardcoded in `BufferGeoJSONView`). A user asking for a 2 km buffer could not get a 2 km runway capsule.
2. **Wrong projection in metric work.** Buffer and capsule generation buffered in **EPSG:3857 Web Mercator**; the nearby-airport DB lookup used **planar 4326 degree distance** (`geom__distance_lte`), which is not a true metric filter. Kenya spans UTM zones 36 and 37, and both hemispheres (Nairobi ≈ 32736, Mombasa ≈ 32737, Lodwar ≈ 32636, Moyale ≈ 32637).

## Decisions

1. **New `obstacle_compliance/projection.py` util** (Python side only — no DB schema change):
   - `utm_epsg(lon, lat)` selects **32636/32637 (N)** or **32736/32737 (S)** by longitude (zone 36 < 39°E, else 37) and hemisphere.
   - `to_utm` / `from_utm` / `buffer_m` / `area_m2` / `distance_m` (pyproj WGS84 Geod).
   - Replaced EPSG:3857 in `get_or_create_buffer()`, `runway_capsule()`, and `calculate_distance(method='projected')`.
2. **Explicit buffer type selection** (`models.py`):
   - `Aerodrome.BUFFER_TYPE_ARP = 'arp'`, `BUFFER_TYPE_RUNWAY = 'runway'`; `buffer_type_of()` normalises legacy `'runway_threshold'` rows.
   - `get_or_create_any_buffer(radius, buffer_type)` dispatches: `'runway'` → capsule (ARP-circle fallback when the aerodrome has no runway geometry); `'arp'` → circle. **Any radius works with either type.** One buffer row per `(aerodrome, radius_km)` (existing unique constraint) — the type is a display mode, switched per radius.
   - `BufferGeoJSONView` takes `?type=arp|runway` (auto when omitted: runway if the aerodrome has runway geometry), applied at any radius.
3. **UI** (`map_view.html`, `dashboard.html`): the radius control became a buffer builder — a **Runway / Point** segmented toggle plus radius presets **3/5/10** and a custom input (1–50). Default radius **10 km** for both pages; the 15 km preset button was removed (see the deferred layer-checker ADR).
4. **Geodesic proximity fallback** (`utils.py get_airports_in_radius`): degree-bbox prefilter (index-assisted) + exact pyproj WGS84 geodesic filter/sort in Python over the small candidate set. No planar-degree distance lookup remains in this path.
5. **`regenerate_buffers` management command**: one-shot UTM regeneration of every `AerodromeBuffer` row (`--radii 3,5,10 --type arp|runway|both [--icao X]`) with corrected `area_km2`.

## Verification

- `python manage.py check` — clean.
- Test suite (`obstacle_compliance.tests`, 27 tests incl. new `ProjectionTests`): UTM zone selection for Nairobi/Kisumu/Mombasa/Moyale/Lodwar; true-metric 1 km buffer (area ≈ π km², UTM extents ≈ 2 km); geodesic JKIA→Wilson ≈ 12.5 km. All pass.

## Deferred (unrelated, tracked separately)

- OLS geodetic kernel unification, transitional 45 m cap, 3D slice fidelity, Annex table re-verification.
- Layer-checker card + per-surface OLS toggles (`ADR-map-layer-checker-15km-buffer.md`).