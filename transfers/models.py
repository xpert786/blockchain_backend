from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid


def transfer_document_upload_path(instance, filename):
    """Generate upload path for transfer documents"""
    return f'transfers/{instance.transfer.id}/documents/{filename}'


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
