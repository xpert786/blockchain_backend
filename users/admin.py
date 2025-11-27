from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Sector, Geography, TwoFactorAuth, EmailVerification, TermsAcceptance, SyndicateProfile, TeamMember

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

admin.site.register(Sector)
admin.site.register(Geography)
admin.site.register(TwoFactorAuth)
admin.site.register(EmailVerification)
admin.site.register(TermsAcceptance)


@admin.register(SyndicateProfile)
class SyndicateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'firm_name', 'is_accredited', 'application_status', 'current_step', 'created_at')
    list_filter = ('is_accredited', 'application_status', 'enable_platform_lp_access', 'created_at')
    search_fields = ('user__username', 'user__email', 'firm_name')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'current_step')
    filter_horizontal = ('sectors', 'geographies')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Step 1: Lead Info', {
            'fields': ('is_accredited', 'understands_regulatory_requirements', 'sectors', 'geographies', 'existing_lp_count', 'enable_platform_lp_access')
        }),
        ('Step 2: Entity Profile', {
            'fields': ('firm_name', 'description', 'logo')
        }),
        ('Step 3: Compliance & Attestation', {
            'fields': ('risk_regulatory_attestation', 'jurisdictional_compliance_acknowledged', 'additional_compliance_policies')
        }),
        ('Step 4: Application Status', {
            'fields': ('application_submitted', 'submitted_at', 'application_status', 'current_step')
        }),
    )
    
    def current_step(self, obj):
        return obj.current_step
    current_step.short_description = 'Current Step'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin interface for TeamMember"""
    list_display = (
        'id', 'name', 'email', 'syndicate_name', 'role',
        'is_registered', 'is_active', 'added_at'
    )
    list_filter = ('role', 'is_active', 'invitation_sent', 'invitation_accepted', 'added_at')
    search_fields = ('name', 'email', 'syndicate__firm_name', 'user__username', 'user__email')
    readonly_fields = ('added_at', 'updated_at', 'is_registered')
    ordering = ('-added_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('syndicate', 'user', 'name', 'email')
        }),
        ('Role & Permissions', {
            'fields': (
                'role',
                'can_access_dashboard', 'can_manage_spvs', 'can_manage_documents',
                'can_manage_investors', 'can_view_reports', 'can_manage_transfers',
                'can_manage_team', 'can_manage_settings'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'invitation_sent', 'invitation_accepted', 'is_registered')
        }),
        ('Metadata', {
            'fields': ('added_by', 'added_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def syndicate_name(self, obj):
        """Display syndicate firm name"""
        return obj.syndicate.firm_name or f"Syndicate {obj.syndicate.id}"
    syndicate_name.short_description = 'Syndicate'
    
    def is_registered(self, obj):
        """Display registration status with colored indicator"""
        if obj.is_registered:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Registered</span>'
            )
        return format_html(
            '<span style="color: orange;">○ Invited</span>'
        )
    is_registered.short_description = 'Status'
    
