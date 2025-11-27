from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Sum, Count, Case, When, IntegerField
from django.utils import timezone
from django.http import FileResponse
from .models import Transfer, TransferDocument, Request, RequestDocument
from .serializers import (
    TransferSerializer,
    TransferListSerializer,
    TransferCreateSerializer,
    TransferDocumentSerializer,
    TransferStatisticsSerializer,
    RequestSerializer,
    RequestListSerializer,
    RequestCreateSerializer,
    RequestDocumentSerializer,
    RequestStatisticsSerializer,
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of transfers or admins to view/edit them."""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access all transfers
        if request.user.is_staff or request.user.role == 'admin':
            return True
        # Users can only access their own transfers (as requester or recipient)
        return obj.requester == request.user or obj.recipient == request.user


class TransferViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transfers
    Provides CRUD operations for Transfer model
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
        if not (user.is_staff or user.role == 'admin'):
            # Users can only see their own transfers
            queryset = queryset.filter(
                Q(requester=user) | Q(recipient=user)
            ).distinct()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by SPV
        spv_id = self.request.query_params.get('spv', None)
        if spv_id:
            queryset = queryset.filter(spv_id=spv_id)
        
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
        
        return queryset.select_related('requester', 'recipient', 'spv', 'approved_by', 'rejected_by').prefetch_related('documents')
    
    def perform_create(self, serializer):
        """Set requester to current user when creating transfer"""
        serializer.save(requester=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get transfer statistics
        GET /api/transfers/statistics/
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_transfers = queryset.count()
        pending_approval = queryset.filter(status='pending_approval').count()
        completed = queryset.filter(status='completed').count()
        rejected = queryset.filter(status='rejected').count()
        approved = queryset.filter(status='approved').count()
        
        # Calculate transfer volume (sum of amounts for completed transfers)
        transfer_volume = queryset.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Count urgent transfers (pending for more than 7 days)
        from datetime import timedelta
        urgent_date = timezone.now() - timedelta(days=7)
        urgent_count = queryset.filter(
            status='pending_approval',
            requested_at__lt=urgent_date
        ).count()
        
        stats = {
            'total_transfers': total_transfers,
            'pending_approval': pending_approval,
            'completed': completed,
            'rejected': rejected,
            'approved': approved,
            'transfer_volume': transfer_volume,
            'urgent_count': urgent_count,
        }
        
        serializer = TransferStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a transfer
        POST /api/transfers/{id}/approve/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can approve transfers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        transfer = self.get_object()
        
        if transfer.status != 'pending_approval':
            return Response({
                'error': f'Transfer is not pending approval. Current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer.status = 'approved'
        transfer.approved_by = request.user
        transfer.approved_at = timezone.now()
        transfer.save()
        
        return Response({
            'message': 'Transfer approved successfully',
            'data': TransferSerializer(transfer).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a transfer
        POST /api/transfers/{id}/reject/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can reject transfers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        transfer = self.get_object()
        
        if transfer.status != 'pending_approval':
            return Response({
                'error': f'Transfer is not pending approval. Current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        rejection_reason = request.data.get('rejection_reason')
        rejection_notes = request.data.get('rejection_notes', '')
        
        if not rejection_reason:
            return Response({
                'error': 'rejection_reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if rejection_reason not in dict(Transfer.REJECTION_REASON_CHOICES):
            return Response({
                'error': f'Invalid rejection reason. Must be one of: {", ".join([choice[0] for choice in Transfer.REJECTION_REASON_CHOICES])}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer.status = 'rejected'
        transfer.rejection_reason = rejection_reason
        transfer.rejection_notes = rejection_notes
        transfer.rejected_by = request.user
        transfer.rejected_at = timezone.now()
        transfer.save()
        
        return Response({
            'message': 'Transfer rejected successfully',
            'data': TransferSerializer(transfer).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark transfer as completed
        POST /api/transfers/{id}/complete/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can complete transfers'
            }, status=status.HTTP_403_FORBIDDEN)
        
        transfer = self.get_object()
        
        if transfer.status != 'approved':
            return Response({
                'error': f'Transfer must be approved before completion. Current status: {transfer.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transfer.status = 'completed'
        transfer.completed_at = timezone.now()
        transfer.save()
        
        return Response({
            'message': 'Transfer completed successfully',
            'data': TransferSerializer(transfer).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """
        Add a document to the transfer
        POST /api/transfers/{id}/add_document/
        """
        transfer = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or 
                transfer.requester == request.user or transfer.recipient == request.user):
            return Response({
                'error': 'You do not have permission to add documents to this transfer'
            }, status=status.HTTP_403_FORBIDDEN)
        
        file = request.FILES.get('file')
        if not file:
            return Response({
                'error': 'File is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        document = TransferDocument.objects.create(
            transfer=transfer,
            file=file,
            uploaded_by=request.user,
        )
        
        serializer = TransferDocumentSerializer(document)
        return Response({
            'message': 'Document added successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class TransferDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing transfer documents
    """
    queryset = TransferDocument.objects.all()
    serializer_class = TransferDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter documents based on user role"""
        user = self.request.user
        queryset = TransferDocument.objects.all()
        
        if not (user.is_staff or user.role == 'admin'):
            # Users can only see documents for their transfers
            queryset = queryset.filter(
                Q(transfer__requester=user) | Q(transfer__recipient=user)
            ).distinct()
        
        # Filter by transfer
        transfer_id = self.request.query_params.get('transfer', None)
        if transfer_id:
            queryset = queryset.filter(transfer_id=transfer_id)
        
        return queryset.select_related('transfer', 'uploaded_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download document file
        GET /api/transfer-documents/{id}/download/
        """
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


# Request ViewSets

class RequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing requests
    Provides CRUD operations for Request model
    """
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return RequestCreateSerializer
        elif self.action == 'list':
            return RequestListSerializer
        return RequestSerializer
    
    def get_queryset(self):
        """Filter requests based on user role and query parameters"""
        user = self.request.user
        queryset = Request.objects.all()
        
        # Filter by user role
        if not (user.is_staff or user.role == 'admin'):
            # Users can only see their own requests
            queryset = queryset.filter(requester=user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by request type
        request_type = self.request.query_params.get('request_type', None)
        if request_type:
            queryset = queryset.filter(request_type=request_type)
        
        # Filter by SPV
        spv_id = self.request.query_params.get('spv', None)
        if spv_id:
            queryset = queryset.filter(spv_id=spv_id)
        
        # Search functionality
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
        """Set requester to current user when creating request"""
        serializer.save(requester=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get request statistics
        GET /api/requests/statistics/
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_requests = queryset.count()
        pending = queryset.filter(status='pending').count()
        approved_today = queryset.filter(
            status='approved',
            approved_at__date=timezone.now().date()
        ).count()
        rejected = queryset.filter(status='rejected').count()
        high_priority = queryset.filter(priority__in=['high', 'urgent']).count()
        
        # Count overdue requests
        overdue = queryset.filter(
            status='pending',
            due_date__lt=timezone.now()
        ).count()
        
        stats = {
            'total_requests': total_requests,
            'pending': pending,
            'approved_today': approved_today,
            'rejected': rejected,
            'high_priority': high_priority,
            'overdue': overdue,
        }
        
        serializer = RequestStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a request
        POST /api/requests/{id}/approve/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
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
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a request
        POST /api/requests/{id}/reject/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
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
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def add_document(self, request, pk=None):
        """
        Add a document to the request
        POST /api/requests/{id}/add_document/
        """
        req = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or 
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
    """
    ViewSet for managing request documents
    """
    queryset = RequestDocument.objects.all()
    serializer_class = RequestDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter documents based on user role"""
        user = self.request.user
        queryset = RequestDocument.objects.all()
        
        if not (user.is_staff or user.role == 'admin'):
            # Users can only see documents for their requests
            queryset = queryset.filter(request__requester=user)
        
        # Filter by request
        request_id = self.request.query_params.get('request', None)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        
        return queryset.select_related('request', 'uploaded_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download document file
        GET /api/request-documents/{id}/download/
        """
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
