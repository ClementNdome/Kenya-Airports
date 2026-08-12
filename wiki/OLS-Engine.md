# OLS Engine

## Regulatory Basis

The engine implements **ICAO Annex 14 Vol I (8th ed., 2018), Tables 4-1 and 4-2** — the tables mirrored by the KCAA Civil Aviation (Aerodromes Design and Operations) Regulations 2018 and referenced by:

- **KCAA AC-AGA005C (June 2024)** — *Control of Obstacles* (supersedes AGA005B)
- **KCAA AC-AGA032A (Feb 2026)** — *Lighting and Marking of Obstacles*

Source PDFs live in [`docs/`](https://github.com/ClementNdome/Kenya-Airports/tree/main/docs).

## Surfaces (Annex 14 Tables 4-1 / 4-2)

### Runway-centric surfaces (`RunwayOLS` in `ols_surfaces.py`)

Computed per runway end from real geometry — thresholds, true/magnetic bearings, and elevations derived from the runway `LineString`:

| Surface | Geometry | Slope / Dimensions |
|---|---|---|
| **Strip** | Rectangular buffer around centreline | Half-width 30/40/75/75 m by code 1–4 (Table 3-1: 60/80/150/150 m full) |
| **Approach** | Diverging wedge from a point before the threshold | 2–5% first slope (by category/code), optional second slope, horizontal section, total length up to 15 000 m |
| **Inner approach** | Wedge inside the approach, over the strip | 2% / 1:50 slope, 40% / 1:2.5 divergence |
| **Transitional** | Along strip edges + alongside approach | 20% (1:5) lateral slope |
| **Inner transitional** | Along strip, between threshold points | 40% (1:2.5) |
| **Balked landing** | After the inner edge, over the strip | 3.33% (1:30) |
| **Take-off climb** | From the departure end | 2.5% (1:40) Table 4-2 |

### ARP-centric surfaces (`AirportOLS`)

| Surface | Extent | Ceiling |
|---|---|---|
| **Inner Horizontal (IHS)** | Radius 2 000–4 000 m by (category, code) | Flat 45 m above aerodrome elevation |
| **Conical** | From IHS outer edge | 5% slope to 35–100 m height (by category/code) |
| **Outer Horizontal** | 15 000 m radius — codes 3/4 only (AC AGA005C §4.2.1.3) | Flat 150 m above aerodrome elevation |

### Ceiling logic

- `AirportOLS.ceiling_at(lat, lon)` returns the **minimum of all applicable surfaces** (most restrictive) together with the surface name and distance from the ARP.
- `RunwayOLS.ceilings_at(lat, lon)` returns `[(ceiling_amsl, surface_label)]` for every applicable runway surface (approach both ends, inner approach, transitional, balked landing, take-off climb).
- `reference_code(length_m)` maps declared runway length to code 1–4 (<800 m → 1, <1200 → 2, <1800 → 3, else 4).

## Compliance Calculator (`utils.py`)

`ComplianceCalculator.evaluate_property(prop_point, height, airport)`:

1. Gets **ground elevation** from the DEM service (SRTM 30 m COG on Cloudflare R2).
2. Computes building-top AMSL = ground + height.
3. Computes the **controlling OLS ceiling** at the point.
4. Flags **hazard** if the building penetrates the ceiling; applies the **lighting rules**.
5. Produces status: **RED** (penetrates), **YELLOW** (caution band), **GREEN** (compliant), plus a 0–100 **compliance score**.

`evaluate_property_all_airports(point, height)`:
- Finds airports via the **15 km buffer containment** (spatial index) with geodesic distance fallback (`get_airports_in_radius` — degree-bbox prefilter + pyproj WGS84 geodesic).
- Evaluates against each, sorts by restrictiveness, and returns the controlling result.

### Lighting rules (AC AGA032A)
- **Lighting required** when a structure is > 30 m AGL **and** > 150 m above aerodrome elevation within 15 000 m (AC AGA005C §4.2.1.3 tall-structure zone).
- **Light levels** = ⌈height / 45 m⌉ (AC AGA032A spacing rule N = Y/45 m).

## Terrain Breach Detection

`terrain_breaches(airport, step_m, max_samples)` grid-samples the DEM over the ~15.2 km reach, comparing terrain AMSL against the controlling OLS ceiling at each sample. Returns GeoJSON points where terrain penetrates surfaces, with worst-breach metadata. Exposed via `/api/terrain-breaches.geojson` and the map's "Terrain" toggle.

## Buffers & Projection (`projection.py`)

| Concept | Implementation |
|---|---|
| **ARP-circle buffer** (`type=arp`) | True-metric circle around the aerodrome reference point |
| **Runway-capsule buffer** (`type=runway`) | Stadium buffer around the runway centreline (per HKNL 03/21 threshold-buffer practice); falls back to ARP circle if no runway geometry |
| **Projection** | Local UTM zone: EPSG 32636/32637 (N) / 32736/32737 (S) selected by longitude (<39°E → 36, else 37) and hemisphere |
| **Distances** | `distance_m` uses pyproj WGS84 geodesic; `get_airports_in_radius` = degree-bbox prefilter + exact geodesic |
| **Regeneration** | `python manage.py regenerate_buffers --radii 3 5 10 --type both` recomputes every row in UTM with corrected `area_km2` |

One buffer row per `(aerodrome, radius_km)` — the **type is a display mode** switched per radius via `?type=arp|runway` in the buffers API. Default radius in the UI: **10 km** (15 km preset removed; the AC-mandated 15 km outer-horizontal/lighting zone remains in the OLS and regulatory logic).

## Verification

- `obstacle_compliance/tests.py` — 32 tests: reference-code thresholds, synthetic code-4 precision runway (approach sections, horizontal, lateral limit, inner approach, transitional, take-off climb, balked landing + termination, conical/outer-horizontal/IHS ceilings, footprints), code-2 non-instrument, 3D surface slices, UTM projection.
- [`docs/OLS_VERIFICATION_MATRIX.md`](https://github.com/ClementNdome/Kenya-Airports/blob/main/docs/OLS_VERIFICATION_MATRIX.md) — hand-computed verification of the engine against the Annex 14 tables (HKJK approach/take-off/ARP surfaces, balked landing, synthetic runway, lighting rules).
