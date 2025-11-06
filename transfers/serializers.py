from rest_framework import serializers
from .models import Transfer, TransferDocument
from users.models import CustomUser


class TransferDocumentSerializer(serializers.ModelSerializer):
    """Serializer for TransferDocument model"""
    
    uploaded_by_detail = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferDocument
        fields = [
            'id',
            'transfer',
            'file',
            'original_filename',
            'file_size',
            'file_size_mb',
            'mime_type',
            'uploaded_by',
            'uploaded_by_detail',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'file_size', 'mime_type', 'uploaded_at']
    
    def get_uploaded_by_detail(self, obj):
        """Get uploader user details"""
        return {
            'id': obj.uploaded_by.id,
            'username': obj.uploaded_by.username,
            'email': obj.uploaded_by.email,
        }
    
    def get_file_size_mb(self, obj):
        """Get file size in MB"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class TransferListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for transfer list views"""
    
    requester_detail = serializers.SerializerMethodField()
    recipient_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    documents_count = serializers.IntegerField(read_only=True)
    is_urgent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'id',
            'transfer_id',
            'requester',
            'requester_detail',
            'recipient',
            'recipient_detail',
            'spv',
            'spv_detail',
            'shares',
            'amount',
            'transfer_fee',
            'net_amount',
            'status',
            'investor_name',
            'requested_at',
            'documents_count',
            'is_urgent',
        ]
        read_only_fields = ['id', 'transfer_id', 'requested_at']
    
    def get_requester_detail(self, obj):
        """Get requester user details"""
        return {
            'id': obj.requester.id,
            'username': obj.requester.username,
            'email': obj.requester.email,
            'full_name': obj.requester.get_full_name() or obj.requester.username,
        }
    
    def get_recipient_detail(self, obj):
        """Get recipient user details"""
        return {
            'id': obj.recipient.id,
            'username': obj.recipient.username,
            'email': obj.recipient.email,
            'full_name': obj.recipient.get_full_name() or obj.recipient.username,
        }
    
    def get_spv_detail(self, obj):
        """Get SPV details"""
        return {
            'id': obj.spv.id,
            'display_name': obj.spv.display_name,
            'status': obj.spv.status,
        }


class TransferSerializer(serializers.ModelSerializer):
    """Full serializer for Transfer model"""
    
    requester_detail = serializers.SerializerMethodField()
    recipient_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    documents = TransferDocumentSerializer(many=True, read_only=True)
    documents_count = serializers.IntegerField(read_only=True)
    approved_by_detail = serializers.SerializerMethodField()
    rejected_by_detail = serializers.SerializerMethodField()
    is_urgent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'id',
            'transfer_id',
            'requester',
            'requester_detail',
            'recipient',
            'recipient_detail',
            'spv',
            'spv_detail',
            'shares',
            'amount',
            'transfer_fee',
            'net_amount',
            'status',
            'rejection_reason',
            'rejection_notes',
            'rejected_by',
            'rejected_by_detail',
            'rejected_at',
            'approved_by',
            'approved_by_detail',
            'approved_at',
            'completed_at',
            'description',
            'investor_name',
            'documents',
            'documents_count',
            'is_urgent',
            'requested_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'transfer_id', 'net_amount',
            'approved_at', 'rejected_at', 'completed_at',
            'requested_at', 'updated_at'
        ]
    
    def get_requester_detail(self, obj):
        """Get requester user details"""
        return {
            'id': obj.requester.id,
            'username': obj.requester.username,
            'email': obj.requester.email,
            'full_name': obj.requester.get_full_name() or obj.requester.username,
        }
    
    def get_recipient_detail(self, obj):
        """Get recipient user details"""
        return {
            'id': obj.recipient.id,
            'username': obj.recipient.username,
            'email': obj.recipient.email,
            'full_name': obj.recipient.get_full_name() or obj.recipient.username,
        }
    
    def get_spv_detail(self, obj):
        """Get SPV details"""
        return {
            'id': obj.spv.id,
            'display_name': obj.spv.display_name,
            'status': obj.spv.status,
        }
    
    def get_approved_by_detail(self, obj):
        """Get approver user details"""
        if obj.approved_by:
            return {
                'id': obj.approved_by.id,
                'username': obj.approved_by.username,
                'email': obj.approved_by.email,
            }
        return None
    
    def get_rejected_by_detail(self, obj):
        """Get rejector user details"""
        if obj.rejected_by:
            return {
                'id': obj.rejected_by.id,
                'username': obj.rejected_by.username,
                'email': obj.rejected_by.email,
            }
        return None


class TransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transfers"""
    
    class Meta:
        model = Transfer
        fields = [
            'requester',
            'recipient',
            'spv',
            'shares',
            'amount',
            'transfer_fee',
            'description',
            'investor_name',
        ]
    
    def validate(self, data):
        """Validate transfer data"""
        requester = data.get('requester')
        recipient = data.get('recipient')
        
        if requester == recipient:
            raise serializers.ValidationError({
                'recipient': 'Recipient must be different from requester.'
            })
        
        return data


class TransferStatisticsSerializer(serializers.Serializer):
    """Serializer for transfer statistics"""
    
    total_transfers = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    completed = serializers.IntegerField()
    rejected = serializers.IntegerField()
    approved = serializers.IntegerField()
    transfer_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    urgent_count = serializers.IntegerField()

