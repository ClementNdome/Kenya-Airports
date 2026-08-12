# ADRs

Architecture Decision Records live in [`docs/ADRs/`](https://github.com/ClementNdome/Kenya-Airports/tree/main/docs/ADRs).

## Status Summary

| ADR | Date | Status | Summary |
|---|---|---|---|
| `ADR-projection-buffer-types.md` | 2026-08-12 | ✅ **Implemented** | UTM projection util (`projection.py`) replaces Web Mercator/planar-degree math; explicit buffer-type selection (`arp` circle vs `runway` capsule at any radius); geodesic proximity fallback; `regenerate_buffers` command |
| `ADR-property-query-public.md` | 2026-08-11 | ✅ **Accepted (Phase 1)** | Public read-only property query tool; user-scoping deferred until auth matures; documents the `TRIM(runway_pair)` join gotcha |
| `ADR-map-layer-checker-15km-buffer.md` | 2026-08-12 | 🟡 **Partially implemented** | Layer-checker card + per-surface OLS toggles (deferred); ✅ 15 km ARP circle dropped, default radius 10 km (done); ✅ AGA005B → AGA005C references corrected (done) |
| `ADR-buffer_OLS_NA_OA.md` | 2026-07-30 | 🟡 **Partially implemented** | Future-implementation tracker: threshold buffers 3/5/10 km (done); true Annex 14 surfaces as 3D geometry — Phase 2.5 done as true surfaces, full SFCGAL 3D deferred; persistent buffer layers + turf.js fallback deferred |
| `ADR-map-visualization-upgrade.md` | 2026-08-12 | ⏸ **Deferred roadmap** | Per-surface OLS layer independence; Leaflet → Mapbox/MapLibre migration (decision gate = prototype); merge property-query into property-check; minimal property-check card on `/map/`; 3D snapshot in PDF reports; property-check proximity visuals |
| `ADR-per_service-OLS-layer-independence.md` | 2026-08-12 (04:35) | ⏸ **Deferred** | Individually toggleable OLS surfaces with distinct colours/legend; friendly popup naming; revisit the 15 km ring vs the Nairobi cluster (HKJK/HKNW/HKRE/HKFP) |
| `3Dvisuilization-and-OLS.md` | n/a | 📝 Note | Wish: render map and buildings in 3D |
| `OLS & buffering.md` | n/a | 📝 Note | Educational explainer of GIS buffering for OLS analysis |

## Implementation Status Legend

- ✅ **Implemented** — decision is in the codebase
- 🟡 **Partially implemented** — some decisions done, others tracked
- ⏸ **Deferred** — accepted but intentionally not yet scheduled
- 📝 **Note** — non-decision document

## Related Documentation

- [`docs/OLS_VERIFICATION_MATRIX.md`](https://github.com/ClementNdome/Kenya-Airports/blob/main/docs/OLS_VERIFICATION_MATRIX.md) — hand-computed engine verification
- [`docs/specific use case.md`](https://github.com/ClementNdome/Kenya-Airports/blob/main/docs/specific%20use%20case.md) — full product specification
- Regulatory PDFs in `docs/`: ICAO Annex 14 Vol I, AC AGA005C (June 2024), AC AGA032A (Feb 2026)
