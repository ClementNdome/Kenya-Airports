from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin


from .models import Aerodrome, AerodromeBuffer, UserProfile, Property, ComplianceCheck, Notification, ComplianceApplication, BulkUploadJob, AerodromeRunway, DeclaredDistance, UserLayer


class Aerodromes(LeafletGeoAdmin):
    list_display = (
        "name",
        "icao_code",
        "fid",
        "type",
        "admin_company",
    )
    

class AerodromeBuffers(LeafletGeoAdmin):
    list_display = (
        "aerodrome",
        "radius_km",
        "fid",
    )
    

admin.site.register(Aerodrome, Aerodromes)
admin.site.register(AerodromeBuffer, AerodromeBuffers)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization_type', 'company', 'email_verified')
    list_filter = ('organization_type', 'email_verified')
    search_fields = ('user__username', 'company')


@admin.register(Property)
class PropertyAdmin(LeafletGeoAdmin):
    list_display = ('name', 'user', 'last_status', 'last_score', 'last_checked', 'height_m')
    list_filter = ('last_status', 'is_active')
    search_fields = ('name', 'user__username', 'address')


@admin.register(ComplianceCheck)
class ComplianceCheckAdmin(admin.ModelAdmin):
    list_display = ('property', 'status', 'score', 'checked_at', 'trigger')
    list_filter = ('status', 'trigger', 'checked_at')
    readonly_fields = ('result_json',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title')


@admin.register(ComplianceApplication)
class ComplianceApplicationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'property', 'user', 'status', 'last_status', 'last_score', 'submitted_at', 'certificate_number')
    list_filter = ('status', 'last_status', 'created_at')
    search_fields = ('user__username', 'property__name', 'certificate_number')

    def save_model(self, request, obj, form, change):
        was = (obj.last_status, obj.last_score) if change else None
        super().save_model(request, obj, form, change)
        if change:
            try:
                from .utils import recheck_application_ols
                changed, check = recheck_application_ols(obj, actor=request.user)
                if changed:
                    self.message_user(request,
                        f'Re-checked OLS for app #{obj.pk}: verdict now {obj.last_status} '
                        f'(score {obj.last_score}). Owner notified.', level='SUCCESS')
            except Exception:
                import logging
                logging.getLogger(__name__).exception(f"Admin re-check failed for application {obj.pk}")


@admin.register(UserLayer)
class UserLayerAdmin(LeafletGeoAdmin):
    list_display = ('name', 'user', 'layer_type', 'created_at')
    list_filter = ('layer_type',)
    search_fields = ('name', 'user__username')


@admin.register(BulkUploadJob)
class BulkUploadJobAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'status', 'total_rows', 'success_count', 'error_count', 'created_at')
    list_filter = ('status', 'created_at')


@admin.register(AerodromeRunway)
class AerodromeRunwayAdmin(LeafletGeoAdmin):
    list_display = ('icao_code', 'runway_pair', 'rwy_designator_1', 'rwy_designator_2', 'length_declared_m', 'width_declared_m', 'strip_dimensions')
    list_filter = ('icao_code',)
    search_fields = ('icao_code', 'runway_pair')


@admin.register(DeclaredDistance)
class DeclaredDistanceAdmin(admin.ModelAdmin):
    list_display = ('icao_code', 'runway_pair', 'tora_m_1', 'toda_m_1', 'asda_m_1', 'lda_m_1')
    list_filter = ('icao_code',)
    search_fields = ('icao_code', 'runway_pair')
    readonly_fields = [f.name for f in DeclaredDistance._meta.fields]