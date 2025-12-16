from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os
import uuid


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'documents/{instance.document_type}/{filename}'


class Document(models.Model):
    """Model for managing investment documents and agreements"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('investment_agreement', 'Investment Agreement'),
        ('kyc_documentation', 'KYC Documentation'),
        ('term_sheet', 'Term Sheet'),
        ('compliance_report', 'Compliance Report'),
        ('transfer_agreement', 'Transfer Agreement'),
        ('operating_agreement', 'Operating Agreement'),
        ('subscription_agreement', 'Subscription Agreement'),
        ('side_letter', 'Side Letter'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('pending_signatures', 'Pending Signatures'),
        ('signed', 'Signed'),
        ('finalized', 'Finalized'),
        ('rejected', 'Rejected'),
    ]
    
    # Basic Information
    document_id = models.CharField(max_length=50, unique=True, editable=False, help_text="Auto-generated document ID")
    title = models.CharField(max_length=255, help_text="Document title")
    description = models.TextField(blank=True, null=True, help_text="Document description")
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES, help_text="Type of document")
    
    # File Information
    file = models.FileField(
        upload_to=document_upload_path, null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'])],
        help_text="Document file"
    )
    original_filename = models.CharField(max_length=255, blank=True, null=True,help_text="Original filename")
    file_size = models.BigIntegerField(null=True, blank=True ,help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, null=True, blank=True ,help_text="MIME type of the file")
    
    # Version Control
    version = models.CharField(max_length=20, default='1.0', help_text="Document version")
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions',
        help_text="Parent document for version tracking"
    )
    
    # Status and Workflow
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft', help_text="Document status")
    requires_admin_review = models.BooleanField(default=False, help_text="Requires admin review")
    review_notes = models.TextField(blank=True, null=True, help_text="Review notes from admin")
    
    # Relationships
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_documents',
        help_text="User who created the document"
    )
    spv = models.ForeignKey(
        'spv.SPV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Associated SPV (if applicable)"
    )
    syndicate = models.ForeignKey(
        'users.SyndicateProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        help_text="Associated Syndicate (if applicable)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True, help_text="Date when document was finalized")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'document'
        verbose_name_plural = 'documents'
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['status']),
            models.Index(fields=['document_type']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.document_id} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.document_id:
            # Generate unique document ID
            prefix = self.document_type.upper()[:3] if self.document_type else 'DOC'
            self.document_id = f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
        
        if self.file:
            if not self.original_filename:
                self.original_filename = os.path.basename(self.file.name)
            if hasattr(self.file, 'size') and self.file.size:
                self.file_size = self.file.size
            if hasattr(self.file, 'content_type') and self.file.content_type:
                self.mime_type = self.file.content_type or 'application/octet-stream'
        
        super().save(*args, **kwargs)
    
    @property
    def signatories_count(self):
        """Get count of signatories"""
        return self.signatories.count()
    
    @property
    def signed_count(self):
        """Get count of signed signatories"""
        return self.signatories.filter(signed=True).count()
    
    @property
    def pending_signatures_count(self):
        """Get count of pending signatures"""
        return self.signatories.filter(signed=False).count()
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0


class DocumentSignatory(models.Model):
    """Model for tracking document signatories and signatures"""
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='signatories',
        help_text="Document to be signed"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_signatures',
        help_text="User who needs to sign"
    )
    role = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Role of the signatory (e.g., 'Investor', 'Manager', 'Admin')"
    )
    signed = models.BooleanField(default=False, help_text="Whether the document has been signed")
    signed_at = models.DateTimeField(null=True, blank=True, help_text="Date and time when signed")
    signature_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP address when signed")
    signature_location = models.CharField(max_length=255, blank=True, null=True, help_text="Location when signed")
    notes = models.TextField(blank=True, null=True, help_text="Additional notes")
    
    # Invitation
    invited_at = models.DateTimeField(auto_now_add=True, help_text="When the signatory was invited")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_signatories',
        help_text="User who invited this signatory"
    )
    
    class Meta:
        verbose_name = 'document signatory'
        verbose_name_plural = 'document signatories'
        unique_together = ['document', 'user']
        ordering = ['-invited_at']
    
    def __str__(self):
        return f"{self.document.document_id} - {self.user.username} ({'Signed' if self.signed else 'Pending'})"


class DocumentTemplate(models.Model):
    """
    Model for document templates used in the template engine.
    
    Templates are versioned, platform-approved document types managed by 
    platform admins or legal ops (NOT syndicate leads).
    
    Templates are stored as HTML/Markdown with placeholders (e.g. {{investor_name}}).
    PDFs are generated at runtime via HTML → PDF rendering.
    """
    
    CATEGORY_CHOICES = [
        ('legal', 'Legal'),
        ('compliance', 'Compliance'),
        ('informational', 'Informational'),
        ('financial', 'Financial'),
        ('other', 'Other'),
    ]
    
    SCOPE_CHOICES = [
        ('spv', 'SPV'),           # Generate blank/reference PDF (no investor fields populated)
        ('investor', 'Investor'),  # Generate investor-bound PDF (only in investor flows)
    ]
    
    JURISDICTION_CHOICES = [
        ('us', 'US Only'),
        ('global', 'Global'),
        ('eu', 'EU Only'),
        ('uk', 'UK Only'),
        ('apac', 'APAC'),
        ('other', 'Other'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('html', 'HTML'),
        ('markdown', 'Markdown'),
        ('jsx', 'JSX'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Template name (e.g., 'Investment Agreement')")
    description = models.TextField(help_text="Template description")
    version = models.CharField(max_length=20, default='1.0', help_text="Template version")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, help_text="Template category")
    
    # Scope and Jurisdiction (NEW - per client requirements)
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='spv',
        help_text="Template scope: 'spv' for SPV-level reference docs, 'investor' for investor-bound PDFs"
    )
    jurisdiction_scope = models.CharField(
        max_length=20,
        choices=JURISDICTION_CHOICES,
        default='global',
        help_text="Jurisdiction scope for the template"
    )
    
    # Template Content (NEW - HTML/Markdown with placeholders)
    # Templates are NOT PDFs - PDFs are generated at runtime
    template_content = models.TextField(
        blank=True,
        null=True,
        help_text="Template content as HTML/Markdown with placeholders (e.g. {{investor_name}}). PDFs generated at runtime."
    )
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='html',
        help_text="Content type of template: html, markdown, or jsx"
    )
    
    # Legacy template file (optional - for backward compatibility)
    template_file = models.FileField(
        upload_to='document_templates/',
        blank=True,
        null=True,
        help_text="Optional template file (DOCX, PDF) - prefer template_content for new templates"
    )
    
    # Required fields schema (JSON field to store required field definitions)
    # NOTE: required_fields are used for document GENERATION (investor-specific PDFs)
    required_fields = models.JSONField(
        default=list,
        help_text="List of required fields with their types and validation rules. Format: [{'name': 'investor_name', 'label': 'Investor Name', 'type': 'text', 'required': True}, ...]"
    )
    
    # Configurable fields for syndicate-level defaults (NOT for document generation)
    # NOTE: configurable_fields are used for saving syndicate-level TEMPLATE DEFAULTS
    configurable_fields = models.JSONField(
        default=list,
        help_text="List of configurable fields for syndicate-level defaults. Format: [{'name': 'field_name', 'label': 'Field Label', 'type': 'text', 'default_value': ''}, ...]"
    )
    
    # Template configuration
    enable_digital_signature = models.BooleanField(
        default=False,
        help_text="Enable digital signature workflow for generated documents"
    )
    is_active = models.BooleanField(default=True, help_text="Whether template is active and available for use")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates',
        help_text="User who created the template"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'document template'
        verbose_name_plural = 'document templates'
        unique_together = ['name', 'version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


def generation_pdf_upload_path(instance, filename):
    """Generate upload path for generated PDFs"""
    return f'generated_documents/{instance.template.id}/{filename}'


class DocumentGeneration(models.Model):
    """Model for tracking document generation from templates"""
    
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name='generations',
        help_text="Template used for generation"
    )
    generated_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='generation_history',
        help_text="Generated document"
    )
    
    # Generated PDF file
    generated_pdf = models.FileField(
        upload_to=generation_pdf_upload_path,
        blank=True,
        null=True,
        help_text="Generated PDF file"
    )
    pdf_filename = models.CharField(max_length=255, blank=True, null=True, help_text="Original PDF filename")
    pdf_file_size = models.BigIntegerField(null=True, blank=True, help_text="PDF file size in bytes")
    
    # Generation data (the field values used)
    generation_data = models.JSONField(
        default=dict,
        help_text="Field values used during document generation"
    )
    
    # Generation metadata
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_documents',
        help_text="User who generated the document"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Options
    enable_digital_signature = models.BooleanField(
        default=False,
        help_text="Whether digital signature workflow was enabled"
    )
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'document generation'
        verbose_name_plural = 'document generations'
    
    def __str__(self):
        return f"{self.template.name} -> {self.generated_document.document_id}"
    
    @property
    def pdf_file_size_mb(self):
        """Get PDF file size in MB"""
        return round(self.pdf_file_size / (1024 * 1024), 2) if self.pdf_file_size else 0


class SyndicateDocumentDefaults(models.Model):
    """
    Store syndicate-level default values for document templates.
    
    This model is used for "Syndicate Document Defaults" - saving template-driven
    defaults from configurable_fields[], NOT for generating specific PDFs.
    
    Documents generated here are SPV-level templates or reference documents.
    Investor-specific documents are generated automatically during allocations,
    capital calls, or transfers.
    """
    
    syndicate = models.ForeignKey(
        'users.SyndicateProfile',
        on_delete=models.CASCADE,
        related_name='document_defaults',
        help_text="Syndicate that owns these defaults"
    )
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.CASCADE,
        related_name='syndicate_defaults',
        help_text="Template for which defaults are saved"
    )
    
    # Default values for configurable fields
    default_values = models.JSONField(
        default=dict,
        help_text="Default values for template's configurable fields. Format: {'field_name': 'default_value', ...}"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_document_defaults',
        help_text="User who created these defaults"
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'syndicate document defaults'
        verbose_name_plural = 'syndicate document defaults'
        unique_together = ['syndicate', 'template']  # One default per syndicate per template
    
    def __str__(self):
        return f"{self.syndicate} - {self.template.name} defaults"
