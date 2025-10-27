from django.contrib import admin
from .models import KYC

@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'submitted_at', 'city', 'country')
    list_filter = ('status', 'country', 'submitted_at')
    search_fields = ('user__username', 'user__email', 'city', 'country', 'Investee_Company_Email')
    autocomplete_fields = ['user']
    readonly_fields = ('submitted_at',)
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'status', 'submitted_at')
        }),
        ('Company Documents', {
            'fields': ('certificate_of_incorporation', 'company_bank_statement', 'company_proof_of_address')
        }),
        ('Company Address', {
            'fields': ('address_1', 'address_2', 'city', 'zip_code', 'country')
        }),
        ('Owner Documents', {
            'fields': ('owner_identity_doc', 'owner_proof_of_address')
        }),
        ('Eligibility & Compliance', {
            'fields': ('sie_eligibilty', 'notary', 'Unlocksley_To_Sign_a_Deed_Of_adherence')
        }),
        ('Contact Information', {
            'fields': ('Investee_Company_Contact_Number', 'Investee_Company_Email')
        }),
        ('Agreements', {
            'fields': ('I_Agree_To_Investee_Terms',)
        }),
    )
    
    actions = ['approve_kyc', 'reject_kyc', 'mark_pending']
    
    def approve_kyc(self, request, queryset):
        updated = queryset.update(status='Approved')
        self.message_user(request, f'{updated} KYC record(s) approved successfully.')
    approve_kyc.short_description = 'Approve selected KYC records'
    
    def reject_kyc(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f'{updated} KYC record(s) rejected.')
    reject_kyc.short_description = 'Reject selected KYC records'
    
    def mark_pending(self, request, queryset):
        updated = queryset.update(status='Pending')
        self.message_user(request, f'{updated} KYC record(s) marked as pending.')
    mark_pending.short_description = 'Mark selected KYC records as pending'
