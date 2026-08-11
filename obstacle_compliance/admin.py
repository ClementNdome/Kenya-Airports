from django.contrib import admin

from leaflet.admin import LeafletGeoAdmin


from .models import Aerodrome, AerodromeBuffer, UserProfile, Property, ComplianceCheck, Notification, ComplianceApplication, BulkUploadJob


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
    list_display = ('pk', 'property', 'user', 'status', 'submitted_at', 'certificate_number')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'property__name', 'certificate_number')


@admin.register(BulkUploadJob)
class BulkUploadJobAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'status', 'total_rows', 'success_count', 'error_count', 'created_at')
    list_filter = ('status', 'created_at')