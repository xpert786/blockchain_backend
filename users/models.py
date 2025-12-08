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
    is_accredited = models.CharField(max_length=3, choices=ACCREDITED_CHOICES, blank=True, null=True)
    understands_regulatory_requirements = models.BooleanField(default=False)
    sectors = models.ManyToManyField(Sector, blank=True, related_name='syndicate_profiles')
    geographies = models.ManyToManyField(Geography, blank=True, related_name='syndicate_profiles')
    existing_lp_count = models.CharField(max_length=10, choices=LP_NETWORK_CHOICES, blank=True, null=True)
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
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    link = models.URLField(max_length=500, blank=True, null=True)
    
    # KYB Verification Fields
    company_legal_name = models.CharField(max_length=255, blank=True, null=True, help_text="Company legal name")
    kyb_full_name = models.CharField(max_length=255, blank=True, null=True, help_text="Your full name")
    kyb_position = models.CharField(max_length=150, blank=True, null=True, help_text="Your position in company")
    certificate_of_incorporation = models.FileField(upload_to='kyb_documents/coi/', blank=True, null=True)
    company_bank_statement = models.FileField(upload_to='kyb_documents/bank_statements/', blank=True, null=True)
    
    # Address Information
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
        ('manager', 'Manager'),
        ('analyst', 'Analyst'),
        ('associate', 'Associate'),
        ('partner', 'Partner'),
        ('admin', 'Admin'),
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
    
    # Individual permissions (can override role-based permissions)
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
            'can_access_dashboard': self.can_access_dashboard,
            'can_manage_spvs': self.can_manage_spvs,
            'can_manage_documents': self.can_manage_documents,
            'can_manage_investors': self.can_manage_investors,
            'can_view_reports': self.can_view_reports,
            'can_manage_transfers': self.can_manage_transfers,
            'can_manage_team': self.can_manage_team,
            'can_manage_settings': self.can_manage_settings,
        }
    
    def apply_role_permissions(self):
        """Apply default permissions based on role"""
        role_permissions = {
            'manager': {
                'can_access_dashboard': True,
                'can_manage_spvs': True,
                'can_manage_documents': True,
                'can_manage_investors': True,
                'can_view_reports': True,
                'can_manage_transfers': True,
                'can_manage_team': True,
                'can_manage_settings': True,
            },
            'partner': {
                'can_access_dashboard': True,
                'can_manage_spvs': True,
                'can_manage_documents': True,
                'can_manage_investors': True,
                'can_view_reports': True,
                'can_manage_transfers': True,
                'can_manage_team': False,
                'can_manage_settings': False,
            },
            'analyst': {
                'can_access_dashboard': True,
                'can_manage_spvs': False,
                'can_manage_documents': True,
                'can_manage_investors': False,
                'can_view_reports': True,
                'can_manage_transfers': False,
                'can_manage_team': False,
                'can_manage_settings': False,
            },
            'associate': {
                'can_access_dashboard': True,
                'can_manage_spvs': False,
                'can_manage_documents': True,
                'can_manage_investors': True,
                'can_view_reports': True,
                'can_manage_transfers': False,
                'can_manage_team': False,
                'can_manage_settings': False,
            },
            'admin': {
                'can_access_dashboard': True,
                'can_manage_spvs': True,
                'can_manage_documents': True,
                'can_manage_investors': True,
                'can_view_reports': True,
                'can_manage_transfers': True,
                'can_manage_team': True,
                'can_manage_settings': True,
            },
            'viewer': {
                'can_access_dashboard': True,
                'can_manage_spvs': False,
                'can_manage_documents': False,
                'can_manage_investors': False,
                'can_view_reports': True,
                'can_manage_transfers': False,
                'can_manage_team': False,
                'can_manage_settings': False,
            }
        }
        
        permissions = role_permissions.get(self.role, role_permissions['viewer'])
        for key, value in permissions.items():
            setattr(self, key, value)