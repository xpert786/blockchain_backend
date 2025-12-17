from django.db import models
from users.models import CustomUser
from spv.models import SPV
from decimal import Decimal


# Create your models here.

class Portfolio(models.Model):
    """Model for investor portfolio tracking"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='portfolio')
    
    # Portfolio Summary
    total_invested = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total amount invested")
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Current portfolio value")
    unrealized_gain = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Unrealized gain/loss")
    realized_gain = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Realized gain/loss")
    
    # Statistics
    total_investments_count = models.IntegerField(default=0, help_text="Total number of investments")
    active_investments_count = models.IntegerField(default=0, help_text="Number of active investments")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated_at = models.DateTimeField(auto_now=True, help_text="Last time portfolio was recalculated")
    
    class Meta:
        verbose_name = 'portfolio'
        verbose_name_plural = 'portfolios'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - Portfolio"
    
    @property
    def portfolio_growth_percentage(self):
        """Calculate portfolio growth percentage"""
        if self.total_invested > 0:
            growth = ((self.current_value - self.total_invested) / self.total_invested) * 100
            return round(growth, 2)
        return 0.00
    
    def recalculate(self):
        """Recalculate portfolio values from investments"""
        from .models import Investment
        
        investments = Investment.objects.filter(investor=self.user, status='active')
        
        self.total_invested = sum(inv.invested_amount for inv in investments)
        self.current_value = sum(inv.current_value for inv in investments)
        self.unrealized_gain = self.current_value - self.total_invested
        self.total_investments_count = investments.count()
        self.active_investments_count = investments.filter(status='active').count()
        
        self.save()


class PortfolioPerformance(models.Model):
    """Model for tracking portfolio value over time for charts"""
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='performance_history')
    date = models.DateField(help_text="Date for this performance record")
    total_invested = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total invested as of this date")
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Portfolio value as of this date")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'portfolio performance'
        verbose_name_plural = 'portfolio performances'
        unique_together = ['portfolio', 'date']
        ordering = ['date']
    
    def __str__(self):
        return f"{self.portfolio.user.username} - {self.date}"


class Investment(models.Model):
    """Model for individual investments"""
    
    STATUS_CHOICES = [
        ('pending_approval', 'Pending Approval'),  # NEW: Investor requested, waiting for syndicate approval
        ('approved', 'Approved'),  # NEW: Syndicate approved, investor can pay
        ('rejected', 'Rejected'),  # NEW: Syndicate rejected the request
        ('pending_payment', 'Pending Payment'),  # Investment approved, waiting for payment
        ('payment_processing', 'Payment Processing'),  # Payment submitted, confirming with Stripe
        ('committed', 'Committed'),  # Payment received, funds secured
        ('pending', 'Pending'),  # Legacy: pending approval
        ('active', 'Active'),  # Investment is live
        ('completed', 'Completed'),  # Investment completed/exited
        ('expired', 'Expired'),  # Investment deadline passed
        ('cancelled', 'Cancelled'),  # Investor cancelled
        ('failed', 'Failed'),  # Payment failed
        ('refunded', 'Refunded'),  # Payment refunded
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    INVESTMENT_TYPE_CHOICES = [
        ('syndicate_deal', 'Syndicate Deal'),
        ('top_syndicate', 'Top Syndicate'),
        ('invite', 'Invite'),
    ]
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='investments')
    spv = models.ForeignKey(SPV, on_delete=models.CASCADE, related_name='investments', null=True, blank=True)
    
    # Payment Link
    payment = models.ForeignKey(
        'payments.Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investment_records',
        help_text="Associated payment record"
    )
    
    # Approval Fields (NEW)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_investments',
        help_text="Syndicate manager who approved/rejected"
    )
    approved_at = models.DateTimeField(blank=True, null=True, help_text="Date when approved/rejected")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection")
    request_message = models.TextField(blank=True, null=True, help_text="Investor's message with request")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Investment Details
    syndicate_name = models.CharField(max_length=255, help_text="Name of the syndicate/deal")
    sector = models.CharField(max_length=100, blank=True, null=True, help_text="Sector (e.g., Technology, Energy)")
    stage = models.CharField(max_length=50, blank=True, null=True, help_text="Investment stage (e.g., Seed, Series A)")
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPE_CHOICES, default='syndicate_deal')
    
    # Financial Details
    allocated = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Allocated amount")
    raised = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Amount raised")
    target = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Target amount")
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount invested by this investor")
    min_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Minimum investment amount")
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Current value of investment")
    
    # Ownership
    ownership_percentage = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=0,
        help_text="Percentage of SPV owned by this investor"
    )
    
    # Status and Timeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    deadline = models.DateField(blank=True, null=True, help_text="Investment deadline")
    days_left = models.IntegerField(default=0, help_text="Days remaining for investment")
    
    # Track Record
    track_record = models.CharField(max_length=50, blank=True, null=True, help_text="Track record percentage")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invested_at = models.DateTimeField(blank=True, null=True, help_text="Date when investment was made")
    commitment_date = models.DateTimeField(blank=True, null=True, help_text="Date when payment was confirmed")
    
    class Meta:
        verbose_name = 'investment'
        verbose_name_plural = 'investments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.investor.username} - {self.syndicate_name}"
    
    @property
    def is_active(self):
        """Check if investment is active"""
        return self.status == 'active'
    
    @property
    def is_payment_pending(self):
        """Check if awaiting payment"""
        return self.status == 'pending_payment'
    
    @property
    def gain_loss(self):
        """Calculate gain/loss for this investment"""
        if self.current_value is not None and self.invested_amount is not None:
            return self.current_value - self.invested_amount
        return 0.00
    
    @property
    def gain_loss_percentage(self):
        """Calculate gain/loss percentage"""
        if self.invested_amount and self.invested_amount > 0 and self.current_value is not None:
            return round(((self.current_value - self.invested_amount) / self.invested_amount) * 100, 2)
        return 0.00
    
    def calculate_ownership(self):
        """Calculate ownership percentage based on SPV allocation"""
        if self.spv and self.spv.allocation and self.spv.allocation > 0:
            self.ownership_percentage = (self.invested_amount / self.spv.allocation) * 100
            self.save(update_fields=['ownership_percentage'])



class Notification(models.Model):
    """Model for user notifications"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('investment', 'Investment'),
        ('document', 'Document'),
        ('transfer', 'Transfer'),
        ('system', 'System'),
    ]
    
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification Details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255, help_text="Notification title")
    message = models.TextField(help_text="Notification message")
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    action_required = models.BooleanField(default=False, help_text="Does this notification require user action?")
    action_url = models.CharField(max_length=500, blank=True, null=True, help_text="URL for action button")
    action_label = models.CharField(max_length=100, blank=True, null=True, help_text="Label for action button")
    
    # Related Objects
    related_investment = models.ForeignKey(Investment, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_spv = models.ForeignKey(SPV, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    
    # Metadata
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon name for notification")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata as JSON")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True, help_text="When notification was read")
    expires_at = models.DateTimeField(blank=True, null=True, help_text="When notification expires")
    
    class Meta:
        verbose_name = 'notification'
        verbose_name_plural = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.status = 'read'
        self.read_at = timezone.now()
        self.save()
    
    def mark_as_unread(self):
        """Mark notification as unread"""
        self.status = 'unread'
        self.read_at = None
        self.save()
    
    @property
    def is_unread(self):
        """Check if notification is unread"""
        return self.status == 'unread'
    
    @property
    def is_action_required(self):
        """Check if action is required"""
        return self.action_required and self.status == 'unread'


class KYCStatus(models.Model):
    """Model for tracking KYC status in dashboard"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='kyc_status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'KYC status'
        verbose_name_plural = 'KYC statuses'
    
    def __str__(self):
        return f"{self.user.username} - KYC: {self.status}"


class Wishlist(models.Model):
    """Model for investor wishlist - SPVs saved by investors"""
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='wishlist_items')
    spv = models.ForeignKey(SPV, on_delete=models.CASCADE, related_name='wishlisted_by')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'wishlist'
        verbose_name_plural = 'wishlists'
        ordering = ['-created_at']
        unique_together = ['investor', 'spv']  # Prevent duplicate entries
    
    def __str__(self):
        return f"{self.investor.username} - {self.spv.display_name}"


def tax_document_upload_path(instance, filename):
    """Generate upload path for tax documents"""
    return f'tax_documents/{instance.investor.id}/{instance.tax_year}/{filename}'


class TaxDocument(models.Model):
    """Model for investor tax documents (K-1, 1099-DIV, etc.)"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('k1', 'K-1'),
        ('1099_div', '1099-DIV'),
        ('1099_int', '1099-INT'),
        ('1099_b', '1099-B'),
        ('1099_misc', '1099-MISC'),
        ('w9', 'W-9'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('available', 'Available'),
        ('downloaded', 'Downloaded'),
    ]
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tax_documents')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='tax_documents', null=True, blank=True)
    
    # Document Details
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, help_text="Type of tax document")
    document_name = models.CharField(max_length=255, help_text="Document name/title")
    tax_year = models.IntegerField(help_text="Tax year (e.g., 2023)")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # File
    file = models.FileField(upload_to=tax_document_upload_path, null=True, blank=True, help_text="Tax document file")
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Dates
    issue_date = models.DateField(null=True, blank=True, help_text="Date when document was issued")
    expected_date = models.DateField(null=True, blank=True, help_text="Expected availability date if pending")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    downloaded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'tax document'
        verbose_name_plural = 'tax documents'
        ordering = ['-tax_year', '-issue_date']
        indexes = [
            models.Index(fields=['investor', 'tax_year']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.investor.username} - {self.get_document_type_display()} ({self.tax_year})"
    
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


class TaxSummary(models.Model):
    """Model for yearly tax summary for investors"""
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='tax_summaries')
    tax_year = models.IntegerField(help_text="Tax year (e.g., 2023)")
    
    # Income Breakdown
    dividend_income = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Dividend income")
    capital_gains = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Capital gains")
    interest_income = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Interest income")
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total income from investments")
    
    # Deductions Breakdown
    management_fees = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Management fees")
    professional_services = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Professional services (legal, accounting)")
    other_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Other investment expenses")
    total_deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Total deductions (investment expenses)")
    
    # Calculated fields
    net_taxable_income = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Net taxable income after deductions")
    estimated_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="Estimated tax liability")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'tax summary'
        verbose_name_plural = 'tax summaries'
        ordering = ['-tax_year']
        unique_together = ['investor', 'tax_year']
    
    def __str__(self):
        return f"{self.investor.username} - Tax Summary {self.tax_year}"
    
    def calculate_totals(self):
        """Calculate total income and deductions from breakdown"""
        self.total_income = self.dividend_income + self.capital_gains + self.interest_income
        self.total_deductions = self.management_fees + self.professional_services + self.other_expenses
        self.calculate()
    
    def calculate(self):
        """Calculate net taxable income and estimated tax"""
        self.net_taxable_income = self.total_income - self.total_deductions
        # Approximate 30% tax rate (this can be customized)
        self.estimated_tax = self.net_taxable_income * Decimal('0.30') if self.net_taxable_income > 0 else Decimal('0.00')
        self.save()


def investor_document_upload_path(instance, filename):
    """Generate upload path for investor documents"""
    return f'investor_documents/{instance.investor.id}/{instance.category}/{filename}'


class InvestorDocument(models.Model):
    """Model for investor documents in Document Center"""
    
    CATEGORY_CHOICES = [
        ('investment', 'Investment'),
        ('reports', 'Reports'),
        ('kyc', 'KYC'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='investor_documents')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='investor_documents', null=True, blank=True)
    
    # Document Details
    title = models.CharField(max_length=255, help_text="Document title/name")
    description = models.TextField(blank=True, null=True, help_text="Document description")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', help_text="Document category")
    
    # File
    file = models.FileField(upload_to=investor_document_upload_path, help_text="Document file")
    file_type = models.CharField(max_length=20, blank=True, null=True, help_text="File type (PDF, DOC, etc.)")
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related SPV/Fund
    spv = models.ForeignKey(SPV, on_delete=models.SET_NULL, null=True, blank=True, related_name='investor_documents', help_text="Related SPV/Fund")
    fund_name = models.CharField(max_length=255, blank=True, null=True, help_text="Related fund name")
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'investor document'
        verbose_name_plural = 'investor documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['investor', 'category']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.investor.username} - {self.title}"
    
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
    
    def save(self, *args, **kwargs):
        if self.file:
            # Extract file type from filename
            import os
            filename = os.path.basename(self.file.name)
            self.file_type = filename.split('.')[-1].upper() if '.' in filename else 'Unknown'
            # Get file size
            if hasattr(self.file, 'size'):
                self.file_size = self.file.size
        super().save(*args, **kwargs)