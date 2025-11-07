from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ParseError
from django.http import QueryDict
import logging
from .models import KYC
from .serializers import (
    KYCSerializer, 
    KYCCreateSerializer,
    KYCUpdateSerializer,
    KYCStatusUpdateSerializer
)

logger = logging.getLogger(__name__)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of KYC or admins to view/edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access all KYC records
        if request.user.is_staff or request.user.role == 'admin':
            return True
        # Users can only access their own KYC records
        return obj.user == request.user


class KYCViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing KYC records
    Provides CRUD operations for KYC model
    """
    queryset = KYC.objects.all()
    serializer_class = KYCSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    # Order matters: MultiPartParser must come first for file uploads
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_parsers(self):
        """
        Override to handle parser selection based on content type.
        Prevents JSON parser from trying to parse binary file data.
        """
        # Get content type from request
        if hasattr(self.request, 'content_type'):
            content_type = self.request.content_type or ''
        else:
            content_type = self.request.META.get('CONTENT_TYPE', '')
        
        # If content type indicates form data, only use form parsers
        if 'multipart/form-data' in content_type.lower() or 'application/x-www-form-urlencoded' in content_type.lower():
            return [MultiPartParser(), FormParser()]
        
        # For JSON content type, only use JSON parser
        if 'application/json' in content_type.lower():
            return [JSONParser()]
        
        # Default: use all parsers (DRF will select appropriate one)
        return super().get_parsers()
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return KYCCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return KYCUpdateSerializer
        elif self.action == 'update_status':
            return KYCStatusUpdateSerializer
        return KYCSerializer
    
    def get_queryset(self):
        """Filter KYC records based on user role"""
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            # Admins can see all KYC records
            return KYC.objects.all()
        else:
            # Users can only see their own KYC records
            return KYC.objects.filter(user=user)
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to catch encoding errors early
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except (UnicodeDecodeError, ValueError, ParseError) as e:
            # Check if this looks like a file upload with wrong Content-Type
            content_type = getattr(request, 'content_type', '') or request.META.get('CONTENT_TYPE', '')
            
            error_msg = str(e)
            if 'utf-8' in error_msg.lower() or 'codec' in error_msg.lower():
                # Encoding error - likely binary data sent as JSON
                if 'application/json' in content_type:
                    # Create a proper exception response
                    from rest_framework.views import exception_handler
                    exc = ParseError({
                        'detail': 'Invalid request encoding. When uploading files, '
                                 'use Content-Type: multipart/form-data, not application/json. '
                                 'For file uploads, send the request as multipart/form-data.'
                    })
                    response = exception_handler(exc, {})
                    if response is not None:
                        return response
            # Re-raise if we can't handle it
            raise
    
    def perform_create(self, serializer):
        """Set the user to current user when creating KYC"""
        # Validate that if files are present, Content-Type is correct
        content_type = getattr(self.request, 'content_type', '') or self.request.META.get('CONTENT_TYPE', '')
        if hasattr(self.request, 'FILES') and self.request.FILES:
            if 'multipart/form-data' not in content_type and 'application/x-www-form-urlencoded' not in content_type:
                raise ParseError({
                    'detail': 'File uploads require Content-Type: multipart/form-data. '
                             'Please set the correct Content-Type header when uploading files.'
                })
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Handle update with file uploads"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or instance.user == request.user):
            return Response({
                'error': 'You do not have permission to update this KYC record'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate Content-Type for file uploads
        content_type = getattr(request, 'content_type', '') or request.META.get('CONTENT_TYPE', '')
        if hasattr(request, 'FILES') and request.FILES:
            if 'multipart/form-data' not in content_type and 'application/x-www-form-urlencoded' not in content_type:
                return Response({
                    'detail': 'File uploads require Content-Type: multipart/form-data. '
                             'Please set the correct Content-Type header when uploading files.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """Handle partial update with file uploads"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def perform_update(self, serializer):
        """Perform the update"""
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_kyc(self, request):
        """
        Get current user's KYC records
        GET /api/kyc/my_kyc/
        """
        kyc_records = KYC.objects.filter(user=request.user)
        serializer = KYCSerializer(kyc_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        """
        Update KYC status (Admin only)
        PATCH /api/kyc/{id}/update_status/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can update KYC status'
            }, status=status.HTTP_403_FORBIDDEN)
        
        kyc = self.get_object()
        serializer = KYCStatusUpdateSerializer(kyc, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'KYC status updated successfully',
                'data': KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pending(self, request):
        """
        Get all pending KYC records (Admin only)
        GET /api/kyc/pending/
        """
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can view pending KYC records'
            }, status=status.HTTP_403_FORBIDDEN)
        
        kyc_records = KYC.objects.filter(status='Pending')
        serializer = KYCSerializer(kyc_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def approved(self, request):
        """
        Get all approved KYC records (Admin only)
        GET /api/kyc/approved/
        """
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can view approved KYC records'
            }, status=status.HTTP_403_FORBIDDEN)
        
        kyc_records = KYC.objects.filter(status='Approved')
        serializer = KYCSerializer(kyc_records, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def rejected(self, request):
        """
        Get all rejected KYC records (Admin only)
        GET /api/kyc/rejected/
        """
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can view rejected KYC records'
            }, status=status.HTTP_403_FORBIDDEN)
        
        kyc_records = KYC.objects.filter(status='Rejected')
        serializer = KYCSerializer(kyc_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def user_kyc_status(self, request, pk=None):
        """
        Get KYC status for a specific user
        GET /api/kyc/{user_id}/user_kyc_status/
        """
        kyc = self.get_object()
        return Response({
            'user_id': kyc.user.id,
            'username': kyc.user.username,
            'status': kyc.status,
            'submitted_at': kyc.submitted_at,
        })
    
    @action(detail=True, methods=['post', 'patch'])
    def upload_document(self, request, pk=None):
        """
        Upload documents to an existing KYC record
        POST/PATCH /api/kyc/{id}/upload_document/
        
        Form Data (multipart/form-data):
        - certificate_of_incorporation: File (optional)
        - company_bank_statement: File (optional)
        - company_proof_of_address: File (optional)
        - owner_identity_doc: File (optional)
        - owner_proof_of_address: File (optional)
        """
        kyc = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or kyc.user == request.user):
            return Response({
                'error': 'You do not have permission to update this KYC record'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle file uploads for all file fields
        uploaded_files = []
        file_fields = {
            'certificate_of_incorporation': 'Certificate of Incorporation',
            'company_bank_statement': 'Company Bank Statement',
            'company_proof_of_address': 'Company Proof of Address',
            'owner_identity_doc': 'Owner Identity Document',
            'owner_proof_of_address': 'Owner Proof of Address',
        }
        
        for field_name, display_name in file_fields.items():
            if field_name in request.FILES:
                file = request.FILES[field_name]
                setattr(kyc, field_name, file)
                uploaded_files.append({
                    'field': field_name,
                    'display_name': display_name,
                    'filename': file.name,
                    'size': file.size,
                    'mime_type': file.content_type
                })
        
        # Save if any files were uploaded
        if uploaded_files:
            kyc.save()
            return Response({
                'success': True,
                'message': 'Document(s) uploaded successfully',
                'uploaded_files': uploaded_files,
                'kyc': KYCSerializer(kyc).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No files were provided for upload. Supported fields: ' + ', '.join(file_fields.keys())
            }, status=status.HTTP_400_BAD_REQUEST)
