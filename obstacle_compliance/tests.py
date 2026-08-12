import math

from django.contrib.gis.geos import Point
from django.test import SimpleTestCase

from . import projection
from .ols_surfaces import AirportOLS, RunwayOLS, reference_code

# Synthetic code-4 precision runway, 3400 m, aligned due east at the equator:
#   t1 = (0.0, 36.0) elev 100 m  ->  t2 = (0.0, 36.03056) elev 110 m
# Approx: 1 deg longitude at the equator = 111319.5 m; 1 deg latitude = 110574 m.
RW4 = {
    't1': (0.0, 36.0),
    't2': (0.0, 36.03056),
    'bearing_rad': math.radians(90.0),
    'elev1_m': 100.0,
    'elev2_m': 110.0,
    'length_m': 3400.0,
    'designator1': '06',
    'designator2': '24',
    'category': 'precision_i',
    'code': 4,
}

M_PER_DEG = 111319.5
M_PER_DEG_LAT = 110574.0


def pt(d_along_m, perp_m=0.0):
    """Point at d_along metres east of t1, perp metres north of the centreline."""
    lat = perp_m / M_PER_DEG_LAT
    lon = 36.0 + d_along_m / M_PER_DEG
    return lat, lon


class ReferenceCodeTests(SimpleTestCase):
    def test_reference_code_thresholds(self):
        self.assertEqual(reference_code(799), 1)
        self.assertEqual(reference_code(800), 2)
        self.assertEqual(reference_code(1199), 2)
        self.assertEqual(reference_code(1200), 3)
        self.assertEqual(reference_code(1799), 3)
        self.assertEqual(reference_code(1800), 4)
        self.assertEqual(reference_code(4117), 4)

    def test_reference_code_unknown(self):
        self.assertEqual(reference_code(None), 3)


class RunwayOLSTests(SimpleTestCase):
    def setUp(self):
        self.rw = RunwayOLS(RW4)
        self.arp = AirportOLS(0.0, 36.01528, 100.0, [self.rw])

    def ceilings_at(self, d_along_m, perp_m=0.0):
        lat, lon = pt(d_along_m, perp_m)
        return self.rw.ceilings_at(lat, lon)

    def min_ceiling(self, d_along_m, perp_m=0.0):
        ceilings = self.ceilings_at(d_along_m, perp_m)
        return min(c for c, _ in ceilings)

    def names_at(self, d_along_m, perp_m=0.0):
        return [name for _, name in self.ceilings_at(d_along_m, perp_m)]

    def test_approach_first_section(self):
        # 1060 m from inner edge (60 m before threshold) at 2% -> 121.2 m AMSL
        self.assertAlmostEqual(self.min_ceiling(1000, 0), 121.2, places=1)
        self.assertIn('approach_06', self.names_at(1000, 0))

    def test_approach_horizontal_section(self):
        # d=11000 east of t1: approach 06 horizontal at 100 + 150 = 250 m
        # (equals the outer horizontal ceiling; conical is higher here)
        self.assertAlmostEqual(self.min_ceiling(11000, 800), 250.0, places=1)
        self.assertIn('approach_06', self.names_at(11000, 800))

    def test_approach_piecewise_elevation(self):
        from .ols_surfaces import approach_elevation
        spec = self.rw.spec
        self.assertAlmostEqual(approach_elevation(spec, 100.0, 1000), 120.0, places=1)
        self.assertAlmostEqual(approach_elevation(spec, 100.0, 4000), 185.0, places=1)   # 60 + 0.025x1000
        self.assertAlmostEqual(approach_elevation(spec, 100.0, 7000), 250.0, places=1)   # 60 + 90 (horizontal)
        self.assertAlmostEqual(approach_elevation(spec, 100.0, 15000), 250.0, places=1)

    def test_approach_lateral_limit(self):
        # half-width at 1060 m = 140 + 0.15 x 1060 = 299 m; 800 m is outside,
        # the transitional-alongside-approach rises 1:7 from that edge
        self.assertAlmostEqual(self.min_ceiling(1000, 800), 121.2 + (800 - 299) / 7.0, delta=1.0)
        self.assertIn('transitional_06', self.names_at(1000, 800))

    def test_approach_inner_edge_half_width(self):
        # Table 4-1 inner edge 280 m is the FULL length; the half-width used
        # by the engine is 140 m each side of the centre line.
        # At d=0, x = 60 m: half-width = 140 + 0.15 x 60 = 149 m.
        self.assertIn('approach_06', self.names_at(0, 100))
        self.assertNotIn('approach_06', self.names_at(0, 200))
        self.assertIn('transitional_06', self.names_at(0, 200))

    def test_inner_approach_half_width(self):
        # Table 4-1 inner approach width is the full 120 m; the engine uses
        # half-widths of 60 m each side.
        self.assertIn('inner_approach_06', self.names_at(100, 50))
        self.assertNotIn('inner_approach_06', self.names_at(100, 70))

    def test_inner_approach_only_on_centreline(self):
        # inner approach half-width is 60 m; p=130 m is inside the approach
        # but outside the inner approach
        names = self.names_at(100, 130)
        self.assertIn('approach_06', names)
        self.assertNotIn('inner_approach_06', names)
        # on the centreline both bind
        names = self.names_at(100, 0)
        self.assertIn('inner_approach_06', names)

    def test_transitional_strip_side(self):
        # mid-runway: strip elevation = 105 m, strip half-width 75 m (code 4),
        # p = 220 m -> 105 + (220-75)/7 = 125.7 m AMSL
        self.assertAlmostEqual(self.min_ceiling(1700, 220), 105.0 + (220 - 75) / 7.0, delta=1.0)
        self.assertIn('transitional_06', self.names_at(1700, 220))

    def test_take_off_climb(self):
        # 1100 m east of t2, take-off climb origin 60 m beyond the end of the
        # strip (t1 + 3460 m): 100 + 0.02 x 1040 = 120.8 m AMSL
        self.assertAlmostEqual(self.min_ceiling(4500, 0), 120.8, delta=0.3)
        self.assertIn('take_off_climb_06', self.names_at(4500, 0))

    def test_balked_landing(self):
        # inner edge 1800 m from threshold 06; at d=2500 m x = 700 m and the
        # surface is 100 + (1/30) x 700 = 123.3 m AMSL (approach 06 is 151.2 m,
        # IHS 145 m; approach 24 does not reach this point)
        self.assertAlmostEqual(self.min_ceiling(2500, 0), 100.0 + 700.0 / 30.0, places=1)
        self.assertIn('balked_landing_06', self.names_at(2500, 0))

    def test_balked_landing_terminates_at_inner_horizontal(self):
        # x > 45 / (1/30) = 1350 m -> the balked landing surface has ended
        self.assertNotIn('balked_landing_06', self.names_at(3400, 0))

    def test_balked_landing_inner_edge_half_width(self):
        # Table 4-1 balked landing inner edge is the full 120 m; the engine
        # uses a 60 m half-width. At x = 50 m past the inner edge the
        # half-width = 60 + 0.10 x 50 = 65 m.
        self.assertIn('balked_landing_06', self.names_at(1850, 50))
        self.assertNotIn('balked_landing_06', self.names_at(1850, 70))

    def test_no_surface_far_away(self):
        self.assertEqual(self.ceilings_at(20000, 0), [])

    def test_conical_north_of_arp(self):
        # 5000 m north of ARP: IHS radius 4000 m (code 4) ->
        # 100 + 45 + (5000-4000) x 0.05 = 195 m AMSL
        ceilings = self.arp.ceiling_at(5000 / M_PER_DEG_LAT, 36.01528)
        self.assertAlmostEqual(ceilings['ceiling_amsl'], 195.0, places=1)
        self.assertIn('conical', ceilings['surfaces'])

    def test_outer_horizontal_limits(self):
        # 10000 m north: outer horizontal 250 m binds below conical 445 m
        ceilings = self.arp.ceiling_at(10000 / M_PER_DEG_LAT, 36.01528)
        self.assertAlmostEqual(ceilings['ceiling_amsl'], 250.0, places=1)
        self.assertIn('outer_horizontal', ceilings['surfaces'])
        # 15100 m north: outside the 15 km outer horizontal -> conical only
        ceilings = self.arp.ceiling_at(15100 / M_PER_DEG_LAT, 36.01528)
        self.assertNotIn('outer_horizontal', ceilings['surfaces'])

    def test_ihs_within_radius(self):
        # 1000 m north of ARP -> flat 45 m above ARP elevation
        ceilings = self.arp.ceiling_at(1000 / M_PER_DEG_LAT, 36.01528)
        self.assertAlmostEqual(ceilings['ceiling_amsl'], 145.0, places=1)
        self.assertIn('inner_horizontal', ceilings['surfaces'])

    def test_default_config_when_no_runways(self):
        a = AirportOLS(0.0, 36.0, 100.0)
        ceilings = a.ceiling_at(1000 / M_PER_DEG_LAT, 36.0)
        self.assertAlmostEqual(ceilings['ceiling_amsl'], 145.0, places=1)

    def test_footprints_closed_polygons(self):
        ring = self.rw.footprint('approach_06')
        self.assertGreater(len(ring), 4)
        self.assertEqual(ring[0], ring[-1])  # closed ring
        fc = self.arp.footprints()
        names = {f['properties']['label'] for f in fc['features']}
        self.assertIn('approach_06', names)
        self.assertIn('approach_24', names)
        self.assertIn('take_off_climb_06', names)
        self.assertIn('take_off_climb_24', names)
        self.assertIn('balked_landing_06', names)
        self.assertIn('strip', names)
        self.assertIn('inner_horizontal', names)
        self.assertIn('conical', names)
        self.assertIn('outer_horizontal', names)


class NonPrecisionRunwayTests(SimpleTestCase):
    """Code-2 non-instrument airstrip - 4% approach and code-2 take-off
    climb (40 m half-width, 4%)."""

    def setUp(self):
        rw2 = dict(RW4)
        rw2.update({
            'length_m': 1000.0,
            'category': 'non_instrument',
            'code': 2,
            'elev2_m': 100.0,
            't2': (0.0, 36.0 + 1000.0 / M_PER_DEG),
        })
        self.rw = RunwayOLS(rw2)

    def ceilings_at(self, d_along_m, perp_m=0.0):
        lat, lon = pt(d_along_m, perp_m)
        return self.rw.ceilings_at(lat, lon)

    def min_ceiling(self, d_along_m, perp_m=0.0):
        return min(c for c, _ in self.ceilings_at(d_along_m, perp_m))

    def test_non_instrument_approach(self):
        # inner edge 80 m, 10% divergence, 2500 m @ 4% (code 2)
        self.assertAlmostEqual(self.min_ceiling(500, 0), 100.0 + 0.04 * 560, places=0)
        self.assertIn('approach_06', [n for _, n in self.ceilings_at(500, 0)])

    def test_take_off_climb_code2(self):
        # origin 60 m beyond the strip end: 100 + 0.04 x 940 = 137.6 m AMSL
        self.assertAlmostEqual(self.min_ceiling(2000, 0), 137.6, places=1)
        self.assertIn('take_off_climb_06', [n for _, n in self.ceilings_at(2000, 0)])

    def test_no_transitional_within_strip(self):
        # p = 30 m < strip half-width 40 m for code 2 -> no transitional
        self.assertNotIn('transitional_06', [n for _, n in self.ceilings_at(500, 30)])


class SurfaceSliceTests(SimpleTestCase):
    """3D footprint slices must carry the true Annex 14 ceiling per slice."""

    def setUp(self):
        self.rw = RunwayOLS(RW4)

    def test_approach_slices_ramp_to_plateau(self):
        slices = self.rw.surface_slices('approach_06', n=8)
        heights = [h for _, h, _ in slices]
        self.assertEqual(heights[0], 37.5)     # 0.02 * 1875 m (15000/8)
        self.assertEqual(heights[-1], 150.0)   # 60 (2%) + 90 (2.5%) plateau
        self.assertEqual(len(slices), 8)
        first_ring = slices[0][0]
        last_ring = slices[-1][0]
        self.assertNotEqual(first_ring[0][0], last_ring[0][0])

    def test_take_off_slices_linear(self):
        slices = self.rw.surface_slices('take_off_climb_06', n=4)
        heights = [h for _, h, _ in slices]
        # 15000 m @ 2% over 4 slices: 75, 150, 225, 300
        self.assertEqual(heights, [75.0, 150.0, 225.0, 300.0])

    def test_conical_wedge_heights(self):
        fc = AirportOLS(0.0, 36.01528, 100.0, [self.rw]).footprints()
        con = [f for f in fc['features'] if f['properties']['surface'] == 'conical']
        self.assertEqual(len(con), 24)  # 8 wedges x 3 radial slices
        heights = sorted({f['properties']['height_m'] for f in con})
        # code-4 precision: cone 3600m -> 6000m, 45m -> 145m; each slice takes
        # its outer-edge height, so the 45 m boundary never appears
        self.assertEqual(heights, [78.3, 111.7, 145.0])

    def test_footprints_have_per_vertex_heights(self):
        fc = AirportOLS(0.0, 36.01528, 100.0, [self.rw]).footprints()
        for f in fc['features']:
            ring = f['geometry']['coordinates'][0]
            self.assertEqual(len(f['properties']['heights']), len(ring))


class NonInstrumentCode1Tests(SimpleTestCase):
    """Code-1 non-instrument strip: approach inner edge is the full 60 m
    (30 m half-width) - pins the Table 4-1 half-width convention."""

    def setUp(self):
        rw1 = dict(RW4)
        rw1.update({
            'length_m': 900.0,
            'category': 'non_instrument',
            'code': 1,
            'elev2_m': 100.0,
            't2': (0.0, 36.0 + 900.0 / M_PER_DEG),
        })
        self.rw = RunwayOLS(rw1)

    def test_approach_inner_edge_half_width(self):
        # x = 100 + 30 (dist from threshold, code 1) = 130 m; half-width =
        # 30 + 0.10 x 130 = 43 m -> p=25 inside, p=50 outside (transitional
        # alongside the approach binds beyond the edge)
        self.assertIn('approach_06', [n for _, n in self.rw.ceilings_at(*pt(100, 25))])
        names = [n for _, n in self.rw.ceilings_at(*pt(100, 50))]
        self.assertNotIn('approach_06', names)
        self.assertIn('transitional_06', names)


class OuterHorizontalSignificanceTests(SimpleTestCase):
    """AC AGA005C 4.2.1.3: an outer-horizontal penetration beyond the conical
    surface is one of 'possible significance', not a hard OLS hazard."""

    def test_significance_classification(self):
        from .utils import significant_outer_horizontal
        self.assertTrue(significant_outer_horizontal(['outer_horizontal'], 300.0, 100.0))
        self.assertFalse(significant_outer_horizontal(['outer_horizontal'], 249.0, 100.0))
        self.assertFalse(significant_outer_horizontal(['outer_horizontal'], 250.0, 100.0))
        self.assertFalse(significant_outer_horizontal(['inner_horizontal', 'outer_horizontal'], 300.0, 100.0))
        self.assertFalse(significant_outer_horizontal([], 500.0, 100.0))


class ProjectionTests(SimpleTestCase):
    """UTM zone selection + true-metric buffering (no DB required)."""

    def test_utm_zone_selection_kenya(self):
        # Nairobi (south, zone 36): EPSG 32736
        self.assertEqual(projection.utm_epsg(36.82, -1.32), 32736)
        # Kisumu (south, zone 36): EPSG 32736
        self.assertEqual(projection.utm_epsg(34.75, -0.10), 32736)
        # Mombasa (south, zone 37): EPSG 32737
        self.assertEqual(projection.utm_epsg(39.67, -4.04), 32737)
        # Moyale (north, zone 37): EPSG 32637
        self.assertEqual(projection.utm_epsg(39.10, 3.50), 32637)
        # Lodwar (north, zone 36): EPSG 32636
        self.assertEqual(projection.utm_epsg(35.60, 3.12), 32636)

    def test_buffer_m_is_true_metric(self):
        p = Point(36.82, -1.32, srid=4326)  # HKJK
        buf = projection.buffer_m(p, 1000.0)
        self.assertIsNotNone(buf)
        area = projection.area_m2(buf)
        self.assertAlmostEqual(area, math.pi * 1_000_000, delta=area * 0.01)
        # Extents in the local UTM zone must be ~2 km both ways.
        u = projection.to_utm(buf.clone())
        xmin, ymin, xmax, ymax = u.extent
        self.assertAlmostEqual(xmax - xmin, 2000.0, delta=25.0)
        self.assertAlmostEqual(ymax - ymin, 2000.0, delta=25.0)

    def test_geodesic_distance(self):
        # JKIA (36.9278, -1.3192) -> Wilson (36.8150, -1.3186): ~12.5 km.
        d = projection.distance_m(Point(36.9278, -1.3192, srid=4326),
                                  Point(36.8150, -1.3186, srid=4326))
        self.assertGreater(d, 12_000)
        self.assertLess(d, 14_000)
