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
    
    # Notification Preferences
    notification_preference = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email Preference'),
            ('lp_alerts', 'New LP Alerts'),
            ('deal_updates', 'Deal Status Updates'),
        ],
        default='email',
        blank=True,
        null=True,
        help_text="Primary notification preference"
    )
    notify_new_lp_alerts = models.BooleanField(default=True, help_text="Receive alerts for new LP activities")
    notify_deal_updates = models.BooleanField(default=True, help_text="Receive updates on deal status changes")
    notify_email_preference = models.BooleanField(default=True, help_text="Receive email notifications")
    
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


class PasswordReset(models.Model):
    """Model for password reset OTP codes"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_resets')
    email = models.EmailField()
    otp = models.CharField(max_length=4)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = 'password reset'
        verbose_name_plural = 'password resets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and not self.is_verified and timezone.now() < self.expires_at


class TwoFactorAuth(models.Model):
    """Model for two-factor authentication"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='two_factor_auths')
    phone_number = models.CharField(max_length=20)
    code = models.CharField(max_length=6, blank=True, null=True)
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
    # Personal Details
    country_of_residence = models.CharField(max_length=100, blank=True, null=True, help_text="Country of residence")
    current_role_title = models.CharField(max_length=150, blank=True, null=True, help_text="Current role or job title")
    years_of_experience = models.CharField(
        max_length=50,
        choices=[
            ('0-2', '0-2 years'),
            ('2-5', '2-5 years'),
            ('5-10', '5-10 years'),
            ('10-15', '10-15 years'),
            ('15+', '15+ years'),
        ],
        blank=True,
        null=True,
        help_text="Years of investing experience"
    )
    linkedin_profile = models.URLField(max_length=500, blank=True, null=True, help_text="LinkedIn profile URL")
    typical_check_size = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Typical investment check size"
    )
    
    # Accreditation & Compliance
    is_accredited = models.CharField(max_length=3, choices=ACCREDITED_CHOICES, blank=True, null=True)
    understands_regulatory_requirements = models.BooleanField(default=False)
    
    # Investment Preferences
    sectors = models.ManyToManyField(Sector, blank=True, related_name='syndicate_profiles')
    geographies = models.ManyToManyField(Geography, blank=True, related_name='syndicate_profiles')
    existing_lp_count = models.CharField(max_length=10, choices=LP_NETWORK_CHOICES, blank=True, null=True)
    lp_base_size = models.IntegerField(blank=True, null=True, help_text="Total number of LPs in your network")
    enable_platform_lp_access = models.BooleanField(default=False)
    allow_platform_contact = models.BooleanField(
        default=True,
        help_text="Allow platform to contact portfolio companies (True=Allow, False=Restrict)"
    )
    
    # Step 2: Entity Profile
    firm_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='syndicate_logos/', blank=True, null=True)
    enable_role_based_access_controls = models.BooleanField(
        default=False, 
        help_text="When enabled, permissions will be automatically assigned based on team member roles and can be overridden individually"
    )
    
    # Settings: General Info
    # Keep per-name fields and also provide convenient full_name/short_bio
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    short_bio = models.TextField(blank=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    
    # KYB Verification Fields - Entity Business Info (Step 3a)
    entity_legal_name = models.CharField(max_length=255, blank=True, null=True, help_text="Entity legal name")
    ENTITY_TYPE_CHOICES = [
        ('trust', 'Trust'),
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('partnership', 'Partnership'),
    ]
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPE_CHOICES, blank=True, null=True, help_text="Entity type")
    country_of_incorporation = models.CharField(max_length=100, blank=True, null=True, help_text="Country of incorporation")
    registration_number = models.CharField(max_length=100, blank=True, null=True, help_text="Registration Number / Company Number")
    
    # Legacy KYB fields (kept for backwards compatibility)
    company_legal_name = models.CharField(max_length=255, blank=True, null=True, help_text="Company legal name")
    kyb_full_name = models.CharField(max_length=255, blank=True, null=True, help_text="Your full name")
    kyb_position = models.CharField(max_length=150, blank=True, null=True, help_text="Your position in company")
    
    # Registered Address
    registered_street_address = models.CharField(max_length=255, blank=True, null=True, help_text="Registered street address")
    registered_area_landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Registered area/landmark")
    registered_postal_code = models.CharField(max_length=20, blank=True, null=True, help_text="Registered postal code")
    registered_city = models.CharField(max_length=150, blank=True, null=True, help_text="Registered city")
    registered_state = models.CharField(max_length=100, blank=True, null=True, help_text="Registered state")
    registered_country = models.CharField(max_length=100, blank=True, null=True, help_text="Registered country")
    
    # Operating Address (Optional)
    operating_street_address = models.CharField(max_length=255, blank=True, null=True, help_text="Operating street address")
    operating_area_landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Operating area/landmark")
    operating_postal_code = models.CharField(max_length=20, blank=True, null=True, help_text="Operating postal code")
    operating_city = models.CharField(max_length=150, blank=True, null=True, help_text="Operating city")
    operating_state = models.CharField(max_length=100, blank=True, null=True, help_text="Operating state")
    operating_country = models.CharField(max_length=100, blank=True, null=True, help_text="Operating country")
    
    # KYB Documents - Company
    certificate_of_incorporation = models.FileField(upload_to='kyb_documents/coi/', blank=True, null=True, help_text="Certificate of Incorporation")
    registered_address_proof = models.FileField(upload_to='kyb_documents/registered_address/', blank=True, null=True, help_text="Proof of registered address")
    directors_register = models.FileField(upload_to='kyb_documents/directors/', blank=True, null=True, help_text="Directors register (optional)")
    
    # KYB Documents - Trust/Foundation
    trust_deed = models.FileField(upload_to='kyb_documents/trust/', blank=True, null=True, help_text="Trust deed document")
    
    # KYB Documents - Partnership
    partnership_agreement = models.FileField(upload_to='kyb_documents/partnership/', blank=True, null=True, help_text="Partnership agreement")
    
    # Legacy document fields
    company_bank_statement = models.FileField(upload_to='kyb_documents/bank_statements/', blank=True, null=True)
    
    # Legacy Address Information (kept for backwards compatibility)
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    town_city = models.CharField(max_length=150, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    company_proof_of_address = models.FileField(upload_to='kyb_documents/proof_of_address/', blank=True, null=True)
    
    # Beneficiary Owner Information
    beneficiary_owner_identity_document = models.FileField(upload_to='kyb_documents/beneficiary_identity/', blank=True, null=True)
    beneficiary_owner_proof_of_address = models.FileField(upload_to='kyb_documents/beneficiary_address/', blank=True, null=True)
    
    # S/SE Eligibility
    SSE_ELIGIBILITY_CHOICES = [
        ('hidden', 'Hidden'),
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    sse_eligibility = models.CharField(max_length=20, choices=SSE_ELIGIBILITY_CHOICES, default='hidden', blank=True)
    
    # Signing Requirements
    is_notary_wet_signing = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='no',
        blank=True,
        help_text="Is Notary / Wet signing of document at close or conversion of share"
    )
    will_require_unlockley = models.CharField(
        max_length=10,
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='no',
        blank=True,
        help_text="Will you required Unlockley to sign a deed of adherence in order to close the deal"
    )
    
    # Investee Company Contact
    investee_company_contact_number = models.CharField(max_length=20, blank=True, null=True)
    investee_company_email = models.EmailField(blank=True, null=True)
    
    # Agreement
    agree_to_investee_terms = models.BooleanField(default=False, help_text="I agree to investee terms")
    kyb_verification_completed = models.BooleanField(default=False)
    kyb_verification_submitted_at = models.DateTimeField(blank=True, null=True)
    
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
        # Only risk_regulatory_attestation is required
        # jurisdictional_compliance_acknowledged is optional
        return self.risk_regulatory_attestation
    
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


# Fee Recipient Model

class FeeRecipient(models.Model):
    """Model for fee recipient setup"""
    
    RECIPIENT_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('trust', 'Trust'),
    ]
    
    syndicate = models.OneToOneField(
        SyndicateProfile,
        on_delete=models.CASCADE,
        related_name='fee_recipient'
    )
    
    # Recipient Info
    recipient_type = models.CharField(
        max_length=20,
        choices=RECIPIENT_TYPE_CHOICES,
        default='individual',
        help_text="Type of fee recipient"
    )
    
    # Entity name (replaces first_name/last_name)
    entity_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the entity (individual, company, or trust)"
    )
    
    # Residence (replaces jurisdiction)
    residence = models.CharField(max_length=100, blank=True, null=True)
    
    # Tax ID
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Tax ID or Entity Reference Code"
    )
    
    # Documents
    id_document = models.FileField(
        upload_to='fee_recipient_documents/',
        blank=True,
        null=True,
        help_text="ID or Incorporation Document"
    )
    proof_of_address = models.FileField(
        upload_to='fee_recipient_documents/',
        blank=True,
        null=True,
        help_text="Proof of Address Document"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'fee recipient'
        verbose_name_plural = 'fee recipients'
    
    def __str__(self):
        return f"{self.entity_name} - {self.syndicate.firm_name}"


# Bank Details Models

class CreditCard(models.Model):
    """Model for credit/debit cards"""
    
    CARD_TYPE_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ]
    
    CARD_CATEGORY_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    syndicate = models.ForeignKey(
        SyndicateProfile,
        on_delete=models.CASCADE,
        related_name='credit_cards'
    )
    
    card_category = models.CharField(
        max_length=20,
        choices=CARD_CATEGORY_CHOICES,
        default='credit_card',
        help_text="Whether this is a credit card or debit card"
    )
    
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES)
    card_number = models.CharField(max_length=19)  # Masked or encrypted in production
    card_holder_name = models.CharField(max_length=255)
    expiry_date = models.CharField(max_length=5, help_text="MM/YY format")  # MM/YY
    cvv = models.CharField(max_length=4, blank=True, null=True)  # Should be encrypted
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary card for transactions"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'credit card'
        verbose_name_plural = 'credit cards'
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"{self.get_card_type_display()} ({self.get_card_category_display()}) - {self.card_number[-4:]}"


class BankAccount(models.Model):
    """Model for bank accounts"""
    
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Checking'),
        ('savings', 'Savings'),
        ('money_market', 'Money Market'),
        ('investment', 'Investment'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    syndicate = models.ForeignKey(
        SyndicateProfile,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    
    bank_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    account_number = models.CharField(max_length=20)
    routing_number = models.CharField(max_length=20, blank=True, null=True)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    iban = models.CharField(max_length=34, blank=True, null=True)
    
    account_holder_name = models.CharField(max_length=255)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary account for transfers"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'bank account'
        verbose_name_plural = 'bank accounts'
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number[-4:]}"


# Compliance & Accreditation Models

def compliance_document_upload_path(instance, filename):
    """Generate upload path for compliance documents"""
    return f'compliance_documents/syndicate_{instance.syndicate.id}/{filename}'


class ComplianceDocument(models.Model):
    """Model for compliance and accreditation documents"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('COI', 'Certificate of Incorporation (COI)'),
        ('Tax', 'Tax Document'),
        ('Attest.', 'Attestation Document'),
        ('Bank', 'Bank Statement'),
        ('Identity', 'Identity Document'),
        ('Address', 'Proof of Address'),
        ('Other', 'Other Compliance Document'),
    ]
    
    JURISDICTION_CHOICES = [
        ('US (NY)', 'United States (New York)'),
        ('US (TX)', 'United States (Texas)'),
        ('US (CA)', 'United States (California)'),
        ('US (DE)', 'United States (Delaware)'),
        ('EU (DE)', 'European Union (Germany)'),
        ('EU (FR)', 'European Union (France)'),
        ('EU (UK)', 'European Union (United Kingdom)'),
        ('Asia (SG)', 'Asia (Singapore)'),
        ('Asia (HK)', 'Asia (Hong Kong)'),
        ('Other', 'Other Jurisdiction'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('ok', 'OK'),
        ('exp', 'Expired'),
        ('missing', 'Missing'),
        ('rejected', 'Rejected'),
    ]
    
    syndicate = models.ForeignKey(
        SyndicateProfile,
        on_delete=models.CASCADE,
        related_name='compliance_documents'
    )
    
    # Document information
    document_name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    jurisdiction = models.CharField(max_length=20, choices=JURISDICTION_CHOICES)
    
    # File details
    file = models.FileField(upload_to=compliance_document_upload_path)
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(help_text="File size in bytes", blank=True, null=True)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Status and review
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_compliance_docs'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry tracking
    expiry_date = models.DateField(null=True, blank=True, help_text="Document expiration date")
    
    # Upload metadata
    uploaded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_compliance_docs'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'compliance document'
        verbose_name_plural = 'compliance documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['syndicate', 'status']),
            models.Index(fields=['document_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.document_name} - {self.syndicate.firm_name or 'Syndicate'}"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size is None:
            return 0
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_expired(self):
        """Check if document is expired"""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False
    
    def mark_as_ok(self, reviewed_by=None):
        """Mark document as OK"""
        self.status = 'ok'
        if reviewed_by:
            self.reviewed_by = reviewed_by
            self.reviewed_at = timezone.now()
        self.save()
    
    def mark_as_expired(self):
        """Mark document as expired"""
        self.status = 'exp'
        self.save()
    
    def mark_as_rejected(self, notes, reviewed_by=None):
        """Mark document as rejected with notes"""
        self.status = 'rejected'
        self.review_notes = notes
        if reviewed_by:
            self.reviewed_by = reviewed_by
            self.reviewed_at = timezone.now()
        self.save()


# Team Management Models

class TeamMember(models.Model):
    """Model for syndicate team members"""
    
    ROLE_CHOICES = [
        ('lead_partner', 'Lead Partner'),
        ('co_lead', 'Co-Lead / Deal Partner'),
        ('operations_manager', 'Operations Manager'),
        ('compliance_officer', 'Compliance Officer'),
        ('analyst_deal_scout', 'Analyst / Deal Scout'),
        ('viewer', 'Viewer'),
    ]
    
    syndicate = models.ForeignKey(
        SyndicateProfile,
        on_delete=models.CASCADE,
        related_name='team_members'
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        null=True,
        blank=True,
        help_text="User account if they are registered, otherwise null for invited members"
    )
    
    # Member info (for invited members who haven't registered yet)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    
    # Role and permissions
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='viewer')
    
    # Deal Permissions
    can_create_spvs = models.BooleanField(default=False, help_text="Create SPVs")
    can_publish_spvs = models.BooleanField(default=False, help_text="Publish SPVs")
    can_upload_deal_materials = models.BooleanField(default=False, help_text="Upload deal materials")
    can_edit_deal_terms = models.BooleanField(default=False, help_text="Edit deal terms")
    
    # Investor Permissions
    can_invite_lps = models.BooleanField(default=False, help_text="Invite LPs")
    can_view_lp_list = models.BooleanField(default=False, help_text="View LP list")
    can_view_lp_commitments = models.BooleanField(default=False, help_text="View LP commitments")
    can_communicate_with_lps = models.BooleanField(default=False, help_text="Communicate with LPs")
    
    # Operations & Finance Permissions
    can_manage_capital_calls = models.BooleanField(default=False, help_text="Manage capital calls")
    can_update_payment_statuses = models.BooleanField(default=False, help_text="Update payment statuses")
    can_manage_bank_accounts = models.BooleanField(default=False, help_text="Manage bank accounts")
    can_send_tax_documents = models.BooleanField(default=False, help_text="Send tax documents")
    
    # Compliance Permissions
    can_review_kyc_kyb = models.BooleanField(default=False, help_text="Review KYC/KYB")
    can_approve_reject_investors = models.BooleanField(default=False, help_text="Approve/reject investors")
    can_view_jurisdiction_flags = models.BooleanField(default=False, help_text="View jurisdiction/eligibility flags")
    can_access_audit_logs = models.BooleanField(default=False, help_text="Access audit logs")
    
    # Team Management Permissions
    can_add_remove_team_members = models.BooleanField(default=False, help_text="Add/remove team members")
    can_edit_roles_permissions = models.BooleanField(default=False, help_text="Edit roles & permissions")
    
    # Legacy permissions (kept for backwards compatibility)
    can_access_dashboard = models.BooleanField(default=True)
    can_manage_spvs = models.BooleanField(default=False)
    can_manage_documents = models.BooleanField(default=False)
    can_manage_investors = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    can_manage_transfers = models.BooleanField(default=False)
    can_manage_team = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)
    
    # Invitation and status
    invitation_sent = models.BooleanField(default=False)
    invitation_token = models.CharField(max_length=100, blank=True, null=True)
    invitation_accepted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Metadata
    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='team_members_added'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'team member'
        verbose_name_plural = 'team members'
        ordering = ['-added_at']
        unique_together = ['syndicate', 'email']
    
    def __str__(self):
        return f"{self.name} - {self.syndicate.firm_name or 'Syndicate'}"
    
    @property
    def is_registered(self):
        """Check if team member has registered user account"""
        return self.user is not None
    
    def get_permissions(self):
        """Get all permissions as dictionary"""
        return {
            # Deal Permissions
            'can_create_spvs': self.can_create_spvs,
            'can_publish_spvs': self.can_publish_spvs,
            'can_upload_deal_materials': self.can_upload_deal_materials,
            'can_edit_deal_terms': self.can_edit_deal_terms,
            # Investor Permissions
            'can_invite_lps': self.can_invite_lps,
            'can_view_lp_list': self.can_view_lp_list,
            'can_view_lp_commitments': self.can_view_lp_commitments,
            'can_communicate_with_lps': self.can_communicate_with_lps,
            # Operations & Finance
            'can_manage_capital_calls': self.can_manage_capital_calls,
            'can_update_payment_statuses': self.can_update_payment_statuses,
            'can_manage_bank_accounts': self.can_manage_bank_accounts,
            'can_send_tax_documents': self.can_send_tax_documents,
            # Compliance
            'can_review_kyc_kyb': self.can_review_kyc_kyb,
            'can_approve_reject_investors': self.can_approve_reject_investors,
            'can_view_jurisdiction_flags': self.can_view_jurisdiction_flags,
            'can_access_audit_logs': self.can_access_audit_logs,
            # Team Management
            'can_add_remove_team_members': self.can_add_remove_team_members,
            'can_edit_roles_permissions': self.can_edit_roles_permissions,
            # Legacy
            'can_access_dashboard': self.can_access_dashboard,
            'can_view_reports': self.can_view_reports,
        }
    
    def apply_role_permissions(self):
        """Apply default permissions based on role"""
        role_permissions = {
            'lead_partner': {
                'can_create_spvs': True, 'can_publish_spvs': True, 'can_upload_deal_materials': True, 'can_edit_deal_terms': True,
                'can_invite_lps': True, 'can_view_lp_list': True, 'can_view_lp_commitments': True, 'can_communicate_with_lps': True,
                'can_manage_capital_calls': True, 'can_update_payment_statuses': True, 'can_manage_bank_accounts': True, 'can_send_tax_documents': True,
                'can_review_kyc_kyb': True, 'can_approve_reject_investors': True, 'can_view_jurisdiction_flags': True, 'can_access_audit_logs': True,
                'can_add_remove_team_members': True, 'can_edit_roles_permissions': True,
                'can_access_dashboard': True, 'can_view_reports': True,
            },
            'co_lead': {
                'can_create_spvs': True, 'can_publish_spvs': True, 'can_upload_deal_materials': True, 'can_edit_deal_terms': True,
                'can_invite_lps': True, 'can_view_lp_list': True, 'can_view_lp_commitments': True, 'can_communicate_with_lps': True,
                'can_manage_capital_calls': True, 'can_update_payment_statuses': True, 'can_manage_bank_accounts': False, 'can_send_tax_documents': True,
                'can_review_kyc_kyb': False, 'can_approve_reject_investors': False, 'can_view_jurisdiction_flags': True, 'can_access_audit_logs': False,
                'can_add_remove_team_members': False, 'can_edit_roles_permissions': False,
                'can_access_dashboard': True, 'can_view_reports': True,
            },
            'operations_manager': {
                'can_create_spvs': False, 'can_publish_spvs': False, 'can_upload_deal_materials': True, 'can_edit_deal_terms': False,
                'can_invite_lps': False, 'can_view_lp_list': True, 'can_view_lp_commitments': True, 'can_communicate_with_lps': True,
                'can_manage_capital_calls': True, 'can_update_payment_statuses': True, 'can_manage_bank_accounts': True, 'can_send_tax_documents': True,
                'can_review_kyc_kyb': False, 'can_approve_reject_investors': False, 'can_view_jurisdiction_flags': False, 'can_access_audit_logs': True,
                'can_add_remove_team_members': False, 'can_edit_roles_permissions': False,
                'can_access_dashboard': True, 'can_view_reports': True,
            },
            'compliance_officer': {
                'can_create_spvs': False, 'can_publish_spvs': False, 'can_upload_deal_materials': False, 'can_edit_deal_terms': False,
                'can_invite_lps': False, 'can_view_lp_list': True, 'can_view_lp_commitments': False, 'can_communicate_with_lps': False,
                'can_manage_capital_calls': False, 'can_update_payment_statuses': False, 'can_manage_bank_accounts': False, 'can_send_tax_documents': False,
                'can_review_kyc_kyb': True, 'can_approve_reject_investors': True, 'can_view_jurisdiction_flags': True, 'can_access_audit_logs': True,
                'can_add_remove_team_members': False, 'can_edit_roles_permissions': False,
                'can_access_dashboard': True, 'can_view_reports': True,
            },
            'analyst_deal_scout': {
                'can_create_spvs': False, 'can_publish_spvs': False, 'can_upload_deal_materials': True, 'can_edit_deal_terms': False,
                'can_invite_lps': False, 'can_view_lp_list': False, 'can_view_lp_commitments': False, 'can_communicate_with_lps': False,
                'can_manage_capital_calls': False, 'can_update_payment_statuses': False, 'can_manage_bank_accounts': False, 'can_send_tax_documents': False,
                'can_review_kyc_kyb': False, 'can_approve_reject_investors': False, 'can_view_jurisdiction_flags': False, 'can_access_audit_logs': False,
                'can_add_remove_team_members': False, 'can_edit_roles_permissions': False,
                'can_access_dashboard': True, 'can_view_reports': True,
            },
            'viewer': {
                'can_create_spvs': False, 'can_publish_spvs': False, 'can_upload_deal_materials': False, 'can_edit_deal_terms': False,
                'can_invite_lps': False, 'can_view_lp_list': False, 'can_view_lp_commitments': False, 'can_communicate_with_lps': False,
                'can_manage_capital_calls': False, 'can_update_payment_statuses': False, 'can_manage_bank_accounts': False, 'can_send_tax_documents': False,
                'can_review_kyc_kyb': False, 'can_approve_reject_investors': False, 'can_view_jurisdiction_flags': False, 'can_access_audit_logs': False,
                'can_add_remove_team_members': False, 'can_edit_roles_permissions': False,
                'can_access_dashboard': True, 'can_view_reports': True,
            }
        }
        
        permissions = role_permissions.get(self.role, role_permissions['viewer'])
        for key, value in permissions.items():
            setattr(self, key, value)


class BeneficialOwner(models.Model):
    """Model for Beneficial Owners (UBOs) of a syndicate"""
    
    ROLE_CHOICES = [
        ('beneficial_owner', 'Beneficial Owner'),
        ('director', 'Director'),
        ('trustee', 'Trustee'),
        ('partner', 'Partner'),
        ('protector', 'Protector'),
    ]
    
    BENEFICIARY_ROLE_CHOICES = [
        ('beneficiary', 'Beneficiary'),
        ('director', 'Director'),
        ('shareholder', 'Shareholder'),
        ('psc', 'PSC'),
        ('trustee', 'Trustee'),
    ]
    
    KYC_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('failed', 'Failed'),
        ('needs_reupload', 'Needs Re-upload'),
    ]
    
    syndicate = models.ForeignKey(
        SyndicateProfile,
        on_delete=models.CASCADE,
        related_name='beneficial_owners'
    )
    
    # Personal Information
    full_name = models.CharField(max_length=255, help_text="Full name of the beneficial owner")
    date_of_birth = models.DateField(blank=True, null=True, help_text="Date of birth")
    nationality = models.CharField(max_length=100, blank=True, null=True, help_text="Nationality")
    email = models.EmailField(blank=True, null=True, help_text="Email address for KYC invite")
    
    # Residential Address
    street_address = models.CharField(max_length=255, blank=True, null=True, help_text="Street address")
    area_landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Area/Landmark")
    postal_code = models.CharField(max_length=20, blank=True, null=True, help_text="Postal code")
    city = models.CharField(max_length=150, blank=True, null=True, help_text="City")
    state = models.CharField(max_length=100, blank=True, null=True, help_text="State")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="Country")
    
    # Role and Ownership
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='beneficial_owner', help_text="Role in the entity")
    ownership_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, 
        default=0, 
        help_text="Ownership percentage (0-100)"
    )
    beneficiary_role = models.CharField(
        max_length=50, 
        choices=BENEFICIARY_ROLE_CHOICES, 
        default='beneficiary',
        blank=True,
        null=True,
        help_text="Beneficiary role type"
    )
    
    # KYC Status
    kyc_status = models.CharField(
        max_length=20, 
        choices=KYC_STATUS_CHOICES, 
        default='pending',
        help_text="KYC verification status"
    )
    kyc_invite_sent = models.BooleanField(default=False, help_text="Whether KYC invite link has been sent")
    kyc_invite_sent_at = models.DateTimeField(blank=True, null=True)
    kyc_completed_at = models.DateTimeField(blank=True, null=True)
    
    # Documents
    identity_document = models.FileField(
        upload_to='kyb_documents/ubo_identity/', 
        blank=True, 
        null=True,
        help_text="Identity document (passport, ID card, etc.)"
    )
    proof_of_address = models.FileField(
        upload_to='kyb_documents/ubo_address/', 
        blank=True, 
        null=True,
        help_text="Proof of residential address"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='beneficial_owners_added'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'beneficial owner'
        verbose_name_plural = 'beneficial owners'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.syndicate.firm_name or 'Syndicate'} ({self.get_role_display()})"
    
    @property
    def full_address(self):
        """Get formatted full address"""
        address_parts = [
            self.street_address,
            self.area_landmark,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, address_parts))