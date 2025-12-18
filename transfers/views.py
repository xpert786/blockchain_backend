"""
Transfer Views - Complete ownership transfer flow with signature/confirmation workflow.

This module provides APIs for:
1. Create/Initiate transfer request
2. Requester confirmation (seller signs)
3. Recipient acceptance/decline (buyer signs)
4. Manager/Admin approval
5. Complete transfer (update ownership)
6. View transfer history and cap table
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, F
from django.db import transaction
from django.utils import timezone
from django.http import FileResponse
from decimal import Decimal

from .models import Transfer, TransferDocument, TransferHistory, OwnershipLedger, Request, RequestDocument, TransferAgreementDocument
from .serializers import (
    TransferSerializer,
    TransferListSerializer,
    TransferCreateSerializer,
    TransferDocumentSerializer,
    TransferStatisticsSerializer,
    TransferHistorySerializer,
    OwnershipLedgerSerializer,
    RequesterConfirmationSerializer,
    RecipientConfirmationSerializer,
    RecipientDeclineSerializer,
    ManagerApprovalSerializer,
    ManagerRejectionSerializer,
    CapTableSerializer,
    OwnershipChainSerializer,
    RequestSerializer,
    RequestListSerializer,
    RequestCreateSerializer,
    RequestDocumentSerializer,
    RequestStatisticsSerializer,
    TransferAgreementDocumentSerializer,
    TransferAgreementDocumentListSerializer,
)
from .document_utils import (
    generate_transfer_request_document,
    generate_acceptance_document,
    generate_final_agreement_document,
)
from investors.dashboard_models import Investment, Notification


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def create_transfer_history(transfer, action, user, request=None, notes=None, **kwargs):
    """Helper function to create transfer history entry"""
    history = TransferHistory.objects.create(
        transfer=transfer,
        action=action,
        action_by=user,
        from_user=transfer.requester,
        to_user=transfer.recipient,
        percentage_transferred=transfer.ownership_percentage_transferred,
        amount_transferred=transfer.amount,
        from_user_ownership_before=transfer.requester_ownership_before,
        from_user_ownership_after=transfer.requester_ownership_after,
        to_user_ownership_before=transfer.recipient_ownership_before,
        to_user_ownership_after=transfer.recipient_ownership_after,
        ip_address=get_client_ip(request) if request else None,
        user_agent=get_user_agent(request) if request else None,
        notes=notes,
        metadata=kwargs.get('metadata', {})
    )
    return history


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of transfers or admins to view/edit them."""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access all transfers
        if request.user.is_staff or getattr(request.user, 'role', None) == 'admin':
            return True
        # Syndicate Manager can access transfers for their SPVs
        if hasattr(obj, 'spv') and obj.spv and obj.spv.created_by == request.user:
            return True
        # Users can only access their own transfers (as requester or recipient)
        return obj.requester == request.user or obj.recipient == request.user


class TransferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ownership transfers.
    
    Provides complete transfer workflow:
    - Create transfer request
    - Requester confirmation
    - Recipient acceptance/decline
    - Manager approval/rejection
    - Execute transfer (update ownership)
    """
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return TransferCreateSerializer
        elif self.action == 'list':
            return TransferListSerializer
        return TransferSerializer
    
    def get_queryset(self):
        """Filter transfers based on user role and query parameters"""
        user = self.request.user
        queryset = Transfer.objects.all()
        
        # Filter by user role
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            # Syndicate managers can see transfers for their SPVs
            from spv.models import SPV
            managed_spvs = SPV.objects.filter(created_by=user).values_list('id', flat=True)
            
            queryset = queryset.filter(
                Q(requester=user) | 
                Q(recipient=user) |
                Q(spv_id__in=managed_spvs)
            ).distinct()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by transfer type
        transfer_type = self.request.query_params.get('transfer_type', None)
        if transfer_type:
            queryset = queryset.filter(transfer_type=transfer_type)
        
        # Filter by SPV
        spv_id = self.request.query_params.get('spv', None)
        if spv_id:
            queryset = queryset.filter(spv_id=spv_id)
        
        # Filter by role (requester/recipient)
        role = self.request.query_params.get('role', None)
        if role == 'requester':
            queryset = queryset.filter(requester=user)
        elif role == 'recipient':
            queryset = queryset.filter(recipient=user)
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(transfer_id__icontains=search) |
                Q(requester__username__icontains=search) |
                Q(requester__email__icontains=search) |
                Q(recipient__username__icontains=search) |
                Q(recipient__email__icontains=search) |
                Q(spv__display_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.select_related(
            'requester', 'recipient', 'spv', 
            'approved_by', 'rejected_by', 'completed_by',
            'source_investment', 'destination_investment'
        ).prefetch_related('documents', 'history')
    
    def perform_create(self, serializer):
        """Set requester to current user when creating transfer"""
        serializer.save(requester=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create a new transfer request"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            transfer = serializer.save()
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='initiated',
                user=request.user,
                request=request,
                notes='Transfer request initiated'
            )
            
            # Notify requester to confirm
            Notification.objects.create(
                user=request.user,
                notification_type='transfer',
                title='Transfer Request Created',
                message=f'Your transfer request to {transfer.recipient.get_full_name() or transfer.recipient.username} has been created. Please confirm to proceed.',
                priority='high',
                action_required=True,
                action_url=f'/transfers/{transfer.id}/confirm',
                action_label='Confirm Transfer'
            )
        
        return Response({
            'success': True,
            'message': 'Transfer request created. Please confirm to proceed.',
            'data': TransferSerializer(transfer).data
        }, status=status.HTTP_201_CREATED)
    
    # ==========================================
    # STEP 1: REQUESTER CONFIRMATION
    # ==========================================
    
    @action(detail=True, methods=['post'])
    def requester_confirm(self, request, pk=None):
        """
        Requester confirms the transfer initiation with checkboxes.
        
        POST /api/transfers/{id}/requester_confirm/
        
        Payload:
        {
            "confirm_transfer": true,
            "acknowledge_ownership_loss": true,
            "accept_terms": true,
            "message_to_recipient": "optional message"
        }
        """
        transfer = self.get_object()
        
        # Verify requester
        if transfer.requester != request.user:
            return Response({
                'success': False,
                'error': 'Only the requester can confirm this transfer.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status
        if transfer.status not in ['draft', 'pending_requester_confirmation']:
            return Response({
                'success': False,
                'error': f'Transfer cannot be confirmed in current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate confirmations
        serializer = RequesterConfirmationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update transfer
            transfer.requester_confirmed = True
            transfer.requester_confirmed_at = timezone.now()
            transfer.requester_ip_address = get_client_ip(request)
            transfer.requester_user_agent = get_user_agent(request)
            transfer.requester_terms_accepted = True
            transfer.requester_ownership_acknowledged = True
            transfer.requester_confirmation_message = serializer.validated_data.get('message_to_recipient', '')
            transfer.status = 'pending_recipient_confirmation'
            transfer.save()
            
            # Generate Transfer Request Document with Requester's signature
            signature = serializer.validated_data.get('signature')
            signature_type = serializer.validated_data.get('signature_type', 'text')
            
            transfer_request_doc = generate_transfer_request_document(
                transfer=transfer,
                requester_signature=signature,
                signature_ip=get_client_ip(request),
                signature_type=signature_type
            )
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='requester_confirmed',
                user=request.user,
                request=request,
                notes='Requester confirmed and signed the transfer request',
                metadata={
                    'document_id': transfer_request_doc.id,
                    'document_number': transfer_request_doc.document_number
                }
            )
            
            # Notify recipient
            Notification.objects.create(
                user=transfer.recipient,
                notification_type='transfer',
                title='Transfer Request Received',
                message=f'{transfer.requester.get_full_name() or transfer.requester.username} wants to transfer {transfer.ownership_percentage_transferred}% ownership in {transfer.spv.display_name} to you.',
                priority='high',
                action_required=True,
                action_url=f'/transfers/{transfer.id}/accept',
                action_label='Review Transfer'
            )
        
        return Response({
            'success': True,
            'message': 'Transfer confirmed. Waiting for recipient acceptance.',
            'data': TransferSerializer(transfer, context={'request': request}).data,
            'document': {
                'id': transfer_request_doc.id,
                'document_number': transfer_request_doc.document_number,
                'document_type': 'transfer_request',
                'title': transfer_request_doc.title,
            }
        })
    
    # ==========================================
    # STEP 2: RECIPIENT ACCEPTANCE/DECLINE
    # ==========================================
    
    @action(detail=True, methods=['post'])
    def recipient_accept(self, request, pk=None):
        """
        Recipient accepts the transfer with checkboxes.
        
        POST /api/transfers/{id}/recipient_accept/
        
        Payload:
        {
            "accept_transfer": true,
            "acknowledge_ownership_receipt": true,
            "accept_terms": true
        }
        """
        transfer = self.get_object()
        
        # Verify recipient
        if transfer.recipient != request.user:
            return Response({
                'success': False,
                'error': 'Only the recipient can accept this transfer.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status
        if transfer.status != 'pending_recipient_confirmation':
            return Response({
                'success': False,
                'error': f'Transfer cannot be accepted in current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check recipient KYC
        from investors.dashboard_models import KYCStatus
        try:
            kyc_status = KYCStatus.objects.get(user=request.user)
            if kyc_status.status != 'verified':
                return Response({
                    'success': False,
                    'error': 'Your KYC must be verified to accept ownership transfers.',
                    'error_code': 'KYC_NOT_VERIFIED'
                }, status=status.HTTP_403_FORBIDDEN)
        except KYCStatus.DoesNotExist:
            return Response({
                'success': False,
                'error': 'You must complete KYC verification to accept ownership transfers.',
                'error_code': 'KYC_REQUIRED'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate confirmations
        serializer = RecipientConfirmationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update transfer
            transfer.recipient_confirmed = True
            transfer.recipient_confirmed_at = timezone.now()
            transfer.recipient_ip_address = get_client_ip(request)
            transfer.recipient_user_agent = get_user_agent(request)
            transfer.recipient_terms_accepted = True
            transfer.recipient_ownership_acknowledged = True
            transfer.status = 'pending_approval'
            transfer.save()
            
            # Get signature data
            signature = serializer.validated_data.get('signature')
            signature_type = serializer.validated_data.get('signature_type', 'text')
            recipient_ip = get_client_ip(request)
            
            # Get requester's signature from transfer request document
            transfer_request_doc = transfer.agreement_documents.filter(
                document_type='transfer_request',
                is_latest=True
            ).first()
            
            requester_signature = transfer_request_doc.requester_signature_data if transfer_request_doc else None
            requester_ip = transfer_request_doc.requester_signature_ip if transfer_request_doc else None
            
            # Generate Acceptance Document (Investor B's signature only)
            acceptance_doc = generate_acceptance_document(
                transfer=transfer,
                recipient_signature=signature,
                signature_ip=recipient_ip,
                signature_type=signature_type
            )
            
            # Generate Final Agreement Document (Both signatures)
            final_agreement_doc = generate_final_agreement_document(
                transfer=transfer,
                requester_signature=requester_signature,
                requester_signature_ip=requester_ip,
                recipient_signature=signature,
                recipient_signature_ip=recipient_ip,
                requester_signature_type='text',
                recipient_signature_type=signature_type
            )
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='recipient_accepted',
                user=request.user,
                request=request,
                notes='Recipient accepted and signed the transfer request',
                metadata={
                    'acceptance_document_id': acceptance_doc.id,
                    'acceptance_document_number': acceptance_doc.document_number,
                    'final_agreement_document_id': final_agreement_doc.id,
                    'final_agreement_document_number': final_agreement_doc.document_number
                }
            )
            
            # Notify requester
            Notification.objects.create(
                user=transfer.requester,
                notification_type='transfer',
                title='Transfer Accepted by Recipient',
                message=f'{transfer.recipient.get_full_name() or transfer.recipient.username} has accepted your transfer request. Waiting for manager approval.',
                priority='normal'
            )
            
            # Notify Syndicate Manager for approval
            if transfer.spv and transfer.spv.created_by:
                Notification.objects.create(
                    user=transfer.spv.created_by,
                    notification_type='transfer',
                    title='Transfer Pending Approval - Documents Ready for Review',
                    message=f'Transfer from {transfer.requester.get_full_name()} to {transfer.recipient.get_full_name()} in {transfer.spv.display_name} requires your approval. All documents have been signed.',
                    priority='high',
                    action_required=True,
                    action_url=f'/transfers/{transfer.id}/review',
                    action_label='Review Transfer'
                )
        
        return Response({
            'success': True,
            'message': 'Transfer accepted. Waiting for manager approval.',
            'data': TransferSerializer(transfer, context={'request': request}).data,
            'documents': {
                'acceptance': {
                    'id': acceptance_doc.id,
                    'document_number': acceptance_doc.document_number,
                    'document_type': 'acceptance',
                    'title': acceptance_doc.title,
                },
                'final_agreement': {
                    'id': final_agreement_doc.id,
                    'document_number': final_agreement_doc.document_number,
                    'document_type': 'final_agreement',
                    'title': final_agreement_doc.title,
                }
            }
        })
    
    @action(detail=True, methods=['post'])
    def recipient_decline(self, request, pk=None):
        """
        Recipient declines the transfer.
        
        POST /api/transfers/{id}/recipient_decline/
        
        Payload:
        {
            "reason": "optional decline reason"
        }
        """
        transfer = self.get_object()
        
        # Verify recipient
        if transfer.recipient != request.user:
            return Response({
                'success': False,
                'error': 'Only the recipient can decline this transfer.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status
        if transfer.status != 'pending_recipient_confirmation':
            return Response({
                'success': False,
                'error': f'Transfer cannot be declined in current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RecipientDeclineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            transfer.status = 'recipient_declined'
            transfer.rejection_reason = 'recipient_declined'
            transfer.recipient_decline_reason = serializer.validated_data.get('reason', 'Recipient declined the transfer')
            transfer.rejected_by = request.user
            transfer.rejected_at = timezone.now()
            transfer.save()
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='recipient_declined',
                user=request.user,
                request=request,
                notes=f'Recipient declined: {transfer.recipient_decline_reason}'
            )
            
            # Notify requester
            Notification.objects.create(
                user=transfer.requester,
                notification_type='transfer',
                title='Transfer Declined',
                message=f'{transfer.recipient.get_full_name() or transfer.recipient.username} declined your transfer request.',
                priority='high'
            )
        
        return Response({
            'success': True,
            'message': 'Transfer declined.',
            'data': TransferSerializer(transfer).data
        })
    
    # ==========================================
    # STEP 3: MANAGER/ADMIN APPROVAL
    # ==========================================
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Manager/Admin approves the transfer.
        
        POST /api/transfers/{id}/approve/
        
        Payload:
        {
            "compliance_verified": true,
            "kyc_verified": true,
            "lockup_verified": true,
            "jurisdiction_verified": true,
            "documents_reviewed": true,
            "approval_notes": "optional notes"
        }
        """
        transfer = self.get_object()
        user = request.user
        
        # Check permissions
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        is_manager = transfer.spv and transfer.spv.created_by == user
        
        if not (is_admin or is_manager):
            return Response({
                'success': False,
                'error': 'Only managers or admins can approve transfers.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status
        if transfer.status != 'pending_approval':
            return Response({
                'success': False,
                'error': f'Transfer cannot be approved in current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify all documents are signed
        agreement_docs = transfer.agreement_documents.filter(is_latest=True)
        if agreement_docs.count() == 0:
            return Response({
                'success': False,
                'error': 'No agreement documents found. Both parties must sign before approval.',
                'error_code': 'NO_DOCUMENTS'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for required document types
        doc_types = set(agreement_docs.values_list('document_type', flat=True))
        required_types = {'transfer_request', 'acceptance', 'final_agreement'}
        missing_types = required_types - doc_types
        if missing_types:
            return Response({
                'success': False,
                'error': f'Missing required documents: {", ".join(missing_types)}',
                'error_code': 'MISSING_DOCUMENTS'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check all documents are fully signed
        for doc in agreement_docs:
            if not doc.is_fully_signed:
                return Response({
                    'success': False,
                    'error': f'Document {doc.document_number} ({doc.get_document_type_display()}) is not fully signed.',
                    'error_code': 'UNSIGNED_DOCUMENTS'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify documents_reviewed flag
        documents_reviewed = request.data.get('documents_reviewed', False)
        if not documents_reviewed:
            return Response({
                'success': False,
                'error': 'You must confirm that you have reviewed all documents before approval.',
                'error_code': 'DOCUMENTS_NOT_REVIEWED'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate approval data
        serializer = ManagerApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            transfer.status = 'approved'
            transfer.approved_by = user
            transfer.approved_at = timezone.now()
            transfer.approver_compliance_verified = serializer.validated_data['compliance_verified']
            transfer.approver_kyc_verified = serializer.validated_data['kyc_verified']
            transfer.approver_lockup_verified = serializer.validated_data.get('lockup_verified', True)
            transfer.approver_jurisdiction_verified = serializer.validated_data.get('jurisdiction_verified', True)
            transfer.approval_notes = serializer.validated_data.get('approval_notes', '')
            transfer.save()
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='approved',
                user=user,
                request=request,
                notes=f'Approved by {user.get_full_name() or user.username}'
            )
            
            # Notify both parties
            Notification.objects.create(
                user=transfer.requester,
                notification_type='transfer',
                title='Transfer Approved',
                message=f'Your transfer to {transfer.recipient.get_full_name()} has been approved. The transfer will be executed shortly.',
                priority='high'
            )
            
            Notification.objects.create(
                user=transfer.recipient,
                notification_type='transfer',
                title='Transfer Approved',
                message=f'The transfer from {transfer.requester.get_full_name()} has been approved. You will receive ownership shortly.',
                priority='high'
            )
        
        return Response({
            'success': True,
            'message': 'Transfer approved successfully.',
            'data': TransferSerializer(transfer).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Manager/Admin rejects the transfer.
        
        POST /api/transfers/{id}/reject/
        
        Payload:
        {
            "rejection_reason": "compliance_issue",
            "rejection_notes": "Details about rejection"
        }
        """
        transfer = self.get_object()
        user = request.user
        
        # Check permissions
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        is_manager = transfer.spv and transfer.spv.created_by == user
        
        if not (is_admin or is_manager):
            return Response({
                'success': False,
                'error': 'Only managers or admins can reject transfers.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status
        if transfer.status != 'pending_approval':
            return Response({
                'success': False,
                'error': f'Transfer cannot be rejected in current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate rejection data
        serializer = ManagerRejectionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            transfer.status = 'rejected'
            transfer.rejection_reason = serializer.validated_data['rejection_reason']
            transfer.rejection_notes = serializer.validated_data.get('rejection_notes', '')
            transfer.rejected_by = user
            transfer.rejected_at = timezone.now()
            transfer.save()
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='rejected',
                user=user,
                request=request,
                notes=f'Rejected: {transfer.get_rejection_reason_display()}'
            )
            
            # Notify both parties
            for notify_user in [transfer.requester, transfer.recipient]:
                Notification.objects.create(
                    user=notify_user,
                    notification_type='transfer',
                    title='Transfer Rejected',
                    message=f'The transfer has been rejected. Reason: {transfer.get_rejection_reason_display()}',
                    priority='high'
                )
        
        return Response({
            'success': True,
            'message': 'Transfer rejected.',
            'data': TransferSerializer(transfer).data
        })
    
    # ==========================================
    # STEP 4: COMPLETE TRANSFER (Execute)
    # ==========================================
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete/Execute the approved transfer and update ownership.
        
        POST /api/transfers/{id}/complete/
        
        This action:
        1. Updates requester's investment (decrease ownership)
        2. Creates/Updates recipient's investment (increase ownership)
        3. Creates ownership ledger entries
        4. Marks transfer as completed
        """
        transfer = self.get_object()
        user = request.user
        
        # Check permissions
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        is_manager = transfer.spv and transfer.spv.created_by == user
        
        if not (is_admin or is_manager):
            return Response({
                'success': False,
                'error': 'Only managers or admins can complete transfers.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status
        if transfer.status != 'approved':
            return Response({
                'success': False,
                'error': f'Transfer must be approved before completion. Current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Get source investment (requester's current investment)
            source_investment = transfer.source_investment
            if not source_investment:
                source_investment = Investment.objects.filter(
                    investor=transfer.requester,
                    spv=transfer.spv,
                    status='active'
                ).first()
            
            if not source_investment:
                return Response({
                    'success': False,
                    'error': 'Requester does not have an active investment in this SPV.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate transferred percentage
            if transfer.transfer_type == 'full':
                transferred_percentage = source_investment.ownership_percentage
                transferred_amount = source_investment.invested_amount
            else:
                transferred_percentage = transfer.ownership_percentage_transferred
                transferred_amount = transfer.amount
            
            # Validate sufficient ownership
            if transferred_percentage > source_investment.ownership_percentage:
                return Response({
                    'success': False,
                    'error': f'Insufficient ownership. Requester has {source_investment.ownership_percentage}%, trying to transfer {transferred_percentage}%.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Store before values
            requester_ownership_before = source_investment.ownership_percentage
            requester_amount_before = source_investment.invested_amount
            
            # Update requester's investment (DECREASE)
            source_investment.ownership_percentage -= transferred_percentage
            source_investment.invested_amount -= transferred_amount
            source_investment.current_value -= transferred_amount
            
            # If full transfer or zero remaining, mark as completed
            if source_investment.ownership_percentage <= 0:
                source_investment.status = 'completed'
                source_investment.ownership_percentage = Decimal('0')
                source_investment.invested_amount = Decimal('0')
                source_investment.current_value = Decimal('0')
            
            source_investment.save()
            
            # Create ledger entry for requester (outgoing)
            OwnershipLedger.objects.create(
                investor=transfer.requester,
                spv=transfer.spv,
                entry_type='transfer_out',
                investment=source_investment,
                transfer=transfer,
                ownership_change=-transferred_percentage,
                ownership_before=requester_ownership_before,
                ownership_after=source_investment.ownership_percentage,
                amount_change=-transferred_amount,
                amount_before=requester_amount_before,
                amount_after=source_investment.invested_amount,
                notes=f'Transferred to {transfer.recipient.username}',
                created_by=user
            )
            
            # Get or create recipient's investment (INCREASE)
            recipient_investment = Investment.objects.filter(
                investor=transfer.recipient,
                spv=transfer.spv,
                status='active'
            ).first()
            
            recipient_ownership_before = Decimal('0')
            recipient_amount_before = Decimal('0')
            
            if recipient_investment:
                recipient_ownership_before = recipient_investment.ownership_percentage
                recipient_amount_before = recipient_investment.invested_amount
                
                recipient_investment.ownership_percentage += transferred_percentage
                recipient_investment.invested_amount += transfer.net_amount
                recipient_investment.current_value += transfer.net_amount
                recipient_investment.save()
            else:
                # Create new investment for recipient
                recipient_investment = Investment.objects.create(
                    investor=transfer.recipient,
                    spv=transfer.spv,
                    syndicate_name=transfer.spv.display_name,
                    sector=source_investment.sector,
                    stage=source_investment.stage,
                    investment_type='syndicate_deal',
                    invested_amount=transfer.net_amount,
                    current_value=transfer.net_amount,
                    ownership_percentage=transferred_percentage,
                    status='active',
                    invested_at=timezone.now(),
                    commitment_date=timezone.now(),
                )
            
            # Create ledger entry for recipient (incoming)
            OwnershipLedger.objects.create(
                investor=transfer.recipient,
                spv=transfer.spv,
                entry_type='transfer_in',
                investment=recipient_investment,
                transfer=transfer,
                ownership_change=transferred_percentage,
                ownership_before=recipient_ownership_before,
                ownership_after=recipient_investment.ownership_percentage,
                amount_change=transfer.net_amount,
                amount_before=recipient_amount_before,
                amount_after=recipient_investment.invested_amount,
                notes=f'Received from {transfer.requester.username}',
                created_by=user
            )
            
            # Update transfer record
            transfer.status = 'completed'
            transfer.completed_at = timezone.now()
            transfer.completed_by = user
            transfer.source_investment = source_investment
            transfer.destination_investment = recipient_investment
            transfer.ownership_percentage_transferred = transferred_percentage
            transfer.requester_ownership_after = source_investment.ownership_percentage
            transfer.recipient_ownership_after = recipient_investment.ownership_percentage
            transfer.save()
            
            # Create history entry
            create_transfer_history(
                transfer=transfer,
                action='completed',
                user=user,
                request=request,
                notes=f'Transfer completed. {transferred_percentage}% ownership transferred.'
            )
            
            # Create ownership_updated history
            create_transfer_history(
                transfer=transfer,
                action='ownership_updated',
                user=user,
                request=request,
                notes=f'Ownership updated in database. Requester: {requester_ownership_before}% → {source_investment.ownership_percentage}%, Recipient: {recipient_ownership_before}% → {recipient_investment.ownership_percentage}%',
                metadata={
                    'requester_before': float(requester_ownership_before),
                    'requester_after': float(source_investment.ownership_percentage),
                    'recipient_before': float(recipient_ownership_before),
                    'recipient_after': float(recipient_investment.ownership_percentage),
                }
            )
            
            # Notify both parties
            Notification.objects.create(
                user=transfer.requester,
                notification_type='transfer',
                title='Transfer Completed',
                message=f'Your transfer of {transferred_percentage}% ownership to {transfer.recipient.get_full_name()} has been completed. Your new ownership: {source_investment.ownership_percentage}%',
                priority='high'
            )
            
            Notification.objects.create(
                user=transfer.recipient,
                notification_type='transfer',
                title='Ownership Received',
                message=f'You have received {transferred_percentage}% ownership in {transfer.spv.display_name} from {transfer.requester.get_full_name()}. Your total ownership: {recipient_investment.ownership_percentage}%',
                priority='high'
            )
        
        return Response({
            'success': True,
            'message': 'Transfer completed successfully. Ownership has been updated.',
            'data': TransferSerializer(transfer).data,
            'ownership_update': {
                'requester': {
                    'before': float(requester_ownership_before),
                    'after': float(source_investment.ownership_percentage),
                    'transferred': float(transferred_percentage)
                },
                'recipient': {
                    'before': float(recipient_ownership_before),
                    'after': float(recipient_investment.ownership_percentage),
                    'received': float(transferred_percentage)
                }
            }
        })
    
    # ==========================================
    # CANCEL TRANSFER
    # ==========================================
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a transfer (only by requester before completion).
        
        POST /api/transfers/{id}/cancel/
        """
        transfer = self.get_object()
        
        # Verify requester or admin
        if transfer.requester != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': 'Only the requester or admin can cancel this transfer.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check status - can only cancel before completion
        if transfer.status in ['completed', 'cancelled']:
            return Response({
                'success': False,
                'error': f'Transfer cannot be cancelled in current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            transfer.status = 'cancelled'
            transfer.save()
            
            create_transfer_history(
                transfer=transfer,
                action='cancelled',
                user=request.user,
                request=request,
                notes='Transfer cancelled by user'
            )
            
            # Notify recipient if they were already notified
            if transfer.requester_confirmed:
                Notification.objects.create(
                    user=transfer.recipient,
                    notification_type='transfer',
                    title='Transfer Cancelled',
                    message=f'The transfer from {transfer.requester.get_full_name()} has been cancelled.',
                    priority='normal'
                )
        
        return Response({
            'success': True,
            'message': 'Transfer cancelled.',
            'data': TransferSerializer(transfer).data
        })
    
    # ==========================================
    # STATISTICS
    # ==========================================
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get transfer statistics.
        
        GET /api/transfers/statistics/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_transfers': queryset.count(),
            'draft': queryset.filter(status='draft').count(),
            'pending_requester_confirmation': queryset.filter(status='pending_requester_confirmation').count(),
            'pending_recipient_confirmation': queryset.filter(status='pending_recipient_confirmation').count(),
            'pending_approval': queryset.filter(status='pending_approval').count(),
            'approved': queryset.filter(status='approved').count(),
            'completed': queryset.filter(status='completed').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
            'transfer_volume': queryset.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
            'urgent_count': 0,  # Calculate urgent transfers
        }
        
        # Count urgent (pending for more than 7 days)
        from datetime import timedelta
        urgent_date = timezone.now() - timedelta(days=7)
        stats['urgent_count'] = queryset.filter(
            status__in=['pending_approval', 'pending_recipient_confirmation'],
            requested_at__lt=urgent_date
        ).count()
        
        serializer = TransferStatisticsSerializer(stats)
        return Response(serializer.data)
    
    # ==========================================
    # TRANSFER HISTORY
    # ==========================================
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """
        Get transfer history/audit trail.
        
        GET /api/transfers/{id}/history/
        """
        transfer = self.get_object()
        history = transfer.history.all().order_by('-action_at')
        serializer = TransferHistorySerializer(history, many=True)
        
        return Response({
            'success': True,
            'transfer_id': transfer.transfer_id,
            'history': serializer.data
        })
    
    # ==========================================
    # DOCUMENTS
    # ==========================================
    
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """
        Add a document to the transfer.
        
        POST /api/transfers/{id}/add_document/
        """
        transfer = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or 
                getattr(request.user, 'role', None) == 'admin' or 
                transfer.requester == request.user or 
                transfer.recipient == request.user):
            return Response({
                'success': False,
                'error': 'You do not have permission to add documents to this transfer.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('file')
        if not file:
            return Response({
                'success': False,
                'error': 'File is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        document = TransferDocument.objects.create(
            transfer=transfer,
            file=file,
            uploaded_by=request.user,
        )
        
        serializer = TransferDocumentSerializer(document)
        return Response({
            'success': True,
            'message': 'Document added successfully.',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


# ==========================================
# CAP TABLE & OWNERSHIP CHAIN VIEWS
# ==========================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_cap_table(request, spv_id):
    """
    Get cap table (ownership distribution) for an SPV.
    
    GET /api/transfers/cap-table/{spv_id}/
    
    Returns list of all investors and their ownership percentages.
    """
    from spv.models import SPV
    
    try:
        spv = SPV.objects.get(id=spv_id)
    except SPV.DoesNotExist:
        return Response({
            'success': False,
            'error': 'SPV not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permission
    user = request.user
    is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
    is_manager = spv.created_by == user
    is_investor = Investment.objects.filter(investor=user, spv=spv, status='active').exists()
    
    if not (is_admin or is_manager or is_investor):
        return Response({
            'success': False,
            'error': 'You do not have permission to view this cap table.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all active investments for this SPV
    investments = Investment.objects.filter(
        spv=spv,
        status='active',
        ownership_percentage__gt=0
    ).select_related('investor').order_by('-ownership_percentage')
    
    cap_table = []
    total_ownership = Decimal('0')
    total_invested = Decimal('0')
    
    for inv in investments:
        # Get last transfer date for this investor
        last_transfer = Transfer.objects.filter(
            Q(requester=inv.investor) | Q(recipient=inv.investor),
            spv=spv,
            status='completed'
        ).order_by('-completed_at').first()
        
        cap_table.append({
            'investor_id': inv.investor.id,
            'investor_username': inv.investor.username,
            'investor_email': inv.investor.email,
            'investor_full_name': inv.investor.get_full_name() or inv.investor.username,
            'ownership_percentage': inv.ownership_percentage,
            'invested_amount': inv.invested_amount,
            'current_value': inv.current_value,
            'investment_date': inv.created_at,
            'last_transfer_date': last_transfer.completed_at if last_transfer else None,
        })
        
        total_ownership += inv.ownership_percentage
        total_invested += inv.invested_amount
    
    return Response({
        'success': True,
        'spv': {
            'id': spv.id,
            'display_name': spv.display_name,
            'allocation': float(spv.allocation or 0),
        },
        'summary': {
            'total_investors': len(cap_table),
            'total_ownership_allocated': float(total_ownership),
            'total_invested': float(total_invested),
        },
        'cap_table': cap_table
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ownership_chain(request, spv_id, investor_id):
    """
    Get ownership chain history for a specific investor in an SPV.
    
    GET /api/transfers/ownership-chain/{spv_id}/{investor_id}/
    
    Returns complete history of how ownership was acquired/transferred.
    """
    from spv.models import SPV
    from users.models import CustomUser
    
    try:
        spv = SPV.objects.get(id=spv_id)
        investor = CustomUser.objects.get(id=investor_id)
    except (SPV.DoesNotExist, CustomUser.DoesNotExist):
        return Response({
            'success': False,
            'error': 'SPV or Investor not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permission
    user = request.user
    is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
    is_manager = spv.created_by == user
    is_self = user.id == investor_id
    
    if not (is_admin or is_manager or is_self):
        return Response({
            'success': False,
            'error': 'You do not have permission to view this ownership chain.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get ledger entries
    ledger_entries = OwnershipLedger.objects.filter(
        investor=investor,
        spv=spv
    ).order_by('created_at')
    
    chain = []
    sequence = 1
    
    for entry in ledger_entries:
        from_user_data = None
        to_user_data = None
        
        if entry.transfer:
            from_user_data = {
                'id': entry.transfer.requester.id,
                'username': entry.transfer.requester.username,
                'full_name': entry.transfer.requester.get_full_name() or entry.transfer.requester.username,
            }
            to_user_data = {
                'id': entry.transfer.recipient.id,
                'username': entry.transfer.recipient.username,
                'full_name': entry.transfer.recipient.get_full_name() or entry.transfer.recipient.username,
            }
        
        chain.append({
            'sequence': sequence,
            'date': entry.created_at,
            'event_type': entry.get_entry_type_display(),
            'from_user': from_user_data,
            'to_user': to_user_data,
            'ownership_percentage': entry.ownership_after,
            'amount': entry.amount_after,
            'transfer_id': entry.transfer.transfer_id if entry.transfer else None,
        })
        sequence += 1
    
    # Get current investment
    current_investment = Investment.objects.filter(
        investor=investor,
        spv=spv,
        status='active'
    ).first()
    
    return Response({
        'success': True,
        'spv': {
            'id': spv.id,
            'display_name': spv.display_name,
        },
        'investor': {
            'id': investor.id,
            'username': investor.username,
            'full_name': investor.get_full_name() or investor.username,
        },
        'current_ownership': {
            'percentage': float(current_investment.ownership_percentage) if current_investment else 0,
            'amount': float(current_investment.invested_amount) if current_investment else 0,
        },
        'ownership_chain': chain
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_transfers(request):
    """
    Get all transfers for current user (as requester or recipient).
    
    GET /api/transfers/my-transfers/
    
    Query params:
    - role: 'requester' or 'recipient' (optional)
    - status: filter by status (optional)
    """
    user = request.user
    queryset = Transfer.objects.filter(
        Q(requester=user) | Q(recipient=user)
    ).select_related('requester', 'recipient', 'spv')
    
    # Filter by role
    role = request.query_params.get('role')
    if role == 'requester':
        queryset = queryset.filter(requester=user)
    elif role == 'recipient':
        queryset = queryset.filter(recipient=user)
    
    # Filter by status
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    serializer = TransferListSerializer(queryset.order_by('-requested_at'), many=True)
    
    return Response({
        'success': True,
        'count': queryset.count(),
        'transfers': serializer.data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pending_actions(request):
    """
    Get transfers requiring action from current user.
    
    GET /api/transfers/pending-actions/
    
    Returns transfers where user needs to:
    - Confirm (as requester)
    - Accept/Decline (as recipient)
    - Approve (as manager/admin)
    """
    user = request.user
    
    # Transfers needing requester confirmation
    need_requester_confirm = Transfer.objects.filter(
        requester=user,
        status='pending_requester_confirmation'
    )
    
    # Transfers needing recipient acceptance
    need_recipient_accept = Transfer.objects.filter(
        recipient=user,
        status='pending_recipient_confirmation'
    )
    
    # Transfers needing manager approval
    need_approval = Transfer.objects.none()
    is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
    
    if is_admin:
        need_approval = Transfer.objects.filter(status='pending_approval')
    else:
        # Check if user is manager of any SPVs
        from spv.models import SPV
        managed_spvs = SPV.objects.filter(created_by=user).values_list('id', flat=True)
        if managed_spvs:
            need_approval = Transfer.objects.filter(
                spv_id__in=managed_spvs,
                status='pending_approval'
            )
    
    return Response({
        'success': True,
        'pending_actions': {
            'need_requester_confirm': {
                'count': need_requester_confirm.count(),
                'transfers': TransferListSerializer(need_requester_confirm, many=True).data
            },
            'need_recipient_accept': {
                'count': need_recipient_accept.count(),
                'transfers': TransferListSerializer(need_recipient_accept, many=True).data
            },
            'need_approval': {
                'count': need_approval.count(),
                'transfers': TransferListSerializer(need_approval, many=True).data
            },
        },
        'total_pending': (
            need_requester_confirm.count() + 
            need_recipient_accept.count() + 
            need_approval.count()
        )
    })


# ==========================================
# TRANSFER DOCUMENT VIEWSET
# ==========================================

class TransferDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing transfer documents"""
    
    queryset = TransferDocument.objects.all()
    serializer_class = TransferDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter documents based on user role"""
        user = self.request.user
        queryset = TransferDocument.objects.all()
        
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            queryset = queryset.filter(
                Q(transfer__requester=user) | Q(transfer__recipient=user)
            ).distinct()
        
        transfer_id = self.request.query_params.get('transfer', None)
        if transfer_id:
            queryset = queryset.filter(transfer_id=transfer_id)
        
        return queryset.select_related('transfer', 'uploaded_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file"""
        document = self.get_object()
        
        if not document.file:
            return Response({
                'error': 'Document file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = FileResponse(
                document.file.open('rb'),
                content_type=document.mime_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
            return response
        except Exception as e:
            return Response({
                'error': f'Error downloading file: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# REQUEST VIEWSETS (Existing functionality)
# ==========================================

class RequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing requests"""
    
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RequestCreateSerializer
        elif self.action == 'list':
            return RequestListSerializer
        return RequestSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Request.objects.all()
        
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            queryset = queryset.filter(requester=user)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        request_type = self.request.query_params.get('request_type', None)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        spv_id = self.request.query_params.get('spv', None)
        if spv_id:
            queryset = queryset.filter(spv_id=spv_id)
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(request_id__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(requester__username__icontains=search) |
                Q(requester__email__icontains=search) |
                Q(related_entity__icontains=search)
            )
        
        return queryset.select_related('requester', 'spv', 'approved_by', 'rejected_by').prefetch_related('documents')
    
    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        
        stats = {
            'total_requests': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'approved_today': queryset.filter(
                status='approved',
                approved_at__date=timezone.now().date()
            ).count(),
            'rejected': queryset.filter(status='rejected').count(),
            'high_priority': queryset.filter(priority__in=['high', 'urgent']).count(),
            'overdue': queryset.filter(
                status='pending',
                due_date__lt=timezone.now()
            ).count(),
        }
        
        serializer = RequestStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'admin'):
            return Response({
                'error': 'Only admins can approve requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        req = self.get_object()
        
        if req.status != 'pending':
            return Response({
                'error': f'Request is not pending. Current status: {req.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        approval_notes = request.data.get('approval_notes', '')
        
        req.status = 'approved'
        req.approved_by = request.user
        req.approved_at = timezone.now()
        req.approval_notes = approval_notes
        req.save()
        
        return Response({
            'message': 'Request approved successfully',
            'data': RequestSerializer(req).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'admin'):
            return Response({
                'error': 'Only admins can reject requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        req = self.get_object()
        
        if req.status != 'pending':
            return Response({
                'error': f'Request is not pending. Current status: {req.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        if not rejection_reason:
            return Response({
                'error': 'rejection_reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        req.status = 'rejected'
        req.rejection_reason = rejection_reason
        req.rejected_by = request.user
        req.rejected_at = timezone.now()
        req.save()
        
        return Response({
            'message': 'Request rejected successfully',
            'data': RequestSerializer(req).data
        })
    
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        req = self.get_object()
        
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'admin' or 
                req.requester == request.user):
            return Response({
                'error': 'You do not have permission to add documents to this request'
            }, status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('file')
        if not file:
            return Response({
                'error': 'File is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        document = RequestDocument.objects.create(
            request=req,
            file=file,
            uploaded_by=request.user,
        )
        
        serializer = RequestDocumentSerializer(document)
        return Response({
            'message': 'Document added successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class RequestDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing request documents"""
    
    queryset = RequestDocument.objects.all()
    serializer_class = RequestDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = RequestDocument.objects.all()
        
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            queryset = queryset.filter(request__requester=user)
        
        request_id = self.request.query_params.get('request', None)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        
        return queryset.select_related('request', 'uploaded_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        document = self.get_object()
        
        if not document.file:
            return Response({
                'error': 'Document file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = FileResponse(
                document.file.open('rb'),
                content_type=document.mime_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
            return response
        except Exception as e:
            return Response({
                'error': f'Error downloading file: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# TRANSFER AGREEMENT DOCUMENT VIEWSET
# ==========================================

class TransferAgreementDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and downloading transfer agreement documents.
    
    These documents are auto-generated during the transfer workflow:
    - transfer_request: Generated when Investor A confirms (has A's signature)
    - acceptance: Generated when Investor B accepts (has B's signature)
    - final_agreement: Generated when B accepts (has both signatures)
    
    Access control:
    - Investor A (requester) can view/download documents they're allowed to see
    - Investor B (recipient) can view/download documents they're allowed to see
    - Syndicate Manager/Admin can view/download all documents
    """
    
    queryset = TransferAgreementDocument.objects.all()
    serializer_class = TransferAgreementDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TransferAgreementDocumentListSerializer
        return TransferAgreementDocumentSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = TransferAgreementDocument.objects.filter(is_latest=True)
        
        # Filter by user role
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        
        if not is_admin:
            # Check if user is syndicate manager
            from spv.models import SPV
            managed_spvs = SPV.objects.filter(created_by=user).values_list('id', flat=True)
            
            # Filter documents where user is requester, recipient, or manages the SPV
            queryset = queryset.filter(
                Q(transfer__requester=user, can_requester_view=True) |
                Q(transfer__recipient=user, can_recipient_view=True) |
                Q(transfer__spv_id__in=managed_spvs)
            ).distinct()
        
        # Filter by transfer ID
        transfer_id = self.request.query_params.get('transfer', None)
        if transfer_id:
            queryset = queryset.filter(transfer_id=transfer_id)
        
        # Filter by document type
        document_type = self.request.query_params.get('document_type', None)
        if document_type:
            queryset = queryset.filter(document_type=document_type)
        
        return queryset.select_related('transfer', 'transfer__requester', 'transfer__recipient', 'transfer__spv')
    
    def retrieve(self, request, *args, **kwargs):
        """Get single document with permission check"""
        document = self.get_object()
        user = request.user
        
        # Check view permission
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        is_manager = document.transfer.spv and document.transfer.spv.created_by == user
        is_requester = document.transfer.requester == user
        is_recipient = document.transfer.recipient == user
        
        if not is_admin and not is_manager:
            if is_requester and not document.can_requester_view:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to view this document.'
                }, status=status.HTTP_403_FORBIDDEN)
            if is_recipient and not document.can_recipient_view:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to view this document.'
                }, status=status.HTTP_403_FORBIDDEN)
            if not is_requester and not is_recipient:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to view this document.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(document)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download the agreement document PDF.
        
        GET /api/transfer-agreement-documents/{id}/download/
        """
        document = self.get_object()
        user = request.user
        
        # Check download permission
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        is_manager = document.transfer.spv and document.transfer.spv.created_by == user
        is_requester = document.transfer.requester == user
        is_recipient = document.transfer.recipient == user
        
        if not is_admin and not is_manager:
            if is_requester and not document.can_requester_download:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to download this document.'
                }, status=status.HTTP_403_FORBIDDEN)
            if is_recipient and not document.can_recipient_download:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to download this document.'
                }, status=status.HTTP_403_FORBIDDEN)
            if not is_requester and not is_recipient:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to download this document.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        if not document.file:
            return Response({
                'success': False,
                'error': 'Document file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Get filename from document
            filename = f"{document.document_number}.pdf"
            
            response = FileResponse(
                document.file.open('rb'),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error downloading file: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def by_transfer(self, request):
        """
        Get all agreement documents for a specific transfer.
        
        GET /api/transfer-agreement-documents/by_transfer/?transfer_id=123
        """
        transfer_id = request.query_params.get('transfer_id')
        if not transfer_id:
            return Response({
                'success': False,
                'error': 'transfer_id query parameter is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get transfer and check permissions
        try:
            transfer = Transfer.objects.get(id=transfer_id)
        except Transfer.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Transfer not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        user = request.user
        is_admin = user.is_staff or getattr(user, 'role', None) == 'admin'
        is_manager = transfer.spv and transfer.spv.created_by == user
        is_requester = transfer.requester == user
        is_recipient = transfer.recipient == user
        
        if not (is_admin or is_manager or is_requester or is_recipient):
            return Response({
                'success': False,
                'error': 'You do not have permission to view documents for this transfer.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get documents based on user role
        documents = transfer.agreement_documents.filter(is_latest=True)
        
        if not (is_admin or is_manager):
            if is_requester:
                documents = documents.filter(can_requester_view=True)
            elif is_recipient:
                documents = documents.filter(can_recipient_view=True)
        
        serializer = TransferAgreementDocumentListSerializer(documents, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'transfer_id': transfer.transfer_id,
            'count': documents.count(),
            'documents': serializer.data
        })
