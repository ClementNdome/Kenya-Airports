# ADR: Future Implementation Tracking

This document records features and improvements explicitly deferred to future phases.
Created: 2026-07-30

---
threshold buffer 3/5/10 km eg for (HKNL 03/21)

Server runway buffer unavailable.

## 1. 3D Obstacle Limitation Surfaces (OLS)

**Status:** to be done

**Current implementation (Phase 2):** 2D polygon approximations for OLS:
- Runway centerline strip (ST_Buffer around LineString)
- Threshold approach wedges as flat 2D polygons
- Complex OLS combining strip + wedges

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


