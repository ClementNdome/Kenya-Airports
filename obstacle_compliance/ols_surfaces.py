# obstacle_compliance/ols_surfaces.py
#
# Obstacle Limitation Surfaces per ICAO Annex 14 Vol I (8th ed 2018),
# Tables 4-1 and 4-2 - the tables mirrored by the KCAA Civil Aviation
# (Aerodromes Design and Operations) Regulations 2018 and referenced by
# Advisory Circular CAA-AC-AGA005C (Control of Obstacles).
#
# All slope/height/length numbers below are transcribed directly from the
# ICAO tables. "inner_edge" values are half-widths (each side of the centre
# line), as Annex 14 defines the inner edge length per side.
import math

from geopy.distance import geodesic

# ---------------------------------------------------------------------------
# Geodetic helpers (shared with utils.py)
# ---------------------------------------------------------------------------

def initial_bearing_rad(lat1, lon1, lat2, lon2):
    """Initial bearing in radians (clockwise from north) between two points."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    x = math.sin(dlam) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return math.atan2(x, y)


def destination_point_rad(lat, lon, bearing_rad, distance_m):
    """Destination coordinates given start point, bearing (radians), distance (m)."""
    R = 6371000.0
    delta = distance_m / R
    phi1 = math.radians(lat)
    lam1 = math.radians(lon)
    phi2 = math.asin(math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(bearing_rad))
    lam2 = lam1 + math.atan2(math.sin(bearing_rad) * math.sin(delta) * math.cos(phi1),
                             math.cos(delta) - math.sin(phi1) * math.sin(phi2))
    return math.degrees(phi2), math.degrees(lam2)


def along_perp_dist(thr_lat, thr_lon, bearing_rad, lat, lon):
    """Project a point onto a line (threshold + bearing).

    Returns (d_along_m, d_perp_m): metres along the line (0 at the origin,
    positive in the bearing direction) and signed lateral offset (positive
    right of the direction of travel). Planar approximation - accurate for
    OLS-sized distances.
    """
    distance = geodesic((thr_lat, thr_lon), (lat, lon)).meters
    p_bearing = initial_bearing_rad(thr_lat, thr_lon, lat, lon)
    delta = (p_bearing - bearing_rad + math.pi) % (2 * math.pi) - math.pi
    return distance * math.cos(delta), distance * math.sin(delta)


# ---------------------------------------------------------------------------
# Reference code (Annex 14 Table 1-1: field length of the critical aeroplane)
# ---------------------------------------------------------------------------

def reference_code(length_m):
    """Code number 1-4 derived from runway declared length."""
    if not length_m or length_m <= 0:
        return 3
    if length_m < 800:
        return 1
    if length_m < 1200:
        return 2
    if length_m < 1800:
        return 3
    return 4


# ---------------------------------------------------------------------------
# Annex 14 Table 4-1 (approach runways) and Table 4-2 (take-off climb)
# ---------------------------------------------------------------------------

CATEGORIES = ('non_instrument', 'non_precision', 'precision_i', 'precision_ii_iii')

# Strip half-width per code number (Table 3-1: 60/80/150/150 m total width)
STRIP_HALF_WIDTH = {1: 30.0, 2: 40.0, 3: 75.0, 4: 75.0}

# Inner horizontal surface: height above the aerodrome elevation datum (45 m
# for all codes) and radius per (category, code).
IHS_HEIGHT = 45.0
IHS_RADIUS = {
    'non_instrument': {1: 2000.0, 2: 2500.0, 3: 4000.0, 4: 4000.0},
    'non_precision': {1: 3500.0, 2: 3500.0, 3: 4000.0, 4: 4000.0},
    'precision_i': {1: 3500.0, 2: 3500.0, 3: 4000.0, 4: 4000.0},
    'precision_ii_iii': {1: 3500.0, 2: 3500.0, 3: 4000.0, 4: 4000.0},
}

# Conical surface: slope 5%; height above the inner horizontal surface.
CONICAL_SLOPE = 0.05
CONICAL_HEIGHT = {
    'non_instrument': {1: 35.0, 2: 55.0, 3: 75.0, 4: 100.0},
    'non_precision': {1: 60.0, 2: 60.0, 3: 75.0, 4: 100.0},
    'precision_i': {1: 60.0, 2: 60.0, 3: 100.0, 4: 100.0},
    'precision_ii_iii': {1: 60.0, 2: 60.0, 3: 100.0, 4: 100.0},
}

# Approach surface. first/second are (length_m, slope); horizontal is the
# length of the horizontal section; total is the overall surface length.
# Distances measured from the inner edge; inner edge lies "distance from
# threshold" before the threshold.
APPROACH = {
    'non_instrument': {
        1: dict(inner_edge=60.0, dist_from_thr=30.0, divergence=0.10,
                first=(1600.0, 0.05), second=None, horizontal=0.0, total=1600.0),
        2: dict(inner_edge=80.0, dist_from_thr=60.0, divergence=0.10,
                first=(2500.0, 0.04), second=None, horizontal=0.0, total=2500.0),
        3: dict(inner_edge=150.0, dist_from_thr=60.0, divergence=0.10,
                first=(3000.0, 0.0333), second=None, horizontal=0.0, total=3000.0),
        4: dict(inner_edge=150.0, dist_from_thr=60.0, divergence=0.10,
                first=(3000.0, 0.025), second=None, horizontal=0.0, total=3000.0),
    },
    'non_precision': {
        1: dict(inner_edge=140.0, dist_from_thr=60.0, divergence=0.15,
                first=(2500.0, 0.0333), second=None, horizontal=0.0, total=2500.0),
        2: dict(inner_edge=140.0, dist_from_thr=60.0, divergence=0.15,
                first=(2500.0, 0.0333), second=None, horizontal=0.0, total=2500.0),
        3: dict(inner_edge=280.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.02), second=(3600.0, 0.025), horizontal=8400.0, total=15000.0),
        4: dict(inner_edge=280.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.02), second=(3600.0, 0.025), horizontal=8400.0, total=15000.0),
    },
    'precision_i': {
        1: dict(inner_edge=140.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.025), second=(12000.0, 0.03), horizontal=0.0, total=15000.0),
        2: dict(inner_edge=140.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.025), second=(12000.0, 0.03), horizontal=0.0, total=15000.0),
        3: dict(inner_edge=280.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.02), second=(3600.0, 0.025), horizontal=8400.0, total=15000.0),
        4: dict(inner_edge=280.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.02), second=(3600.0, 0.025), horizontal=8400.0, total=15000.0),
    },
    'precision_ii_iii': {
        1: dict(inner_edge=140.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.025), second=(12000.0, 0.03), horizontal=0.0, total=15000.0),
        2: dict(inner_edge=140.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.025), second=(12000.0, 0.03), horizontal=0.0, total=15000.0),
        3: dict(inner_edge=280.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.02), second=(3600.0, 0.025), horizontal=8400.0, total=15000.0),
        4: dict(inner_edge=280.0, dist_from_thr=60.0, divergence=0.15,
                first=(3000.0, 0.02), second=(3600.0, 0.025), horizontal=8400.0, total=15000.0),
    },
}

# Transitional surface slope per code number (20% code 1/2, 14.3% code 3/4)
TRANSITIONAL_SLOPE = {1: 0.20, 2: 0.20, 3: 1.0 / 7.0, 4: 1.0 / 7.0}

# Inner approach surface (precision runways only): hw = half-width each side,
# dist = distance of inner edge before the threshold.
INNER_APPROACH = {
    1: dict(hw=90.0, dist=60.0, length=900.0, slope=0.025),
    2: dict(hw=90.0, dist=60.0, length=900.0, slope=0.025),
    3: dict(hw=120.0, dist=60.0, length=900.0, slope=0.02),
    4: dict(hw=120.0, dist=60.0, length=900.0, slope=0.02),
}

# Inner transitional surface slope (precision runways only): 40% code 1/2,
# 33.3% code 3/4.
INNER_TRANSITIONAL_SLOPE = {1: 0.40, 2: 0.40, 3: 1.0 / 3.0, 4: 1.0 / 3.0}

# Balked landing surface (precision runways only). dist = distance of the
# inner edge after the threshold (end of strip for code 1/2).
BALKED_LANDING = {
    1: dict(hw=90.0, dist=0.0, divergence=0.10, slope=0.04, strip_end=True),
    2: dict(hw=90.0, dist=0.0, divergence=0.10, slope=0.04, strip_end=True),
    3: dict(hw=120.0, dist=1800.0, divergence=0.10, slope=1.0 / 30.0, strip_end=False),
    4: dict(hw=120.0, dist=1800.0, divergence=0.10, slope=1.0 / 30.0, strip_end=False),
}

# Take-off climb surface (Table 4-2). hw = half of "length of inner edge",
# final_width is the total width; divergence applies until final half-width
# is reached, then the width stays constant.
TAKE_OFF_CLIMB = {
    1: dict(hw=30.0, dist_from_end=30.0, divergence=0.10, length=1600.0,
            slope=0.05, final_half=190.0),
    2: dict(hw=40.0, dist_from_end=60.0, divergence=0.10, length=2500.0,
            slope=0.04, final_half=290.0),
    3: dict(hw=90.0, dist_from_end=60.0, divergence=0.125, length=15000.0,
            slope=0.02, final_half=600.0),
    4: dict(hw=90.0, dist_from_end=60.0, divergence=0.125, length=15000.0,
            slope=0.02, final_half=600.0),
}

# Outer horizontal surface - not an Annex 14 table item; per KCAA AC
# AGA005B 4.2.1.3 tall structures are significant when higher than 30 m AGL
# and higher than 150 m above aerodrome elevation within 15 000 m of the
# aerodrome centre (runway code number 3 or 4).
OUTER_HORIZONTAL_HEIGHT = 150.0
OUTER_HORIZONTAL_RADIUS = 15000.0
OUTER_HORIZONTAL_CODES = (3, 4)


def approach_elevation(spec, elev_thr, x):
    """Elevation of the approach surface at distance x (m) from its inner edge."""
    first_len, first_slope = spec['first']
    if x <= first_len:
        return elev_thr + first_slope * x
    e = elev_thr + first_slope * first_len
    second = spec.get('second')
    if second:
        second_len, second_slope = second
        if x <= first_len + second_len:
            return e + second_slope * (x - first_len)
        e += second_slope * second_len
    return e


# ---------------------------------------------------------------------------
# Per-runway OLS evaluation
# ---------------------------------------------------------------------------

class RunwayOLS:
    """Evaluates the runway-dependent OLS surfaces of a single runway.

    runway_data keys: t1, t2 (lat,lon), bearing_rad (t1->t2), elev1_m,
    elev2_m, length_m, designator1, designator2, category, code.
    """

    def __init__(self, rw):
        self.rw = rw
        self.category = rw.get('category') or 'non_precision'
        self.code = rw.get('code') or reference_code(rw.get('length_m'))
        self.length_m = rw['length_m']
        self.elev1 = rw.get('elev1_m', 0.0)
        self.elev2 = rw.get('elev2_m', 0.0)
        self.bearing = rw['bearing_rad']
        self.strip_hw = STRIP_HALF_WIDTH.get(self.code, 75.0)
        self.trans_slope = TRANSITIONAL_SLOPE.get(self.code, 1.0 / 7.0)
        self.precision = self.category in ('precision_i', 'precision_ii_iii')
        self.spec = APPROACH.get(self.category, APPROACH['non_precision']).get(self.code)

    def _strip_elevation(self, d_along):
        """Interpolated runway centreline elevation at distance d_along (m)."""
        if self.length_m <= 0:
            return self.elev1
        f = max(0.0, min(1.0, d_along / self.length_m))
        return self.elev1 + (self.elev2 - self.elev1) * f

    def ceilings_at(self, lat, lon):
        """Return [(ceiling_amsl, surface_label), ...] for every surface that
        covers the point (lat, lon)."""
        out = []
        b1 = self.bearing
        b2 = self.bearing + math.pi if self.bearing <= 0 else self.bearing - math.pi

        # ---- Approach surface (both ends) ----
        if self.spec:
            for (thr, elev, brg, label) in (
                (self.rw['t1'], self.elev1, b1, self.rw.get('designator1', 'end1')),
                (self.rw['t2'], self.elev2, b2, self.rw.get('designator2', 'end2')),
            ):
                d, p = along_perp_dist(thr[0], thr[1], brg, lat, lon)
                x = d + self.spec['dist_from_thr']
                if 0.0 <= x <= self.spec['total']:
                    hw = self.spec['inner_edge'] + self.spec['divergence'] * x
                    if abs(p) <= hw:
                        out.append((approach_elevation(self.spec, elev, x), 'approach_%s' % label))
                        # A point inside the approach is inside the (steeper)
                        # inner approach / OFZ zone as well when precision.
                        if self.precision:
                            ia = INNER_APPROACH.get(self.code)
                            if ia and 0.0 <= x <= ia['dist'] + ia['length']:
                                if abs(p) <= ia['hw']:
                                    out.append((elev + ia['slope'] * x, 'inner_approach_%s' % label))

        # ---- Inner approach (rectangle, precision runways) ----
        if self.precision:
            ia = INNER_APPROACH.get(self.code)
            if ia:
                for (thr, elev, brg, label) in (
                    (self.rw['t1'], self.elev1, b1, self.rw.get('designator1', 'end1')),
                    (self.rw['t2'], self.elev2, b2, self.rw.get('designator2', 'end2')),
                ):
                    d, p = along_perp_dist(thr[0], thr[1], brg, lat, lon)
                    x = d + ia['dist']
                    if 0.0 <= x <= ia['length'] and abs(p) <= ia['hw']:
                        out.append((elev + ia['slope'] * x, 'inner_approach_%s' % label))

        # ---- Transitional surfaces (strip side, both sides of the strip) ----
        for (thr, elev, brg, label, d_start, d_end) in (
            (self.rw['t1'], self.elev1, b1, self.rw.get('designator1', 'end1'), 0.0, self.length_m),
            (self.rw['t2'], self.elev2, b2, self.rw.get('designator2', 'end2'), 0.0, self.length_m),
        ):
            d, p = along_perp_dist(thr[0], thr[1], brg, lat, lon)
            if 0.0 <= d <= d_end:
                base = self._strip_elevation(d if d_start == 0 else d_end - d)
                if abs(p) > self.strip_hw:
                    out.append((base + (abs(p) - self.strip_hw) * self.trans_slope, 'transitional_%s' % label))
                    if self.precision:
                        its = INNER_TRANSITIONAL_SLOPE.get(self.code, 1.0 / 3.0)
                        out.append((base + (abs(p) - self.strip_hw) * its, 'inner_transitional_%s' % label))

        # ---- Transitional alongside the approach surface ----
        if self.spec:
            for (thr, elev, brg, label) in (
                (self.rw['t1'], self.elev1, b1, self.rw.get('designator1', 'end1')),
                (self.rw['t2'], self.elev2, b2, self.rw.get('designator2', 'end2')),
            ):
                d, p = along_perp_dist(thr[0], thr[1], brg, lat, lon)
                x = d + self.spec['dist_from_thr']
                if 0.0 <= x <= self.spec['total']:
                    hw = self.spec['inner_edge'] + self.spec['divergence'] * x
                    if abs(p) > hw:
                        ap_elev = approach_elevation(self.spec, elev, x)
                        out.append((ap_elev + (abs(p) - hw) * self.trans_slope, 'transitional_%s' % label))

        # ---- Balked landing surface (precision runways) ----
        if self.precision:
            bl = BALKED_LANDING.get(self.code)
            if bl:
                bl_dist = self.length_m + bl.get('strip_extra', 0.0) if bl['strip_end'] else bl['dist']
                # Surface ends where it meets the inner horizontal surface
                # (45 m above the ARP datum).
                end_len = min(IHS_HEIGHT / bl['slope'], 13500.0)
                for (thr, elev, brg, label) in (
                    (self.rw['t1'], self.elev1, b1, self.rw.get('designator1', 'end1')),
                    (self.rw['t2'], self.elev2, b2, self.rw.get('designator2', 'end2')),
                ):
                    d, p = along_perp_dist(thr[0], thr[1], brg, lat, lon)
                    x = d - bl_dist
                    if 0.0 <= x <= end_len:
                        hw = bl['hw'] + bl['divergence'] * x
                        if abs(p) <= hw:
                            out.append((elev + bl['slope'] * x, 'balked_landing_%s' % label))

        # ---- Take-off climb surface (both ends) ----
        toc = TAKE_OFF_CLIMB.get(self.code)
        if toc:
            for (end_pt, elev, brg, label) in (
                (self.rw['t1'], self.elev1, b1, self.rw.get('designator1', 'end1')),
                (self.rw['t2'], self.elev2, b2, self.rw.get('designator2', 'end2')),
            ):
                origin = destination_point_rad(end_pt[0], end_pt[1], brg, self.length_m + toc['dist_from_end'])
                d, p = along_perp_dist(origin[0], origin[1], brg, lat, lon)
                if 0.0 <= d <= toc['length']:
                    hw = min(toc['hw'] + toc['divergence'] * d, toc['final_half'])
                    if abs(p) <= hw:
                        out.append((elev + toc['slope'] * d, 'take_off_climb_%s' % label))

        return out

    # ------------------------------------------------------------------
    # Footprint polygons (for map/3D visualization) - returns GeoJSON
    # geometry dicts in WGS84 [lon, lat] order.
    # ------------------------------------------------------------------

    @staticmethod
    def _ring(points):
        pts = [[lon, lat] for (lat, lon) in points]
        if pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return pts

    def _quad(self, centre_pt, brg, half_w, start, end):
        """Trapezoid along bearing brg from distance start to end (m)."""
        c1 = destination_point_rad(centre_pt[0], centre_pt[1], brg, start)
        c2 = destination_point_rad(centre_pt[0], centre_pt[1], brg, end)
        left1 = destination_point_rad(c1[0], c1[1], brg - math.pi / 2, half_w)
        right1 = destination_point_rad(c1[0], c1[1], brg + math.pi / 2, half_w)
        left2 = destination_point_rad(c2[0], c2[1], brg - math.pi / 2, half_w)
        right2 = destination_point_rad(c2[0], c2[1], brg + math.pi / 2, half_w)
        return self._ring([left1, right1, right2, left2])

    def footprint(self, name):
        """Return a GeoJSON polygon for a named surface, or None."""
        b1 = self.bearing
        b2 = self.bearing + math.pi if self.bearing <= 0 else self.bearing - math.pi
        ends = [
            (self.rw['t1'], b1, self.rw.get('designator1', 'end1')),
            (self.rw['t2'], b2, self.rw.get('designator2', 'end2')),
        ]
        spec = self.spec
        if name.startswith('approach_') and spec:
            label = name.split('_', 1)[1]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                x0, x1 = 0.0, spec['total']
                w0 = spec['inner_edge']
                w1 = spec['inner_edge'] + spec['divergence'] * spec['total']
                start = -spec['dist_from_thr']
                c1 = destination_point_rad(thr[0], thr[1], brg, start)
                c2 = destination_point_rad(thr[0], thr[1], brg, spec['total'] - spec['dist_from_thr'])
                return self._ring([
                    destination_point_rad(c1[0], c1[1], brg - math.pi / 2, w0),
                    destination_point_rad(c1[0], c1[1], brg + math.pi / 2, w0),
                    destination_point_rad(c2[0], c2[1], brg + math.pi / 2, w1),
                    destination_point_rad(c2[0], c2[1], brg - math.pi / 2, w1),
                ])
        if name == 'strip':
            pts = []
            for (thr, brg, dlabel) in ends:
                c = destination_point_rad(thr[0], thr[1], brg, self.length_m)
                for lat, lon in (c, thr):
                    left = destination_point_rad(lat, lon, brg - math.pi / 2, self.strip_hw)
                    right = destination_point_rad(lat, lon, brg + math.pi / 2, self.strip_hw)
                    pts.extend([left, right])
            return self._ring(pts)
        if name.startswith('inner_approach_') and self.precision:
            ia = INNER_APPROACH.get(self.code)
            if not ia:
                return None
            label = name.split('_', 2)[2]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                start = -ia['dist']
                return self._quad(thr, brg, ia['hw'], start, start + ia['length'])
        if name.startswith('take_off_climb_'):
            toc = TAKE_OFF_CLIMB.get(self.code)
            if not toc:
                return None
            label = name.rsplit('_', 1)[1]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                origin = destination_point_rad(thr[0], thr[1], brg, self.length_m + toc['dist_from_end'])
                # half-width reaches final_half at d_break, then stays constant
                d_break = (toc['final_half'] - toc['hw']) / toc['divergence']
                d_break = min(d_break, toc['length'])
                corners = []
                for d, hw in ((0.0, toc['hw']), (d_break, toc['final_half']), (toc['length'], toc['final_half'])):
                    c = destination_point_rad(origin[0], origin[1], brg, d)
                    corners.extend([
                        destination_point_rad(c[0], c[1], brg - math.pi / 2, hw),
                        destination_point_rad(c[0], c[1], brg + math.pi / 2, hw),
                    ])
                return self._ring([corners[0], corners[1], corners[3], corners[5], corners[4], corners[2]])
        if name.startswith('balked_landing_') and self.precision:
            bl = BALKED_LANDING.get(self.code)
            if not bl:
                return None
            label = name.rsplit('_', 1)[1]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                bl_dist = self.length_m if bl['strip_end'] else bl['dist']
                end_len = min(IHS_HEIGHT / bl['slope'], 13500.0)
                return self._quad(thr, brg, bl['hw'], bl_dist, bl_dist + end_len)
        return None

    def _slices(self, centre_pt, brg, xs, ws, hs):
        """Trapezoid slices along bearing brg.

        xs: along-track distances of the slice boundaries, ws: half-widths,
        hs: surface rise (m) at each boundary. Returns a list of
        (ring, max_h, per_vertex_heights) tuples.
        """
        out = []
        for i in range(len(xs) - 1):
            c1 = destination_point_rad(centre_pt[0], centre_pt[1], brg, xs[i])
            c2 = destination_point_rad(centre_pt[0], centre_pt[1], brg, xs[i + 1])
            h = max(hs[i], hs[i + 1])
            out.append((
                self._ring([
                    destination_point_rad(c1[0], c1[1], brg - math.pi / 2, ws[i]),
                    destination_point_rad(c1[0], c1[1], brg + math.pi / 2, ws[i]),
                    destination_point_rad(c2[0], c2[1], brg + math.pi / 2, ws[i + 1]),
                    destination_point_rad(c2[0], c2[1], brg - math.pi / 2, ws[i + 1]),
                ]),
                round(h, 1),
                [round(hs[i], 1), round(hs[i], 1), round(hs[i + 1], 1), round(hs[i + 1], 1),
                 round(hs[i], 1)],
            ))
        return out

    def surface_slices(self, name, n=6):
        """Footprint of a named surface split into axis slices for 3D.

        Each slice carries its real Annex 14 ceiling rise (height_m, plus a
        per-vertex heights array), so fill-extrusion rendering shows the
        correct tapered/stepped shape instead of one flat max-height prism.
        Returns a list of (ring, height_m, heights) tuples, or None.
        """
        b1 = self.bearing
        b2 = self.bearing + math.pi if self.bearing <= 0 else self.bearing - math.pi
        ends = [
            (self.rw['t1'], b1, self.rw.get('designator1', 'end1')),
            (self.rw['t2'], b2, self.rw.get('designator2', 'end2')),
        ]
        spec = self.spec
        if name.startswith('approach_') and spec:
            label = name.split('_', 1)[1]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                start = -spec['dist_from_thr']
                xs = [start + spec['total'] * i / n for i in range(n + 1)]
                ws = [spec['inner_edge'] + spec['divergence'] * (x - start) for x in xs]
                hs = [approach_elevation(spec, 0.0, x - start) for x in xs]
                return self._slices(thr, brg, xs, ws, hs)
        if name.startswith('inner_approach_') and self.precision:
            ia = INNER_APPROACH.get(self.code)
            if not ia:
                return None
            label = name.split('_', 2)[2]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                start = -ia['dist']
                xs = [start + ia['length'] * i / n for i in range(n + 1)]
                ws = [ia['hw']] * (n + 1)
                hs = [ia['slope'] * x for x in (x - start for x in xs)]
                return self._slices(thr, brg, xs, ws, hs)
        if name.startswith('take_off_climb_'):
            toc = TAKE_OFF_CLIMB.get(self.code)
            if not toc:
                return None
            label = name.rsplit('_', 1)[1]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                origin = destination_point_rad(thr[0], thr[1], brg,
                                               self.length_m + toc['dist_from_end'])
                xs = [toc['length'] * i / n for i in range(n + 1)]
                ws = [min(toc['hw'] + toc['divergence'] * x, toc['final_half']) for x in xs]
                hs = [toc['slope'] * x for x in xs]
                return self._slices(origin, brg, xs, ws, hs)
        if name.startswith('balked_landing_') and self.precision:
            bl = BALKED_LANDING.get(self.code)
            if not bl:
                return None
            label = name.rsplit('_', 1)[1]
            for (thr, brg, dlabel) in ends:
                if dlabel != label:
                    continue
                bl_dist = self.length_m if bl['strip_end'] else bl['dist']
                end_len = min(IHS_HEIGHT / bl['slope'], 13500.0)
                xs = [bl_dist + end_len * i / n for i in range(n + 1)]
                ws = [bl['hw'] + bl['divergence'] * (x - bl_dist) for x in xs]
                hs = [bl['slope'] * (x - bl_dist) for x in xs]
                return self._slices(thr, brg, xs, ws, hs)
        return None

    def _footprint_height(self, name):
        """Representative vertical rise (m) of a footprint, used for 3D
        extrusion of the surface volume."""
        if name.startswith('approach_') and self.spec:
            return round(approach_elevation(self.spec, 0.0, self.spec['total']), 1)
        if name.startswith('take_off_climb_'):
            toc = TAKE_OFF_CLIMB.get(self.code)
            if toc:
                return round(toc['slope'] * toc['length'], 1)
        if name.startswith('inner_approach_'):
            ia = INNER_APPROACH.get(self.code)
            if ia:
                return round(ia['slope'] * ia['length'], 1)
        if name.startswith('balked_landing_'):
            bl = BALKED_LANDING.get(self.code)
            if bl:
                return round(min(IHS_HEIGHT / bl['slope'], 13500.0) * bl['slope'], 1)
        return 0.0


# ---------------------------------------------------------------------------
# Aerodrome-level evaluation (runways + ARP-centred surfaces)
# ---------------------------------------------------------------------------

class AirportOLS:
    """Aggregates all runways plus the ARP-centred surfaces of an aerodrome."""

    def __init__(self, arp_lat, arp_lon, arp_elev_m, runways=None, default_config=None):
        self.arp = (arp_lat, arp_lon)
        self.arp_elev = float(arp_elev_m or 0.0)
        self.runways = [r for r in (runways or []) if r is not None]
        self.default_config = default_config or {'code': 4, 'category': 'non_precision'}

    def _arp_configs(self):
        """(category, code) configs: per-runway when present, else default."""
        if self.runways:
            return [(rw.category, rw.code) for rw in self.runways]
        return [(self.default_config['category'], self.default_config['code'])]

    def _arp_surfaces(self, lat, lon):
        """IHS, conical and outer horizontal ceilings at a point."""
        out = []
        d = geodesic(self.arp, (lat, lon)).meters
        for category, code in self._arp_configs():
            radius = IHS_RADIUS.get(category, IHS_RADIUS['non_precision']).get(code, 4000.0)
            height = CONICAL_HEIGHT.get(category, CONICAL_HEIGHT['non_precision']).get(code, 100.0)
            if d <= radius:
                out.append((self.arp_elev + IHS_HEIGHT, 'inner_horizontal'))
            elif d <= radius + height / CONICAL_SLOPE:
                out.append((self.arp_elev + IHS_HEIGHT + (d - radius) * CONICAL_SLOPE, 'conical'))
            if code in OUTER_HORIZONTAL_CODES and d <= OUTER_HORIZONTAL_RADIUS:
                out.append((self.arp_elev + OUTER_HORIZONTAL_HEIGHT, 'outer_horizontal'))
        return out

    def ceiling_at(self, lat, lon):
        """Controlling OLS ceiling at a point.

        Returns dict(ceiling_amsl, surfaces, distance_m) or None when no
        surface covers the point.
        """
        ceilings = []
        for rw in self.runways:
            ceilings.extend(rw.ceilings_at(lat, lon))
        ceilings.extend(self._arp_surfaces(lat, lon))
        if not ceilings:
            return None
        ceilings.sort(key=lambda x: x[0])
        min_ceiling = ceilings[0][0]
        surfaces = sorted({name for c, name in ceilings if abs(c - min_ceiling) < 0.5})
        return {
            'ceiling_amsl': min_ceiling,
            'surfaces': surfaces,
            'distance_m': geodesic(self.arp, (lat, lon)).meters,
            'runway_count': len(self.runways),
        }

    def footprints(self):
        """GeoJSON FeatureCollection of every surface footprint.

        Runway surfaces are split into axis slices so each feature carries
        'height_m' - the Annex 14 ceiling rise at that slice - plus a
        per-vertex 'heights' array; 3D extrusions therefore show the true
        tapered surface shape. ARP-centred circles keep a flat height (IHS /
        outer horizontal) or are sliced radially (conical).
        """
        features = []
        for rw in self.runways:
            names = ['approach_%s' % rw.rw.get('designator1', 'end1'),
                     'approach_%s' % rw.rw.get('designator2', 'end2'),
                     'take_off_climb_%s' % rw.rw.get('designator1', 'end1'),
                     'take_off_climb_%s' % rw.rw.get('designator2', 'end2'),
                     'inner_approach_%s' % rw.rw.get('designator1', 'end1'),
                     'inner_approach_%s' % rw.rw.get('designator2', 'end2'),
                     'balked_landing_%s' % rw.rw.get('designator1', 'end1'),
                     'balked_landing_%s' % rw.rw.get('designator2', 'end2'),
                     'strip']
            for name in names:
                if name == 'strip':
                    ring = rw.footprint('strip')
                    if ring:
                        features.append(self._feature(rw, name, ring, 0.0, [0.0] * len(ring)))
                    continue
                n_slices = 8 if name.startswith('approach_') else \
                           8 if name.startswith('take_off_climb_') else \
                           2 if name.startswith('inner_approach_') else 3
                for ring, height_m, heights in (rw.surface_slices(name, n_slices) or []):
                    features.append(self._feature(rw, name, ring, height_m, heights))
        # ARP-centred circles (densified; conical sliced radially)
        for rw in self.runways:
            radius = IHS_RADIUS.get(rw.category, IHS_RADIUS['non_precision']).get(rw.code, 4000.0)
            height = CONICAL_HEIGHT.get(rw.category, CONICAL_HEIGHT['non_precision']).get(rw.code, 100.0)
            ihs = self._circle_ring(radius)
            features.append(self._feature(rw, 'inner_horizontal', ihs, round(IHS_HEIGHT, 1),
                                          [round(IHS_HEIGHT, 1)] * len(ihs)))
            cone_len = height / CONICAL_SLOPE
            nw, nr = 8, 3
            for k in range(nw):
                a0 = 2 * math.pi * k / nw
                a1 = 2 * math.pi * (k + 1) / nw
                for j in range(nr):
                    r0 = radius + cone_len * j / nr
                    r1 = radius + cone_len * (j + 1) / nr
                    h0 = round(IHS_HEIGHT + (r0 - radius) * CONICAL_SLOPE, 1)
                    h1 = round(IHS_HEIGHT + (r1 - radius) * CONICAL_SLOPE, 1)
                    p00 = destination_point_rad(self.arp[0], self.arp[1], a0, r0)
                    p01 = destination_point_rad(self.arp[0], self.arp[1], a1, r0)
                    p10 = destination_point_rad(self.arp[0], self.arp[1], a0, r1)
                    p11 = destination_point_rad(self.arp[0], self.arp[1], a1, r1)
                    ring = self._ring([p00, p01, p11, p10])
                    features.append(self._feature(rw, 'conical', ring, max(h0, h1),
                                                  [h0, h0, h1, h1, h0]))
            if rw.code in OUTER_HORIZONTAL_CODES:
                outer = self._circle_ring(OUTER_HORIZONTAL_RADIUS)
                features.append(self._feature(rw, 'outer_horizontal', outer,
                                              round(OUTER_HORIZONTAL_HEIGHT, 1),
                                              [round(OUTER_HORIZONTAL_HEIGHT, 1)] * len(outer)))
        return {'type': 'FeatureCollection', 'features': features}

    def _feature(self, rw, name, ring, height_m, heights):
        return {
            'type': 'Feature',
            'properties': {
                'surface': name.split('_')[0],
                'label': name,
                'icao': rw.rw.get('icao_code'),
                'category': rw.category,
                'code': rw.code,
                'height_m': height_m,
                'heights': heights,
            },
            'geometry': {'type': 'Polygon', 'coordinates': [ring]},
        }

    def _circle_ring(self, radius_m, steps=72):
        pts = []
        for i in range(steps):
            brg = 2 * math.pi * i / steps
            pts.append(destination_point_rad(self.arp[0], self.arp[1], brg, radius_m))
        return self._ring(pts)

    @staticmethod
    def _ring(points):
        pts = [[lon, lat] for (lat, lon) in points]
        if pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        return pts
