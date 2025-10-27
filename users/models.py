from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

role_choices = (
    ('admin', 'Admin'),
    ('syndicate_manager', 'Syndicate Manager'),
    ('investor', 'Investor'),
)

class CustomUser(AbstractUser):
    role = models.CharField(max_length=50, choices=role_choices, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Two-Factor Authentication fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_method = models.CharField(
        max_length=20, 
        choices=[
            ('sms', 'SMS'),
            ('email', 'Email'),
        ],
        default='sms',
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'sector'
        verbose_name_plural = 'sectors'
    
    def __str__(self):
        return self.name

class Geography(models.Model):
    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=50, blank=True, null=True)  # e.g., "North America", "Europe"
    country_code = models.CharField(max_length=3, blank=True, null=True)  # ISO country code
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['region', 'name']
        verbose_name = 'geography'
        verbose_name_plural = 'geographies'
    
    def __str__(self):
        return f"{self.name} ({self.region})" if self.region else self.name


class EmailVerification(models.Model):
    """Model for email verification codes"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_verifications')
    email = models.EmailField()
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'email verification'
        verbose_name_plural = 'email verifications'
    
    def __str__(self):
        return f"{self.email} - {self.code}"


class TwoFactorAuth(models.Model):
    """Model for two-factor authentication"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='two_factor_auths')
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'two factor authentication'
        verbose_name_plural = 'two factor authentications'
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"


class TermsAcceptance(models.Model):
    """Model for tracking terms of service acceptance"""
    TERMS_CHOICES = [
        ('general_terms', 'General Terms of Services'),
        ('investing_banking_terms', 'Investing Banking Terms'),
        ('e_sign_consent', 'E-Sign Consent'),
        ('infrafi_deposit', 'InfraFi Deposit Placement and Custodial Agreement'),
        ('cookie_consent', 'Cookie Consent Preferences'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='terms_acceptances')
    terms_type = models.CharField(max_length=50, choices=TERMS_CHOICES)
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'terms acceptance'
        verbose_name_plural = 'terms acceptances'
        unique_together = ['user', 'terms_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_terms_type_display()}"

class Syndicate(models.Model):
    ACREDITED_CHOICES = (
    ('Yes', 'Yes'),
    ('No', 'No'),
)
    LP_CHOICES = (
    ('Yes', 'Yes'),
    ('No', 'No'),
)
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # The user who manages the syndicate
    description = models.TextField(blank=True, null=True)
    accredited = models.CharField(max_length=3, choices=ACREDITED_CHOICES, blank=True, null=True)   
    sectors = models.ManyToManyField(Sector, blank=True, related_name='syndicates')
    geographies = models.ManyToManyField(Geography, blank=True, related_name='syndicates')
    lp_network = models.TextField(blank=True, null=True)
    enable_lp_network = models.CharField(max_length=3, choices=LP_CHOICES, blank=True, null=True) 
    firm_name = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='syndicate_logos/', blank=True, null=True)
    team_member = models.TextField(blank=True, null=True)
    Risk_Regulatory_Attestation = models.TextField(blank=True, null=True)
    jurisdictional_requirements = models.TextField(blank=True, null=True)
    additional_compliance_policies = models.TextField(blank=True, null=True)
    time_of_register = models.DateTimeField(auto_now_add=True, verbose_name="Registration Time")
    
    class Meta:
        verbose_name = 'syndicate'
        verbose_name_plural = 'syndicates'

    def __str__(self):
        return self.name


# Import document models at the end to avoid circular imports
from .syndicate_document_models import SyndicateDocument, SyndicateTeamMember, SyndicateBeneficiary, SyndicateCompliance
from .syndicate_image_models import SyndicateImage