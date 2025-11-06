from rest_framework import serializers
from .models import Document, DocumentSignatory
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


class DocumentSerializer(serializers.ModelSerializer):
    """Full serializer for Document model"""
    
    created_by_detail = serializers.SerializerMethodField()
    signatories = DocumentSignatorySerializer(many=True, read_only=True)
    signatories_count = serializers.IntegerField(read_only=True)
    signed_count = serializers.IntegerField(read_only=True)
    pending_signatures_count = serializers.IntegerField(read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
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
            'created_at', 'updated_at', 'finalized_at'
        ]
    
    def get_created_by_detail(self, obj):
        """Get creator user details"""
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username,
            'email': obj.created_by.email,
            'full_name': obj.created_by.get_full_name() or obj.created_by.username,
        }
    
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

