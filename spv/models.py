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


class InstrumentType(models.Model):
    """Model for instrument types (e.g., SAFE, Convertible Note, Equity)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Order for display in dropdown")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'instrument type'
        verbose_name_plural = 'instrument types'
    
    def __str__(self):
        return self.name


class ShareClass(models.Model):
    """Model for share classes (e.g., Preferred, Common, Series A)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Order for display in dropdown")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'share class'
        verbose_name_plural = 'share classes'
    
    def __str__(self):
        return self.name


class Round(models.Model):
    """Model for funding rounds (e.g., Seed, Series A, Series B)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Order for display in dropdown")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'round'
        verbose_name_plural = 'rounds'
    
    def __str__(self):
        return self.name


class MasterPartnershipEntity(models.Model):
    """Model for master partnership entities"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Order for display in dropdown")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'master partnership entity'
        verbose_name_plural = 'master partnership entities'
    
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
    portfolio_company = models.ForeignKey(PortfolioCompany, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='spvs')
    portfolio_company_name = models.CharField(max_length=255, help_text="Portfolio company name (if not in database)"
    )
    
    # Company Details
    company_stage = models.ForeignKey(CompanyStage, on_delete=models.SET_NULL, null=True, blank=True,related_name='spvs'
    )
    country_of_incorporation = models.CharField(max_length=100, blank=True, null=True)
    incorporation_type = models.ForeignKey(IncorporationType, on_delete=models.SET_NULL, null=True, blank=True,related_name='spvs'
    )
    
    # Contact Information
    founder_email = models.EmailField(help_text="Founder email for deal validation")
    
    # Documents
    pitch_deck = models.FileField(upload_to='spv/pitch_decks/', blank=True, null=True,help_text="Upload pitch deck (PDF, PPT, PPTX)"
    )
    
    # Step 2: Terms
    TRANSACTION_TYPE_CHOICES = [('primary', 'Primary'),('secondary', 'Secondary'),]
    
    VALUATION_TYPE_CHOICES = [('pre_money', 'Pre money'),('post_money', 'Post money'),]
    
    transaction_type = models.CharField(max_length=20,choices=TRANSACTION_TYPE_CHOICES,blank=True,null=True,
        help_text="Transaction type: Primary or Secondary")
    instrument_type = models.ForeignKey('InstrumentType',on_delete=models.SET_NULL,null=True,blank=True,
        related_name='spvs',help_text="Legal instrument used for the deal")
    valuation_type = models.CharField(max_length=20,choices=VALUATION_TYPE_CHOICES,blank=True,null=True,
        help_text="Valuation type: Pre money or Post money")
    share_class = models.ForeignKey('ShareClass',on_delete=models.SET_NULL,null=True,blank=True,related_name='spvs',
        help_text="Share class for the deal")
    round = models.ForeignKey('Round',on_delete=models.SET_NULL,null=True,blank=True,related_name='spvs',
        help_text="Funding round")
    round_size = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True,
        help_text="Total round size in currency")
    allocation = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True,
        help_text="Your allocation amount in currency")
    
    # Step 3: Adviser & Legal Structure
    ADVISER_ENTITY_CHOICES = [('platform_advisers', 'Platform Advisers LLC'),('self_advised', 'Self-Advised Entity'),]
    ACCESS_MODE_CHOICES = [('private', 'Private'),('visible', 'Visible to all'),]
    INVESTMENT_VISIBILITY_CHOICES = [('hidden', 'Hidden'),('visible', 'Visible to all'),]
    
    adviser_entity = models.CharField(max_length=30,choices=ADVISER_ENTITY_CHOICES,default='platform_advisers',
        blank=True,null=True,help_text="Adviser entity type")
    master_partnership_entity = models.ForeignKey('MasterPartnershipEntity',on_delete=models.SET_NULL,null=True,
        blank=True,related_name='spvs',help_text="Master partnership entity (appears on cap table)")
    fund_lead = models.ForeignKey(CustomUser,on_delete=models.SET_NULL,null=True,blank=True,
        related_name='led_spvs',help_text="Fund lead (designated in fund documentation)")
    
    # Step 4: Fundraising & Jurisdiction
    jurisdiction = models.CharField(max_length=100,blank=True,null=True,help_text="Jurisdiction for the deal")
    entity_type = models.CharField(max_length=100,blank=True,null=True,help_text="Entity type based on jurisdiction")
    minimum_lp_investment = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True,
        help_text="Minimum LP investment amount")
    target_closing_date = models.DateField(blank=True,null=True,help_text="Target closing date")
    total_carry_percentage = models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True,
        help_text="Total carry percentage")
    carry_recipient = models.CharField(max_length=255,blank=True,null=True,help_text="Carry recipient entity")
    gp_commitment = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True,help_text="GP commitment amount")
    deal_partners = models.TextField(blank=True,null=True,help_text="Strategic or deal partners (comma separated)")
    deal_name = models.CharField(max_length=255,blank=True,null=True,help_text="Deal name for investor-facing materials")
    access_mode = models.CharField(max_length=20,choices=ACCESS_MODE_CHOICES,default='private',help_text="Access mode for investors")
    
    # Step 5: Invite LPs
    lp_invite_emails = models.JSONField(default=list,blank=True,help_text="List of LP email addresses invited")
    lp_invite_message = models.TextField(blank=True,null=True,help_text="Default email message content")
    lead_carry_percentage = models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True,help_text="Lead carry percentage")
    investment_visibility = models.CharField(max_length=20,choices=INVESTMENT_VISIBILITY_CHOICES,default='hidden',
        help_text="Visibility setting for investment and fund valuations")
    auto_invite_active_spvs = models.BooleanField(default=False,help_text="Automatically invite to all current SPVs")
    invite_private_note = models.TextField(blank=True,null=True,help_text="Private notes for the invite")
    invite_tags = models.JSONField(default=list,blank=True,help_text="Tags to apply to invitees")
    
    # Step 5: Additional Information
    deal_tags = models.JSONField(default=list,blank=True,help_text="Tags describing the deal")
    syndicate_selection = models.CharField(max_length=255,blank=True,null=True,help_text="Selected syndicate")
    deal_memo = models.TextField(blank=True,null=True,help_text="Deal memo content"
    )
    supporting_document = models.FileField(upload_to='spv/supporting_documents/',blank=True,null=True,
        help_text="Additional document upload")
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Final Submission Legal Confirmations
    legal_review_confirmed          = models.BooleanField(default=False)
    terms_accepted                  = models.BooleanField(default=False)
    electronic_signature_confirmed  = models.BooleanField(default=False)

    
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

