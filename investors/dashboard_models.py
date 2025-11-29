from django.db import models
from users.models import CustomUser
from spv.models import SPV


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


class Investment(models.Model):
    """Model for individual investments"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    INVESTMENT_TYPE_CHOICES = [
        ('syndicate_deal', 'Syndicate Deal'),
        ('top_syndicate', 'Top Syndicate'),
        ('invite', 'Invite'),
    ]
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='investments')
    spv = models.ForeignKey(SPV, on_delete=models.CASCADE, related_name='investments', null=True, blank=True)
    
    # Investment Details
    syndicate_name = models.CharField(max_length=255, help_text="Name of the syndicate/deal")
    sector = models.CharField(max_length=100, blank=True, null=True, help_text="Sector (e.g., Technology, Energy)")
    stage = models.CharField(max_length=50, blank=True, null=True, help_text="Investment stage (e.g., Seed, Series A)")
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_TYPE_CHOICES, default='syndicate_deal')
    
    # Financial Details
    allocated = models.DecimalField(max_digits=15, decimal_places=2, help_text="Allocated amount")
    raised = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount raised")
    target = models.DecimalField(max_digits=15, decimal_places=2, help_text="Target amount")
    invested_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount invested by this investor")
    min_investment = models.DecimalField(max_digits=15, decimal_places=2, help_text="Minimum investment amount")
    current_value = models.DecimalField(max_digits=15, decimal_places=2, help_text="Current value of investment")
    
    # Status and Timeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    deadline = models.DateField(blank=True, null=True, help_text="Investment deadline")
    days_left = models.IntegerField(default=0, help_text="Days remaining for investment")
    
    # Track Record
    track_record = models.CharField(max_length=50, blank=True, null=True, help_text="Track record percentage")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    invested_at = models.DateTimeField(blank=True, null=True, help_text="Date when investment was made")
    
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