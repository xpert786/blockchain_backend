from django.contrib import admin
from django.utils.html import format_html
from .models import Transfer, TransferDocument


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
