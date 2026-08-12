# obstacle_compliance/models.py
from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.contrib.postgres.indexes import GistIndex  # Add this import

import logging
from django.contrib.gis.geos import MultiPolygon

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

    # Data Unification fields (from airports_strips.Airports)
    iata_code = models.CharField(max_length=10, null=True, blank=True)
    runway_length_m = models.FloatField(null=True, blank=True, help_text="Runway length in meters")
    nearest_city = models.CharField(max_length=254, null=True, blank=True)
    airlines = models.TextField(null=True, blank=True, help_text="Operating airlines")
    source = models.CharField(
        max_length=50,
        choices=[('geojson', 'KCAA GeoJSON'), ('geopackage', 'OurAirports GPKG'), ('merged', 'Merged')],
        default='geojson',
    )
    last_synced = models.DateTimeField(null=True, blank=True)

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
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not parse elevation from: '{self.elevation_m_ft}' for airport {self.icao_code}")
        return None
    
    # ==================== NEW METHOD ====================
        # ==================== FIXED METHOD ====================
    def get_or_create_buffer(self, radius_km):
        """Create a buffer for this aerodrome if it doesn't exist yet.
        Uses proper projection for accuracy. Now handles NOT NULL geom correctly."""
        radius_km = int(radius_km)
        if not self.geom:
            logging.getLogger(__name__).warning(f"Aerodrome {self.icao_code} has no geometry")
            return None

        # === Step 1: Compute the accurate buffer geometry FIRST ===
        try:
            geom_3857 = self.geom.transform(3857, clone=True)
            buffered_3857 = geom_3857.buffer(radius_km * 1000)
            area_km2 = round(buffered_3857.area / 1_000_000, 2)
            geom_4326 = buffered_3857.transform(4326, clone=True)
            if geom_4326.geom_type == 'Polygon':
                geom_4326 = MultiPolygon(geom_4326)
        except Exception as e:
            logging.getLogger(__name__).error(f"Buffer geometry calculation failed for {self.icao_code}: {e}")
            return None

        # === Step 2: Now get_or_create with FULL defaults (including geom) ===
        defaults = {
            'fid': None,
            'type': self.type or "Aerodrome Buffer",
            'latitude': self.latitude,
            'longitude': self.longitude,
            'latitude_decimal': self.geom.y,
            'longitude_decimal': self.geom.x,
            'elevation_m_ft': self.elevation_m_ft,
            'geoid_undulation_m': self.geoid_undulation_m,
            'remarks_spatial': self.remarks_spatial,
            'admin_company': self.admin_company,
            'admin_address': self.admin_address,
            'admin_telephone': self.admin_telephone,
            'admin_afs': self.admin_afs,
            'admin_email': self.admin_email,
            'traffic_permitted': self.traffic_permitted,
            'magnetic_variation': self.magnetic_variation,
            'annual_change': self.annual_change,
            'remarks_nonspatial': self.remarks_nonspatial,
            'admin_website': self.admin_website,
            'layer': f"{radius_km}km_buffer",
            'geom': geom_4326,
            'area_km2': area_km2,
        }

        buf, created = AerodromeBuffer.objects.get_or_create(
            aerodrome=self,
            radius_km=radius_km,
            defaults=defaults
        )

        if created:
            logging.getLogger(__name__).info(f"✅ Created new {radius_km}km buffer for {self.icao_code} (area: {area_km2} km²)")
        else:
            logging.getLogger(__name__).debug(f"Buffer {radius_km}km already existed for {self.icao_code}")

        return buf
    
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


# ============================================
# RUNWAY DATA (unmanaged — loaded externally)
# ============================================

class AerodromeRunway(models.Model):
    """
    Runway geometry for aerodromes. Unmanaged: the table exists in PostgreSQL
    (public."aerodrome-runways") and was loaded externally. geom is the
    centerline LineString (WGS84); thresholds/bearings are derived from it
    at query time so stale coordinate fields never drift.
    """
    id = models.IntegerField(primary_key=True)
    geom = models.LineStringField(srid=4326, null=True, blank=True)
    gid = models.IntegerField(null=True, blank=True)
    icao_code = models.CharField(max_length=30, null=True, blank=True)
    country_name = models.CharField(max_length=100, null=True, blank=True)
    runway_pair = models.CharField(max_length=20, null=True, blank=True)
    rwy_designator_1 = models.CharField(max_length=10, null=True, blank=True)
    rwy_designator_2 = models.CharField(max_length=10, null=True, blank=True)
    thr_latitude_1_dms = models.CharField(max_length=50, null=True, blank=True)
    thr_longitude_1_dms = models.CharField(max_length=50, null=True, blank=True)
    thr_latitude_2_dms = models.CharField(max_length=50, null=True, blank=True)
    thr_longitude_2_dms = models.CharField(max_length=50, null=True, blank=True)
    thr_latitude_1 = models.FloatField(null=True, blank=True)
    thr_longitude_1 = models.FloatField(null=True, blank=True)
    thr_latitude_2 = models.FloatField(null=True, blank=True)
    thr_longitude_2 = models.FloatField(null=True, blank=True)
    thr_elevation_1_m = models.FloatField(null=True, blank=True)
    thr_elevation_2_m = models.FloatField(null=True, blank=True)
    thr_elevation_1_ft = models.FloatField(null=True, blank=True)
    thr_elevation_2_ft = models.FloatField(null=True, blank=True)
    true_bearing_1 = models.CharField(max_length=30, null=True, blank=True)
    true_bearing_2 = models.CharField(max_length=30, null=True, blank=True)
    mag_bearing_1 = models.CharField(max_length=30, null=True, blank=True)
    mag_bearing_2 = models.CharField(max_length=30, null=True, blank=True)
    dimensions_m = models.CharField(max_length=100, null=True, blank=True)
    length_declared_m = models.FloatField(null=True, blank=True)
    width_declared_m = models.CharField(max_length=50, null=True, blank=True)
    strength_pcn_surface = models.CharField(max_length=200, null=True, blank=True)
    slope_pct = models.CharField(max_length=30, null=True, blank=True)
    swy_dimensions_m = models.CharField(max_length=100, null=True, blank=True)
    cwy_dimensions_m = models.CharField(max_length=100, null=True, blank=True)
    cwy_dimensions_m_2 = models.CharField(max_length=100, null=True, blank=True)
    strip_dimensions = models.CharField(max_length=150, null=True, blank=True)
    strip_dimensions_m = models.CharField(max_length=150, null=True, blank=True)
    ofz = models.CharField(max_length=200, null=True, blank=True)
    resa_dimensions_m = models.CharField(max_length=100, null=True, blank=True)
    arresting_system = models.CharField(max_length=100, null=True, blank=True)
    geoid_undulation_m = models.CharField(max_length=50, null=True, blank=True)
    length_calculated_m = models.FloatField(null=True, blank=True)
    length_difference_m = models.FloatField(null=True, blank=True)
    length_difference_pct = models.CharField(max_length=30, null=True, blank=True)
    remarks = models.CharField(max_length=300, null=True, blank=True)

    APPROACH_CATEGORY_CHOICES = [
        ('non_instrument', 'Non-instrument (visual)'),
        ('non_precision', 'Non-precision'),
        ('precision_i', 'Precision CAT I'),
        ('precision_ii_iii', 'Precision CAT II/III'),
    ]
    approach_category = models.CharField(
        max_length=20,
        choices=APPROACH_CATEGORY_CHOICES,
        null=True,
        blank=True,
        help_text="Runway use category - determines the OLS approach/OFZ surfaces (Annex 14 Table 4-1).",
    )

    class Meta:
        managed = False
        db_table = 'aerodrome-runways'
        verbose_name = "Aerodrome Runway"
        verbose_name_plural = "Aerodrome Runways"

    def __str__(self):
        return f"{self.icao_code} {self.runway_pair or ''}".strip()

    @property
    def aerodrome(self):
        """Lookup helper — the runway table is linked to Aerodrome by icao_code."""
        if not self.icao_code:
            return None
        return Aerodrome.objects.filter(icao_code=self.icao_code).first()

    @property
    def declared(self):
        """Declared distances for this runway end pair (whitespace-padded join)."""
        if not self.icao_code or not self.runway_pair:
            return None
        from django.db.models.functions import Trim
        return DeclaredDistance.objects.filter(
            icao_code=self.icao_code,
        ).annotate(pair=Trim('runway_pair')).filter(pair=self.runway_pair.strip()).first()


class DeclaredDistance(models.Model):
    """
    Declared distances (TORA/TODA/ASDA/LDA) per runway end. Unmanaged table
    public."runways-declared_distances". runway_pair is whitespace-padded —
    always compare via .strip()/__iexact against AerodromeRunway.runway_pair.
    """
    id = models.CharField(primary_key=True, max_length=50)
    country = models.CharField(max_length=100, null=True, blank=True)
    icao_code = models.CharField(max_length=30, null=True, blank=True)
    runway_pair = models.CharField(max_length=30, null=True, blank=True)
    rwy_designator_1 = models.CharField(max_length=10, null=True, blank=True)
    rwy_designator_2 = models.CharField(max_length=10, null=True, blank=True)
    tora_m_1 = models.CharField(max_length=20, null=True, blank=True)
    toda_m_1 = models.CharField(max_length=20, null=True, blank=True)
    asda_m_1 = models.CharField(max_length=20, null=True, blank=True)
    lda_m_1 = models.CharField(max_length=20, null=True, blank=True)
    remarks_1 = models.CharField(max_length=300, null=True, blank=True)
    tora_m_2 = models.CharField(max_length=20, null=True, blank=True)
    toda_m_2 = models.CharField(max_length=20, null=True, blank=True)
    asda_m_2 = models.CharField(max_length=20, null=True, blank=True)
    lda_m_2 = models.CharField(max_length=20, null=True, blank=True)
    remarks_2 = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'runways-declared_distances'
        verbose_name = "Declared Distance"
        verbose_name_plural = "Declared Distances"

    def __str__(self):
        return f"{self.icao_code} {self.runway_pair or ''}".strip()

    def parse(self, field_name):
        """Parse a declared distance field to meters (float) or None."""
        raw = getattr(self, field_name, None)
        if not raw:
            return None
        try:
            return float(str(raw).strip())
        except (TypeError, ValueError):
            return None


# ============================================
# USER & PORTFOLIO MODELS (Feature 1)
# ============================================

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

STATUS_CHOICES = [
    ('GREEN', 'Compliant'),
    ('YELLOW', 'Caution - Within Regulatory Zone'),
    ('RED', 'Hazard Detected'),
    ('UNKNOWN', 'Not Checked'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    organization_type = models.CharField(
        max_length=50,
        choices=[
            ('developer', 'Property Developer'),
            ('architect', 'Architect / Engineer'),
            ('agent', 'Real Estate Agent'),
            ('public', 'General Public'),
            ('kcaa', 'KCAA Regulator'),
            ('other', 'Other'),
        ],
        default='public',
    )
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Property(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=255, help_text="e.g., 'Sunset Towers'")
    address = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    height_m = models.FloatField(help_text="Height in meters AGL")
    geom = models.PointField(srid=4326, null=True, blank=True)
    parcel_boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)

    last_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNKNOWN')
    last_score = models.FloatField(null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Properties'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'last_status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def save(self, *args, **kwargs):
        from django.contrib.gis.geos import Point
        if self.latitude and self.longitude:
            self.geom = Point(self.longitude, self.latitude, srid=4326)
        super().save(*args, **kwargs)

    def run_compliance_check(self):
        from .utils import ComplianceCalculator
        from django.contrib.gis.geos import Point

        calculator = ComplianceCalculator()
        point = Point(self.longitude, self.latitude, srid=4326)
        result = calculator.evaluate_property_all_airports(point, self.height_m)

        check = ComplianceCheck.objects.create(
            property=self,
            result_json=result,
            status=result.get('status', 'UNKNOWN'),
            score=result.get('compliance_score', 0),
            primary_airport_icao=result.get('primary_airport', {}).get('icao', ''),
            airports_affected=result.get('airports_affected_count', 0),
            requires_lighting=result.get('requires_lighting', False),
            is_hazard=result.get('is_hazard', False),
            trigger='manual',
        )

        self.last_status = check.status
        self.last_score = check.score
        self.last_checked = check.checked_at
        self.save(update_fields=['last_status', 'last_score', 'last_checked'])

        return check


class ComplianceCheck(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='checks')
    result_json = models.JSONField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    score = models.FloatField()
    primary_airport_icao = models.CharField(max_length=10, null=True, blank=True)
    airports_affected = models.IntegerField(default=0)
    requires_lighting = models.BooleanField(default=False)
    is_hazard = models.BooleanField(default=False)
    checked_at = models.DateTimeField(auto_now_add=True)
    trigger = models.CharField(
        max_length=20,
        choices=[
            ('manual', 'Manual Check'),
            ('auto', 'Automatic Re-assessment'),
            ('bulk', 'Bulk Upload'),
        ],
        default='manual',
    )

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        return f"{self.property.name} @ {self.checked_at.strftime('%Y-%m-%d %H:%M')} — {self.status}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('status_change', 'Compliance Status Changed'),
        ('regulation_update', 'Regulation Updated'),
        ('application_update', 'Application Status Changed'),
        ('reassessment', 'Automatic Re-assessment Complete'),
        ('bulk_complete', 'Bulk Upload Complete'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, help_text="Relative URL to related page")
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"


class ComplianceApplication(models.Model):
    APP_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revoked', 'Revoked'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=APP_STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer_notes = models.TextField(blank=True)
    certificate_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    certificate_pdf = models.FileField(upload_to='certificates/', null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    fee_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['certificate_number']),
        ]

    def __str__(self):
        return f"App #{self.pk} — {self.property.name} ({self.get_status_display()})"


class BulkUploadJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bulk_uploads')
    csv_file = models.FileField(upload_to='bulk_uploads/')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    results_file = models.FileField(upload_to='bulk_results/', null=True, blank=True)
    error_log = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Bulk #{self.pk} — {self.status} ({self.success_count}/{self.total_rows})"
