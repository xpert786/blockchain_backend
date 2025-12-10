from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


def transfer_document_upload_path(instance, filename):
    """Generate upload path for transfer documents"""
    return f'transfers/{instance.transfer.id}/documents/{filename}'


def request_document_upload_path(instance, filename):
    """Generate upload path for request documents"""
    return f'requests/{instance.request.id}/documents/{filename}'


class Transfer(models.Model):
    """Model for ownership transfer requests"""
    
    STATUS_CHOICES = [
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    REJECTION_REASON_CHOICES = [
        ('recipient_not_verified', 'Recipient is not a verified investor'),
        ('insufficient_funds', 'Insufficient funds'),
        ('invalid_documents', 'Invalid or missing documents'),
        ('compliance_issue', 'Compliance issue'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    transfer_id = models.CharField(max_length=50, unique=True, editable=False, help_text="Auto-generated transfer ID")
    
    # Participants
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_transfers',
        help_text="User requesting the transfer"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_transfers',
        help_text="User receiving the transfer"
    )
    
    # SPV and Investment Details
    spv = models.ForeignKey(
        'spv.SPV',
        on_delete=models.CASCADE,
        related_name='transfers',
        help_text="SPV associated with the transfer"
    )
    
    # Transfer Details
    shares = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of shares to transfer"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Transfer amount"
    )
    transfer_fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Transfer fee"
    )
    net_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Net amount after fees"
    )
    
    # Status and Workflow
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending_approval',
        help_text="Transfer status"
    )
    
    # Rejection Information
    rejection_reason = models.CharField(
        max_length=50,
        choices=REJECTION_REASON_CHOICES,
        blank=True,
        null=True,
        help_text="Reason for rejection"
    )
    rejection_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about rejection"
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_transfers',
        help_text="User who rejected the transfer"
    )
    rejected_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when rejected")
    
    # Approval Information
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_transfers',
        help_text="User who approved the transfer"
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when approved")
    
    # Completion Information
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when completed")
    
    # Additional Information
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description or notes about the transfer"
    )
    investor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Investor name (if different from requester)"
    )
    
    # Metadata
    requested_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when transfer was requested")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'transfer'
        verbose_name_plural = 'transfers'
        indexes = [
            models.Index(fields=['transfer_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.transfer_id} - {self.requester.username} to {self.recipient.username}"
    
    def save(self, *args, **kwargs):
        if not self.transfer_id:
            # Generate unique transfer ID
            self.transfer_id = f"TXN-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate net amount
        if self.amount and self.transfer_fee is not None:
            self.net_amount = self.amount - self.transfer_fee
        
        super().save(*args, **kwargs)
    
    @property
    def is_urgent(self):
        """Check if transfer is urgent (pending for more than 7 days)"""
        if self.status == 'pending_approval':
            from django.utils import timezone
            from datetime import timedelta
            return (timezone.now() - self.requested_at) > timedelta(days=7)
        return False


class TransferDocument(models.Model):
    """Model for transfer-related documents"""
    
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Transfer this document belongs to"
    )
    file = models.FileField(
        upload_to=transfer_document_upload_path,
        help_text="Document file"
    )
    original_filename = models.CharField(max_length=255, help_text="Original filename")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, help_text="MIME type of the file")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_transfer_documents',
        help_text="User who uploaded the document"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'transfer document'
        verbose_name_plural = 'transfer documents'
    
    def __str__(self):
        return f"{self.transfer.transfer_id} - {self.original_filename}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            import os
            self.original_filename = os.path.basename(self.file.name)
            if hasattr(self.file, 'size') and self.file.size:
                self.file_size = self.file.size
            if hasattr(self.file, 'content_type') and self.file.content_type:
                self.mime_type = self.file.content_type or 'application/octet-stream'
        super().save(*args, **kwargs)


class Request(models.Model):
    """Model for general approval requests and workflows"""
    
    REQUEST_TYPE_CHOICES = [
        ('spv_update', 'Update SPV Investment Terms'),
        ('contact_update', 'Update Contact Information'),
        ('document_approval', 'Document Approval'),
        ('kyc_update', 'KYC Update'),
        ('investment_change', 'Investment Change'),
        ('transfer_approval', 'Transfer Approval'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    request_id = models.CharField(max_length=50, unique=True, editable=False, help_text="Auto-generated request ID")
    request_type = models.CharField(
        max_length=50,
        choices=REQUEST_TYPE_CHOICES,
        help_text="Type of request"
    )
    title = models.CharField(max_length=255, help_text="Request title")
    description = models.TextField(help_text="Detailed description of the request")
    
    # Priority
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Request priority"
    )
    
    # Participants
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_requests',
        help_text="User who submitted the request"
    )
    
    # Related Entity (optional)
    related_entity = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Related entity reference (e.g., SPV-001, User ID)"
    )
    spv = models.ForeignKey(
        'spv.SPV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        help_text="Related SPV (if applicable)"
    )
    
    # Status and Workflow
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Request status"
    )
    
    # Approval Information
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_requests',
        help_text="User who approved the request"
    )
    approved_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when approved")
    approval_notes = models.TextField(blank=True, null=True, help_text="Notes about approval")
    
    # Rejection Information
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rejected_requests',
        help_text="User who rejected the request"
    )
    rejected_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when rejected")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, help_text="Date and time when request was created")
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True, help_text="Due date for request")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'request'
        verbose_name_plural = 'requests'
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.request_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            # Generate unique request ID
            prefix = self.request_type.upper()[:3] if self.request_type else 'REQ'
            self.request_id = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if request is overdue"""
        if self.status == 'pending' and self.due_date:
            from django.utils import timezone
            return timezone.now() > self.due_date
        return False
    
    @property
    def is_urgent_priority(self):
        """Check if request has high or urgent priority"""
        return self.priority in ['high', 'urgent']


class RequestDocument(models.Model):
    """Model for request-related documents"""
    
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Request this document belongs to"
    )
    file = models.FileField(
        upload_to=request_document_upload_path,
        help_text="Document file"
    )
    original_filename = models.CharField(max_length=255, help_text="Original filename")
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, help_text="MIME type of the file")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_request_documents',
        help_text="User who uploaded the document"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'request document'
        verbose_name_plural = 'request documents'
    
    def __str__(self):
        return f"{self.request.request_id} - {self.original_filename}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            import os
            self.original_filename = os.path.basename(self.file.name)
            if hasattr(self.file, 'size') and self.file.size:
                self.file_size = self.file.size
            if hasattr(self.file, 'content_type') and self.file.content_type:
                self.mime_type = self.file.content_type or 'application/octet-stream'
        super().save(*args, **kwargs)
