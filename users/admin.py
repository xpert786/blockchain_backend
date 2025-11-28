from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Sector, Geography, TwoFactorAuth, EmailVerification, TermsAcceptance, SyndicateProfile, TeamMember, ComplianceDocument, FeeRecipient, CreditCard, BankAccount

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


@admin.register(FeeRecipient)
class FeeRecipientAdmin(admin.ModelAdmin):
    """Admin interface for Fee Recipients"""
    list_display = (
        'id', 'entity_name', 'recipient_type', 'residence',
        'syndicate_name', 'tax_id', 'created_at'
    )
    list_filter = ('recipient_type', 'residence', 'created_at')
    search_fields = (
        'entity_name', 'tax_id',
        'syndicate__firm_name', 'syndicate__user__username'
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Syndicate Information', {
            'fields': ('syndicate',)
        }),
        ('Recipient Information', {
            'fields': ('recipient_type', 'entity_name', 'residence')
        }),
        ('Tax Information', {
            'fields': ('tax_id',)
        }),
        ('Documents', {
            'fields': ('id_document', 'proof_of_address')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def syndicate_name(self, obj):
        """Display syndicate firm name"""
        return obj.syndicate.firm_name or f"Syndicate {obj.syndicate.id}"
    syndicate_name.short_description = 'Syndicate'


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
        ('KYB Verification', {
            'fields': (
                'company_legal_name', 'kyb_full_name', 'kyb_position',
                'certificate_of_incorporation', 'company_bank_statement',
                'address_line_1', 'address_line_2', 'town_city', 'postal_code', 'country',
                'company_proof_of_address', 'beneficiary_owner_identity_document',
                'beneficiary_owner_proof_of_address', 'sse_eligibility',
                'is_notary_wet_signing', 'will_require_unlockley',
                'investee_company_contact_number', 'investee_company_email',
                'agree_to_investee_terms', 'kyb_verification_completed', 'kyb_verification_submitted_at'
            ),
            'classes': ('collapse',)
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


@admin.register(ComplianceDocument)
class ComplianceDocumentAdmin(admin.ModelAdmin):
    """Admin interface for Compliance Documents"""
    list_display = (
        'id', 'document_name', 'document_type', 'jurisdiction',
        'status_badge', 'syndicate_name', 'file_size_display',
        'expiry_display', 'uploaded_at'
    )
    list_filter = ('document_type', 'jurisdiction', 'status', 'uploaded_at')
    search_fields = ('document_name', 'syndicate__firm_name', 'original_filename')
    readonly_fields = ('uploaded_at', 'updated_at', 'file_size', 'mime_type', 'original_filename', 'file_size_mb', 'is_expired')
    ordering = ('-uploaded_at',)
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Document Information', {
            'fields': ('syndicate', 'document_name', 'document_type', 'jurisdiction')
        }),
        ('File Details', {
            'fields': ('file', 'original_filename', 'file_size', 'file_size_mb', 'mime_type')
        }),
        ('Status & Review', {
            'fields': ('status', 'review_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Expiry', {
            'fields': ('expiry_date', 'is_expired')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def syndicate_name(self, obj):
        """Display syndicate firm name"""
        return obj.syndicate.firm_name or f"Syndicate {obj.syndicate.id}"
    syndicate_name.short_description = 'Syndicate'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'ok': 'green',
            'pending': 'orange',
            'exp': 'red',
            'missing': 'gray',
            'rejected': 'darkred'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def file_size_display(self, obj):
        """Display file size in MB"""
        return f"{obj.file_size_mb} MB"
    file_size_display.short_description = 'Size'
    
    def expiry_display(self, obj):
        """Display expiry status"""
        if not obj.expiry_date:
            return format_html('<span style="color: gray;">No expiry</span>')
        
        if obj.is_expired:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Expired ({})</span>',
                obj.expiry_date
            )
        
        # Check if expiring soon (within 30 days)
        from datetime import timedelta
        from django.utils import timezone
        days_until_expiry = (obj.expiry_date - timezone.now().date()).days
        if days_until_expiry <= 30:
            return format_html(
                '<span style="color: orange;">⚠ {} days ({})</span>',
                days_until_expiry, obj.expiry_date
            )
        
        return format_html('<span style="color: green;">✓ {}</span>', obj.expiry_date)
    expiry_display.short_description = 'Expiry'


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    """Admin interface for Credit Cards"""
    list_display = (
        'id', 'card_type_display', 'card_number_masked', 'card_holder_name',
        'expiry_date', 'status_badge', 'is_primary', 'syndicate_name', 'created_at'
    )
    list_filter = ('card_type', 'status', 'is_primary', 'created_at')
    search_fields = ('card_holder_name', 'card_number', 'syndicate__firm_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-is_primary', '-created_at')
    
    fieldsets = (
        ('Syndicate Information', {
            'fields': ('syndicate',)
        }),
        ('Card Information', {
            'fields': ('card_type', 'card_number', 'card_holder_name', 'expiry_date', 'cvv')
        }),
        ('Status & Settings', {
            'fields': ('status', 'is_primary')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def card_number_masked(self, obj):
        """Display masked card number"""
        if obj.card_number:
            return f"****-****-****-{obj.card_number[-4:]}"
        return "N/A"
    card_number_masked.short_description = 'Card Number'
    
    def card_type_display(self, obj):
        """Display card type"""
        return obj.get_card_type_display()
    card_type_display.short_description = 'Card Type'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'active': 'green',
            'expired': 'red',
            'suspended': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def syndicate_name(self, obj):
        """Display syndicate firm name"""
        return obj.syndicate.firm_name or f"Syndicate {obj.syndicate.id}"
    syndicate_name.short_description = 'Syndicate'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin interface for Bank Accounts"""
    list_display = (
        'id', 'bank_name', 'account_number_masked', 'account_type_display',
        'account_holder_name', 'status_badge', 'is_primary', 'syndicate_name', 'created_at'
    )
    list_filter = ('account_type', 'status', 'is_primary', 'created_at')
    search_fields = ('bank_name', 'account_number', 'account_holder_name', 'syndicate__firm_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-is_primary', '-created_at')
    
    fieldsets = (
        ('Syndicate Information', {
            'fields': ('syndicate',)
        }),
        ('Bank Account Information', {
            'fields': (
                'bank_name', 'account_type', 'account_number', 'account_holder_name'
            )
        }),
        ('Routing Information', {
            'fields': ('routing_number', 'swift_code', 'iban'),
            'classes': ('collapse',)
        }),
        ('Status & Settings', {
            'fields': ('status', 'is_primary')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_number_masked(self, obj):
        """Display masked account number"""
        if obj.account_number:
            return f"****-****-****-{obj.account_number[-4:]}"
        return "N/A"
    account_number_masked.short_description = 'Account Number'
    
    def account_type_display(self, obj):
        """Display account type"""
        return obj.get_account_type_display()
    account_type_display.short_description = 'Account Type'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'suspended': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def syndicate_name(self, obj):
        """Display syndicate firm name"""
        return obj.syndicate.firm_name or f"Syndicate {obj.syndicate.id}"
    syndicate_name.short_description = 'Syndicate'
