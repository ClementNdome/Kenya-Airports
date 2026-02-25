# obstacle_compliance/models.py
from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.contrib.postgres.indexes import GistIndex  # Add this import

class Aerodrome(models.Model):
    """Your exact model from the data - with targeted enhancements"""
    fid = models.IntegerField(primary_key=True)
    icao_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=50)
    latitude = models.CharField(max_length=20)
    longitude = models.CharField(max_length=20)
    elevation_m_ft = models.CharField(max_length=30)  # This field contains mixed formats
    elevation_m = models.FloatField(null=True, blank=True)  # NEW: Parsed elevation in meters
    geoid_undulation_m = models.CharField(max_length=20)
    remarks_spatial = models.TextField(blank=True, null=True)
    admin_company = models.CharField(max_length=200, blank=True, null=True)
    admin_address = models.TextField(blank=True, null=True)
    admin_telephone = models.CharField(max_length=100, blank=True, null=True)
    admin_afs = models.CharField(max_length=100, blank=True, null=True)
    admin_email = models.CharField(max_length=100, blank=True, null=True)
    traffic_permitted = models.CharField(max_length=50, blank=True, null=True)
    magnetic_variation = models.CharField(max_length=30, blank=True, null=True)
    annual_change = models.CharField(max_length=30, blank=True, null=True)
    remarks_nonspatial = models.TextField(blank=True, null=True)
    admin_website = models.URLField(max_length=200, blank=True, null=True)
    geom = models.PointField(srid=4326)

    class Meta:
        verbose_name = "Aerodrome"
        verbose_name_plural = "Aerodromes"
        indexes = [
            models.Index(fields=["icao_code"]),
            models.Index(fields=["type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["icao_code"], name="unique_icao_code"
            ),
        ]

    def __str__(self):
        return f"{self.icao_code} - {self.name or 'Unnamed Aerodrome'}"

    def save(self, *args, **kwargs):
        # Auto-populate elevation_m when saving
        if self.elevation_m_ft and self.elevation_m is None:
            self.elevation_m = self._parse_elevation()
        super().save(*args, **kwargs)

    def _parse_elevation(self):
        """
        Extract elevation in meters from the elevation_m_ft field.
        Handles multiple formats:
        - "6945 FT (2117 M)" → 2117
        - "1690 / 5546" → 1690 (assuming first is meters)
        - "13 / 42.65" → 13
        - "231 / 756.9" → 231
        - "18 FT (5 M)" → 5
        - "2115 FT (645 M)" → 645
        """
        if not self.elevation_m_ft:
            return None
        
        elev_str = str(self.elevation_m_ft).strip()
        
        # Pattern 1: "6945 FT (2117 M)" or "18 FT (5 M)"
        import re
        
        # Try to extract meters from parentheses with "M" suffix
        m_pattern = r'\((\d+(?:\.\d+)?)\s*M\)'
        match = re.search(m_pattern, elev_str, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Pattern 2: "1690 / 5546" (assuming first number is meters)
        if '/' in elev_str and 'FT' not in elev_str.upper():
            parts = elev_str.split('/')
            if parts:
                try:
                    # Clean the first part and convert to float
                    first_part = parts[0].strip()
                    return float(first_part)
                except ValueError:
                    pass
        
        # Pattern 3: If it's just a number (assume meters)
        try:
            return float(elev_str)
        except ValueError:
            pass
        
        # Pattern 4: Try to extract any number followed by M
        m_alt_pattern = r'(\d+(?:\.\d+)?)\s*M(?!\()'
        match = re.search(m_alt_pattern, elev_str, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # Pattern 5: Extract feet and convert if necessary
        ft_pattern = r'(\d+(?:\.\d+)?)\s*FT'
        match = re.search(ft_pattern, elev_str, re.IGNORECASE)
        if match:
            try:
                feet = float(match.group(1))
                # Convert feet to meters (1 ft = 0.3048 m)
                return round(feet * 0.3048, 1)
            except ValueError:
                pass
        
        # If all else fails, log warning and return None
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not parse elevation from: '{self.elevation_m_ft}' for airport {self.icao_code}")
        return None

# new model for buffers - can be linked to Aerodrome via FK
class AerodromeBuffer(models.Model):
    aerodrome = models.ForeignKey(
        Aerodrome, on_delete=models.CASCADE, related_name="buffers"
    )
    radius_km = models.IntegerField()  # e.g., 3,5,10,15 (or custom later)
    fid = models.IntegerField(blank=True, null=True)  # From GeoJSON
    type = models.CharField(
        max_length=50, blank=True
    )  # Increased max_length for safety
    latitude = models.CharField(max_length=20, blank=True)
    longitude = models.CharField(max_length=20, blank=True)
    # Add new decimal fields for calculations
    latitude_decimal = models.FloatField(blank=True, null=True)
    longitude_decimal = models.FloatField(blank=True, null=True)
    elevation_m_ft = models.CharField(max_length=100, blank=True)
    geoid_undulation_m = models.CharField(max_length=20, blank=True)
    remarks_spatial = models.TextField(
        blank=True
    )  # Use TextField for potentially longer content
    admin_company = models.CharField(max_length=200, blank=True)
    admin_address = models.TextField(blank=True)
    admin_telephone = models.CharField(max_length=100, blank=True)
    admin_afs = models.CharField(max_length=20, blank=True)
    admin_email = models.EmailField(blank=True)
    traffic_permitted = models.CharField(max_length=200, blank=True)
    magnetic_variation = models.CharField(max_length=30, blank=True)
    annual_change = models.CharField(max_length=30, blank=True)
    remarks_nonspatial = models.TextField(blank=True)
    admin_website = models.URLField(blank=True, null=True)
    area_km2 = models.FloatField(blank=True, null=True)
    layer = models.CharField(max_length=100, blank=True)
    geom = models.MultiPolygonField(srid=4326)  # WGS84

    class Meta:
        unique_together = (
            "aerodrome",
            "radius_km",
        )  # No duplicates per aerodrome-radius
        indexes = [
            models.Index(fields=["aerodrome", "radius_km"]),  # For fast queries
            GistIndex(fields=["geom"]),  # Spatial index for intersections/lookups
        ]
        verbose_name = "Aerodrome Buffer"
        verbose_name_plural = "Aerodrome Buffers"

    def __str__(self):
        return f"{self.aerodrome.icao_code} - {self.radius_km}km Buffer"
