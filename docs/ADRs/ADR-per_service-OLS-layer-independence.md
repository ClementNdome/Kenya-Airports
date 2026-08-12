# ADR: Per-surface OLS layer independence — deferred roadmap

Status: **Accepted (deferred)** · Date: 2026-08-12 4.35am· Applies to: `obstacle_compliance` (Kenya-Airports)

## Decisions (deferred)

### 1. Per-surface OLS layer independence

Currently all OLS surfaces are rendered as a single merged layer (one color/opacity, one toggle).
We want:

- Each Annex 14 surface **individually toggleable** (approach, take-off climb, transitional, inner horizontal, conical, inner approach, inner transitional, balked landing, plus the strip/runway surface).
- Distinct colors + legend per surface.
- The OLS GeoJSON API to return per-surface features (`surface` property already exists per feature — client-side grouping is enough; no backend change required beyond maybe `?surface=` filtering).
- Same treatment on the dashboard and map view.



- all the OLS layers in the .../map/ page should be checked on unchecked separately ' the 3D version' in the same page has this already done
- the naming[ the popup names of the OLS layers when clicked] are a bit difficult for a normal user to know what those are .. we might need to simplify things
- we shall revisit the bounding box of around 15km which is in the OLS and if it is trully necessary or if it really adds value to the whole thing cause it might be a bit large and if in some cases like for HKJK,HKNW, HKRE and also HKFP airports/aerodromes whihc are so close together.. that 15km buffer on normal ARP points and now the same 15km in the OLS have so much intersections in these airports and kind of might feel like  noise espcially for this case ; -- all these airports are in the city[Nairobi] but each is serving their own purpose in some cases  and also they all have different categories [international], [millitary], [private], [others compbine].. so we might need to cross check the 15km ring on the OLS and even the buffer one for all airports too not only these ones, and then compare that with ICAO and KCAA specifications .. i have a feeling of dropping the 15km both on points, LINESTRING[runways] and also on the OLS implemantation, a deep study and research is needed for this


## Status of referenced features

- OLS GeoJSON API with per-surface features: **done** (`/api/ols.geojson`, `surface` property).