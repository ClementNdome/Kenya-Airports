# Testing

## Run

```sh
python manage.py test obstacle_compliance
```

## Test Suite

**32 test methods** across 7 classes in `obstacle_compliance/tests.py`. All are `SimpleTestCase` — **no database required**, so the suite runs anywhere Django boots.

| Class | Covers |
|---|---|
| `ReferenceCodeTests` | Code 1–4 thresholds from declared runway length |
| `RunwayOLSTests` | Synthetic code-4 precision runway: approach sections, horizontal section, lateral limits, inner approach, transitional, take-off climb, balked landing + termination, conical/outer-horizontal/IHS ceilings, footprint geometry |
| `NonPrecisionRunwayTests` | Code-2 non-instrument surfaces |
| `NonInstrumentCode1Tests` | Code-1 non-instrument surfaces |
| `SurfaceSliceTests` | 3D slice heights: approach ramp → plateau, take-off linear rise, conical wedges, per-vertex heights |
| `OuterHorizontalSignificanceTests` | 15 km / 150 m outer-horizontal significance rules (AC AGA005C §4.2.1.3) |
| `ProjectionTests` | UTM zone selection for 5 Kenyan cities (Nairobi/Kisumu/Mombasa/Moyale/Lodwar), true-metric 1 km buffer (area ≈ π km², extents ≈ 2 km), geodesic JKIA→Wilson ≈ 12.5 km |

## Verification Matrix

[`docs/OLS_VERIFICATION_MATRIX.md`](https://github.com/ClementNdome/Kenya-Airports/blob/main/docs/OLS_VERIFICATION_MATRIX.md) contains hand-computed, table-by-table verification of the OLS engine against ICAO Annex 14:

- HKJK approach / take-off / ARP-centred surfaces
- Balked landing on a synthetic runway
- Lighting rules (AC AGA032A)

## CI

- **GitHub Actions** (`.github/workflows/django.yml`) — push/PR to `main`; Python 3.7/3.8/3.9 matrix (⚠ outdated for Django 5.1, needs ≥3.10 — and no PostGIS service, so DB-backed flows would fail).
- **GitLab CI** (`.gitlab-ci.yml`) — `python:3.12-slim` + `postgis/postgis:15-3.3` service; runs `check`, `migrate`, `test`; artifacts `htmlcov/`.
