from django.db import models
from users.models import CustomUser


def investor_upload_path(instance, filename):
    """Generate upload path for investor documents"""
    return f'investor_documents/{instance.user.id}/{filename}'


# Create your models here.

class InvestorProfile(models.Model):
    """Model for investor onboarding profile - Complete 6-step process"""
    
    # Investor Type Choices
    INVESTOR_TYPE_CHOICES = [
    ('individual', 'Individual'),
    ('family_office', 'Family Office'),
    ('corporate_vehicle', 'Corporate Vehicle'),
    ('trust_foundation', 'Trust / Foundation'),
    ]

    
    # Accreditation Method Choices
    ACCREDITATION_METHOD_CHOICES = [
        ('at_least_5m', 'I have at least $5M in investment'),
        ('between_2.2m_5m', 'I have between $2.2M and $5M in assets'),
        ('between_1m_2.2m', 'I have between $1M and $2.2M in assets'),
        ('income_200k', 'I have income of $200k (or $300k jointly with spouse) for the past 2 years and expect the same this year'),
        ('series_7_65_82', 'I am a Series 7, Series 65 or Series 82 holder and my license is active and in good standing'),
        ('not_accredited', "I'm not accredited yet"),
    ]
    
    # Investment Amount Choices
    INVESTMENT_AMOUNT_CHOICES = [
        ('up_to_20k', 'Up to $20,000'),
        ('up_to_50k', 'Up to $50,000'),
        ('up_to_100k', 'Up to $100,000'),
        ('up_to_250k', 'Up to $250,000'),
        ('up_to_500k', 'Up to $500,000'),
        ('more_than_500k', 'More than $500,000'),
    ]
    
    # Net Worth Percentage Choices
    NET_WORTH_PERCENTAGE_CHOICES = [
        ('up_to_5', 'Up to 5%'),
        ('up_to_10', 'Up to 10%'),
        ('up_to_15', 'Up to 15%'),
        ('more_than_15', 'More than 15%'),
    ]
    
    # Investment Strategy Choices
    INVESTMENT_STRATEGY_CHOICES = [
        ('unlocksley_syndicates', 'Picking companies to invest in (Unlocksley syndicates)'),
        ('index_funds', 'Investing in funds that broadly index venture, such as Unlocksley access fund (Unlocksley Managed Funds)'),
        ('rolling_or_venture_funds', 'Investing behind fund managers who pick companies to invest in (Unlocksley Rolling or Venture Funds)'),
    ]
    
    # Venture Experience Choices
    VENTURE_EXPERIENCE_CHOICES = [
        ('invested_spv', 'I invested in a startup directly or through a single-purpose vehicle (SPV)'),
        ('invested_vc_fund', 'I invested in startups indirectly through a venture fund'),
        ('work_at_vc', 'I work or worked at a venture capital or investment firm'),
        ('family_office_ria', 'I represent or represented a family office or Registered Investment Advisor (RIA)'),
        ('none', 'None of the above'),
    ]
    
    # Tech Startup Experience Choices
    TECH_STARTUP_EXPERIENCE_CHOICES = [
        ('work_at_tech', 'I work or worked at a tech startup'),
        ('advise_tech', 'I advise or advised a tech startup'),
        ('am_founder', 'I am or was a tech startup founder'),
        ('none', 'None of the above'),
    ]
    
    # How Did You Hear Choices
    HOW_HEARD_CHOICES = [
        ('google_search', 'Google search'),
        ('newsletter_media', 'Newsletter/Media site (TechCrunch, etc.)'),
        ('x_twitter', 'X (Twitter)'),
        ('friend_connection', 'Friend or Connection'),
        ('syndicate_lead_manager', 'Unlocksley Syndicate Lead or Fund Manager'),
        ('other', 'Other (please specify)'),
    ]
    
    # Reason for Choosing Choices
    REASON_CHOICES = [
        ('generating_returns', 'Generating financial returns for your portfolio'),
        ('meeting_people', 'Meeting new people to expand your network'),
        ('accessing_dealflow', 'Accessing dealflow you can\'t get anywhere else'),
        ('learning_tech', 'Learning more about tech and startups'),
    ]
    
    # Basic info
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='investor_profile')
    
    # Step 1: Basic Information
    full_name = models.CharField(max_length=255, blank=True, null=True, help_text="Full Name")
    email_address = models.EmailField(blank=True, null=True, help_text="Email Address")
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Phone Number")
    country_of_residence = models.CharField(max_length=100, default='United States', blank=True, null=True, help_text="Country of Residence")
    tax_residency = models.CharField(max_length=100, blank=True, null=True, help_text="Tax Residency Country")
    national_id = models.CharField(max_length=100, blank=True, null=True, help_text="National ID")
    
    # Step 2: KYC / Identity Verification
    government_id = models.FileField(upload_to=investor_upload_path, blank=True, null=True, help_text="Upload Government-Issued ID")
    date_of_birth = models.DateField(blank=True, null=True, help_text="Date of Birth")
    
    # Residential Address
    street_address = models.CharField(max_length=255, blank=True, null=True, help_text="Street Address")
    city = models.CharField(max_length=100, blank=True, null=True, help_text="City")
    state_province = models.CharField(max_length=100, blank=True, null=True, help_text="State / Province")
    zip_postal_code = models.CharField(max_length=20, blank=True, null=True, help_text="ZIP / Postal Code")
    country = models.CharField(max_length=100, blank=True, null=True, help_text="Country")
    
    # Step 3: Bank Details / Payment Setup
    bank_account_number = models.CharField(max_length=100, blank=True, null=True, help_text="Bank Account Number / Wallet Address")
    bank_name = models.CharField(max_length=255, blank=True, null=True, help_text="Bank Name")
    account_holder_name = models.CharField(max_length=255, blank=True, null=True, help_text="Account Holder's Name")
    swift_ifsc_code = models.CharField(max_length=50, blank=True, null=True, help_text="SWIFT/IFSC/Sort Code")
    proof_of_bank_ownership = models.FileField(upload_to=investor_upload_path, blank=True, null=True, help_text="Upload Proof of Bank Ownership")
    
    # Step 3.5: Jurisdiction-Aware Accreditation Check (NEW SCREEN)
    accreditation_jurisdiction = models.CharField(max_length=10, blank=True, null=True, help_text="Country/Jurisdiction code for accreditation (e.g., 'US', 'SG')")
    accreditation_rules_selected = models.JSONField(default=list, blank=True, help_text="List of selected accreditation rule IDs that user checked")
    accreditation_check_completed = models.BooleanField(default=False, help_text="Whether the jurisdiction-aware accreditation check was completed")
    accreditation_check_completed_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when accreditation check was completed")
    
    # Step 4: Accreditation (If Applicable)
    investor_type = models.CharField(max_length=20, choices=INVESTOR_TYPE_CHOICES, blank=True, null=True, help_text="Will you be investing money as an Individual, a Trust, or a Firm or Fund?")
    full_legal_name = models.CharField(max_length=255, blank=True, null=True, help_text="What is your full legal name?")
    legal_place_of_residence = models.CharField(max_length=100, blank=True, null=True, help_text="Where is your legal place of residence?")
    accreditation_method = models.CharField(max_length=100, choices=ACCREDITATION_METHOD_CHOICES, blank=True, null=True, help_text="How are you accredited?")
    proof_of_income_net_worth = models.FileField(upload_to=investor_upload_path, blank=True, null=True, help_text="Upload Proof of Income or Net Worth")
    is_accredited_investor = models.BooleanField(default=False, help_text="Are you an accredited investor?")
    meets_local_investment_thresholds = models.BooleanField(default=False, help_text="Do you meet your local investment thresholds?")
    
    # Step 5: Accept Agreements
    terms_and_conditions_accepted = models.BooleanField(default=False, help_text="I have read and agree to the Terms & Conditions")
    risk_disclosure_accepted = models.BooleanField(default=False, help_text="I acknowledge and understand the associated investment risks")
    privacy_policy_accepted = models.BooleanField(default=False, help_text="I agree to the Privacy Policy and data usage terms")
    confirmation_of_true_information = models.BooleanField(default=False, help_text="I confirm that all the information provided is true and I accept all the agreements above")
    
    # Step 6: Final Review (Read-only display of all information)
    
    # Application Status
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
    application_submitted = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(blank=True, null=True)
    
    # ============================================
    # INVESTOR SETTINGS FIELDS
    # ============================================
    
    # Tax & Compliance Settings
    tax_identification_number = models.CharField(max_length=50, blank=True, null=True, help_text="Tax Identification Number (TIN/SSN)")
    us_person_status = models.BooleanField(default=False, help_text="U.S. Person Status for tax reporting purposes")
    w9_form_submitted = models.BooleanField(default=False, help_text="W-9 Form Submitted")
    k1_acceptance = models.BooleanField(default=True, help_text="Accept K-1 tax documents")
    tax_reporting_consent = models.BooleanField(default=True, help_text="Receive tax documents electronically")
    accreditation_expiry_date = models.DateField(blank=True, null=True, help_text="Accreditation Expiry/Review Date")
    
    # Eligibility Settings
    delaware_spvs_allowed = models.BooleanField(default=True, help_text="Allow investment in Delaware entities")
    bvi_spvs_allowed = models.BooleanField(default=False, help_text="Allow investment in British Virgin Islands entities")
    auto_reroute_consent = models.BooleanField(default=True, help_text="Offer alternative jurisdiction if ineligible")
    max_annual_commitment = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, help_text="Self-imposed annual investment limit")
    deal_stage_preferences = models.JSONField(default=list, blank=True, help_text="Deal stage preferences: ['early_stage', 'growth', 'late_stage']")
    
    # Financial Settings
    CURRENCY_CHOICES = [
        ('USD', 'USD (US Dollar)'),
        ('EUR', 'EUR (Euro)'),
        ('GBP', 'GBP (British Pound)'),
        ('JPY', 'JPY (Japanese Yen)'),
        ('CAD', 'CAD (Canadian Dollar)'),
    ]
    preferred_investment_currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default='USD', help_text="Preferred Investment Currency")
    escrow_partner_selection = models.CharField(max_length=255, blank=True, null=True, help_text="Escrow Partner Selection (e.g., Silicon Valley Bank)")
    capital_call_notification_preferences = models.JSONField(default=dict, blank=True, help_text="Capital Call Notification Preferences: {'email': bool, 'sms': bool, 'in_app': bool}")
    CARRY_FEES_DISPLAY_CHOICES = [
        ('detailed_breakdown', 'Detailed Breakdown'),
        ('summary', 'Summary'),
        ('hidden', 'Hidden'),
    ]
    carry_fees_display_preference = models.CharField(max_length=20, choices=CARRY_FEES_DISPLAY_CHOICES, default='detailed_breakdown', help_text="Carry/Fees Display Preference")
    
    # Portfolio Settings
    PORTFOLIO_VIEW_CHOICES = [
        ('deal_by_deal', 'Deal-by-Deal'),
        ('aggregated', 'Aggregated'),
        ('performance', 'Performance View'),
    ]
    portfolio_view_settings = models.CharField(max_length=20, choices=PORTFOLIO_VIEW_CHOICES, default='deal_by_deal', help_text="Portfolio View Settings")
    secondary_transfer_consent = models.BooleanField(default=True, help_text="Allow listing holdings for resale")
    LIQUIDITY_PREFERENCE_CHOICES = [
        ('long_term', 'Long-term Holdings'),
        ('medium_term', 'Medium-term Holdings'),
        ('short_term', 'Short-term Holdings'),
        ('flexible', 'Flexible'),
    ]
    liquidity_preference = models.CharField(max_length=20, choices=LIQUIDITY_PREFERENCE_CHOICES, default='long_term', help_text="Liquidity Preference")
    whitelist_secondary_trading = models.BooleanField(default=False, help_text="Pre-approved counterparties for secondary trading")
    
    # Security & Privacy Settings
    two_factor_authentication_enabled = models.BooleanField(default=False, help_text="Two-Factor Authentication Enabled")
    SESSION_TIMEOUT_CHOICES = [
        (15, '15 minutes'),
        (30, '30 minutes'),
        (60, '60 minutes'),
        (120, '120 minutes'),
        (240, '240 minutes'),
    ]
    session_timeout_minutes = models.IntegerField(choices=SESSION_TIMEOUT_CHOICES, default=30, help_text="Session Timeout (minutes)")
    soft_wall_deal_preview = models.BooleanField(default=True, help_text="Show teaser info before full KYC")
    discovery_opt_in = models.BooleanField(default=False, help_text="Allow syndicate leads outside network to invite you")
    anonymity_preference = models.BooleanField(default=False, help_text="Hide name from other LPs in same SPV")
    
    # Communication Settings
    CONTACT_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone', 'Phone'),
        ('in_app', 'In App'),
    ]
    preferred_contact_method = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES, default='email', help_text="Preferred Contact Method")
    UPDATE_FREQUENCY_CHOICES = [
        ('real_time', 'Real-time'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
        ('monthly', 'Monthly Digest'),
    ]
    update_frequency = models.CharField(max_length=20, choices=UPDATE_FREQUENCY_CHOICES, default='weekly', help_text="Update Frequency")
    event_alerts = models.JSONField(default=dict, blank=True, help_text="Event Alerts: {'capital_calls': bool, 'secondary_offers': bool, 'portfolio_updates': bool, 'distributions': bool}")
    marketing_consent = models.BooleanField(default=False, help_text="Product updates and partner offers")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'investor profile'
        verbose_name_plural = 'investor profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.full_name or 'Draft Profile'}"
    
    @property
    def step1_completed(self):
        """Check if Step 1 (Basic Information) is completed"""
        return all([
            self.full_name,
            self.email_address,
            self.phone_number,
            self.country_of_residence
        ])
    
    @property
    def step2_completed(self):
        """Check if Step 2 (KYC / Identity Verification) is completed"""
        return all([
            self.government_id,
            self.date_of_birth,
            self.street_address,
            self.city,
            self.state_province,
            self.zip_postal_code,
            self.country
        ])
    
    @property
    def step3_completed(self):
        """Check if Step 3 (Bank Details / Payment Setup) is completed"""
        return all([
            self.bank_account_number,
            self.bank_name,
            self.account_holder_name,
            self.swift_ifsc_code,
            self.proof_of_bank_ownership
        ])
    
    @property
    def step4_completed(self):
        """Check if Step 4 (Accreditation - Optional) is completed"""
        # This step is optional, so we check if any accreditation info is provided
        # Or we can consider it complete if user has indicated they are not accredited
        return True  # Optional step, always consider complete
    
    @property
    def step5_completed(self):
        """Check if Step 5 (Accept Agreements) is completed"""
        return all([
            self.terms_and_conditions_accepted,
            self.risk_disclosure_accepted,
            self.privacy_policy_accepted,
            self.confirmation_of_true_information
        ])
    
    @property
    def step6_completed(self):
        """Check if Step 6 (Final Review) is completed - this is submission"""
        return self.application_submitted
    
    @property
    def current_step(self):
        """Determine current step in the onboarding process"""
        if not self.step1_completed:
            return 1
        elif not self.step2_completed:
            return 2
        elif not self.step3_completed:
            return 3
        elif not self.step4_completed:
            return 4
        elif not self.step5_completed:
            return 5
        elif not self.step6_completed:
            return 6
        else:
            return 7  # Completed


# Import dashboard models
from .dashboard_models import Portfolio, Investment, Notification, KYCStatus
