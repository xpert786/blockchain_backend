from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import KYC
from .serializers import (
    KYCSerializer, 
    KYCCreateSerializer,
    KYCUpdateSerializer,
    KYCStatusUpdateSerializer
)


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
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
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
    
    def perform_create(self, serializer):
        """Set the user to current user when creating KYC"""
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
        Upload a document to an existing KYC record
        POST/PATCH /api/kyc/{id}/upload_document/
        
        Form Data (multipart/form-data):
        - company_proof_of_address: File (optional, if updating this field)
        """
        kyc = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or kyc.user == request.user):
            return Response({
                'error': 'You do not have permission to update this KYC record'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle file uploads
        uploaded_files = []
        
        if 'company_proof_of_address' in request.FILES:
            file = request.FILES['company_proof_of_address']
            kyc.company_proof_of_address = file
            uploaded_files.append({
                'field': 'company_proof_of_address',
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
                'error': 'No files were provided for upload'
            }, status=status.HTTP_400_BAD_REQUEST)
