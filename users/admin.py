from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Sector, Geography, TwoFactorAuth, EmailVerification, PasswordReset, TermsAcceptance, SyndicateProfile, Syndicate, TeamMember, ComplianceDocument, FeeRecipient, CreditCard, BankAccount, BeneficialOwner

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


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    """Admin interface for Password Reset OTPs"""
    list_display = (
        'id', 'user_display', 'email', 'otp', 'status_badge',
        'is_verified', 'is_used', 'created_at', 'expires_at'
    )
    list_filter = ('is_verified', 'is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'user__username', 'user__email', 'otp')
    readonly_fields = ('created_at', 'is_valid_display')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'email')
        }),
        ('OTP Details', {
            'fields': ('otp', 'created_at', 'expires_at', 'is_valid_display')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_used')
        }),
    )
    
    def user_display(self, obj):
        """Display user information"""
        return f"{obj.user.username} ({obj.user.email})"
    user_display.short_description = 'User'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        from django.utils import timezone
        
        if obj.is_used:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">USED</span>'
            )
        elif obj.is_verified:
            if timezone.now() > obj.expires_at:
                return format_html(
                    '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">VERIFIED (EXPIRED)</span>'
                )
            return format_html(
                '<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">VERIFIED</span>'
            )
        elif timezone.now() > obj.expires_at:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">EXPIRED</span>'
            )
        else:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">PENDING</span>'
            )
    status_badge.short_description = 'Status'
    
    def is_valid_display(self, obj):
        """Display if OTP is currently valid"""
        if obj.is_valid():
            return format_html('<span style="color: green; font-weight: bold;">✓ Valid</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Invalid</span>')
    is_valid_display.short_description = 'Currently Valid'


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


# Register proxy model Syndicate using the same admin as SyndicateProfile
try:
    admin.site.register(Syndicate, SyndicateProfileAdmin)
except Exception:
    # If Syndicate is already registered or SyndicateProfileAdmin incompatible, ignore
    pass


@admin.register(SyndicateProfile)
class SyndicateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'firm_name', 'full_name', 'entity_type', 'is_accredited', 'application_status', 'current_step', 'created_at')
    list_filter = ('is_accredited', 'application_status', 'entity_type', 'enable_platform_lp_access', 'created_at')
    search_fields = ('user__username', 'user__email', 'firm_name', 'first_name', 'last_name', 'full_name', 'entity_legal_name', 'registration_number')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'current_step')
    filter_horizontal = ('sectors', 'geographies')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'full_name', 'bio', 'short_bio', 'link')
        }),
        ('Step 1: Lead Info - Personal & Accreditation', {
            'fields': (
                'country_of_residence', 'current_role_title', 'years_of_experience',
                'linkedin_profile', 'typical_check_size',
                'is_accredited', 'understands_regulatory_requirements'
            )
        }),
        ('Step 1: Lead Info - Investment Focus & LP Network', {
            'fields': (
                'sectors', 'geographies', 'existing_lp_count', 'lp_base_size',
                'enable_platform_lp_access'
            )
        }),
        ('Step 2: Entity Profile', {
            'fields': ('firm_name', 'description', 'logo')
        }),
        ('Step 3a: Entity KYB - Basic Info', {
            'fields': (
                'entity_legal_name', 'entity_type', 'country_of_incorporation', 'registration_number'
            )
        }),
        ('Step 3a: Entity KYB - Registered Address', {
            'fields': (
                'registered_street_address', 'registered_area_landmark', 'registered_postal_code',
                'registered_city', 'registered_state', 'registered_country'
            ),
            'classes': ('collapse',)
        }),
        ('Step 3a: Entity KYB - Operating Address (Optional)', {
            'fields': (
                'operating_street_address', 'operating_area_landmark', 'operating_postal_code',
                'operating_city', 'operating_state', 'operating_country'
            ),
            'classes': ('collapse',)
        }),
        ('Step 3a: Entity KYB - Documents', {
            'fields': (
                'certificate_of_incorporation', 'registered_address_proof', 'directors_register',
                'trust_deed', 'partnership_agreement'
            ),
            'classes': ('collapse',)
        }),
        ('KYB Verification (Legacy)', {
            'fields': (
                'company_legal_name', 'kyb_full_name', 'kyb_position',
                'company_bank_statement',
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
        'id', 'card_type_display', 'card_category_display', 'card_number_masked', 'card_holder_name',
        'expiry_date', 'status_badge', 'is_primary', 'syndicate_name', 'created_at'
    )
    list_filter = ('card_category', 'card_type', 'status', 'is_primary', 'created_at')
    search_fields = ('card_holder_name', 'card_number', 'syndicate__firm_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-is_primary', '-created_at')
    
    fieldsets = (
        ('Syndicate Information', {
            'fields': ('syndicate',)
        }),
        ('Card Information', {
            'fields': ('card_category', 'card_type', 'card_number', 'card_holder_name', 'expiry_date', 'cvv')
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
    
    def card_category_display(self, obj):
        """Display card category"""
        return obj.get_card_category_display()
    card_category_display.short_description = 'Card Category'
    
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


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin interface for Team Members"""
    list_display = (
        'id', 'name', 'email', 'role', 'syndicate_name', 
        'is_active', 'is_registered', 'invitation_accepted', 'added_at'
    )
    list_filter = (
        'role', 'is_active', 'invitation_sent', 'invitation_accepted',
        'can_create_spvs', 'can_add_remove_team_members'
    )
    search_fields = ('name', 'email', 'syndicate__firm_name', 'user__username', 'user__email')
    ordering = ('-added_at',)
    autocomplete_fields = ['syndicate', 'user', 'added_by']
    readonly_fields = ('added_at', 'updated_at', 'is_registered')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('syndicate', 'user', 'name', 'email', 'role')
        }),
        ('Deal Permissions', {
            'fields': (
                'can_create_spvs', 'can_publish_spvs', 
                'can_upload_deal_materials', 'can_edit_deal_terms'
            ),
            'classes': ('collapse',)
        }),
        ('Investor Permissions', {
            'fields': (
                'can_invite_lps', 'can_view_lp_list', 
                'can_view_lp_commitments', 'can_communicate_with_lps'
            ),
            'classes': ('collapse',)
        }),
        ('Operations & Finance Permissions', {
            'fields': (
                'can_manage_capital_calls', 'can_update_payment_statuses',
                'can_manage_bank_accounts', 'can_send_tax_documents'
            ),
            'classes': ('collapse',)
        }),
        ('Compliance Permissions', {
            'fields': (
                'can_review_kyc_kyb', 'can_approve_reject_investors',
                'can_view_jurisdiction_flags', 'can_access_audit_logs'
            ),
            'classes': ('collapse',)
        }),
        ('Team Management Permissions', {
            'fields': (
                'can_add_remove_team_members', 'can_edit_roles_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('General Permissions', {
            'fields': (
                'can_access_dashboard', 'can_view_reports',
                'can_manage_spvs', 'can_manage_documents',
                'can_manage_investors', 'can_manage_transfers',
                'can_manage_team', 'can_manage_settings'
            ),
            'classes': ('collapse',)
        }),
        ('Invitation & Status', {
            'fields': (
                'invitation_sent', 'invitation_token', 
                'invitation_accepted', 'is_active'
            )
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
        """Check if team member has registered user account"""
        if obj.user:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: orange;">✗ No</span>')
    is_registered.short_description = 'Registered'


@admin.register(BeneficialOwner)
class BeneficialOwnerAdmin(admin.ModelAdmin):
    """Admin interface for Beneficial Owners (UBOs)"""
    list_display = (
        'id', 'full_name', 'email', 'nationality', 'syndicate_name',
        'role', 'ownership_percentage', 'kyc_status_badge', 'is_active', 'created_at'
    )
    list_filter = ('role', 'beneficiary_role', 'kyc_status', 'is_active', 'nationality', 'created_at')
    search_fields = ('full_name', 'email', 'syndicate__firm_name', 'nationality', 'city', 'country')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'full_address', 'kyc_invite_sent_at', 'kyc_completed_at')
    
    fieldsets = (
        ('Syndicate Information', {
            'fields': ('syndicate',)
        }),
        ('Personal Information', {
            'fields': ('full_name', 'date_of_birth', 'nationality', 'email')
        }),
        ('Residential Address', {
            'fields': (
                'street_address', 'area_landmark', 'postal_code',
                'city', 'state', 'country', 'full_address'
            ),
            'classes': ('collapse',)
        }),
        ('Role & Ownership', {
            'fields': ('role', 'ownership_percentage', 'beneficiary_role')
        }),
        ('KYC Verification', {
            'fields': (
                'kyc_status', 'kyc_invite_sent', 'kyc_invite_sent_at', 'kyc_completed_at'
            )
        }),
        ('Documents', {
            'fields': ('identity_document', 'proof_of_address'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('is_active', 'added_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def syndicate_name(self, obj):
        """Display syndicate firm name"""
        return obj.syndicate.firm_name or f"Syndicate {obj.syndicate.id}"
    syndicate_name.short_description = 'Syndicate'
    
    def kyc_status_badge(self, obj):
        """Display KYC status with colored badge"""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'failed': 'red',
            'needs_reupload': 'purple'
        }
        color = colors.get(obj.kyc_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_kyc_status_display()
        )
    kyc_status_badge.short_description = 'KYC Status'
