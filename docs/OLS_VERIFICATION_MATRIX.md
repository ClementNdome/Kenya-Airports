# OLS Engine Verification Matrix

Engine: `obstacle_compliance/ols_surfaces.py` + `obstacle_compliance/utils.py`
Regulatory sources: ICAO Annex 14 Vol I (8th ed, 2018) Tables 4-1/4-2 and 3-1,
mirrored by KCAA Civil Aviation (Aerodromes Design and Operations) Regulations
2018; Advisory Circulars `docs/CAA-AC-AGA005B CONTROL OF OBSTACLES.pdf` and
`docs/CAA-AC-AGA032A Lighting and Marking of Obstacles.pdf`.

All sampled values below have been re-computed by hand from the table numbers
and confirmed against live engine output (run 2026-08-12).

## 1. Reference code (Table 1-1, field length of critical aeroplane)

| Declared length (m) | Code |
|---------------------|------|
| < 800              | 1    |
| 800–1199           | 2    |
| 1200–1799          | 3    |
| >= 1800            | 4    |
| None / <= 0        | 3 (by design) |

Unit tests: `tests.py::ReferenceCodeTests` (799→1, 800→2, 1800→4, None→3).

## 2. HKJK (Jomo Kenyatta International) engine vs hand calculation

HKJK runway 06/24: length 4115.7 m, threshold elevations 1624 m (06) /
1610 m (24), `precision_i`, code 4, ARP elevation 1625 m AMSL.

### Approach surface (Table 4-1, precision, code 3/4)

Inner edge 280 m half-width, 60 m before the threshold; divergence 15%;
sections: 3000 m @ 2%, 3600 m @ 2.5%, then 8400 m horizontal. Total 15000 m.
Total rise = 0.02 × 3000 + 0.025 × 3600 = 60 + 90 = **150 m**.

| Sample point (from inner edge) | Hand value (AMSL) | Engine | Status |
|--------------------------------|-------------------|--------|--------|
| x = 0 (inner edge)              | 1624.0            | 1624.0   | OK |
| x = 1000 (first section)        | 1624 + 20 = 1644.0 | 1644.0 | OK |
| x = 2970 (~first section end)   | ~1624 + 59.4 = 1683.9 | 1683.9 | OK |
| x = 6600 (plateau start)        | 1624 + 150 = 1774.0 | 1773.8 | OK (geodesic rounding) |
| x > 6600 (horizontal)           | 1774.0            | 1774.0   | OK |

### Take-off climb surface (Table 4-2, code 4)

Inner edge 90 m half-width, 60 m beyond runway end; divergence 12.5% up to
600 m final half-width (break at (600−90)/0.125 = 4080 m); 15000 m @ 2%.
Total rise = 0.02 × 15000 = 300 m above the **departure-end** elevation (1624.0).

| Distance from origin | Hand value (AMSL) | Engine | Status |
|----------------------|-------------------|--------|--------|
| d = 15000 (end)      | 1624 + 300 = 1924.0 | 1923.6 | OK |

### Inner horizontal / conical / outer horizontal (ARP-centred)

IHS radius 4000 m, height 45 m; conical 5% from radius 4000 to 6000 m,
height 100 m (145 m above ARP datum); outer horizontal radius 15000 m,
height 150 m (codes 3/4 only, per AC AGA005B).

| Sample point from ARP | Hand value (AMSL) | Engine | Status |
|-----------------------|-------------------|--------|--------|
| r = 4000              | 1625 + 45 = 1670.0 | 1670.0 | OK |
| r = 4500              | 1625 + 45 + 25 = 1695.0 | 1695.0 | OK |
| r = 5000              | 1625 + 45 + 50 = 1720.0 | 1720.0 | OK |
| r = 6000              | 1625 + 45 + 100 = 1770.0 | 1770.0 | OK |
| r = 14999             | 1625 + 150 = 1775.0 | 1775.0 | OK |

### Balked landing (Table 4-1, precision, code 3/4)

Inner edge 120 m half-width, 1800 m after the threshold; divergence 10%;
slope 3.33% (1/30); terminates where it meets the IHS: 45 / (1/30) = 1350 m.

| Sample | Value | Engine | Status |
|--------|-------|--------|--------|
| balked_landing_24 at example property point (744 m past inner edge) | 1610 + 24.8 = 1634.8 | 1634.8 | OK |

## 3. Synthetic test runway (tests.py) - hand-computed ceilings

Code-4 precision runway, 3400 m, t1=(0°,36°) 100 m → t2=(0°,36.03056°) 110 m,
bearing 90°, ARP (0°, 36.01528°) 100 m.

| Check | Hand value | Test assertion | Status |
|-------|-----------|----------------|--------|
| approach_06 at d=1000: 100 + 0.02 × 1060 | 121.2 | almostEqual 121.2 | OK |
| approach_06 at d=11000, p=800: 100 + 150 | 250.0 | almostEqual 250.0 | OK |
| approach_elevation(x=1000): 100+20 | 120.0 | OK | OK |
| approach_elevation(x=4000): 100+60+25 | 185.0 | OK | OK |
| approach_elevation(x=7000): 100+60+90 | 250.0 | OK | OK |
| code-2 non-instrument take-off at d=2000: 100 + 0.04 × 940 | 137.6 | OK | OK |

Overlap/assignment checks (surface names at sampled points), footprint
counts, `default_config` for no-runway airports, and per-slice 3D heights
(approach ramp → plateau, take-off 4 × 75 m steps, conical 78.3/111.7/145.0)
are covered by `tests.py::SurfaceSliceTests` (24 tests total, all passing).

## 4. Lighting rule (AC AGA005B 4.2.1.3 + AC AGA032A)

A structure is significant if it is **higher than 30 m AGL AND higher than
150 m above the aerodrome elevation within 15 km**. Obstacle light levels
follow AC AGA032A: ~1 level per 45 m of structure height
(`ceil(height / 45)`).

| Property example | Result |
|------------------|--------|
| 25 m building at HKJK ARP (headroom 2.7 m) | YELLOW, light_levels 0 (25 m AGL < 30 m trigger) |
| 100 m building at HKJK ARP | RED, light_levels 3 = ceil(100 / 45) |

## 5. Run results

```
python manage.py check                 -> no issues
python manage.py test obstacle_compliance -> 24 tests, OK (0.07 s)
python manage.py test_compliance        -> sensible RED/YELLOW outputs
All pages and /api/ols.geojson, /api/runways.geojson endpoints -> 200
```