from rest_framework import serializers
from .models import Transfer, TransferDocument, TransferHistory, OwnershipLedger, Request, RequestDocument, TransferAgreementDocument
from users.models import CustomUser
from decimal import Decimal


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


class TransferHistorySerializer(serializers.ModelSerializer):
    """Serializer for TransferHistory model (Audit Trail)"""
    
    action_by_detail = serializers.SerializerMethodField()
    from_user_detail = serializers.SerializerMethodField()
    to_user_detail = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = TransferHistory
        fields = [
            'id',
            'transfer',
            'action',
            'action_display',
            'action_by',
            'action_by_detail',
            'action_at',
            'from_user',
            'from_user_detail',
            'to_user',
            'to_user_detail',
            'percentage_transferred',
            'amount_transferred',
            'from_user_ownership_before',
            'from_user_ownership_after',
            'to_user_ownership_before',
            'to_user_ownership_after',
            'ip_address',
            'notes',
            'metadata',
        ]
        read_only_fields = ['id', 'action_at']
    
    def get_action_by_detail(self, obj):
        if obj.action_by:
            return {
                'id': obj.action_by.id,
                'username': obj.action_by.username,
                'full_name': obj.action_by.get_full_name() or obj.action_by.username,
            }
        return None
    
    def get_from_user_detail(self, obj):
        if obj.from_user:
            return {
                'id': obj.from_user.id,
                'username': obj.from_user.username,
                'full_name': obj.from_user.get_full_name() or obj.from_user.username,
            }
        return None
    
    def get_to_user_detail(self, obj):
        if obj.to_user:
            return {
                'id': obj.to_user.id,
                'username': obj.to_user.username,
                'full_name': obj.to_user.get_full_name() or obj.to_user.username,
            }
        return None


class OwnershipLedgerSerializer(serializers.ModelSerializer):
    """Serializer for OwnershipLedger model (Cap Table Entry)"""
    
    investor_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)
    created_by_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = OwnershipLedger
        fields = [
            'id',
            'investor',
            'investor_detail',
            'spv',
            'spv_detail',
            'entry_type',
            'entry_type_display',
            'investment',
            'transfer',
            'ownership_change',
            'ownership_before',
            'ownership_after',
            'amount_change',
            'amount_before',
            'amount_after',
            'notes',
            'created_at',
            'created_by',
            'created_by_detail',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_investor_detail(self, obj):
        return {
            'id': obj.investor.id,
            'username': obj.investor.username,
            'email': obj.investor.email,
            'full_name': obj.investor.get_full_name() or obj.investor.username,
        }
    
    def get_spv_detail(self, obj):
        return {
            'id': obj.spv.id,
            'display_name': obj.spv.display_name,
        }
    
    def get_created_by_detail(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username,
            }
        return None


class TransferListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for transfer list views"""
    
    requester_detail = serializers.SerializerMethodField()
    recipient_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    is_urgent = serializers.BooleanField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transfer_type_display = serializers.CharField(source='get_transfer_type_display', read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            'id',
            'transfer_id',
            'transfer_type',
            'transfer_type_display',
            'requester',
            'requester_detail',
            'recipient',
            'recipient_detail',
            'spv',
            'spv_detail',
            'shares',
            'ownership_percentage_transferred',
            'amount',
            'transfer_fee',
            'net_amount',
            'status',
            'status_display',
            'investor_name',
            'requested_at',
            'documents_count',
            'is_urgent',
            # Confirmation status
            'requester_confirmed',
            'recipient_confirmed',
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
    
    def get_documents_count(self, obj):
        return obj.documents.count() if hasattr(obj, 'documents') else 0


class TransferSerializer(serializers.ModelSerializer):
    """Full serializer for Transfer model with all fields"""
    
    requester_detail = serializers.SerializerMethodField()
    recipient_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    documents = TransferDocumentSerializer(many=True, read_only=True)
    history = TransferHistorySerializer(many=True, read_only=True)
    agreement_documents = serializers.SerializerMethodField()  # NEW: Agreement documents
    documents_count = serializers.SerializerMethodField()
    agreement_documents_count = serializers.SerializerMethodField()  # NEW
    approved_by_detail = serializers.SerializerMethodField()
    rejected_by_detail = serializers.SerializerMethodField()
    completed_by_detail = serializers.SerializerMethodField()
    is_urgent = serializers.BooleanField(read_only=True)
    is_full_transfer = serializers.BooleanField(read_only=True)
    is_partial_transfer = serializers.BooleanField(read_only=True)
    all_confirmations_received = serializers.BooleanField(read_only=True)
    ready_for_approval = serializers.BooleanField(read_only=True)
    can_complete = serializers.BooleanField(read_only=True)
    all_documents_signed = serializers.SerializerMethodField()  # NEW: Check if all docs signed
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transfer_type_display = serializers.CharField(source='get_transfer_type_display', read_only=True)
    esign_status_display = serializers.CharField(source='get_esign_status_display', read_only=True)
    
    class Meta:
        model = Transfer
        fields = [
            # Basic Info
            'id',
            'transfer_id',
            'transfer_type',
            'transfer_type_display',
            
            # Participants
            'requester',
            'requester_detail',
            'recipient',
            'recipient_detail',
            'recipient_email',
            
            # SPV & Investment
            'spv',
            'spv_detail',
            'source_investment',
            'destination_investment',
            
            # Transfer Details
            'shares',
            'ownership_percentage_transferred',
            'requester_ownership_before',
            'recipient_ownership_before',
            'requester_ownership_after',
            'recipient_ownership_after',
            
            # Financial
            'amount',
            'transfer_fee',
            'transfer_fee_percentage',
            'net_amount',
            
            # Status
            'status',
            'status_display',
            
            # Requester Confirmations
            'requester_confirmed',
            'requester_confirmed_at',
            'requester_ip_address',
            'requester_terms_accepted',
            'requester_ownership_acknowledged',
            'requester_confirmation_message',
            
            # Recipient Confirmations
            'recipient_confirmed',
            'recipient_confirmed_at',
            'recipient_ip_address',
            'recipient_terms_accepted',
            'recipient_ownership_acknowledged',
            'recipient_decline_reason',
            
            # Approval
            'approved_by',
            'approved_by_detail',
            'approved_at',
            'approver_compliance_verified',
            'approver_kyc_verified',
            'approver_lockup_verified',
            'approver_jurisdiction_verified',
            'approval_notes',
            
            # Rejection
            'rejection_reason',
            'rejection_notes',
            'rejected_by',
            'rejected_by_detail',
            'rejected_at',
            
            # Completion
            'completed_at',
            'completed_by',
            'completed_by_detail',
            
            # E-Sign
            'esign_required',
            'esign_status',
            'esign_status_display',
            'esign_provider',
            'esign_envelope_id',
            'esign_document_url',
            'requester_esign_at',
            'recipient_esign_at',
            'signed_document',
            
            # Additional
            'description',
            'investor_name',
            
            # Related Data
            'documents',
            'documents_count',
            'agreement_documents',  # NEW
            'agreement_documents_count',  # NEW
            'history',
            
            # Computed Properties
            'is_urgent',
            'is_full_transfer',
            'is_partial_transfer',
            'all_confirmations_received',
            'ready_for_approval',
            'can_complete',
            'all_documents_signed',  # NEW
            
            # Timestamps
            'requested_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'transfer_id', 'net_amount',
            'approved_at', 'rejected_at', 'completed_at',
            'requested_at', 'updated_at',
            'requester_confirmed_at', 'recipient_confirmed_at',
            'requester_ownership_after', 'recipient_ownership_after',
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
            'allocation': float(obj.spv.allocation or 0),
        }
    
    def get_approved_by_detail(self, obj):
        """Get approver user details"""
        if obj.approved_by:
            return {
                'id': obj.approved_by.id,
                'username': obj.approved_by.username,
                'email': obj.approved_by.email,
                'full_name': obj.approved_by.get_full_name() or obj.approved_by.username,
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
    
    def get_completed_by_detail(self, obj):
        """Get completer user details"""
        if obj.completed_by:
            return {
                'id': obj.completed_by.id,
                'username': obj.completed_by.username,
                'email': obj.completed_by.email,
            }
        return None
    
    def get_documents_count(self, obj):
        return obj.documents.count() if hasattr(obj, 'documents') else 0
    
    def get_agreement_documents(self, obj):
        """Get agreement documents for this transfer"""
        if hasattr(obj, 'agreement_documents'):
            from .serializers import TransferAgreementDocumentListSerializer
            return TransferAgreementDocumentListSerializer(
                obj.agreement_documents.filter(is_latest=True), 
                many=True,
                context=self.context
            ).data
        return []
    
    def get_agreement_documents_count(self, obj):
        """Get count of agreement documents"""
        if hasattr(obj, 'agreement_documents'):
            return obj.agreement_documents.filter(is_latest=True).count()
        return 0
    
    def get_all_documents_signed(self, obj):
        """Check if all required agreement documents are signed"""
        if hasattr(obj, 'agreement_documents'):
            agreement_docs = obj.agreement_documents.filter(is_latest=True)
            if agreement_docs.count() == 0:
                return False
            # All documents must be fully signed
            return all(doc.is_fully_signed for doc in agreement_docs)
        return False


class TransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/initiating transfers"""
    
    recipient_email = serializers.EmailField(required=False, allow_blank=True)
    
    class Meta:
        model = Transfer
        fields = [
            'recipient',
            'recipient_email',
            'spv',
            'transfer_type',
            'shares',
            'ownership_percentage_transferred',
            'amount',
            'transfer_fee',
            'description',
            'investor_name',
            'requester_confirmation_message',
        ]
    
    def validate(self, data):
        """Validate transfer data"""
        request = self.context.get('request')
        requester = request.user if request else None
        recipient = data.get('recipient')
        spv = data.get('spv')
        transfer_type = data.get('transfer_type', 'full')
        ownership_percentage = data.get('ownership_percentage_transferred', 0)
        
        # Cannot transfer to self
        if requester and recipient and requester == recipient:
            raise serializers.ValidationError({
                'recipient': 'Cannot transfer ownership to yourself.'
            })
        
        # Validate ownership percentage for partial transfer
        if transfer_type == 'partial':
            if not ownership_percentage or ownership_percentage <= 0:
                raise serializers.ValidationError({
                    'ownership_percentage_transferred': 'Ownership percentage is required for partial transfers.'
                })
            if ownership_percentage > 100:
                raise serializers.ValidationError({
                    'ownership_percentage_transferred': 'Ownership percentage cannot exceed 100%.'
                })
        
        # Validate requester has investment in SPV
        if requester and spv:
            from investors.dashboard_models import Investment
            investment = Investment.objects.filter(
                investor=requester,
                spv=spv,
                status='active'
            ).first()
            
            if not investment:
                raise serializers.ValidationError({
                    'spv': 'You do not have an active investment in this SPV.'
                })
            
            # For partial transfer, validate percentage doesn't exceed ownership
            if transfer_type == 'partial' and ownership_percentage:
                if ownership_percentage > investment.ownership_percentage:
                    raise serializers.ValidationError({
                        'ownership_percentage_transferred': f'You cannot transfer more than your current ownership ({investment.ownership_percentage}%).'
                    })
        
        return data
    
    def create(self, validated_data):
        """Create transfer with calculated fields"""
        request = self.context.get('request')
        requester = request.user if request else validated_data.get('requester')
        spv = validated_data.get('spv')
        
        # Get requester's current investment
        from investors.dashboard_models import Investment
        source_investment = Investment.objects.filter(
            investor=requester,
            spv=spv,
            status='active'
        ).first()
        
        # Calculate transfer fee (example: 1%)
        amount = validated_data.get('amount', Decimal('0'))
        transfer_fee = validated_data.get('transfer_fee')
        if transfer_fee is None:
            transfer_fee = amount * Decimal('0.01')  # 1% fee
        
        # Set ownership before values
        validated_data['requester_ownership_before'] = source_investment.ownership_percentage if source_investment else 0
        
        # Check recipient's existing ownership
        recipient = validated_data.get('recipient')
        recipient_investment = Investment.objects.filter(
            investor=recipient,
            spv=spv,
            status='active'
        ).first()
        validated_data['recipient_ownership_before'] = recipient_investment.ownership_percentage if recipient_investment else 0
        
        # Set source investment
        validated_data['source_investment'] = source_investment
        
        # Set status to pending requester confirmation
        validated_data['status'] = 'pending_requester_confirmation'
        
        # Calculate transfer fee percentage
        if amount > 0:
            validated_data['transfer_fee_percentage'] = (transfer_fee / amount) * 100
        
        validated_data['transfer_fee'] = transfer_fee
        validated_data['requester'] = requester
        
        return super().create(validated_data)


class RequesterConfirmationSerializer(serializers.Serializer):
    """Serializer for requester confirmation step with signature"""
    
    confirm_transfer = serializers.BooleanField(required=True)
    acknowledge_ownership_loss = serializers.BooleanField(required=True)
    accept_terms = serializers.BooleanField(required=True)
    message_to_recipient = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    # Signature field - can be text signature or base64 encoded image
    signature = serializers.CharField(
        required=True,
        help_text="Signature data (text or base64 encoded image)"
    )
    signature_type = serializers.ChoiceField(
        choices=[('text', 'Text Signature'), ('image', 'Image Signature')],
        default='text',
        help_text="Type of signature: 'text' for typed name, 'image' for drawn signature"
    )
    
    def validate(self, data):
        if not all([data.get('confirm_transfer'), data.get('acknowledge_ownership_loss'), data.get('accept_terms')]):
            raise serializers.ValidationError('All confirmations must be checked to proceed.')
        if not data.get('signature'):
            raise serializers.ValidationError({'signature': 'Signature is required.'})
        return data


class RecipientConfirmationSerializer(serializers.Serializer):
    """Serializer for recipient acceptance step with signature"""
    
    accept_transfer = serializers.BooleanField(required=True)
    acknowledge_ownership_receipt = serializers.BooleanField(required=True)
    accept_terms = serializers.BooleanField(required=True)
    
    # Signature field - can be text signature or base64 encoded image
    signature = serializers.CharField(
        required=True,
        help_text="Signature data (text or base64 encoded image)"
    )
    signature_type = serializers.ChoiceField(
        choices=[('text', 'Text Signature'), ('image', 'Image Signature')],
        default='text',
        help_text="Type of signature: 'text' for typed name, 'image' for drawn signature"
    )
    
    def validate(self, data):
        if not all([data.get('accept_transfer'), data.get('acknowledge_ownership_receipt'), data.get('accept_terms')]):
            raise serializers.ValidationError('All confirmations must be checked to accept the transfer.')
        if not data.get('signature'):
            raise serializers.ValidationError({'signature': 'Signature is required.'})
        return data


class RecipientDeclineSerializer(serializers.Serializer):
    """Serializer for recipient declining transfer"""
    
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class ManagerApprovalSerializer(serializers.Serializer):
    """Serializer for manager/admin approval step"""
    
    compliance_verified = serializers.BooleanField(required=True)
    kyc_verified = serializers.BooleanField(required=True)
    lockup_verified = serializers.BooleanField(default=True)
    jurisdiction_verified = serializers.BooleanField(default=True)
    documents_reviewed = serializers.BooleanField(
        required=True,
        help_text="Confirm that all transfer documents have been reviewed"
    )
    approval_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    
    def validate(self, data):
        if not data.get('compliance_verified'):
            raise serializers.ValidationError({
                'compliance_verified': 'Compliance verification is required.'
            })
        if not data.get('kyc_verified'):
            raise serializers.ValidationError({
                'kyc_verified': 'KYC verification is required.'
            })
        if not data.get('documents_reviewed'):
            raise serializers.ValidationError({
                'documents_reviewed': 'You must confirm that you have reviewed all documents.'
            })
        return data


class ManagerRejectionSerializer(serializers.Serializer):
    """Serializer for manager/admin rejection"""
    
    rejection_reason = serializers.ChoiceField(
        choices=Transfer.REJECTION_REASON_CHOICES,
        required=True
    )
    rejection_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class TransferStatisticsSerializer(serializers.Serializer):
    """Serializer for transfer statistics"""
    
    total_transfers = serializers.IntegerField()
    draft = serializers.IntegerField()
    pending_requester_confirmation = serializers.IntegerField()
    pending_recipient_confirmation = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    approved = serializers.IntegerField()
    completed = serializers.IntegerField()
    rejected = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    transfer_volume = serializers.DecimalField(max_digits=20, decimal_places=2)
    urgent_count = serializers.IntegerField()


class CapTableSerializer(serializers.Serializer):
    """Serializer for SPV cap table (ownership distribution)"""
    
    investor_id = serializers.IntegerField()
    investor_username = serializers.CharField()
    investor_email = serializers.EmailField()
    investor_full_name = serializers.CharField()
    ownership_percentage = serializers.DecimalField(max_digits=10, decimal_places=4)
    invested_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    current_value = serializers.DecimalField(max_digits=20, decimal_places=2)
    investment_date = serializers.DateTimeField()
    last_transfer_date = serializers.DateTimeField(allow_null=True)


class OwnershipChainSerializer(serializers.Serializer):
    """Serializer for ownership chain history of a specific investment"""
    
    sequence = serializers.IntegerField()
    date = serializers.DateTimeField()
    event_type = serializers.CharField()
    from_user = serializers.DictField(allow_null=True)
    to_user = serializers.DictField(allow_null=True)
    ownership_percentage = serializers.DecimalField(max_digits=10, decimal_places=4)
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    transfer_id = serializers.CharField(allow_null=True)


# Request Serializers

class RequestDocumentSerializer(serializers.ModelSerializer):
    """Serializer for RequestDocument model"""
    
    uploaded_by_detail = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = RequestDocument
        fields = [
            'id',
            'request',
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


class RequestListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for request list views"""
    
    requester_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    is_urgent_priority = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Request
        fields = [
            'id',
            'request_id',
            'request_type',
            'title',
            'priority',
            'requester',
            'requester_detail',
            'related_entity',
            'spv',
            'spv_detail',
            'status',
            'created_at',
            'due_date',
            'documents_count',
            'is_overdue',
            'is_urgent_priority',
        ]
        read_only_fields = ['id', 'request_id', 'created_at']
    
    def get_requester_detail(self, obj):
        """Get requester user details"""
        return {
            'id': obj.requester.id,
            'username': obj.requester.username,
            'email': obj.requester.email,
            'full_name': obj.requester.get_full_name() or obj.requester.username,
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
    
    def get_documents_count(self, obj):
        return obj.documents.count() if hasattr(obj, 'documents') else 0


class RequestSerializer(serializers.ModelSerializer):
    """Full serializer for Request model"""
    
    requester_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    documents = RequestDocumentSerializer(many=True, read_only=True)
    documents_count = serializers.SerializerMethodField()
    approved_by_detail = serializers.SerializerMethodField()
    rejected_by_detail = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    is_urgent_priority = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Request
        fields = [
            'id',
            'request_id',
            'request_type',
            'title',
            'description',
            'priority',
            'requester',
            'requester_detail',
            'related_entity',
            'spv',
            'spv_detail',
            'status',
            'approved_by',
            'approved_by_detail',
            'approved_at',
            'approval_notes',
            'rejected_by',
            'rejected_by_detail',
            'rejected_at',
            'rejection_reason',
            'documents',
            'documents_count',
            'is_overdue',
            'is_urgent_priority',
            'created_at',
            'updated_at',
            'due_date',
        ]
        read_only_fields = [
            'id', 'request_id', 'approved_at', 'rejected_at',
            'created_at', 'updated_at'
        ]
    
    def get_requester_detail(self, obj):
        """Get requester user details"""
        return {
            'id': obj.requester.id,
            'username': obj.requester.username,
            'email': obj.requester.email,
            'full_name': obj.requester.get_full_name() or obj.requester.username,
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
    
    def get_documents_count(self, obj):
        return obj.documents.count() if hasattr(obj, 'documents') else 0


class RequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating requests"""
    
    class Meta:
        model = Request
        fields = [
            'request_type',
            'title',
            'description',
            'priority',
            'related_entity',
            'spv',
            'due_date',
        ]


class RequestStatisticsSerializer(serializers.Serializer):
    """Serializer for request statistics"""
    
    total_requests = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved_today = serializers.IntegerField()
    rejected = serializers.IntegerField()
    high_priority = serializers.IntegerField()
    overdue = serializers.IntegerField()


# ===========================================
# TRANSFER AGREEMENT DOCUMENT SERIALIZERS
# ===========================================

class TransferAgreementDocumentSerializer(serializers.ModelSerializer):
    """Serializer for TransferAgreementDocument model"""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    requester_signature_status_display = serializers.CharField(source='get_requester_signature_status_display', read_only=True)
    recipient_signature_status_display = serializers.CharField(source='get_recipient_signature_status_display', read_only=True)
    is_fully_signed = serializers.BooleanField(read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    file_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferAgreementDocument
        fields = [
            'id',
            'transfer',
            'document_type',
            'document_type_display',
            'document_number',
            'title',
            'description',
            'file',
            'file_url',
            'download_url',
            'file_size',
            'file_size_display',
            
            # Requester Signature
            'requester_signature_status',
            'requester_signature_status_display',
            'requester_signed_at',
            'requester_signature_ip',
            
            # Recipient Signature
            'recipient_signature_status',
            'recipient_signature_status_display',
            'recipient_signed_at',
            'recipient_signature_ip',
            
            # Document Data
            'document_data',
            
            # Version & Access
            'version',
            'is_latest',
            'can_requester_view',
            'can_recipient_view',
            'can_requester_download',
            'can_recipient_download',
            
            # Computed
            'is_fully_signed',
            
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'document_number', 'file_size', 
            'created_at', 'updated_at'
        ]
    
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
                return request.build_absolute_uri(f'/api/transfer-agreement-documents/{obj.id}/download/')
            return f'/api/transfer-agreement-documents/{obj.id}/download/'
        return None


class TransferAgreementDocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for agreement document list views"""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    is_fully_signed = serializers.BooleanField(read_only=True)
    file_size_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = TransferAgreementDocument
        fields = [
            'id',
            'transfer',
            'document_type',
            'document_type_display',
            'document_number',
            'title',
            'requester_signature_status',
            'recipient_signature_status',
            'is_fully_signed',
            'file_size_display',
            'can_requester_view',
            'can_recipient_view',
            'created_at',
        ]
        read_only_fields = ['id', 'document_number', 'created_at']
