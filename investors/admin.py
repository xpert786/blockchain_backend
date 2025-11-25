from django.contrib import admin
from .models import InvestorProfile

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
