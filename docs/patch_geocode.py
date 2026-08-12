# -*- coding: utf-8 -*-
"""Patch views.py: GeocodeView overhaul (autocomplete + Kenya coverage +
airport blending + 200-on-empty) and parcel-aware cache key."""
P = r"E:\DEVELOPMENT_\DJANGOS\new-refined\Kenya-Airports\obstacle_compliance\views.py"
src = open(P, encoding="utf-8").read()

def rep(old, new, label, count=1):
    global src
    cnt = src.count(old)
    assert cnt == count, f"{label}: anchor found {cnt} times (expected {count})"
    src = src.replace(old, new)
    print(f"[ok] {label}")

# ---- 1. GeocodeView constants ----
rep("""    MAPBOX_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json'
    MAPBOX_TYPES = 'address,place,locality,neighborhood,district,poi'
    NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
    USER_AGENT = 'KCAAObstacleCompliance/1.0'
    CACHE_DURATION = 86400""",
    """    MAPBOX_URL = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json'
    MAPBOX_TYPES = 'address,place,locality,neighborhood,district,region,poi'
    NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
    USER_AGENT = 'KCAAObstacleCompliance/1.0'
    CACHE_DURATION = 86400
    EMPTY_CACHE_DURATION = 3600
    KENYA_BBOX = '33.9,-4.7,41.9,5.5'  # lon_min,lat_min,lon_max,lat_max""",
    "geocode constants")

# ---- 2. GeocodeView.get: no more 404, source field, airport blending, empty caching ----
rep("""        cache_key = f'geocode_{hashlib.md5(address.lower().encode()).hexdigest()}'
        cached = cache.get(cache_key)
        if cached:
            return JsonResponse(cached)

        suggestions = self._geocode_mapbox(address)
        if suggestions is None:
            suggestions = self._geocode_nominatim(address)

        if suggestions is None:
            return JsonResponse({'error': 'Geocoding service unavailable'}, status=503)
        if not suggestions:
            return JsonResponse({'error': 'Address not found'}, status=404)

        response_data = {'results': suggestions}
        cache.set(cache_key, response_data, self.CACHE_DURATION)
        return JsonResponse(response_data)""",
    """        cache_key = f'geocode_{hashlib.md5(address.lower().encode()).hexdigest()}'
        cached = cache.get(cache_key)
        if cached is not None:
            return JsonResponse(cached)

        # Mapbox first, Nominatim fallback
        suggestions = self._geocode_mapbox(address)
        source = 'mapbox'
        if suggestions is None:
            suggestions = self._geocode_nominatim(address)
            source = 'nominatim'

        if suggestions is None:
            return JsonResponse({'error': 'Geocoding service unavailable'}, status=503)

        # Kenyan aerodromes that match (ICAO / name / operator) rank first
        airports = self._geocode_airports(address)
        if airports:
            suggestions = airports + suggestions
            source = source + ',airports'

        response_data = {'results': suggestions, 'source': source}
        if suggestions:
            cache.set(cache_key, response_data, self.CACHE_DURATION)
        else:
            cache.set(cache_key, response_data, self.EMPTY_CACHE_DURATION)
        return JsonResponse(response_data)""",
    "geocode get flow")

# ---- 3. Mapbox params: autocomplete, limit 10, Kenya bbox ----
rep("""                params={
                    'access_token': token,
                    'country': 'ke',
                    'limit': 5,
                    'types': self.MAPBOX_TYPES,
                    'language': 'en',
                },""",
    """                params={
                    'access_token': token,
                    'country': 'ke',
                    'bbox': self.KENYA_BBOX,
                    'autocomplete': 'true',
                    'limit': 10,
                    'types': self.MAPBOX_TYPES,
                    'language': 'en',
                },""",
    "mapbox params")

# ---- 4. Nominatim params: limit 10 + Kenya viewbox bounded ----
rep("""        params = {
            'q': address,
            'format': 'json',
            'limit': 5,
            'addressdetails': 1,
            'countrycodes': 'ke',
        }""",
    """        params = {
            'q': address,
            'format': 'json',
            'limit': 10,
            'addressdetails': 1,
            'countrycodes': 'ke',
            'viewbox': self.KENYA_BBOX,
            'bounded': 1,
        }""",
    "nominatim params")

# ---- 5. Airport blending method (inserted before ReverseGeocodeView) ----
rep("""class ReverseGeocodeView(View):""",
    """    def _geocode_airports(self, address):
        \"\"\"Kenyan aerodromes matching the query (ICAO / name / operator).

        Uses the local aerodrome table so partial codes like 'jki' or 'wil'
        immediately surface Jomo Kenyatta Intl and Wilson without depending
        on external POI coverage. Returns a normalized list (may be empty).\"\"\"
        q = address.strip().lower()
        if len(q) < 2:
            return []
        try:
            matches = Aerodrome.objects.filter(
                Q(icao_code__icontains=q) |
                Q(name__icontains=q) |
                Q(admin_company__icontains=q)
            ).filter(geom__isnull=False)[:5]
        except Exception as e:
            logger.error(f"Airport geocode blend error: {e}")
            return []

        results = []
        seen = set()
        for ad in matches:
            code = ad.icao_code or ''
            if code in seen:
                continue
            seen.add(code)
            results.append({
                'lat': float(ad.geom.y),
                'lon': float(ad.geom.x),
                'display_name': f"{ad.name or ad.admin_company or code} ({code})",
                'text': ad.name or code,
                'type': 'airport',
                'icao': code,
            })
        return results


class ReverseGeocodeView(View):""",
    "airport blending")

# ---- 6. Parcel-aware cache key (move parcel parse before cache check) ----
rep("""            # Check cache
            cache_key = f"compliance_api_{lat}_{lon}_{height}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return JsonResponse(cached_result)
            
            # Optional parcel ring: "lat1,lon1|lat2,lon2|..." (closed polygon)
            parcel_ring = None
            parcel_str = request.GET.get('parcel')
            if parcel_str:
                try:
                    parcel_ring = [tuple(float(v) for v in pair.split(',')) for pair in parcel_str.split('|')]
                    if len(parcel_ring) < 3:
                        parcel_ring = None
                except (ValueError, TypeError):
                    parcel_ring = None""",
    """            # Optional parcel ring: "lat1,lon1|lat2,lon2|..." (closed polygon)
            parcel_str = request.GET.get('parcel')
            parcel_ring = None
            if parcel_str:
                try:
                    parcel_ring = [tuple(float(v) for v in pair.split(',')) for pair in parcel_str.split('|')]
                    if len(parcel_ring) < 3:
                        parcel_ring = None
                except (ValueError, TypeError):
                    parcel_ring = None

            # Check cache (parcel-aware so a point check never satisfies a
            # parcel check or vice versa)
            key_suffix = hashlib.md5((parcel_str or '').encode()).hexdigest()[:10] if parcel_str else 'point'
            cache_key = f"compliance_api_{lat}_{lon}_{height}_{key_suffix}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return JsonResponse(cached_result)""",
    "parcel cache key")

open(P, "w", encoding="utf-8").write(src)
print("VIEWS PATCH COMPLETE -", len(src.splitlines()), "lines")