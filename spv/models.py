from django.db import models
from users.models import CustomUser


class CompanyStage(models.Model):
    """Model for company funding stages"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Order for display in dropdown")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'company stage'
        verbose_name_plural = 'company stages'
    
    def __str__(self):
        return self.name


class IncorporationType(models.Model):
    """Model for company incorporation types"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'incorporation type'
        verbose_name_plural = 'incorporation types'
    
    def __str__(self):
        return self.name


class PortfolioCompany(models.Model):
    """Model for portfolio companies"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'portfolio company'
        verbose_name_plural = 'portfolio companies'
    
    def __str__(self):
        return self.name


class SPV(models.Model):
    """Model for Special Purpose Vehicle (SPV) deals"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_spvs')
    display_name = models.CharField(max_length=255, help_text="Display name for SPV")
    
    # Portfolio Company Information
    portfolio_company = models.ForeignKey(
        PortfolioCompany, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='spvs'
    )
    portfolio_company_name = models.CharField(
        max_length=255, 
        help_text="Portfolio company name (if not in database)"
    )
    
    # Company Details
    company_stage = models.ForeignKey(
        CompanyStage, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='spvs'
    )
    country_of_incorporation = models.CharField(max_length=100, blank=True, null=True)
    incorporation_type = models.ForeignKey(
        IncorporationType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='spvs'
    )
    
    # Contact Information
    founder_email = models.EmailField(help_text="Founder email for deal validation")
    
    # Documents
    pitch_deck = models.FileField(
        upload_to='spv/pitch_decks/', 
        blank=True, 
        null=True,
        help_text="Upload pitch deck (PDF, PPT, PPTX)"
    )
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SPV'
        verbose_name_plural = 'SPVs'
    
    def __str__(self):
        return f"{self.display_name} - {self.get_status_display()}"
    
    @property
    def company_name(self):
        """Return portfolio company name"""
        if self.portfolio_company:
            return self.portfolio_company.name
        return self.portfolio_company_name
