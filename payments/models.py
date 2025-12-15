from django.db import models
from django.conf import settings
import uuid


class SPVStripeAccount(models.Model):
    """
    Store Stripe Connect account details for SPVs.
    Each SPV that wants to receive investments needs a connected Stripe account.
    """
    
    ACCOUNT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('onboarding', 'Onboarding'),
        ('active', 'Active'),
        ('restricted', 'Restricted'),
        ('disabled', 'Disabled'),
    ]
    
    spv = models.OneToOneField(
        'spv.SPV',
        on_delete=models.CASCADE,
        related_name='stripe_account',
        help_text="SPV that owns this Stripe account"
    )
    
    # Stripe Account Details
    stripe_account_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stripe Connect account ID (acct_xxx)"
    )
    
    # Account Status
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default='pending',
        help_text="Current status of the Stripe account"
    )
    charges_enabled = models.BooleanField(
        default=False,
        help_text="Whether the account can accept charges"
    )
    payouts_enabled = models.BooleanField(
        default=False,
        help_text="Whether the account can receive payouts"
    )
    details_submitted = models.BooleanField(
        default=False,
        help_text="Whether all required details have been submitted"
    )
    
    # Onboarding
    onboarding_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL for completing Stripe Connect onboarding"
    )
    onboarding_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the onboarding link expires"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SPV Stripe Account'
        verbose_name_plural = 'SPV Stripe Accounts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.spv.display_name} - {self.stripe_account_id}"
    
    @property
    def is_ready_for_payments(self):
        """Check if account can receive payments"""
        return self.charges_enabled and self.details_submitted


class Payment(models.Model):
    """
    Track all investment payments made through Stripe.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('requires_action', 'Requires Action'),  # 3D Secure
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('ach', 'ACH Direct Debit'),
    ]
    
    # Unique Payment ID
    payment_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Auto-generated payment ID"
    )
    
    # Participants
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Investor making the payment"
    )
    spv = models.ForeignKey(
        'spv.SPV',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="SPV receiving the payment"
    )
    investment = models.ForeignKey(
        'investors.Investment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text="Related investment record"
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Payment amount"
    )
    currency = models.CharField(
        max_length=3,
        default='usd',
        help_text="Currency code (e.g., usd, eur)"
    )
    
    # Stripe Details
    stripe_payment_intent_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stripe PaymentIntent ID (pi_xxx)"
    )
    stripe_charge_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stripe Charge ID (ch_xxx)"
    )
    stripe_transfer_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stripe Transfer ID to connected account"
    )
    client_secret = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Client secret for frontend payment confirmation"
    )
    
    # Payment Method
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='card',
        help_text="Payment method used"
    )
    payment_method_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stripe PaymentMethod ID (pm_xxx)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Payment status"
    )
    
    # Fees
    platform_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Platform fee amount"
    )
    platform_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=2.0,
        help_text="Platform fee percentage"
    )
    stripe_fee = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Stripe processing fee"
    )
    net_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Net amount SPV receives after fees"
    )
    
    # Error Handling
    error_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stripe error code if payment failed"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if payment failed"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Payment description"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When payment was completed"
    )
    
    class Meta:
        verbose_name = 'payment'
        verbose_name_plural = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['status']),
            models.Index(fields=['investor', 'status']),
        ]
    
    def __str__(self):
        return f"{self.payment_id} - {self.investor.username} -> {self.spv.display_name}"
    
    def save(self, *args, **kwargs):
        if not self.payment_id:
            self.payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate fees if amount is set
        if self.amount and not self.net_amount:
            self.platform_fee = self.amount * (self.platform_fee_percentage / 100)
            self.net_amount = self.amount - self.platform_fee
        
        super().save(*args, **kwargs)


class PaymentWebhookEvent(models.Model):
    """
    Log all Stripe webhook events for debugging and auditing.
    """
    
    stripe_event_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stripe event ID (evt_xxx)"
    )
    event_type = models.CharField(
        max_length=100,
        help_text="Event type (e.g., payment_intent.succeeded)"
    )
    payload = models.JSONField(
        default=dict,
        help_text="Full event payload"
    )
    processed = models.BooleanField(
        default=False,
        help_text="Whether event has been processed"
    )
    error = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if processing failed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When event was processed"
    )
    
    class Meta:
        verbose_name = 'payment webhook event'
        verbose_name_plural = 'payment webhook events'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.stripe_event_id} - {self.event_type}"
