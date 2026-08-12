# ADR: Map/Visualization Experience Upgrade — deferred roadmap

Status: **Accepted (deferred)** · Date: 2026-08-12 · Applies to: `obstacle_compliance` (Kenya-Airports)

## Context

The 3D OLS visuals and the map experience work, but several gaps were identified during ADR gap-review. This ADR records the items **intentionally deferred** so they can be picked up later without losing context. Each item is independent and can be scheduled on its own.

## Decisions (deferred)

### 1. Per-surface OLS layer independence

Currently all OLS surfaces are rendered as a single merged layer (one color/opacity, one toggle).
We want:

- Each Annex 14 surface **individually toggleable** (approach, take-off climb, transitional, inner horizontal, conical, inner approach, inner transitional, balked landing, plus the strip/runway surface).
- Distinct colors + legend per surface.
- The OLS GeoJSON API to return per-surface features (`surface` property already exists per feature — client-side grouping is enough; no backend change required beyond maybe `?surface=` filtering).
- Same treatment on the dashboard and map view.

### 2. Migration from Leaflet to Mapbox GL JS / MapLibre GL

Evaluate replacing Leaflet with Mapbox GL JS or MapLibre GL for the interactive map + OLS visuals:

- Allows complex 3D visuals (fill-extrusions, per-feature heights from properties, pitch/rotation, terrain 3D) without janky DOM/CSS hacks and without the current per-frame CPU fallback.
- Better performance on large feature sets (WebGL rendering).
- Keep the existing Leaflet implementation as a fallback until parity (markers, popups, geocoder, buffers, search) is confirmed.
- Key risk: rework of `property_check.html`, `map_view.html`, `dashboard.html` JS; two basemaps (Maptiler satellite + OSM) must keep working (Maptiler serves vector tiles usable by MapLibre; OSM raster fallback for MapLibre requires a raster-tile adapter or keeping Leaflet for the default basemap).
- Decision gate: prototype the OLS 3D extrusion + terrain on MapLibre in a standalone page; if the prototype is acceptable, plan the migration; otherwise keep Leaflet and invest in the current renderer.

### 3. Merge property-query into property-check routing

- The public property query tool (`/obstacle-compliance/query/`) is currently not linked from the home page or anywhere else.
- Goal: embed the query experience inside the property-check page (tab or section) to avoid routing users around, or at minimum link it from the home page and map controls.
- Note: the query API (`/api/properties/query/`) is already public and reusable, so the UI work is mostly client-side.

### 4. Minimal property-check card on the /map/ page

- The map page already has the property-check FAB button. Goal: bring a collapsible card with the essential property-check controls (lat/lon/height + "Check") into the map page itself; results render on the map (3D boxes + OLS as today) and in a compact card.
- Complex flows (parcel drawing, full report, profile charts, lighting/notams, save-to-portfolio) keep routing to the dedicated `/property-check/` page.
- This mirrors the same component used by property-check; reuse the JS where possible.

### 5. property check:
the chck compliance is working perfectly but there are some improvements too
- when compliance is been checked and since we have the 3D map effect choices after compliance is done; we can be ensuring that the 3D map is showing the airport onto the area or building was checked agaisnt
- then for the report generation engine, we also need to see if it possible to get a snapshort of the 3D map for the results generated and it is attached to the map- this should be done without overwhelming the system/application at all- hence this is an area of exploration so that results rendered and downloaded are not only just pdf telling someone what is happening but one which has a 3D snapshot of the same too 
- again on the property-check/ the reason i was thinking we should also have it working on the map/ page is cause currently the user only searches an area or draws tone or uses their current location and that result of their action is shown on the side-map; then they proceed with the "cehck compliance" and the compliance results show below the side-map section which is okay but for the map itself nothing changes, nothing else is shown so basically the map is only there to show the user their location after searching- i think we can improve this here too , like showing a client-side buffer or even a server-side buffer(depends on which one that is quick and does not cause any spikes to the resource usage of the system significantly) or even a line or something else too that plays the role of showing the users proximity to the aerodrome point or runway or restricted areas..... thsi is be done on the ../property-check/ page map or subtly on the .../map/ page but not by default- dependent on whether the user decides to use the property-check card that is to be done too

## Status of referenced features

- OLS GeoJSON API with per-surface features: **done** (`/api/ols.geojson`, `surface` property).
- Property query API + page: **done** but unlinked.
- Map page FAB → property-check link: **done**.
- Real 3D sloped OLS surfaces, flyover 4D sim, skyline max-height layer, threshold buffers: implemented separately (see ADR-buffer_OLS_NA_OA.md and 3Dvisuilization-and-OLS.md).
- property check improvements

- by default, the 15km buffer ring should not be checked but rather the 10km ring instead