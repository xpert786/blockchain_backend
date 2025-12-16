from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Document, DocumentSignatory, DocumentTemplate, DocumentGeneration, SyndicateDocumentDefaults


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_id',
        'title',
        'document_type',
        'status',
        'version',
        'file_size_display',
        'signatories_display',
        'created_by',
        'created_at',
    )
    list_filter = (
        'status',
        'document_type',
        'requires_admin_review',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'document_id',
        'title',
        'description',
        'original_filename',
        'created_by__username',
        'created_by__email',
    )
    readonly_fields = (
        'document_id',
        'file_size',
        'mime_type',
        'created_at',
        'updated_at',
        'finalized_at',
        'signatories_count_display',
        'signed_count_display',
        'pending_signatures_count_display',
    )
    autocomplete_fields = ['created_by', 'spv', 'syndicate', 'parent_document']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'document_id',
                'title',
                'description',
                'document_type',
            )
        }),
        ('File Information', {
            'fields': (
                'file',
                'original_filename',
                'file_size',
                'mime_type',
            )
        }),
        ('Version Control', {
            'fields': (
                'version',
                'parent_document',
            )
        }),
        ('Status and Workflow', {
            'fields': (
                'status',
                'requires_admin_review',
                'review_notes',
            )
        }),
        ('Relationships', {
            'fields': (
                'created_by',
                'spv',
                'syndicate',
            )
        }),
        ('Signatories', {
            'fields': (
                'signatories_count_display',
                'signed_count_display',
                'pending_signatures_count_display',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
                'finalized_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_pending_review',
        'mark_signed',
        'mark_finalized',
        'mark_rejected',
    ]
    
    def file_size_display(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        return "-"
    file_size_display.short_description = 'File Size'
    
    def signatories_display(self, obj):
        """Display signatories count"""
        signed = obj.signed_count
        total = obj.signatories_count
        if total > 0:
            return format_html(
                '<span style="color: green;">{}</span> / {}',
                signed,
                total
            )
        return "0"
    signatories_display.short_description = 'Signatures'
    
    def signatories_count_display(self, obj):
        """Display total signatories count"""
        return obj.signatories_count
    signatories_count_display.short_description = 'Total Signatories'
    
    def signed_count_display(self, obj):
        """Display signed count"""
        return obj.signed_count
    signed_count_display.short_description = 'Signed'
    
    def pending_signatures_count_display(self, obj):
        """Display pending signatures count"""
        return obj.pending_signatures_count
    pending_signatures_count_display.short_description = 'Pending'
    
    def mark_pending_review(self, request, queryset):
        updated = queryset.update(status='pending_review', requires_admin_review=True)
        self.message_user(request, f'{updated} document(s) marked as pending review.')
    mark_pending_review.short_description = 'Mark selected as pending review'
    
    def mark_signed(self, request, queryset):
        updated = queryset.update(status='signed')
        self.message_user(request, f'{updated} document(s) marked as signed.')
    mark_signed.short_description = 'Mark selected as signed'
    
    def mark_finalized(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='finalized', finalized_at=timezone.now())
        self.message_user(request, f'{updated} document(s) marked as finalized.')
    mark_finalized.short_description = 'Mark selected as finalized'
    
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} document(s) marked as rejected.')
    mark_rejected.short_description = 'Mark selected as rejected'


@admin.register(DocumentSignatory)
class DocumentSignatoryAdmin(admin.ModelAdmin):
    list_display = (
        'document',
        'user',
        'role',
        'signed',
        'signed_at',
        'invited_at',
    )
    list_filter = (
        'signed',
        'invited_at',
        'signed_at',
    )
    search_fields = (
        'document__document_id',
        'document__title',
        'user__username',
        'user__email',
        'role',
    )
    readonly_fields = ('invited_at', 'signed_at')
    autocomplete_fields = ['document', 'user', 'invited_by']
    
    fieldsets = (
        ('Document and User', {
            'fields': ('document', 'user', 'role')
        }),
        ('Signature Information', {
            'fields': (
                'signed',
                'signed_at',
                'signature_ip',
                'signature_location',
                'notes',
            )
        }),
        ('Invitation', {
            'fields': (
                'invited_at',
                'invited_by',
            )
        }),
    )


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'version',
        'category',
        'scope',
        'jurisdiction_scope',
        'content_type',
        'is_active',
        'enable_digital_signature',
        'created_by',
        'created_at',
    )
    list_filter = (
        'category',
        'scope',
        'jurisdiction_scope',
        'content_type',
        'is_active',
        'enable_digital_signature',
        'created_at',
    )
    search_fields = (
        'name',
        'description',
        'version',
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'description',
                'version',
                'category',
            )
        }),
        ('Scope & Jurisdiction', {
            'fields': (
                'scope',
                'jurisdiction_scope',
            ),
            'description': "scope='spv' for SPV reference docs, 'investor' for investor-bound PDFs"
        }),
        ('Template Content', {
            'fields': (
                'template_content',
                'content_type',
                'template_file',
            ),
            'description': 'Store template as HTML/Markdown with {{placeholders}}. PDFs generated at runtime.'
        }),
        ('Fields Configuration', {
            'fields': (
                'required_fields',
                'configurable_fields',
            ),
            'description': 'required_fields for doc generation, configurable_fields for syndicate defaults'
        }),
        ('Settings', {
            'fields': (
                'enable_digital_signature',
                'is_active',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_active', 'mark_inactive']
    
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} template(s) marked as active.')
    mark_active.short_description = 'Mark selected templates as active'
    
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} template(s) marked as inactive.')
    mark_inactive.short_description = 'Mark selected templates as inactive'


@admin.register(DocumentGeneration)
class DocumentGenerationAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'generated_document',
        'has_pdf',
        'pdf_size_display',
        'generated_by',
        'generated_at',
        'enable_digital_signature',
    )
    list_filter = (
        'generated_at',
        'enable_digital_signature',
        'template',
    )
    search_fields = (
        'template__name',
        'generated_document__document_id',
        'generated_document__title',
        'generated_by__username',
        'generated_by__email',
    )
    readonly_fields = ('generated_at', 'pdf_file_size')
    autocomplete_fields = ['template', 'generated_document', 'generated_by']
    
    fieldsets = (
        ('Generation Information', {
            'fields': (
                'template',
                'generated_document',
                'generated_by',
                'generated_at',
            )
        }),
        ('Generated PDF', {
            'fields': (
                'generated_pdf',
                'pdf_filename',
                'pdf_file_size',
            )
        }),
        ('Generation Data', {
            'fields': (
                'generation_data',
                'enable_digital_signature',
            )
        }),
    )
    
    def has_pdf(self, obj):
        """Check if PDF was generated"""
        if obj.generated_pdf:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    has_pdf.short_description = 'PDF Generated'
    
    def pdf_size_display(self, obj):
        """Display PDF file size"""
        if obj.pdf_file_size:
            size_mb = obj.pdf_file_size / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        return "-"
    pdf_size_display.short_description = 'PDF Size'


@admin.register(SyndicateDocumentDefaults)
class SyndicateDocumentDefaultsAdmin(admin.ModelAdmin):
    """
    Admin for Syndicate Document Defaults.
    
    Used for "Syndicate Document Defaults" - saving template-driven defaults
    from configurable_fields[], NOT for generating specific PDFs.
    """
    list_display = (
        'syndicate',
        'template',
        'created_by',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'template',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'syndicate__firm_name',
        'template__name',
        'created_by__username',
    )
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['syndicate', 'template', 'created_by']
    
    fieldsets = (
        ('Syndicate and Template', {
            'fields': (
                'syndicate',
                'template',
            )
        }),
        ('Default Values', {
            'fields': (
                'default_values',
            ),
            'description': 'Default values for template configurable_fields[]. Format: {"field_name": "value", ...}'
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
