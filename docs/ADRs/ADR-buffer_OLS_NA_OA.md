# ADR: Future Implementation Tracking

This document records features and improvements explicitly deferred to future phases.
Created: 2026-07-30

---
**IMPLEMENTED 2026-08-12 â UTM projection + buffer type selection**
See `ADR-projection-buffer-types.md` in this folder for the full decision record.
(Threshold buffers 3/5/10 km per HKNL 03/21 are now server-generated for any radius.)

---
threshold buffer 3/5/10 km eg for (HKNL 03/21)

Server runway buffer unavailable.

## 1. 3D Obstacle Limitation Surfaces (OLS)

**Status:** IN PROGRESS — runway data now available (2026-08-11)

**Current implementation (Phase 2):** 2D polygon approximations for OLS:
- Runway centerline strip (ST_Buffer around LineString)
- Threshold approach wedges as flat 2D polygons
- Complex OLS combining strip + wedges

**Data unlocked:** 23 runways (19 aerodromes) in `public."aerodrome-runways"`
(LineString `geom`, threshold coordinates/elevations, true/mag bearings, declared length,
strip dimensions) + `public."runways-declared_distances"` (TORA/TODA/ASDA/LDA per runway end,
joined via `(icao_code, TRIM(runway_pair))`). All rows link to existing `Aerodrome` rows.

**Implemented (Phase 2.5, see `obstacle_compliance/utils.py`):**
- True Annex 14 surfaces computed from runway geometry (geodetic bearing from `geom` endpoints):
  - Strip: half-width from `strip_dimensions` or 150m (≥1800m) / 75m (<1800m)
  - Approach surface: 2% (1:50) slope per runway end, 15% lateral divergence,
    inner width = 2× strip half-width, length 3000m
  - Transitional surface: 1:7 (14.3%) from strip edge
  - Horizontal surface: flat 45m ceiling within 4km of ARP
  - Conical surface: 5% slope 4–6km from ARP
- Ceiling at a point = minimum of all applicable surfaces (most restrictive)
- Hybrid fallback: aerodromes without runway rows keep the centroid approximation

**Future requirement:** True 3D sloped surfaces:
- Approach surface: climbs from threshold at defined gradient (e.g. 2%) to a defined width/distance
- Transitional surface: slopes upward from runway strip edges
- Horizontal surface: flat ceiling at defined altitude above aerodrome elevation
- Conical surface: slopes upward from horizontal surface outer edge

**Dependencies:** [already in place as w have a stored COG file at cloudflare R2 and that DEM used as Service in the utils.py in the obstacles_compliance app]
- Digital Elevation Model (DEM) data integration
- 3D geometry support (PostGIS SFCGAL extension or similar)
- Terrain intersection queries (ST_3DIntersects)
- Aviation regulatory data (approach gradients, surface dimensions per ICAO Annex 14)

**Trigger:** When DEM data pipeline is established and 3D obstacle assessment becomes a user requirement.

---

## 2. Persistent Buffer Layers

**Status:** Deferred to future phase after user login and sessions are implemented


** requirement:** Users can save analysis results (buffer polygons, overlay results) as named, persistent layers that appear in the layer panel with visibility toggles, similar to User-Defined Data Layers



---


---

## 3. Client-Side Turf.js Fallback — Complex OLS

**Status:** should be done

**Current implementation:** Complex OLS (strip + approach wedges) is computed server-side via PostGIS only. The turf.js client fallback handles basic centerline and threshold buffers only.

**Future requirement:** Implement complex OLS fallback in turf.js for offline/resilient operation.

---

## 4. Query Tool — Server-Side Spatial + Attribute Queries~~~~~~~~~~~


