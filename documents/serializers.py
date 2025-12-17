from rest_framework import serializers
from .models import Document, DocumentSignatory, DocumentTemplate, DocumentGeneration, SyndicateDocumentDefaults
from users.models import CustomUser


class DocumentSignatorySerializer(serializers.ModelSerializer):
    """Serializer for DocumentSignatory model"""
    
    user_detail = serializers.SerializerMethodField()
    invited_by_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentSignatory
        fields = [
            'id',
            'document',
            'user',
            'user_detail',
            'role',
            'signed',
            'signed_at',
            'signature_ip',
            'signature_location',
            'notes',
            'invited_at',
            'invited_by',
            'invited_by_detail',
        ]
        read_only_fields = ['id', 'invited_at']
    
    def get_user_detail(self, obj):
        """Get user details"""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'full_name': obj.user.get_full_name() or obj.user.username,
        }
    
    def get_invited_by_detail(self, obj):
        """Get invited by user details"""
        if obj.invited_by:
            return {
                'id': obj.invited_by.id,
                'username': obj.invited_by.username,
                'email': obj.invited_by.email,
            }
        return None


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document list views"""
    
    created_by_name = serializers.SerializerMethodField()
    signatories_count = serializers.IntegerField(read_only=True)
    signed_count = serializers.IntegerField(read_only=True)
    pending_signatures_count = serializers.IntegerField(read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    file_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    generation_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'document_id',
            'title',
            'document_type',
            'status',
            'version',
            'file_size_mb',
            'file_url',
            'download_url',
            'generation_info',
            'signatories_count',
            'signed_count',
            'pending_signatures_count',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'document_id', 'created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        """Get creator name"""
        return obj.created_by.get_full_name() or obj.created_by.username
    
    def get_file_url(self, obj):
        """Get absolute URL for document file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_download_url(self, obj):
        """Get download URL for document file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/blockchain-backend/api/documents/{obj.id}/download/')
            return f'/blockchain-backend/api/documents/{obj.id}/download/'
        return None
    
    def get_generation_info(self, obj):
        """Get generation info if document was generated from a template"""
        # Check if this document has a generation record
        generation = obj.generation_history.first() if hasattr(obj, 'generation_history') else None
        if not generation:
            try:
                generation = DocumentGeneration.objects.filter(generated_document=obj).first()
            except:
                return None
        
        if generation:
            request = self.context.get('request')
            pdf_url = None
            if generation.generated_pdf:
                if request:
                    pdf_url = request.build_absolute_uri(generation.generated_pdf.url)
                else:
                    pdf_url = generation.generated_pdf.url
            
            return {
                'is_generated': True,
                'template_id': generation.template.id if generation.template else None,
                'template_name': generation.template.name if generation.template else None,
                'generated_pdf_url': pdf_url,
                'investor_id': generation.generation_data.get('investor_id') if generation.generation_data else None,
                'spv_id': generation.generation_data.get('spv_id') if generation.generation_data else None,
                'generated_at': generation.generated_at.isoformat() if generation.generated_at else None,
            }
        return None


class DocumentSerializer(serializers.ModelSerializer):
    """Full serializer for Document model"""
    
    created_by_detail = serializers.SerializerMethodField()
    signatories = DocumentSignatorySerializer(many=True, read_only=True)
    signatories_count = serializers.IntegerField(read_only=True)
    signed_count = serializers.IntegerField(read_only=True)
    pending_signatures_count = serializers.IntegerField(read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    file_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    syndicate_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id',
            'document_id',
            'title',
            'description',
            'document_type',
            'file',
            'file_url',
            'download_url',
            'original_filename',
            'file_size',
            'file_size_mb',
            'mime_type',
            'version',
            'parent_document',
            'status',
            'requires_admin_review',
            'review_notes',
            'created_by',
            'created_by_detail',
            'spv',
            'spv_detail',
            'syndicate',
            'syndicate_detail',
            'signatories',
            'signatories_count',
            'signed_count',
            'pending_signatures_count',
            'finalized_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'document_id', 'file_size', 'mime_type',
            'created_at', 'updated_at', 'finalized_at', 'file_url', 'download_url'
        ]
    
    def get_created_by_detail(self, obj):
        """Get creator user details"""
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username,
            'email': obj.created_by.email,
            'full_name': obj.created_by.get_full_name() or obj.created_by.username,
        }
    
    def get_file_url(self, obj):
        """Get absolute URL for document file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_download_url(self, obj):
        """Get download URL for document file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                # Return the download endpoint URL
                return request.build_absolute_uri(f'/api/documents/{obj.id}/download/')
            return f'/api/documents/{obj.id}/download/'
        return None
    
    def get_spv_detail(self, obj):
        """Get SPV details"""
        if obj.spv:
            return {
                'id': obj.spv.id,
                'display_name': obj.spv.display_name,
                'status': obj.spv.status,
            }
        return None
    
    def get_syndicate_detail(self, obj):
        """Get Syndicate details"""
        if obj.syndicate:
            return {
                'id': obj.syndicate.id,
                'firm_name': obj.syndicate.firm_name,
                'user': obj.syndicate.user.username,
            }
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating documents"""
    
    class Meta:
        model = Document
        fields = [
            'title',
            'description',
            'document_type',
            'file',
            'version',
            'status',
            'spv',
            'syndicate',
        ]
    
    def validate(self, data):
        """Validate document data"""
        if not data.get('file') and not self.instance:
            raise serializers.ValidationError({
                'file': 'File is required when creating a document.'
            })
        return data


class DocumentStatisticsSerializer(serializers.Serializer):
    """Serializer for document statistics"""
    
    total_documents = serializers.IntegerField()
    pending_signatures = serializers.IntegerField()
    signed_documents = serializers.IntegerField()
    rejected = serializers.IntegerField()
    draft = serializers.IntegerField()
    pending_review = serializers.IntegerField()
    finalized = serializers.IntegerField()


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for DocumentTemplate model"""
    
    created_by_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id',
            'name',
            'description',
            'version',
            'category',
            'scope',
            'jurisdiction_scope',
            'template_content',
            'content_type',
            'template_file',
            'required_fields',
            'configurable_fields',
            'enable_digital_signature',
            'is_active',
            'created_by',
            'created_by_detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_created_by_detail(self, obj):
        """Get creator user details"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email,
            }
        return None


class DocumentTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template list views"""
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id',
            'name',
            'description',
            'version',
            'category',
            'scope',
            'jurisdiction_scope',
            'content_type',
            'configurable_fields',
            'enable_digital_signature',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DocumentGenerationSerializer(serializers.ModelSerializer):
    """Serializer for DocumentGeneration model"""
    
    template_detail = DocumentTemplateListSerializer(source='template', read_only=True)
    generated_document_detail = DocumentListSerializer(source='generated_document', read_only=True)
    generated_by_detail = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    pdf_download_url = serializers.SerializerMethodField()
    pdf_file_size_mb = serializers.FloatField(read_only=True)
    
    class Meta:
        model = DocumentGeneration
        fields = [
            'id',
            'template',
            'template_detail',
            'generated_document',
            'generated_document_detail',
            'generated_pdf',
            'pdf_url',
            'pdf_download_url',
            'pdf_filename',
            'pdf_file_size',
            'pdf_file_size_mb',
            'generation_data',
            'generated_by',
            'generated_by_detail',
            'generated_at',
            'enable_digital_signature',
        ]
        read_only_fields = ['id', 'generated_at']
    
    def get_generated_by_detail(self, obj):
        """Get generator user details"""
        return {
            'id': obj.generated_by.id,
            'username': obj.generated_by.username,
            'email': obj.generated_by.email,
            'full_name': obj.generated_by.get_full_name() or obj.generated_by.username,
        }
    
    def get_pdf_url(self, obj):
        """Get absolute URL for generated PDF file"""
        if obj.generated_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.generated_pdf.url)
            return obj.generated_pdf.url
        return None
    
    def get_pdf_download_url(self, obj):
        """Get download URL for generated PDF file"""
        if obj.generated_pdf:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/document-generations/{obj.id}/download/')
            return f'/api/document-generations/{obj.id}/download/'
        return None


class DocumentGenerationRequestSerializer(serializers.Serializer):
    """
    Serializer for document generation request.
    
    Supports two ways to provide investor and SPV names:
    1. Direct: Pass investor_name and spv_name in field_data
    2. By ID: Pass investor_id and spv_id - names will be resolved automatically
    
    Example payload with IDs:
    {
        "template_id": 5,
        "investor_id": 10,  // Optional - resolves to investor_name
        "spv_id": 3,        // Optional - resolves to spv_name
        "field_data": {
            "investment_amount": 100000,
            "default_close_period_days": "30",
            "legal_entity_name": "Entity Name"
        }
    }
    """
    
    template_id = serializers.IntegerField(help_text="ID of the template to use")
    field_data = serializers.JSONField(help_text="Field values for template generation")
    enable_digital_signature = serializers.BooleanField(
        default=False,
        help_text="Enable digital signature workflow"
    )
    title = serializers.CharField(
        required=False,
        help_text="Custom title for generated document (optional)"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Description for generated document (optional)"
    )
    # ID-based resolution for investor and SPV names
    investor_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Investor user ID - will auto-resolve to investor_name in field_data"
    )
    spv_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="SPV ID - will auto-resolve to spv_name in field_data. Also used for document association."
    )
    syndicate_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Associated Syndicate ID (optional)"
    )
    signatories = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text="List of signatories. Format: [{'user_id': 1, 'role': 'Investor'}, ...]"
    )
    
    def validate_template_id(self, value):
        """Validate template exists and is active"""
        try:
            template = DocumentTemplate.objects.get(id=value, is_active=True)
        except DocumentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found or is not active.")
        return value
    
    def validate_investor_id(self, value):
        """Validate investor user exists"""
        if value is not None:
            from users.models import CustomUser
            try:
                user = CustomUser.objects.get(id=value, role='investor')
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("Investor not found with the given ID.")
        return value
    
    def validate_spv_id(self, value):
        """Validate SPV exists"""
        if value is not None:
            from spv.models import SPV
            try:
                spv = SPV.objects.get(id=value)
            except SPV.DoesNotExist:
                raise serializers.ValidationError("SPV not found with the given ID.")
        return value
    
    def validate_field_data(self, value):
        """Validate field data is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("field_data must be a dictionary.")
        return value


class SyndicateDocumentDefaultsSerializer(serializers.ModelSerializer):
    """
    Serializer for SyndicateDocumentDefaults model.
    
    Used for "Syndicate Document Defaults" section in the UI.
    Renders fields from template.configurable_fields[] (NOT required_fields[]).
    The goal is to save syndicate-level defaults, not generate a specific PDF.
    """
    
    template_detail = DocumentTemplateListSerializer(source='template', read_only=True)
    syndicate_detail = serializers.SerializerMethodField()
    created_by_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = SyndicateDocumentDefaults
        fields = [
            'id',
            'syndicate',
            'syndicate_detail',
            'template',
            'template_detail',
            'default_values',
            'created_by',
            'created_by_detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_syndicate_detail(self, obj):
        """Get syndicate details"""
        if obj.syndicate:
            return {
                'id': obj.syndicate.id,
                'firm_name': obj.syndicate.firm_name if hasattr(obj.syndicate, 'firm_name') else str(obj.syndicate),
                'user': obj.syndicate.user.username if obj.syndicate.user else None,
            }
        return None
    
    def get_created_by_detail(self, obj):
        """Get creator user details"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
                'email': obj.created_by.email,
            }
        return None
    
    def validate_default_values(self, value):
        """Validate default_values is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("default_values must be a dictionary.")
        return value


class SyndicateDocumentDefaultsCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating syndicate document defaults"""
    
    class Meta:
        model = SyndicateDocumentDefaults
        fields = [
            'syndicate',
            'template',
            'default_values',
        ]
    
    def validate_default_values(self, value):
        """Validate default_values is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("default_values must be a dictionary.")
        return value
