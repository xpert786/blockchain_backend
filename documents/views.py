from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import FileResponse
from users.models import CustomUser
from .models import Document, DocumentSignatory, DocumentTemplate, DocumentGeneration
from .serializers import (
    DocumentSerializer,
    DocumentListSerializer,
    DocumentCreateSerializer,
    DocumentSignatorySerializer,
    DocumentStatisticsSerializer,
    DocumentTemplateSerializer,
    DocumentTemplateListSerializer,
    DocumentGenerationSerializer,
    DocumentGenerationRequestSerializer,
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of documents or admins to view/edit them."""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access all documents
        if request.user.is_staff or request.user.role == 'admin':
            return True
        # Users can only access their own documents or documents they need to sign
        return obj.created_by == request.user or obj.signatories.filter(user=request.user).exists()

# create document ,listing document
class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing documents
    Provides CRUD operations for Document model
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return DocumentCreateSerializer
        elif self.action == 'list':
            return DocumentListSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """Filter documents based on user role and query parameters"""
        user = self.request.user
        queryset = Document.objects.all()
        
        # Filter by user role
        if not (user.is_staff or user.role == 'admin'):
            # Users can only see their own documents or documents they need to sign
            queryset = queryset.filter(
                Q(created_by=user) | Q(signatories__user=user)
            ).distinct()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by document type
        doc_type = self.request.query_params.get('document_type', None)
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(document_id__icontains=search) |
                Q(description__icontains=search) |
                Q(original_filename__icontains=search)
            )
        
        return queryset.select_related('created_by', 'spv', 'syndicate').prefetch_related('signatories')
    
    def perform_create(self, serializer):
        """Set the creator to current user when creating document"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get document statistics
        GET /api/documents/statistics/
        """
        user = request.user
        queryset = self.get_queryset()
        
        stats = {
            'total_documents': queryset.count(),
            'pending_signatures': queryset.filter(status='pending_signatures').count(),
            'signed_documents': queryset.filter(status='signed').count(),
            'rejected': queryset.filter(status='rejected').count(),
            'draft': queryset.filter(status='draft').count(),
            'pending_review': queryset.filter(status='pending_review').count(),
            'finalized': queryset.filter(status='finalized').count(),
        }
        
        serializer = DocumentStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download document file
        GET /api/documents/{id}/download/
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
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update document status
        PATCH /api/documents/{id}/update_status/
        """
        document = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Document.STATUS_CHOICES):
            return Response({
                'error': f'Invalid status. Must be one of: {", ".join([choice[0] for choice in Document.STATUS_CHOICES])}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions for status changes
        if new_status in ['finalized', 'rejected'] and not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can finalize or reject documents'
            }, status=status.HTTP_403_FORBIDDEN)
        
        document.status = new_status
        if new_status == 'finalized':
            from django.utils import timezone
            document.finalized_at = timezone.now()
        document.save()
        
        return Response({
            'message': 'Document status updated successfully',
            'data': DocumentSerializer(document).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def add_signatory(self, request, pk=None):
        """
        Add a signatory to the document
        POST /api/documents/{id}/add_signatory/
        """
        document = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', '')
        
        if not user_id:
            return Response({
                'error': 'user_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        signatory, created = DocumentSignatory.objects.get_or_create(
            document=document,
            user=user,
            defaults={
                'role': role,
                'invited_by': request.user,
            }
        )
        
        if not created:
            return Response({
                'error': 'Signatory already exists for this document'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DocumentSignatorySerializer(signatory)
        return Response({
            'message': 'Signatory added successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """
        Sign the document (for current user)
        POST /api/documents/{id}/sign/
        """
        document = self.get_object()
        
        try:
            signatory = DocumentSignatory.objects.get(
                document=document,
                user=request.user
            )
        except DocumentSignatory.DoesNotExist:
            return Response({
                'error': 'You are not a signatory for this document'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if signatory.signed:
            return Response({
                'error': 'Document already signed by you'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from django.utils import timezone
        signatory.signed = True
        signatory.signed_at = timezone.now()
        signatory.signature_ip = self._get_client_ip(request)
        signatory.save()
        
        # Check if all signatories have signed
        all_signed = document.signatories.filter(signed=False).count() == 0
        if all_signed and document.status == 'pending_signatures':
            document.status = 'signed'
            document.save()
        
        return Response({
            'message': 'Document signed successfully',
            'data': DocumentSignatorySerializer(signatory).data
        }, status=status.HTTP_200_OK)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# List all signatories of a document, Add signatories
class DocumentSignatoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document signatories
    """
    queryset = DocumentSignatory.objects.all()
    serializer_class = DocumentSignatorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter signatories based on user role"""
        user = self.request.user
        queryset = DocumentSignatory.objects.all()
        
        if not (user.is_staff or user.role == 'admin'):
            # Users can only see signatories for documents they created or where they are signatories
            queryset = queryset.filter(
                Q(document__created_by=user) | Q(user=user)
            ).distinct()
        
        # Filter by document
        document_id = self.request.query_params.get('document', None)
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        
        return queryset.select_related('document', 'user', 'invited_by')

# List all templates, Retrieve a single template,Create/update/delete a template
class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing document templates
    """
    queryset = DocumentTemplate.objects.filter(is_active=True)
    serializer_class = DocumentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return DocumentTemplateListSerializer
        return DocumentTemplateSerializer
    
    def get_queryset(self):
        """Filter templates"""
        queryset = DocumentTemplate.objects.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('name', '-version')
    
    def perform_create(self, serializer):
        """Set creator when creating template"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def required_fields(self, request, pk=None):
        """
        Get required fields for a template
        GET /api/document-templates/{id}/required_fields/
        """
        template = self.get_object()
        
        # Ensure required_fields is a list
        required_fields = template.required_fields or []
        if isinstance(required_fields, str):
            import json
            try:
                required_fields = json.loads(required_fields)
            except json.JSONDecodeError:
                required_fields = []
        
        return Response({
            'template_id': template.id,
            'template_name': template.name,
            'required_fields': required_fields,
            'enable_digital_signature': template.enable_digital_signature,
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """
        Duplicate a template (create a new version)
        POST /api/document-templates/{id}/duplicate/
        """
        template = self.get_object()
        
        # Create a new template based on the existing one
        new_template = DocumentTemplate.objects.create(
            name=template.name,
            description=template.description,
            version=f"{float(template.version) + 0.1:.1f}",  # Increment version
            category=template.category,
            template_file=template.template_file,
            required_fields=template.required_fields,
            enable_digital_signature=template.enable_digital_signature,
            is_active=True,
            created_by=request.user,
        )
        
        serializer = DocumentTemplateSerializer(new_template)
        return Response({
            'message': 'Template duplicated successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


# takes a document template/Creates a new Document record
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_document_from_template(request):
    """
    Generate a document from a template
    POST /api/documents/generate-from-template/
    """
    serializer = DocumentGenerationRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    template_id = serializer.validated_data['template_id']
    field_data = serializer.validated_data['field_data']
    enable_digital_signature = serializer.validated_data.get('enable_digital_signature', False)
    title = serializer.validated_data.get('title')
    description = serializer.validated_data.get('description', '')
    spv_id = serializer.validated_data.get('spv_id')
    syndicate_id = serializer.validated_data.get('syndicate_id')
    
    try:
        template = DocumentTemplate.objects.get(id=template_id, is_active=True)
    except DocumentTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found or is not active'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Validate required fields
    required_fields = template.required_fields or []
    
    # Ensure required_fields is a list (parse if it's a string)
    if isinstance(required_fields, str):
        import json
        try:
            required_fields = json.loads(required_fields)
        except json.JSONDecodeError:
            required_fields = []
    
    missing_fields = []
    for field_def in required_fields:
        # Skip if field_def is not a dict
        if not isinstance(field_def, dict):
            continue
            
        field_name = field_def.get('name')
        if field_def.get('required', False) and field_name not in field_data:
            missing_fields.append(field_def.get('label', field_name))
    
    if missing_fields:
        return Response({
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate document title if not provided
    if not title:
        title = f"{template.name} - {field_data.get('investor_name', 'Document')}"
    
    # Create the document
    document = Document.objects.create(
        title=title,
        description=description or template.description,
        document_type='other',  # Can be customized based on template
        version='1.0',
        status='draft',
        created_by=request.user,
        spv_id=spv_id if spv_id else None,
        syndicate_id=syndicate_id if syndicate_id else None,
    )
    
    # Create generation record
    generation = DocumentGeneration.objects.create(
        template=template,
        generated_document=document,
        generation_data=field_data,
        generated_by=request.user,
        enable_digital_signature=enable_digital_signature,
    )
    
    # Handle signatories if provided
    signatories_data = serializer.validated_data.get('signatories', [])
    if signatories_data:
        for signatory_data in signatories_data:
            user_id = signatory_data.get('user_id')
            role = signatory_data.get('role', '')
            
            try:
                signatory_user = CustomUser.objects.get(id=user_id)
                DocumentSignatory.objects.get_or_create(
                    document=document,
                    user=signatory_user,
                    defaults={
                        'role': role,
                        'invited_by': request.user,
                    }
                )
            except CustomUser.DoesNotExist:
                pass  # Skip invalid user IDs
    
    # If digital signature is enabled, set status to pending_signatures
    if enable_digital_signature:
        document.status = 'pending_signatures'
        document.save()
    
    # Refresh document to get updated signatories
    document.refresh_from_db()
    
    return Response({
        'message': 'Document generated successfully',
        'data': {
            'document': DocumentSerializer(document).data,
            'generation': DocumentGenerationSerializer(generation).data,
        }
    }, status=status.HTTP_201_CREATED)


# returns a list of all documents that were generated from templates.like an audit log.
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_generated_documents(request):
    """
    Get all documents generated from templates
    GET /api/documents/generated-documents/
    """
    user = request.user
    queryset = DocumentGeneration.objects.all()
    
    # Filter by user role
    if not (user.is_staff or user.role == 'admin'):
        queryset = queryset.filter(generated_by=user)
    
    # Filter by template
    template_id = request.query_params.get('template', None)
    if template_id:
        queryset = queryset.filter(template_id=template_id)
    
    serializer = DocumentGenerationSerializer(queryset, many=True)
    return Response(serializer.data)

