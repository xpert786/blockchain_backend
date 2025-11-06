from django.contrib import admin
from .models import SPV, PortfolioCompany, CompanyStage, IncorporationType


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
    list_filter = ('status', 'company_stage', 'country_of_incorporation', 'created_at')
    search_fields = (
        'display_name', 
        'portfolio_company_name', 
        'founder_email', 
        'created_by__username',
        'created_by__email'
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['created_by', 'portfolio_company', 'company_stage', 'incorporation_type']
    
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
