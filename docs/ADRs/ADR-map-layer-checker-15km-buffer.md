# ADR: Map layer checker card + drop 15 km ARP circle buffer — deferred implementation

Status: **Accepted (deferred)** · Date: 2026-08-12 · Applies to: `obstacle_compliance` (Kenya-Airports)

## Context

Three approved decisions from the OLS/buffer audit, deferred for a later implementation round:

1. **Layer checker card on `/map/`** — the 2D layer toggles should look and behave like the 3D viewer's legend card, placed below the basemap switcher, with per-surface OLS sub-toggles.
2. **Drop the 15 km ARP circle buffer** — it duplicates the KCAA-mandated OLS outer horizontal (both are 15 km rings around the ARP). New default radius: **10 km**.
3. **Correct regulatory references** — `CAA-AC-AGA005B` is superseded by **`CAA-AC-AGA005C` (June 2024)**; code comments and docs still cite the old circular.

### Research basis

- The **OLS outer horizontal (15 km / 150 m AGL)** is NOT optional: KCAA AC AGA005C §4.2.1.3 treats tall structures (>30 m AGL and >150 m above aerodrome elevation within 15 000 m) as significant for code 3/4 aerodromes. It stays — it is the regulatory tall-structure notification zone.
- The **15 km ARP circle buffer** is a rough generic safeguarding ring, not defined by ICAO/KCAA. It overlaps the outer horizontal entirely, so it is redundant visual noise (worst in the Nairobi cluster: HKJK/HKNW/HKRE/HKFP). Removed from the UI; the outer horizontal keeps full 15 km regulatory coverage when OLS is on.
- `utils.py` `KCAA_ZONE = 15000` and the 15 km lighting logic stay — that is the AC-mandated tall-structure zone, unrelated to the dropped visual circle.

## Decisions

### 1. Layer checker card on `/map/` (style + per-surface OLS toggles)

- Remove the layer-toggle buttons (Airports / Buffers / Runways / OLS / Terrain / 3D OLS / My Props / My Layers) from the bottom `.map-controls` pill row. Keep only the radius buttons + custom input there.
- Add a `#layerChecker` card directly below the basemap switcher (top-right, `top: 140px; right: 10px`), styled like the 3D legend card: white/translucent blur, rounded 12 px, shadow, collapsible header ("Layers" + chevron).
- Rows: main layers, with indented OLS surface sub-rows (color swatch + checkbox). Default state: **only `inner_horizontal` checked**; all other surfaces off until the user enables them.
- Consolidate `SURFACE_META` (labels + colors) into a single shared constant used by both the 2D card and the 3D legend so names/colors never drift. Friendly popup labels (e.g. `Outer horizontal (150 m)`, `Conical (5%)`, `Inner horizontal (45 m)`).
- OLS loading (`loadOls()`): one fetch, route features into per-surface `L.layerGroup()`s; master `olsLayer` unchanged so the OLS master toggle still works. Surface checkbox = `map.addLayer/removeLayer(olsGroups[s])` — no refetch.
- Convert button handlers (`toggleOls`, terrain, airports, etc.) to checkbox handlers; keep internal layer vars and `updateLayerIndicators` behavior.
- Dashboard: `defaultRadiusBtn` 15 → 10, drop the 15 km button, `currentRadius = 10`, initial `loadBuffers(10)`, line `buffer_stats.15km` → `buffer_stats.10km`, plus a compact OLS surface sub-checklist (popover from the OLS button) so both views get per-surface control.

### 2. Drop the 15 km ARP circle buffer; default radius 10 km

- `map_view.html`: remove `data-radius="15"` button; `currentRadius = 10`; initial `loadBuffers(10)`; custom-input placeholder `1-15` → `1-50`.
- `views.py`: default radius 15 → 10 in map view, airport map view, and buffers API (`'10'`); colors dict `{3,5,10}` + gray fallback for custom radii; `buffer_stats` drops the `'15km'` key.
- Existing `radius_km=15` DB rows are left in place (harmless, unused by the UI).

### 3. Update AC references

- `utils.py` lines 38, 332, 590, 604; `views.py` line 2174; `ols_surfaces.py` line 187 comment: `AGA005B` → `AGA005C (June 2024)`.
- `docs/OLS_VERIFICATION_MATRIX.md` lines 6, 57, 95.
- `views.py` line 2067 API doc link: `?radius=15` → `?radius=10`.
- `docs/control-obs.md` is a PDF-extraction log — leave untouched.

## Implementation plan (for the later round)

1. `obstacle_compliance/templates/obstacle_compliance/map_view.html` — layer-checker card (HTML/CSS/JS), per-surface OLS groups, radius default 10.
2. `obstacle_compliance/templates/obstacle_compliance/dashboard.html` — radius default 10, OLS surface sub-checklist, buffer count text.
3. `obstacle_compliance/views.py` — defaults 15 → 10, colors dict, buffer_stats, comments.
4. `obstacle_compliance/utils.py` + `ols_surfaces.py` — AC reference comments.
5. `docs/OLS_VERIFICATION_MATRIX.md` — AC references.
6. Update this ADR + `ADR-buffer_OLS_NA_OA.md` and `ADR-per_service-OLS-layer-independence.md` to record the implemented decisions.

## Verification (when implemented)

- `python manage.py check`.
- Run the relevant `obstacle_compliance` tests (fix any asserting radius 15 defaults).
- Manual pass on `/map/?airport=HKJK`: per-surface toggles work, popups show friendly names, buffers default to 10 km, card sits below the basemap switcher.

## Out of scope

- `radius_km=15` DB rows (kept).
- `utils.py` regulatory 15 km zone + lighting logic (kept, AC-mandated).
- `docs/control-obs.md` (log file).
- The OLS outer horizontal surface itself (kept, AC-mandated; simply off by default in the 2D card).
