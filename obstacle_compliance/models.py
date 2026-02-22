# obstacle_compliance/models.py
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.contrib.postgres.fields import JSONField  # Django 3.1+
from airports_strips.models import Airports  # Import from existing app

class AerodromeBuffer(models.Model):
    """Pre-computed buffer zones for each airport at various radii"""
    airport = models.ForeignKey(Airports, on_delete=models.CASCADE, related_name='buffers')
    radius_km = models.IntegerField(help_text="Buffer radius in kilometers")
    geometry = gis_models.PolygonField(srid=4326, geography=True)
    area_sqkm = models.FloatField(null=True, blank=True)
    properties_count = models.IntegerField(default=0)
    estimated_population = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['airport', 'radius_km']
        indexes = [
            models.Index(fields=['airport', 'radius_km']),
            gis_models.GiSTIndex(fields=['geometry']),
        ]
    
    def __str__(self):
        return f"{self.airport.name} - {self.radius_km}km buffer"

class GazettedArea(models.Model):
    """Areas mentioned in KCAA gazette notices (like Nairobi West, Karen, etc.)"""
    name = models.CharField(max_length=100)
    airport = models.ForeignKey(Airports, on_delete=models.CASCADE, related_name='gazetted_areas')
    geometry = gis_models.MultiPolygonField(srid=4326, geography=True)
    description = models.TextField(blank=True)
    gazette_reference = models.CharField(max_length=100, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [gis_models.GiSTIndex(fields=['geometry'])]
    
    def __str__(self):
        return f"{self.name} (near {self.airport.name})"

class Property(models.Model):
    """Property records for compliance checking"""
    parcel_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    coordinates = gis_models.PointField(srid=4326, geography=True)
    address = models.TextField()
    area_sqm = models.FloatField(null=True, blank=True)
    county = models.CharField(max_length=50)
    sub_county = models.CharField(max_length=50)
    ward = models.CharField(max_length=50)
    town = models.CharField(max_length=100, blank=True)
    land_use = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [gis_models.GiSTIndex(fields=['coordinates'])]
    
    def __str__(self):
        return self.address[:50]

class Building(models.Model):
    """Buildings on properties"""
    COMPLIANCE_STATUS = [
        ('compliant', 'Compliant'),
        ('height_violation', 'Height Violation'),
        ('lights_violation', 'Lights Violation'),
        ('both_violation', 'Both Violations'),
        ('pending', 'Pending Verification'),
        ('exempt', 'Exempt'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='buildings')
    height_m = models.FloatField(help_text="Building height in meters")
    floor_count = models.IntegerField(null=True, blank=True)
    construction_year = models.IntegerField(null=True, blank=True)
    building_type = models.CharField(max_length=50, blank=True)
    footprint = gis_models.PolygonField(srid=4326, geography=True, null=True, blank=True)
    compliance_status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS, default='pending')
    lights_installed = models.BooleanField(default=False)
    lights_last_verified = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [gis_models.GiSTIndex(fields=['footprint'])]
    
    def __str__(self):
        return f"Building at {self.property.address[:30]} - {self.height_m}m"

class ComplianceCheck(models.Model):
    """Record of compliance checks performed"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='checks')
    airport = models.ForeignKey(Airports, on_delete=models.CASCADE)
    distance_m = models.FloatField()
    max_allowed_height_m = models.FloatField()
    status = models.CharField(max_length=20, choices=Building.COMPLIANCE_STATUS)
    checked_at = models.DateTimeField(auto_now_add=True)
    checked_by_ip = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-checked_at']
    
    def __str__(self):
        return f"Check #{self.id} - {self.status}"

class PermitApplication(models.Model):
    """Development permit applications"""
    STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('appealed', 'Appealed'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='permits')
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=20)
    proposed_height_m = models.FloatField()
    proposed_floors = models.IntegerField()
    drawings = models.FileField(upload_to='permits/drawings/%Y/%m/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    permit_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    permit_document = models.FileField(upload_to='permits/issued/%Y/%m/', null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Permit #{self.permit_number or 'Draft'} - {self.applicant_name}"

class EnforcementCase(models.Model):
    """Enforcement cases for violations"""
    SEVERITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS = [
        ('open', 'Open'),
        ('notice_sent', 'Notice Sent'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
        ('penalty_issued', 'Penalty Issued'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='enforcements')
    violation_type = models.CharField(max_length=20, choices=Building.COMPLIANCE_STATUS)
    severity = models.CharField(max_length=10, choices=SEVERITY, default='medium')
    detected_at = models.DateTimeField(auto_now_add=True)
    detected_by = models.CharField(max_length=50, blank=True)  # 'inspection', 'drone', 'public', 'satellite'
    notice_sent_at = models.DateField(null=True, blank=True)
    compliance_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    penalty_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-detected_at']
    
    def __str__(self):
        return f"Case #{self.id} - {self.building} - {self.violation_type}"