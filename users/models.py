from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

role_choices = (
    ('admin', 'Admin'),
    ('syndicate', 'Syndicate'),
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

# Choices for SyndicateProfile
ACCREDITED_CHOICES = [
    ('yes', 'I am an accredited investor'),
    ('no', 'I am not an accredited investor'),
]

LP_NETWORK_CHOICES = [
    ('0', 'No'),
    ('1-10', '1-10'),
    ('11-25', '11-25'),
    ('26-50', '26-50'),
    ('51-100', '51-100'),
    ('100+', '100+'),
]


class SyndicateProfile(models.Model):
    """Model for syndicate onboarding profile"""
    
    # Basic info
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='syndicate_profile')
    
    # Step 1: Lead Info
    is_accredited = models.CharField(max_length=3, choices=ACCREDITED_CHOICES, blank=True, null=True)
    understands_regulatory_requirements = models.BooleanField(default=False)
    sectors = models.ManyToManyField(Sector, blank=True, related_name='syndicate_profiles')
    geographies = models.ManyToManyField(Geography, blank=True, related_name='syndicate_profiles')
    existing_lp_count = models.CharField(max_length=10, choices=LP_NETWORK_CHOICES, blank=True, null=True)
    enable_platform_lp_access = models.BooleanField(default=False)
    
    # Step 2: Entity Profile
    firm_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='syndicate_logos/', blank=True, null=True)
    enable_role_based_access_controls = models.BooleanField(
        default=False, 
        help_text="When enabled, permissions will be automatically assigned based on team member roles and can be overridden individually"
    )
    
    # Step 3: Compliance & Attestation
    risk_regulatory_attestation = models.BooleanField(default=False)
    jurisdictional_compliance_acknowledged = models.BooleanField(default=False)
    additional_compliance_policies = models.FileField(upload_to='syndicate_compliance/', blank=True, null=True)
    
    # Step 4: Final Review & Submit
    application_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(blank=True, null=True)
    application_status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('under_review', 'Under Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='draft'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'syndicate profile'
        verbose_name_plural = 'syndicate profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.firm_name or 'Draft Profile'}"
    
    @property
    def step1_completed(self):
        """Check if Step 1 is completed"""
        return all([
            self.is_accredited,
            self.understands_regulatory_requirements,
            self.sectors.exists(),
            self.geographies.exists(),
            self.existing_lp_count
        ])
    
    @property
    def step2_completed(self):
        """Check if Step 2 is completed"""
        return all([
            self.firm_name,
            self.description
        ])
    
    @property
    def step3_completed(self):
        """Check if Step 3 is completed"""
        return all([
            self.risk_regulatory_attestation,
            self.jurisdictional_compliance_acknowledged
        ])
    
    @property
    def step4_completed(self):
        """Check if Step 4 is completed"""
        return self.application_submitted
    
    @property
    def current_step(self):
        """Determine current step"""
        if not self.step1_completed:
            return 1
        elif not self.step2_completed:
            return 2
        elif not self.step3_completed:
            return 3
        elif not self.step4_completed:
            return 4
        else:
            return 5  # Completed
            
class Syndicate(SyndicateProfile):
    class Meta:
        proxy = True
        verbose_name = 'syndicate'
        verbose_name_plural = 'syndicates'