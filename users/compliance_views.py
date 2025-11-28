"""
Compliance & Accreditation Document Management Views
Handles document upload, status tracking, and review workflows
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Case, When, IntegerField
from .models import ComplianceDocument, SyndicateProfile
from .serializers import (
    ComplianceDocumentSerializer,
    ComplianceDocumentListSerializer,
    ComplianceDocumentUploadSerializer,
    ComplianceDocumentStatusUpdateSerializer
)


class IsSyndicateOwnerOrManager(IsAuthenticated):
    """Permission: User must be syndicate owner or team manager"""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        
        # Check if user has syndicate profile
        try:
            syndicate = request.user.syndicate_profile
            return True
        except SyndicateProfile.DoesNotExist:
            return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user owns the syndicate"""
        try:
            syndicate = request.user.syndicate_profile
            return obj.syndicate == syndicate
        except SyndicateProfile.DoesNotExist:
            return False


class ComplianceDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Compliance Document Management
    
    Provides CRUD operations for compliance documents with:
    - Document upload with validation
    - Status management (pending, ok, expired, rejected)
    - Type and jurisdiction filtering
    - Expiry tracking
    - Review workflow
    """
    
    permission_classes = [IsSyndicateOwnerOrManager]
    serializer_class = ComplianceDocumentSerializer
    
    def get_queryset(self):
        """Return documents for user's syndicate"""
        try:
            syndicate = self.request.user.syndicate_profile
            queryset = ComplianceDocument.objects.filter(syndicate=syndicate)
            
            # Filter by document type
            doc_type = self.request.query_params.get('type')
            if doc_type:
                queryset = queryset.filter(document_type=doc_type)
            
            # Filter by jurisdiction
            jurisdiction = self.request.query_params.get('jurisdiction')
            if jurisdiction:
                queryset = queryset.filter(jurisdiction=jurisdiction)
            
            # Filter by status
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            # Filter by expiry
            expiry_filter = self.request.query_params.get('expiry')
            if expiry_filter == 'expired':
                queryset = queryset.filter(
                    expiry_date__isnull=False,
                    expiry_date__lt=timezone.now().date()
                )
            elif expiry_filter == 'expiring_soon':
                # Expiring within 30 days
                from datetime import timedelta
                expiry_threshold = timezone.now().date() + timedelta(days=30)
                queryset = queryset.filter(
                    expiry_date__isnull=False,
                    expiry_date__lte=expiry_threshold,
                    expiry_date__gt=timezone.now().date()
                )
            
            return queryset.select_related('uploaded_by', 'reviewed_by')
        except SyndicateProfile.DoesNotExist:
            return ComplianceDocument.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return ComplianceDocumentListSerializer
        elif self.action == 'create':
            return ComplianceDocumentUploadSerializer
        elif self.action == 'update_status':
            return ComplianceDocumentStatusUpdateSerializer
        return ComplianceDocumentSerializer
    
    def get_serializer_context(self):
        """Add syndicate to context"""
        context = super().get_serializer_context()
        try:
            context['syndicate'] = self.request.user.syndicate_profile
        except SyndicateProfile.DoesNotExist:
            context['syndicate'] = None
        return context
    
    def list(self, request, *args, **kwargs):
        """
        List all compliance documents
        
        Query Parameters:
        - type: Filter by document type (COI, Tax, Attest., etc.)
        - jurisdiction: Filter by jurisdiction
        - status: Filter by status (pending, ok, exp, missing, rejected)
        - expiry: Filter by expiry (expired, expiring_soon)
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': queryset.count(),
            'documents': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """
        Upload a new compliance document
        
        Request Body:
        - document_name: Document name
        - document_type: Type (COI, Tax, Attest., etc.)
        - jurisdiction: Jurisdiction code
        - file: Document file (pdf, docx, jpg, png - max 25MB)
        - expiry_date: Optional expiry date (YYYY-MM-DD)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        
        # Return full document details
        output_serializer = ComplianceDocumentSerializer(document, context=self.get_serializer_context())
        
        return Response({
            'success': True,
            'message': 'Document uploaded successfully',
            'document': output_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, *args, **kwargs):
        """Get details of a specific document"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'document': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """
        Update document details (excluding file)
        
        Request Body:
        - document_name: Updated name
        - document_type: Updated type
        - jurisdiction: Updated jurisdiction
        - expiry_date: Updated expiry date
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Don't allow file update via PUT/PATCH
        if 'file' in request.data:
            return Response({
                'success': False,
                'error': 'Cannot update file. Please upload a new document instead.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'message': 'Document updated successfully',
            'document': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete a compliance document"""
        instance = self.get_object()
        document_name = instance.document_name
        instance.delete()
        
        return Response({
            'success': True,
            'message': f'Document "{document_name}" deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update document status
        
        POST /api/compliance-documents/{id}/update_status/
        
        Request Body:
        - status: New status (pending, ok, exp, missing, rejected)
        - review_notes: Optional review notes
        """
        document = self.get_object()
        serializer = ComplianceDocumentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        review_notes = serializer.validated_data.get('review_notes', '')
        
        document.status = new_status
        if review_notes:
            document.review_notes = review_notes
        document.reviewed_by = request.user
        document.reviewed_at = timezone.now()
        document.save()
        
        output_serializer = ComplianceDocumentSerializer(document, context=self.get_serializer_context())
        
        return Response({
            'success': True,
            'message': f'Document status updated to {document.get_status_display()}',
            'document': output_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve document (set status to OK)
        
        POST /api/compliance-documents/{id}/approve/
        """
        document = self.get_object()
        document.mark_as_ok(reviewed_by=request.user)
        
        serializer = ComplianceDocumentSerializer(document, context=self.get_serializer_context())
        
        return Response({
            'success': True,
            'message': 'Document approved successfully',
            'document': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject document
        
        POST /api/compliance-documents/{id}/reject/
        
        Request Body:
        - notes: Rejection reason (required)
        """
        document = self.get_object()
        notes = request.data.get('notes')
        
        if not notes:
            return Response({
                'success': False,
                'error': 'Rejection notes are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        document.mark_as_rejected(notes=notes, reviewed_by=request.user)
        
        serializer = ComplianceDocumentSerializer(document, context=self.get_serializer_context())
        
        return Response({
            'success': True,
            'message': 'Document rejected',
            'document': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_expired(self, request, pk=None):
        """
        Mark document as expired
        
        POST /api/compliance-documents/{id}/mark_expired/
        """
        document = self.get_object()
        document.mark_as_expired()
        
        serializer = ComplianceDocumentSerializer(document, context=self.get_serializer_context())
        
        return Response({
            'success': True,
            'message': 'Document marked as expired',
            'document': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get compliance document statistics
        
        GET /api/compliance-documents/statistics/
        
        Returns:
        - Total documents
        - Documents by status
        - Documents by type
        - Expired documents count
        - Expiring soon count
        """
        queryset = self.get_queryset()
        
        # Count by status
        status_counts = queryset.values('status').annotate(count=Count('id'))
        status_breakdown = {item['status']: item['count'] for item in status_counts}
        
        # Count by type
        type_counts = queryset.values('document_type').annotate(count=Count('id'))
        type_breakdown = {item['document_type']: item['count'] for item in type_counts}
        
        # Expired documents
        expired_count = queryset.filter(
            expiry_date__isnull=False,
            expiry_date__lt=timezone.now().date()
        ).count()
        
        # Expiring soon (within 30 days)
        from datetime import timedelta
        expiry_threshold = timezone.now().date() + timedelta(days=30)
        expiring_soon_count = queryset.filter(
            expiry_date__isnull=False,
            expiry_date__lte=expiry_threshold,
            expiry_date__gt=timezone.now().date()
        ).count()
        
        return Response({
            'success': True,
            'statistics': {
                'total_documents': queryset.count(),
                'by_status': status_breakdown,
                'by_type': type_breakdown,
                'expired': expired_count,
                'expiring_soon': expiring_soon_count
            }
        })
    
    @action(detail=False, methods=['get'])
    def document_types(self, request):
        """
        Get available document types
        
        GET /api/compliance-documents/document_types/
        """
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in ComplianceDocument.DOCUMENT_TYPE_CHOICES]
        
        return Response({
            'success': True,
            'document_types': types
        })
    
    @action(detail=False, methods=['get'])
    def jurisdictions(self, request):
        """
        Get available jurisdictions
        
        GET /api/compliance-documents/jurisdictions/
        """
        jurisdictions = [{'value': choice[0], 'label': choice[1]} 
                        for choice in ComplianceDocument.JURISDICTION_CHOICES]
        
        return Response({
            'success': True,
            'jurisdictions': jurisdictions
        })
    
    @action(detail=False, methods=['get'])
    def status_options(self, request):
        """
        Get available status options
        
        GET /api/compliance-documents/status_options/
        """
        statuses = [{'value': choice[0], 'label': choice[1]} 
                   for choice in ComplianceDocument.STATUS_CHOICES]
        
        return Response({
            'success': True,
            'statuses': statuses
        })
