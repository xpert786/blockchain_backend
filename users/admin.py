from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Syndicate, Sector, Geography, TwoFactorAuth, EmailVerification

# Register CustomUser with Django admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Fields to display in the admin list view
    list_display = ('id', 'username', 'email', 'role', 'is_active', 'is_staff', 'two_factor_status', 'email_verified', 'phone_verified')
    # Add filters in the right sidebar
    list_filter = ('role', 'is_active', 'is_staff', 'two_factor_enabled', 'email_verified', 'phone_verified')
    # Fields to search by (required for autocomplete)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    # Default ordering
    ordering = ('id',)
    # Fieldsets to organize the edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'role')}),
        ('Verification Status', {'fields': ('email_verified', 'phone_verified')}),
        ('Two-Factor Authentication', {
            'fields': ('two_factor_enabled', 'two_factor_method'),
            'classes': ('collapse',)
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ()
    
    def two_factor_status(self, obj):
        if obj.two_factor_enabled:
            return format_html(
                '<span style="color: green;">✓ Enabled ({})</span>',
                obj.get_two_factor_method_display()
            )
        return format_html('<span style="color: red;">✗ Disabled</span>')
    two_factor_status.short_description = '2FA Status'

# Register Sector and Geography models
@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Geography)
class GeographyAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'country_code', 'created_at')
    list_filter = ('region',)
    search_fields = ('name', 'region', 'country_code')
    ordering = ('region', 'name')

# Register Syndicate as a normal model
@admin.register(Syndicate)
class SyndicateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'manager', 'accredited', 'get_sectors', 'get_geographies', 'firm_name', 'time_of_register')
    list_filter = ('accredited', 'enable_lp_network', 'sectors', 'geographies', 'time_of_register')
    search_fields = ('name', 'manager__username', 'firm_name')
    autocomplete_fields = ['manager']
    filter_horizontal = ('sectors', 'geographies')
    readonly_fields = ('time_of_register',)
    date_hierarchy = 'time_of_register'
    ordering = ('-time_of_register',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'manager', 'description', 'firm_name', 'logo', 'time_of_register')
        }),
        ('Investment Details', {
            'fields': ('accredited', 'sectors', 'geographies')
        }),
        ('LP Network', {
            'fields': ('enable_lp_network', 'lp_network', 'team_member')
        }),
        ('Compliance', {
            'fields': ('Risk_Regulatory_Attestation', 'jurisdictional_requirements', 'additional_compliance_policies')
        }),
    )
    
    def get_sectors(self, obj):
        return ", ".join([sector.name for sector in obj.sectors.all()])
    get_sectors.short_description = 'Sectors'
    
    def get_geographies(self, obj):
        return ", ".join([geo.name for geo in obj.geographies.all()])
    get_geographies.short_description = 'Geographies'


# Register Two-Factor Authentication models
@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_verified', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('is_verified', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('code', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    def is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'is_verified', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('is_verified', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'email')
    readonly_fields = ('code', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    def is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
