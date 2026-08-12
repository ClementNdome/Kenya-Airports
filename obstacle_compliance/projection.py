# obstacle_compliance/projection.py
#
# Metric projection helpers for Kenya. Web Mercator (EPSG:3857) and planar
# EPSG:4326 degree math are both unsuitable for precise metric buffering and
# distance work, so every geometry-generation path in this project should go
# through UTM. Kenya spans two UTM zones and both hemispheres:
#
#   zone 36: 33°E - 39°E     zone 37: 39°E - 45°E
#   north:   EPSG 32636/32637   south: EPSG 32736/32737
import logging

from django.contrib.gis.geos import GEOSGeometry

import pyproj

logger = logging.getLogger(__name__)

ZONE_36_MAX_LON = 39.0  # zones are 6° wide; 33-39°E = 36, 39-45°E = 37


def utm_epsg(lon, lat):
    """EPSG code of the UTM zone covering (lon, lat).

    Zone by longitude (36 below 39°E, else 37); hemisphere by latitude
    (EPSG 326xx north of the equator, 327xx south).
    """
    zone = 36 if lon < ZONE_36_MAX_LON else 37
    return (32600 if lat >= 0 else 32700) + zone


def to_utm(geom, lon=None, lat=None):
    """Transform a GEOS geometry (SRID 4326) into its local UTM zone.

    lon/lat default to the geometry's own centroid when omitted.
    """
    if geom is None:
        return None
    if geom.srid == 4326:
        if lon is None or lat is None:
            lon, lat = geom.centroid.coords[0], geom.centroid.coords[1]
        geom.transform(utm_epsg(lon, lat))
    return geom


def from_utm(geom):
    """Transform a UTM geometry back to WGS84 (SRID 4326)."""
    if geom is None:
        return None
    if geom.srid not in (4326, None):
        geom.transform(4326)
    return geom


def buffer_m(geom, meters, lon=None, lat=None):
    """True-metric buffer of a 4326 geometry, computed in its UTM zone.

    Returns the buffered geometry transformed back to SRID 4326 (its
    original SRID), or None on failure.
    """
    if geom is None:
        return None
    src_srid = geom.srid or 4326
    try:
        buf = to_utm(geom.clone(), lon, lat)
        buf = buf.buffer(float(meters))
        return from_utm(buf) if src_srid == 4326 else buf
    except Exception as exc:
        logger.warning("buffer_m failed (%s): %s", meters, exc)
        return None


def area_m2(geom, lon=None, lat=None):
    """Planimetric area (m²) of a 4326 geometry, measured in its UTM zone."""
    if geom is None:
        return 0.0
    try:
        return to_utm(geom.clone(), lon, lat).area
    except Exception as exc:
        logger.warning("area_m2 failed: %s", exc)
        return 0.0


def distance_m(a, b):
    """Exact WGS84 geodesic distance (m) between two 4326 geometries/points.

    Uses pyproj.Geod on the WGS84 ellipsoid - the same kernel OLS math
    should use.
    """
    ax, ay = a.x, a.y
    bx, by = b.x, b.y
    fwd, back, dist = pyproj.Geod(ellps="WGS84").inv(ax, ay, bx, by)
    return abs(dist)


def lon_lat(geom):
    """(lon, lat) tuple for a geometry, tolerating None."""
    if geom is None:
        return None
    return geom.x, geom.y
