from django.db import models
from django.conf import settings
import os


def syndicate_document_upload_path(instance, filename):
    """Generate upload path for syndicate documents"""
    return f'syndicate_documents/{instance.syndicate.id}/{instance.document_type}/{filename}'


class SyndicateDocument(models.Model):
    """Model for storing syndicate-related documents"""
    
    DOCUMENT_TYPES = [
        ('syndicate_logo', 'Syndicate Logo'),
        ('company_certificate', 'Company Certificate of Incorporation'),
        ('company_bank_statement', 'Company Bank Statement'),
        ('company_proof_of_address', 'Company Proof of Address'),
        ('beneficiary_government_id', 'Beneficiary Government ID Proof'),
        ('beneficiary_source_of_funds', 'Beneficiary Source of Funds Proof'),
        ('beneficiary_tax_id', 'Beneficiary Tax ID Proof'),
        ('beneficiary_identity_document', 'Beneficiary Identity Document'),
        ('additional_policies', 'Additional Compliance Policies'),
        ('kyb_documents', 'KYB Verification Documents'),
        ('compliance_documents', 'Compliance & Attestation Documents'),
    ]
    
    syndicate = models.ForeignKey('users.SyndicateProfile', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to=syndicate_document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # File size in bytes
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verification_notes = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'syndicate document'
        verbose_name_plural = 'syndicate documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.syndicate.firm_name or self.syndicate.user.username} - {self.get_document_type_display()}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = os.path.basename(self.file.name)
            self.file_size = self.file.size
            self.mime_type = getattr(self.file, 'content_type', 'application/octet-stream')
        super().save(*args, **kwargs)


class SyndicateTeamMember(models.Model):
    """Model for syndicate team members"""
    
    syndicate = models.ForeignKey('users.SyndicateProfile', on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    role = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    # Permissions
    can_create_deals = models.BooleanField(default=False, help_text="Permission to create deals")
    can_messaging = models.BooleanField(default=False, help_text="Permission for messaging")
    can_access_cap_tables = models.BooleanField(default=False, help_text="Permission to access cap tables")
    can_access_up_data = models.BooleanField(default=False, help_text="Permission to access UP data")
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'syndicate team member'
        verbose_name_plural = 'syndicate team members'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.role}"


class SyndicateBeneficiary(models.Model):
    """Model for syndicate beneficiaries (KYB verification)"""
    
    syndicate = models.ForeignKey('users.SyndicateProfile', on_delete=models.CASCADE, related_name='beneficiaries')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    relationship = models.CharField(max_length=100, blank=True, null=True)  # e.g., "Owner", "Director"
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'syndicate beneficiary'
        verbose_name_plural = 'syndicate beneficiaries'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.relationship}"


class SyndicateCompliance(models.Model):
    """Model for syndicate compliance and attestations"""
    
    syndicate = models.ForeignKey('users.SyndicateProfile', on_delete=models.CASCADE, related_name='compliance_records')
    risk_regulatory_attestation = models.BooleanField(default=False)
    jurisdictional_requirements = models.BooleanField(default=False)
    additional_compliance_policies = models.BooleanField(default=False)
    self_knowledge_aml_policies = models.BooleanField(default=False)
    is_regulated_entity = models.BooleanField(default=False)
    is_ml_tf_risk = models.BooleanField(default=False)
    attestation_text = models.TextField(blank=True, null=True)
    attested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attested_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'syndicate compliance'
        verbose_name_plural = 'syndicate compliance records'
    
    def __str__(self):
        return f"{self.syndicate.firm_name or self.syndicate.user.username} - Compliance Record"
