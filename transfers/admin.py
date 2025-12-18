from django.contrib import admin
from django.utils.html import format_html
from .models import Transfer, TransferDocument, TransferAgreementDocument, TransferHistory, OwnershipLedger


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        'transfer_id',
        'requester',
        'recipient',
        'spv',
        'shares',
        'amount',
        'net_amount',
        'status',
        'requested_at',
    )
    list_filter = (
        'status',
        'requested_at',
        'approved_at',
        'completed_at',
        'rejected_at',
    )
    search_fields = (
        'transfer_id',
        'requester__username',
        'requester__email',
        'recipient__username',
        'recipient__email',
        'spv__display_name',
        'description',
    )
    readonly_fields = (
        'transfer_id',
        'net_amount',
        'requested_at',
        'updated_at',
        'approved_at',
        'rejected_at',
        'completed_at',
        'documents_count_display',
    )
    autocomplete_fields = ['requester', 'recipient', 'spv', 'approved_by', 'rejected_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'transfer_id',
                'requester',
                'recipient',
                'spv',
            )
        }),
        ('Transfer Details', {
            'fields': (
                'shares',
                'amount',
                'transfer_fee',
                'net_amount',
            )
        }),
        ('Status and Workflow', {
            'fields': (
                'status',
                'approved_by',
                'approved_at',
                'rejected_by',
                'rejected_at',
                'rejection_reason',
                'rejection_notes',
                'completed_at',
            )
        }),
        ('Additional Information', {
            'fields': (
                'description',
                'investor_name',
            )
        }),
        ('Documents', {
            'fields': ('documents_count_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'requested_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_approved',
        'mark_completed',
        'mark_rejected',
    ]
    
    def documents_count_display(self, obj):
        """Display documents count"""
        return obj.documents.count()
    documents_count_display.short_description = 'Documents'
    
    def mark_approved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending_approval').update(
            status='approved',
            approved_by=request.user,
            approved_at=timezone.now()
        )
        self.message_user(request, f'{updated} transfer(s) marked as approved.')
    mark_approved.short_description = 'Mark selected as approved'
    
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='approved').update(
            status='completed',
            completed_at=timezone.now()
        )
        self.message_user(request, f'{updated} transfer(s) marked as completed.')
    mark_completed.short_description = 'Mark selected as completed'
    
    def mark_rejected(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending_approval').update(
            status='rejected',
            rejected_by=request.user,
            rejected_at=timezone.now()
        )
        self.message_user(request, f'{updated} transfer(s) marked as rejected.')
    mark_rejected.short_description = 'Mark selected as rejected'


@admin.register(TransferDocument)
class TransferDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'transfer',
        'original_filename',
        'file_size_display',
        'uploaded_by',
        'uploaded_at',
    )
    list_filter = (
        'uploaded_at',
    )
    search_fields = (
        'transfer__transfer_id',
        'original_filename',
        'uploaded_by__username',
        'uploaded_by__email',
    )
    readonly_fields = ('file_size', 'mime_type', 'uploaded_at')
    autocomplete_fields = ['transfer', 'uploaded_by']
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'transfer',
                'file',
                'original_filename',
                'file_size',
                'mime_type',
            )
        }),
        ('Metadata', {
            'fields': (
                'uploaded_by',
                'uploaded_at',
            )
        }),
    )
    
    def file_size_display(self, obj):
        """Display file size in MB"""
        if obj.file_size:
            size_mb = obj.file_size / (1024 * 1024)
            return f"{size_mb:.2f} MB"
        return "-"
    file_size_display.short_description = 'File Size'


@admin.register(TransferAgreementDocument)
class TransferAgreementDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'document_number',
        'transfer',
        'document_type',
        'title',
        'requester_signature_status',
        'recipient_signature_status',
        'is_fully_signed_display',
        'created_at',
    )
    list_filter = (
        'document_type',
        'requester_signature_status',
        'recipient_signature_status',
        'is_latest',
        'created_at',
    )
    search_fields = (
        'document_number',
        'title',
        'transfer__transfer_id',
        'transfer__requester__username',
        'transfer__requester__email',
        'transfer__recipient__username',
        'transfer__recipient__email',
    )
    readonly_fields = (
        'document_number',
        'file_size',
        'requester_signed_at',
        'requester_signature_ip',
        'recipient_signed_at',
        'recipient_signature_ip',
        'created_at',
        'updated_at',
        'is_fully_signed_display',
        'file_size_display',
    )
    autocomplete_fields = ['transfer']
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'transfer',
                'document_type',
                'document_number',
                'title',
                'description',
            )
        }),
        ('File', {
            'fields': (
                'file',
                'file_size',
                'file_size_display',
            )
        }),
        ('Requester (Investor A) Signature', {
            'fields': (
                'requester_signature_status',
                'requester_signed_at',
                'requester_signature_ip',
                'requester_signature_data',
            )
        }),
        ('Recipient (Investor B) Signature', {
            'fields': (
                'recipient_signature_status',
                'recipient_signed_at',
                'recipient_signature_ip',
                'recipient_signature_data',
            )
        }),
        ('Document Data', {
            'fields': ('document_data',),
            'classes': ('collapse',)
        }),
        ('Version & Access Control', {
            'fields': (
                'version',
                'is_latest',
                'can_requester_view',
                'can_recipient_view',
                'can_requester_download',
                'can_recipient_download',
            )
        }),
        ('Status', {
            'fields': ('is_fully_signed_display',),
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def is_fully_signed_display(self, obj):
        """Display if document is fully signed with colored icon"""
        if obj.is_fully_signed:
            return format_html('<span style="color: green;">✅ Fully Signed</span>')
        return format_html('<span style="color: orange;">⏳ Pending Signatures</span>')
    is_fully_signed_display.short_description = 'Signature Status'
    
    def file_size_display(self, obj):
        """Display file size in human readable format"""
        return obj.file_size_display
    file_size_display.short_description = 'File Size'


@admin.register(TransferHistory)
class TransferHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'transfer',
        'action',
        'action_by',
        'action_at',
        'percentage_transferred',
        'amount_transferred',
    )
    list_filter = (
        'action',
        'action_at',
    )
    search_fields = (
        'transfer__transfer_id',
        'action_by__username',
        'action_by__email',
        'notes',
    )
    readonly_fields = (
        'action_at',
        'ip_address',
        'user_agent',
    )
    autocomplete_fields = ['transfer', 'action_by', 'from_user', 'to_user']
    
    fieldsets = (
        ('Transfer', {
            'fields': ('transfer',)
        }),
        ('Action Details', {
            'fields': (
                'action',
                'action_by',
                'action_at',
            )
        }),
        ('Parties', {
            'fields': (
                'from_user',
                'to_user',
            )
        }),
        ('Transfer Details', {
            'fields': (
                'percentage_transferred',
                'amount_transferred',
            )
        }),
        ('Ownership Snapshot', {
            'fields': (
                'from_user_ownership_before',
                'from_user_ownership_after',
                'to_user_ownership_before',
                'to_user_ownership_after',
            )
        }),
        ('Additional Info', {
            'fields': (
                'ip_address',
                'user_agent',
                'notes',
                'metadata',
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(OwnershipLedger)
class OwnershipLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'investor',
        'spv',
        'entry_type',
        'ownership_change',
        'ownership_after',
        'amount_change',
        'created_at',
    )
    list_filter = (
        'entry_type',
        'created_at',
    )
    search_fields = (
        'investor__username',
        'investor__email',
        'spv__display_name',
        'notes',
    )
    readonly_fields = ('created_at',)
    autocomplete_fields = ['investor', 'spv', 'investment', 'transfer', 'created_by']
    
    fieldsets = (
        ('Investor & SPV', {
            'fields': (
                'investor',
                'spv',
            )
        }),
        ('Entry Details', {
            'fields': (
                'entry_type',
                'investment',
                'transfer',
            )
        }),
        ('Ownership Change', {
            'fields': (
                'ownership_change',
                'ownership_before',
                'ownership_after',
            )
        }),
        ('Amount Change', {
            'fields': (
                'amount_change',
                'amount_before',
                'amount_after',
            )
        }),
        ('Metadata', {
            'fields': (
                'notes',
                'created_at',
                'created_by',
            )
        }),
    )
