from django.contrib import admin
from .models import InvestorProfile
from .dashboard_models import Portfolio, Investment, Notification, KYCStatus

# Register your models here.


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    """Admin interface for InvestorProfile"""
    
    list_display = [
        'id',
        'user',
        'full_name',
        'email_address',
        'is_accredited_investor',
        'application_status',
        'current_step',
        'created_at',
        'submitted_at'
    ]
    
    list_filter = [
        'application_status',
        'is_accredited_investor',
        'meets_local_investment_thresholds',
        'country_of_residence',
        'created_at',
        'submitted_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'full_name',
        'email_address',
        'phone_number',
        'country_of_residence'
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
        ('Step 4: Accreditation (If Applicable)', {
            'fields': (
                'proof_of_income_net_worth',
                'is_accredited_investor',
                'meets_local_investment_thresholds',
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
