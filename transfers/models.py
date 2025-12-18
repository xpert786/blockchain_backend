from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


def transfer_document_upload_path(instance, filename):
    """Generate upload path for transfer documents"""
    return f'transfers/{instance.transfer.id}/documents/{filename}'


def request_document_upload_path(instance, filename):
    """Generate upload path for request documents"""
    return f'requests/{instance.request.id}/documents/{filename}'


def signed_document_upload_path(instance, filename):
    """Generate upload path for signed transfer documents"""
    return f'transfers/{instance.id}/signed/{filename}'


class Transfer(models.Model):
    """
    Model for ownership transfer requests.
    Supports both full and partial transfers with signature/confirmation workflow.
    
    Flow: draft → pending_requester_confirmation → pending_recipient_confirmation 
          → pending_approval → approved → completed
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_requester_confirmation', 'Pending Requester Confirmation'),
        ('pending_recipient_confirmation', 'Pending Recipient Confirmation'),
        ('recipient_declined', 'Recipient Declined'),
        ('pending_approval', 'Pending Manager Approval'),
        ('approved', 'Approved'),
        ('pending_esign', 'Pending E-Signatures'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    TRANSFER_TYPE_CHOICES = [
        ('full', 'Full Transfer'),
        ('partial', 'Partial Transfer'),
    ]
    
    REJECTION_REASON_CHOICES = [
        ('recipient_not_verified', 'Recipient is not a verified investor'),
        ('recipient_not_accredited', 'Recipient is not accredited'),
        ('recipient_declined', 'Recipient declined the transfer'),
        ('insufficient_ownership', 'Insufficient ownership to transfer'),
        ('lockup_period_active', 'Lock-up period is still active'),
        ('jurisdiction_restriction', 'Jurisdiction restriction'),
        ('invalid_documents', 'Invalid or missing documents'),
        ('compliance_issue', 'Compliance issue'),
        ('other', 'Other'),
    ]
    
    ESIGN_STATUS_CHOICES = [
        ('not_required', 'Not Required'),
        ('pending', 'Pending Signatures'),
        ('requester_signed', 'Requester Signed'),
        ('recipient_signed', 'Recipient Signed'),
        ('all_signed', 'All Parties Signed'),
        ('expired', 'Signature Request Expired'),
    ]
    
    # ==========================================
    # BASIC INFORMATION
    # ==========================================
    transfer_id = models.CharField(
        max_length=50, 
        unique=True, 
        editable=False, 
        help_text="Auto-generated transfer ID (e.g., TXN-ABC123)"
    )
    
    # Transfer Type
    transfer_type = models.CharField(
        max_length=10,
        choices=TRANSFER_TYPE_CHOICES,
        default='full',
        help_text="Full transfer or partial transfer"
    )
    
    # ==========================================
    # PARTICIPANTS
    # ==========================================
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_transfers',
        help_text="User requesting the transfer (seller/current owner)"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_transfers',
        help_text="User receiving the transfer (buyer/new owner)"
    )
    recipient_email = models.EmailField(
        blank=True, null=True,
        help_text="Recipient email (used if recipient user not yet identified)"
    )
    
    # ==========================================
    # SPV AND INVESTMENT DETAILS
    # ==========================================
    spv = models.ForeignKey(
        'spv.SPV',
        on_delete=models.CASCADE,
        related_name='transfers',
        help_text="SPV associated with the transfer"
    )
    
    # Source Investment (requester's current investment)
    source_investment = models.ForeignKey(
        'investors.Investment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='outgoing_transfers',
        help_text="Requester's investment record being transferred from"
    )
    
    # Destination Investment (created/updated for recipient)
    destination_investment = models.ForeignKey(
        'investors.Investment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incoming_transfers',
        help_text="Recipient's investment record receiving the transfer"
    )
    
    # ==========================================
    # TRANSFER DETAILS
    # ==========================================
    shares = models.IntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Number of shares/units to transfer"
    )
    
    # Ownership percentage being transferred
    ownership_percentage_transferred = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Percentage of SPV ownership being transferred"
    )
    
    # Before transfer ownership (for audit)
    requester_ownership_before = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Requester's ownership % before transfer"
    )
    recipient_ownership_before = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Recipient's ownership % before transfer (0 if new)"
    )
    
    # After transfer ownership (filled after completion)
    requester_ownership_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Requester's ownership % after transfer"
    )
    recipient_ownership_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Recipient's ownership % after transfer"
    )
    
    # Financial Details
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Transfer amount (value of ownership being transferred)"
    )
    transfer_fee = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Platform transfer fee"
    )
    transfer_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Transfer fee percentage applied"
    )
    net_amount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Net amount after fees (received by seller)"
    )
    
    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current transfer status"
    )
    
    # ==========================================
    # REQUESTER (SELLER) CONFIRMATIONS
    # ==========================================
    requester_confirmed = models.BooleanField(
        default=False,
        help_text="Requester confirmed the transfer initiation"
    )
    requester_confirmed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When requester confirmed"
    )
    requester_ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP address of requester at confirmation"
    )
    requester_user_agent = models.TextField(
        blank=True, null=True,
        help_text="Browser/device info at confirmation"
    )
    requester_terms_accepted = models.BooleanField(
        default=False,
        help_text="Requester accepted transfer terms & conditions"
    )
    requester_ownership_acknowledged = models.BooleanField(
        default=False,
        help_text="Requester acknowledged giving up ownership"
    )
    requester_confirmation_message = models.TextField(
        blank=True, null=True,
        help_text="Optional message from requester to recipient"
    )
    
    # ==========================================
    # RECIPIENT (BUYER) CONFIRMATIONS
    # ==========================================
    recipient_confirmed = models.BooleanField(
        default=False,
        help_text="Recipient accepted the transfer"
    )
    recipient_confirmed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When recipient accepted"
    )
    recipient_ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP address of recipient at confirmation"
    )
    recipient_user_agent = models.TextField(
        blank=True, null=True,
        help_text="Browser/device info at confirmation"
    )
    recipient_terms_accepted = models.BooleanField(
        default=False,
        help_text="Recipient accepted transfer terms & conditions"
    )
    recipient_ownership_acknowledged = models.BooleanField(
        default=False,
        help_text="Recipient acknowledged receiving ownership"
    )
    recipient_decline_reason = models.TextField(
        blank=True, null=True,
        help_text="Reason if recipient declined"
    )
    
    # ==========================================
    # MANAGER/ADMIN APPROVAL
    # ==========================================
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_transfers',
        help_text="Manager/Admin who approved the transfer"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True, 
        help_text="Date and time when approved"
    )
    approver_compliance_verified = models.BooleanField(
        default=False,
        help_text="Approver verified compliance requirements"
    )
    approver_kyc_verified = models.BooleanField(
        default=False,
        help_text="Approver verified recipient's KYC status"
    )
    approver_lockup_verified = models.BooleanField(
        default=False,
        help_text="Approver verified no lock-up period violations"
    )
    approver_jurisdiction_verified = models.BooleanField(
        default=False,
        help_text="Approver verified jurisdiction requirements"
    )
    approval_notes = models.TextField(
        blank=True, null=True,
        help_text="Notes from approver"
    )
    
    # ==========================================
    # REJECTION INFORMATION
    # ==========================================
    rejection_reason = models.CharField(
        max_length=50,
        choices=REJECTION_REASON_CHOICES,
        blank=True, null=True,
        help_text="Reason for rejection"
    )
    rejection_notes = models.TextField(
        blank=True, null=True,
        help_text="Additional notes about rejection"
    )
    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='rejected_transfers',
        help_text="User who rejected the transfer"
    )
    rejected_at = models.DateTimeField(
        null=True, blank=True, 
        help_text="Date and time when rejected"
    )
    
    # ==========================================
    # COMPLETION INFORMATION
    # ==========================================
    completed_at = models.DateTimeField(
        null=True, blank=True, 
        help_text="Date and time when transfer completed"
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='completed_transfers',
        help_text="User who completed/executed the transfer"
    )
    
    # ==========================================
    # E-SIGNATURE FIELDS (Future Integration)
    # ==========================================
    esign_required = models.BooleanField(
        default=False,
        help_text="Is e-signature required for this transfer?"
    )
    esign_status = models.CharField(
        max_length=20,
        choices=ESIGN_STATUS_CHOICES,
        default='not_required',
        help_text="E-signature status"
    )
    esign_provider = models.CharField(
        max_length=50,
        blank=True, null=True,
        help_text="E-sign provider (DocuSign, HelloSign, etc.)"
    )
    esign_envelope_id = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text="DocuSign/HelloSign envelope ID"
    )
    esign_document_url = models.URLField(
        blank=True, null=True,
        help_text="URL to signed document"
    )
    requester_esign_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When requester e-signed"
    )
    recipient_esign_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When recipient e-signed"
    )
    signed_document = models.FileField(
        upload_to=signed_document_upload_path,
        blank=True, null=True,
        help_text="Final signed transfer agreement document"
    )
    
    # ==========================================
    # ADDITIONAL INFORMATION
    # ==========================================
    description = models.TextField(
        blank=True, null=True,
        help_text="Description or notes about the transfer"
    )
    investor_name = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text="Investor name (if different from requester)"
    )
    
    # ==========================================
    # METADATA
    # ==========================================
    requested_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date and time when transfer was requested"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'transfer'
        verbose_name_plural = 'transfers'
        indexes = [
            models.Index(fields=['transfer_id']),
            models.Index(fields=['status']),
            models.Index(fields=['transfer_type']),
            models.Index(fields=['-requested_at']),
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['recipient', 'status']),
        ]
    
    def __str__(self):
        return f"{self.transfer_id} - {self.requester.username} to {self.recipient.username} ({self.transfer_type})"
    
    def save(self, *args, **kwargs):
        if not self.transfer_id:
            # Generate unique transfer ID
            self.transfer_id = f"TXN-{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate net amount
        if self.amount:
            if self.transfer_fee is None:
                self.transfer_fee = Decimal('0')
            self.net_amount = self.amount - self.transfer_fee
        
        super().save(*args, **kwargs)
    
    @property
    def is_urgent(self):
        """Check if transfer is urgent (pending for more than 7 days)"""
        if self.status in ['pending_approval', 'pending_recipient_confirmation']:
            from django.utils import timezone
            from datetime import timedelta
            return (timezone.now() - self.requested_at) > timedelta(days=7)
        return False
    
    @property
    def is_full_transfer(self):
        """Check if this is a full ownership transfer"""
        return self.transfer_type == 'full'
    
    @property
    def is_partial_transfer(self):
        """Check if this is a partial ownership transfer"""
        return self.transfer_type == 'partial'
    
    @property
    def all_confirmations_received(self):
        """Check if both parties have confirmed"""
        return self.requester_confirmed and self.recipient_confirmed
    
    @property
    def ready_for_approval(self):
        """Check if transfer is ready for manager approval"""
        return (
            self.status == 'pending_approval' and
            self.requester_confirmed and
            self.recipient_confirmed
        )
    
    @property
    def can_complete(self):
        """Check if transfer can be completed"""
        return self.status == 'approved'


class TransferHistory(models.Model):
    """
    Model for tracking ownership transfer history (Audit Trail).
    Every transfer creates a history record for compliance and tracking.
    """
    
    ACTION_CHOICES = [
        ('initiated', 'Transfer Initiated'),
        ('requester_confirmed', 'Requester Confirmed'),
        ('recipient_accepted', 'Recipient Accepted'),
        ('recipient_declined', 'Recipient Declined'),
        ('submitted_for_approval', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('ownership_updated', 'Ownership Updated'),
    ]
    
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="Transfer this history belongs to"
    )
    
    # Action Details
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        help_text="Action performed"
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfer_actions',
        help_text="User who performed the action"
    )
    action_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When action was performed"
    )
    
    # Ownership Snapshot
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfer_from_history',
        help_text="User transferring ownership"
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transfer_to_history',
        help_text="User receiving ownership"
    )
    
    # Ownership Details at time of action
    percentage_transferred = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Ownership percentage transferred"
    )
    amount_transferred = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Amount transferred"
    )
    
    # Before/After snapshot
    from_user_ownership_before = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0
    )
    from_user_ownership_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0
    )
    to_user_ownership_before = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0
    )
    to_user_ownership_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0
    )
    
    # Additional Info
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP address at time of action"
    )
    user_agent = models.TextField(
        blank=True, null=True,
        help_text="Browser/device info"
    )
    notes = models.TextField(
        blank=True, null=True,
        help_text="Additional notes"
    )
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text="Additional metadata as JSON"
    )
    
    class Meta:
        ordering = ['-action_at']
        verbose_name = 'transfer history'
        verbose_name_plural = 'transfer histories'
        indexes = [
            models.Index(fields=['transfer', '-action_at']),
            models.Index(fields=['action']),
        ]
    
    def __str__(self):
        return f"{self.transfer.transfer_id} - {self.get_action_display()}"


class OwnershipLedger(models.Model):
    """
    Model for tracking complete ownership history per investor per SPV.
    Acts as a ledger/cap table entry.
    """
    
    ENTRY_TYPE_CHOICES = [
        ('initial_investment', 'Initial Investment'),
        ('additional_investment', 'Additional Investment'),
        ('transfer_in', 'Transfer In (Received)'),
        ('transfer_out', 'Transfer Out (Sent)'),
        ('adjustment', 'Adjustment'),
        ('distribution', 'Distribution'),
    ]
    
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ownership_ledger',
        help_text="Investor"
    )
    spv = models.ForeignKey(
        'spv.SPV',
        on_delete=models.CASCADE,
        related_name='ownership_ledger',
        help_text="SPV"
    )
    
    # Entry Details
    entry_type = models.CharField(
        max_length=30,
        choices=ENTRY_TYPE_CHOICES,
        help_text="Type of ledger entry"
    )
    
    # Related Records
    investment = models.ForeignKey(
        'investors.Investment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ledger_entries',
        help_text="Related investment record"
    )
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ledger_entries',
        help_text="Related transfer record"
    )
    
    # Ownership Change
    ownership_change = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="Change in ownership % (+ve for increase, -ve for decrease)"
    )
    ownership_before = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Ownership % before this entry"
    )
    ownership_after = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        help_text="Ownership % after this entry"
    )
    
    # Amount Change
    amount_change = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        help_text="Change in amount (+ve for increase, -ve for decrease)"
    )
    amount_before = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Investment amount before this entry"
    )
    amount_after = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        help_text="Investment amount after this entry"
    )
    
    # Metadata
    notes = models.TextField(
        blank=True, null=True,
        help_text="Notes about this entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_ledger_entries',
        help_text="User who created this entry"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ownership ledger'
        verbose_name_plural = 'ownership ledgers'
        indexes = [
            models.Index(fields=['investor', 'spv']),
            models.Index(fields=['spv', '-created_at']),
            models.Index(fields=['entry_type']),
        ]
    
    def __str__(self):
        return f"{self.investor.username} - {self.spv.display_name} - {self.get_entry_type_display()}"


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


def agreement_document_upload_path(instance, filename):
    """Generate upload path for transfer agreement documents"""
    return f'transfers/{instance.transfer.id}/agreements/{filename}'


class TransferAgreementDocument(models.Model):
    """
    Model for transfer agreement documents with signatures.
    
    Document Types:
    1. transfer_request - Generated when Investor A confirms (Investor A's signature)
    2. acceptance - Generated when Investor B accepts (Investor B's signature)
    3. final_agreement - Generated when both sign (Both signatures)
    """
    
    DOCUMENT_TYPE_CHOICES = [
        ('transfer_request', 'Transfer Request Document'),
        ('acceptance', 'Acceptance Document'),
        ('final_agreement', 'Final Transfer Agreement'),
    ]
    
    SIGNATURE_STATUS_CHOICES = [
        ('pending', 'Pending Signature'),
        ('signed', 'Signed'),
        ('rejected', 'Rejected'),
    ]
    
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.CASCADE,
        related_name='agreement_documents',
        help_text="Transfer this agreement belongs to"
    )
    
    # Document Type
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Type of agreement document"
    )
    
    # Document Details
    document_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique document number (e.g., DOC-TXN-ABC123-001)"
    )
    title = models.CharField(
        max_length=255,
        help_text="Document title"
    )
    description = models.TextField(
        blank=True, null=True,
        help_text="Document description"
    )
    
    # Generated PDF
    file = models.FileField(
        upload_to=agreement_document_upload_path,
        help_text="Generated PDF document"
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text="File size in bytes"
    )
    
    # Investor A (Requester/Seller) Signature
    requester_signature_status = models.CharField(
        max_length=20,
        choices=SIGNATURE_STATUS_CHOICES,
        default='pending'
    )
    requester_signed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When Investor A signed"
    )
    requester_signature_ip = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP address when Investor A signed"
    )
    requester_signature_data = models.TextField(
        blank=True, null=True,
        help_text="Signature data (base64 or text)"
    )
    
    # Investor B (Recipient/Buyer) Signature
    recipient_signature_status = models.CharField(
        max_length=20,
        choices=SIGNATURE_STATUS_CHOICES,
        default='pending'
    )
    recipient_signed_at = models.DateTimeField(
        null=True, blank=True,
        help_text="When Investor B signed"
    )
    recipient_signature_ip = models.GenericIPAddressField(
        null=True, blank=True,
        help_text="IP address when Investor B signed"
    )
    recipient_signature_data = models.TextField(
        blank=True, null=True,
        help_text="Signature data (base64 or text)"
    )
    
    # Document Content (JSON for template rendering)
    document_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Document content data for PDF generation"
    )
    
    # Version Control
    version = models.IntegerField(
        default=1,
        help_text="Document version"
    )
    is_latest = models.BooleanField(
        default=True,
        help_text="Is this the latest version"
    )
    
    # Access Control
    can_requester_view = models.BooleanField(
        default=True,
        help_text="Can Investor A view this document"
    )
    can_recipient_view = models.BooleanField(
        default=True,
        help_text="Can Investor B view this document"
    )
    can_requester_download = models.BooleanField(
        default=True,
        help_text="Can Investor A download this document"
    )
    can_recipient_download = models.BooleanField(
        default=True,
        help_text="Can Investor B download this document"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'transfer agreement document'
        verbose_name_plural = 'transfer agreement documents'
        indexes = [
            models.Index(fields=['transfer', 'document_type']),
            models.Index(fields=['document_number']),
            models.Index(fields=['document_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        if not self.document_number:
            # Generate unique document number
            doc_type_prefix = {
                'transfer_request': 'REQ',
                'acceptance': 'ACC',
                'final_agreement': 'AGR',
            }.get(self.document_type, 'DOC')
            self.document_number = f"{doc_type_prefix}-{self.transfer.transfer_id}-{uuid.uuid4().hex[:4].upper()}"
        
        # Update file size
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)
    
    @property
    def is_fully_signed(self):
        """Check if document is signed by all required parties"""
        if self.document_type == 'transfer_request':
            return self.requester_signature_status == 'signed'
        elif self.document_type == 'acceptance':
            return self.recipient_signature_status == 'signed'
        elif self.document_type == 'final_agreement':
            return (self.requester_signature_status == 'signed' and 
                    self.recipient_signature_status == 'signed')
        return False
    
    @property
    def file_size_display(self):
        """Get file size in human readable format"""
        if not self.file_size:
            return "N/A"
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
