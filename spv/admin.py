from django.contrib import admin
from django.db.models import QuerySet
from .models import (
    SPV, PortfolioCompany, CompanyStage, IncorporationType,
    InstrumentType, ShareClass, Round, MasterPartnershipEntity
)


class SPVQuerySet(QuerySet):
    """Custom queryset that avoids Decimal field deserialization issues in SQLite"""
    def for_changelist(self):
        """Return only safe fields for admin changelist to avoid Decimal conversion errors"""
        return self.values_list(
            'id', 'display_name', 'company_name', 'company_stage_id', 
            'founder_email', 'status', 'created_by_id', 'created_at'
        )


@admin.register(CompanyStage)
class CompanyStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(IncorporationType)
class IncorporationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(InstrumentType)
class InstrumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(ShareClass)
class ShareClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(MasterPartnershipEntity)
class MasterPartnershipEntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')


@admin.register(PortfolioCompany)
class PortfolioCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SPV)
class SPVAdmin(admin.ModelAdmin):
    list_display = (
        'display_name', 
        'company_name', 
        'company_stage', 
        'founder_email', 
        'status', 
        'created_by', 
        'created_at'
    )
    list_filter = (
        'status', 'company_stage', 'country_of_incorporation',
        'transaction_type', 'valuation_type', 'round', 'adviser_entity',
        'access_mode', 'investment_visibility', 'created_at'
    )
    search_fields = (
        'display_name', 
        'portfolio_company_name', 
        'founder_email', 
        'created_by__username',
        'created_by__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = [
        'created_by', 'portfolio_company', 'company_stage', 'incorporation_type',
        'instrument_type', 'share_class', 'round', 'master_partnership_entity', 'fund_lead'
    ]
    
    def get_queryset(self, request):
        """Override queryset to exclude Decimal fields that cause SQLite conversion errors"""
        queryset = super().get_queryset(request)
        # For the changelist view, exclude Decimal fields to avoid InvalidOperation
        # Check if this is a changelist view by examining the request path
        if 'changelist' in request.path or request.path.endswith('/spv/'):
            # Use defer() to exclude the problematic Decimal fields from the queryset
            queryset = queryset.defer(
                'round_size', 'allocation', 'minimum_lp_investment',
                'total_carry_percentage', 'gp_commitment', 'lead_carry_percentage'
            )
        return queryset
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('created_by', 'display_name', 'status')
        }),
        ('Portfolio Company', {
            'fields': ('portfolio_company', 'portfolio_company_name')
        }),
        ('Company Details', {
            'fields': ('company_stage', 'country_of_incorporation', 'incorporation_type')
        }),
        ('Contact Information', {
            'fields': ('founder_email',)
        }),
        ('Documents', {
            'fields': ('pitch_deck',)
        }),
        ('Step 2: Terms', {
            'fields': (
                'transaction_type',
                'instrument_type',
                'valuation_type',
                'share_class',
                'round',
                'round_size',
                'allocation',
            )
        }),
        ('Step 3: Adviser & Legal Structure', {
            'fields': (
                'adviser_entity',
                'master_partnership_entity',
                'fund_lead',
            )
        }),
        ('Step 4: Fundraising & Jurisdiction', {
            'fields': (
                'jurisdiction',
                'entity_type',
                'minimum_lp_investment',
                'target_closing_date',
                'total_carry_percentage',
                'carry_recipient',
                'gp_commitment',
                'deal_partners',
                'deal_name',
                'access_mode',
            )
        }),
        ('Step 5: Invite LPs & Additional Info', {
            'fields': (
                'lp_invite_emails',
                'lp_invite_message',
                'lead_carry_percentage',
                'investment_visibility',
                'auto_invite_active_spvs',
                'invite_private_note',
                'invite_tags',
                'deal_tags',
                'syndicate_selection',
                'deal_memo',
                'supporting_document',
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_approved', 'mark_active', 'mark_closed', 'mark_cancelled']
    
    def mark_approved(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} SPV(s) marked as approved.')
    mark_approved.short_description = 'Mark selected SPVs as approved'
    
    def mark_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} SPV(s) marked as active.')
    mark_active.short_description = 'Mark selected SPVs as active'
    
    def mark_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} SPV(s) marked as closed.')
    mark_closed.short_description = 'Mark selected SPVs as closed'
    
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} SPV(s) marked as cancelled.')
    mark_cancelled.short_description = 'Mark selected SPVs as cancelled'
