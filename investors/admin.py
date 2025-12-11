from django.contrib import admin
from .models import InvestorProfile
from .dashboard_models import Portfolio, Investment, Notification, KYCStatus, Wishlist, PortfolioPerformance, TaxDocument, TaxSummary, InvestorDocument

# Register your models here.


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    """Admin interface for InvestorProfile"""
    
    list_display = [
        'id',
        'user',
        'full_name',
        'email_address',
        'accreditation_jurisdiction',
        'accreditation_check_completed',
        'accreditation_check_completed_at',
        'is_accredited_investor',
        'application_status',
        'current_step',
        'two_factor_authentication_enabled',
        'preferred_investment_currency',
        'created_at',
        'submitted_at'
    ]
    
    list_filter = [
        'application_status',
        'is_accredited_investor',
        'meets_local_investment_thresholds',
        'country_of_residence',
        'preferred_investment_currency',
        'two_factor_authentication_enabled',
        'us_person_status',
        'delaware_spvs_allowed',
        'bvi_spvs_allowed',
        'created_at',
        'submitted_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'full_name',
        'full_legal_name',
        'email_address',
        'phone_number',
        'country_of_residence',
        'national_id',
        'tax_identification_number',
        'escrow_partner_selection'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'submitted_at',
        'current_step',
        'step1_completed',
        'step2_completed',
        'step3_completed',
        'step4_completed',
        'step5_completed',
        'step6_completed'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Step 1: Basic Information', {
            'fields': (
                'full_name',
                'email_address',
                'phone_number',
                'country_of_residence',
                'tax_residency',
                'national_id',
            )
        }),
        ('Step 2: KYC / Identity Verification', {
            'fields': (
                'government_id',
                'date_of_birth',
                'street_address',
                'city',
                'state_province',
                'zip_postal_code',
                'country',
            )
        }),
        ('Step 3: Bank Details / Payment Setup', {
            'fields': (
                'bank_account_number',
                'bank_name',
                'account_holder_name',
                'swift_ifsc_code',
                'proof_of_bank_ownership',
            )
        }),
        ('Step 3.5: Jurisdiction-Aware Accreditation Check', {
            'fields': (
                'accreditation_jurisdiction',
                'accreditation_rules_selected',
                'accreditation_check_completed',
                'accreditation_check_completed_at',
            )
        }),
        ('Step 4: Accreditation (If Applicable)', {
            'fields': (
                'investor_type',
                'full_legal_name',
                'legal_place_of_residence',
                'accreditation_method',
                'proof_of_income_net_worth',
                'is_accredited_investor',
                'meets_local_investment_thresholds',
                'accreditation_expiry_date',
            )
        }),
        ('Step 5: Accept Agreements', {
            'fields': (
                'terms_and_conditions_accepted',
                'risk_disclosure_accepted',
                'privacy_policy_accepted',
                'confirmation_of_true_information',
            )
        }),
        ('Application Status', {
            'fields': (
                'application_status',
                'application_submitted',
                'submitted_at',
            )
        }),
        ('Tax & Compliance Settings', {
            'fields': (
                'tax_identification_number',
                'us_person_status',
                'w9_form_submitted',
                'k1_acceptance',
                'tax_reporting_consent',
            ),
            'classes': ('collapse',)
        }),
        ('Eligibility Settings', {
            'fields': (
                'delaware_spvs_allowed',
                'bvi_spvs_allowed',
                'auto_reroute_consent',
                'max_annual_commitment',
                'deal_stage_preferences',
            ),
            'classes': ('collapse',)
        }),
        ('Financial Settings', {
            'fields': (
                'preferred_investment_currency',
                'escrow_partner_selection',
                'capital_call_notification_preferences',
                'carry_fees_display_preference',
            ),
            'classes': ('collapse',)
        }),
        ('Portfolio Settings', {
            'fields': (
                'portfolio_view_settings',
                'secondary_transfer_consent',
                'liquidity_preference',
                'whitelist_secondary_trading',
            ),
            'classes': ('collapse',)
        }),
        ('Security & Privacy Settings', {
            'fields': (
                'two_factor_authentication_enabled',
                'session_timeout_minutes',
                'soft_wall_deal_preview',
                'discovery_opt_in',
                'anonymity_preference',
            ),
            'classes': ('collapse',)
        }),
        ('Communication Settings', {
            'fields': (
                'preferred_contact_method',
                'update_frequency',
                'event_alerts',
                'marketing_consent',
            ),
            'classes': ('collapse',)
        }),
        ('Progress Tracking', {
            'fields': (
                'current_step',
                'step1_completed',
                'step2_completed',
                'step3_completed',
                'step4_completed',
                'step5_completed',
                'step6_completed',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after submission"""
        readonly = list(self.readonly_fields)
        
        if obj and obj.application_submitted:
            # Make most fields readonly after submission
            readonly.extend([
                'full_name',
                'email_address',
                'phone_number',
                'country_of_residence',
                'national_id',
                'government_id',
                'date_of_birth',
                'street_address',
                'city',
                'state_province',
                'zip_postal_code',
                'country',
                'bank_account_number',
                'bank_name',
                'account_holder_name',
                'swift_ifsc_code',
                'proof_of_bank_ownership',
                'proof_of_income_net_worth',
                'is_accredited_investor',
                'meets_local_investment_thresholds',
                'terms_and_conditions_accepted',
                'risk_disclosure_accepted',
                'privacy_policy_accepted',
                'confirmation_of_true_information',
            ])
        
        return readonly


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """Admin interface for Portfolio"""
    
    list_display = [
        'id',
        'user',
        'total_invested',
        'current_value',
        'unrealized_gain',
        'portfolio_growth_percentage',
        'total_investments_count',
        'updated_at'
    ]
    
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_calculated_at',
        'portfolio_growth_percentage'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Portfolio Summary', {
            'fields': (
                'total_invested',
                'current_value',
                'unrealized_gain',
                'realized_gain',
                'portfolio_growth_percentage',
            )
        }),
        ('Statistics', {
            'fields': (
                'total_investments_count',
                'active_investments_count',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_calculated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """Admin interface for Investment"""
    
    list_display = [
        'id',
        'investor',
        'syndicate_name',
        'sector',
        'investment_type',
        'invested_amount',
        'current_value',
        'gain_loss_percentage',
        'status',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'investment_type',
        'sector',
        'stage',
        'created_at'
    ]
    
    search_fields = [
        'investor__username',
        'investor__email',
        'syndicate_name',
        'sector'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'gain_loss',
        'gain_loss_percentage',
        'is_active'
    ]
    
    fieldsets = (
        ('Investor Information', {
            'fields': ('investor', 'spv')
        }),
        ('Investment Details', {
            'fields': (
                'syndicate_name',
                'sector',
                'stage',
                'investment_type',
            )
        }),
        ('Financial Details', {
            'fields': (
                'allocated',
                'raised',
                'target',
                'invested_amount',
                'min_investment',
                'current_value',
                'gain_loss',
                'gain_loss_percentage',
            )
        }),
        ('Status and Timeline', {
            'fields': (
                'status',
                'deadline',
                'days_left',
                'track_record',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'invested_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification"""
    
    list_display = [
        'id',
        'user',
        'notification_type',
        'title',
        'status',
        'priority',
        'action_required',
        'created_at'
    ]
    
    list_filter = [
        'notification_type',
        'status',
        'priority',
        'action_required',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'title',
        'message'
    ]
    
    readonly_fields = [
        'created_at',
        'read_at',
        'is_unread',
        'is_action_required'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Notification Details', {
            'fields': (
                'notification_type',
                'title',
                'message',
                'icon',
            )
        }),
        ('Status and Priority', {
            'fields': (
                'status',
                'priority',
                'action_required',
                'action_url',
                'action_label',
                'is_unread',
                'is_action_required',
            )
        }),
        ('Related Objects', {
            'fields': (
                'related_investment',
                'related_spv',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'read_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        for notification in queryset:
            notification.mark_as_read()
        self.message_user(request, f'{queryset.count()} notification(s) marked as read')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        for notification in queryset:
            notification.mark_as_unread()
        self.message_user(request, f'{queryset.count()} notification(s) marked as unread')
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(KYCStatus)
class KYCStatusAdmin(admin.ModelAdmin):
    """Admin interface for KYC Status"""
    
    list_display = [
        'id',
        'user',
        'status',
        'created_at',
        'verified_at'
    ]
    
    list_filter = ['status', 'created_at', 'verified_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
        }),
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Admin interface for Wishlist"""
    
    list_display = [
        'id',
        'investor',
        'spv',
        'spv_display_name',
        'spv_status',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'created_at',
        'updated_at',
        'spv__status'
    ]
    
    search_fields = [
        'investor__username',
        'investor__email',
        'spv__display_name',
        'spv__portfolio_company_name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Investor Information', {
            'fields': ('investor',)
        }),
        ('SPV Information', {
            'fields': ('spv',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def spv_display_name(self, obj):
        """Display SPV name"""
        return obj.spv.display_name if obj.spv else '-'
    spv_display_name.short_description = 'SPV Name'
    
    def spv_status(self, obj):
        """Display SPV status"""
        return obj.spv.get_status_display() if obj.spv else '-'
    spv_status.short_description = 'SPV Status'


@admin.register(PortfolioPerformance)
class PortfolioPerformanceAdmin(admin.ModelAdmin):
    """Admin interface for Portfolio Performance time-series data"""
    
    list_display = [
        'id',
        'portfolio',
        'get_user',
        'date',
        'total_invested',
        'current_value',
        'created_at'
    ]
    
    list_filter = [
        'date',
        'created_at',
        'portfolio__user'
    ]
    
    search_fields = [
        'portfolio__user__username',
        'portfolio__user__email'
    ]
    
    readonly_fields = ['created_at']
    
    ordering = ['-date']
    
    fieldsets = (
        ('Portfolio Information', {
            'fields': ('portfolio',)
        }),
        ('Performance Data', {
            'fields': (
                'date',
                'total_invested',
                'current_value',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_user(self, obj):
        """Display username for the portfolio"""
        return obj.portfolio.user.username if obj.portfolio else '-'
    get_user.short_description = 'User'
    get_user.admin_order_field = 'portfolio__user__username'


@admin.register(TaxDocument)
class TaxDocumentAdmin(admin.ModelAdmin):
    """Admin interface for Tax Documents"""
    
    list_display = [
        'id',
        'investor',
        'document_type',
        'document_name',
        'tax_year',
        'status',
        'issue_date',
        'file_size_display',
        'created_at'
    ]
    
    list_filter = [
        'document_type',
        'status',
        'tax_year',
        'created_at'
    ]
    
    search_fields = [
        'investor__username',
        'investor__email',
        'document_name'
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'downloaded_at', 'file_size_display']
    
    ordering = ['-tax_year', '-issue_date']
    
    fieldsets = (
        ('Investor Information', {
            'fields': ('investor', 'investment')
        }),
        ('Document Details', {
            'fields': (
                'document_type',
                'document_name',
                'tax_year',
                'status',
            )
        }),
        ('File', {
            'fields': ('file', 'file_size', 'file_size_display')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expected_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'downloaded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaxSummary)
class TaxSummaryAdmin(admin.ModelAdmin):
    """Admin interface for Tax Summary"""
    
    list_display = [
        'id',
        'investor',
        'tax_year',
        'total_income',
        'total_deductions',
        'net_taxable_income',
        'estimated_tax',
        'updated_at'
    ]
    
    list_filter = ['tax_year', 'created_at']
    
    search_fields = [
        'investor__username',
        'investor__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    ordering = ['-tax_year']
    
    fieldsets = (
        ('Investor Information', {
            'fields': ('investor', 'tax_year')
        }),
        ('Income Breakdown', {
            'fields': (
                'dividend_income',
                'capital_gains',
                'interest_income',
                'total_income',
            )
        }),
        ('Deductions Breakdown', {
            'fields': (
                'management_fees',
                'professional_services',
                'other_expenses',
                'total_deductions',
            )
        }),
        ('Calculated', {
            'fields': (
                'net_taxable_income',
                'estimated_tax',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InvestorDocument)
class InvestorDocumentAdmin(admin.ModelAdmin):
    """Admin interface for Investor Documents"""
    
    list_display = [
        'id',
        'investor',
        'title',
        'category',
        'file_type',
        'file_size_display',
        'status',
        'fund_name',
        'uploaded_at'
    ]
    
    list_filter = [
        'category',
        'status',
        'file_type',
        'uploaded_at'
    ]
    
    search_fields = [
        'investor__username',
        'investor__email',
        'title',
        'fund_name'
    ]
    
    readonly_fields = ['file_type', 'file_size', 'file_size_display', 'uploaded_at', 'updated_at']
    
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Investor Information', {
            'fields': ('investor', 'investment', 'spv')
        }),
        ('Document Details', {
            'fields': (
                'title',
                'description',
                'category',
                'status',
                'fund_name',
            )
        }),
        ('File', {
            'fields': ('file', 'file_type', 'file_size', 'file_size_display')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
