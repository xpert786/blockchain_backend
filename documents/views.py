from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import FileResponse
from django.conf import settings
from django.core.files.base import ContentFile
import os
import re
import uuid
from io import BytesIO
from users.models import CustomUser
from spv.models import SPV
from .models import Document, DocumentSignatory, DocumentTemplate, DocumentGeneration, SyndicateDocumentDefaults

# PDF generation - try multiple libraries for cross-platform support
# Priority: xhtml2pdf (best for Windows), WeasyPrint (Linux/Mac), ReportLab (fallback)
WEASYPRINT_AVAILABLE = False
XHTML2PDF_AVAILABLE = False
REPORTLAB_AVAILABLE = False

# Try xhtml2pdf first (best for Windows, no external dependencies)
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

# Try WeasyPrint (good for Linux/Mac, requires GTK on Windows)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

# Fallback to ReportLab (basic text rendering)
if not XHTML2PDF_AVAILABLE and not WEASYPRINT_AVAILABLE:
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False
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
    SyndicateDocumentDefaultsSerializer,
    SyndicateDocumentDefaultsCreateSerializer,
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
    
    Query Parameters:
    - status: Filter by document status (draft, pending_review, etc.)
    - document_type: Filter by document type
    - search: Search in title, document_id, description, filename
    - source: Filter by source ('generated' = only template-generated documents, 'uploaded' = only uploaded)
    - spv_id: Filter by SPV ID
    - investor_id: Filter by investor ID (shows documents generated for this investor)
    - include_generation: Include generation details in response (true/false)
    
    Note: Investors automatically see documents generated FOR them (where investor_id matches their user id).
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
        
        # Helper function to get document IDs for a specific investor (SQLite compatible)
        def get_investor_document_ids(target_investor_id):
            """Get document IDs where the investor_id in generation_data matches target_investor_id"""
            doc_ids = []
            for gen in DocumentGeneration.objects.all():
                gen_data = gen.generation_data or {}
                if gen_data.get('investor_id') == target_investor_id:
                    doc_ids.append(gen.generated_document_id)
            return doc_ids
        
        # Filter by user role
        if not (user.is_staff or user.role == 'admin'):
            # Get document IDs where this user is the investor (from generation_data)
            # Using Python filtering for SQLite compatibility
            investor_doc_ids = get_investor_document_ids(user.id)
            
            # Users can see:
            # 1. Documents they created
            # 2. Documents they need to sign (signatories)
            # 3. Documents generated FOR them (investor_id matches their user id)
            queryset = queryset.filter(
                Q(created_by=user) | 
                Q(signatories__user=user) |
                Q(id__in=investor_doc_ids)
            ).distinct()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by document type
        doc_type = self.request.query_params.get('document_type', None)
        if doc_type:
            queryset = queryset.filter(document_type=doc_type)
        
        # Filter by source (generated from template or uploaded)
        source = self.request.query_params.get('source', None)
        if source == 'generated':
            # Only show documents that were generated from templates
            generated_doc_ids = DocumentGeneration.objects.values_list('generated_document_id', flat=True)
            queryset = queryset.filter(id__in=generated_doc_ids)
        elif source == 'uploaded':
            # Only show documents that were NOT generated from templates (uploaded manually)
            generated_doc_ids = DocumentGeneration.objects.values_list('generated_document_id', flat=True)
            queryset = queryset.exclude(id__in=generated_doc_ids)
        
        # Filter by SPV
        spv_id = self.request.query_params.get('spv_id', None)
        if spv_id:
            queryset = queryset.filter(spv_id=spv_id)
        
        # Filter by investor_id (documents generated for a specific investor)
        investor_id_param = self.request.query_params.get('investor_id', None)
        if investor_id_param:
            try:
                target_investor_id = int(investor_id_param)
                # Get document IDs generated for this investor (SQLite compatible)
                investor_doc_ids = get_investor_document_ids(target_investor_id)
                queryset = queryset.filter(id__in=investor_doc_ids)
            except (ValueError, TypeError):
                pass  # Invalid investor_id, ignore filter
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(document_id__icontains=search) |
                Q(description__icontains=search) |
                Q(original_filename__icontains=search)
            )
        
        return queryset.select_related('created_by', 'spv', 'syndicate').prefetch_related('signatories', 'generation_history')
    
    def list(self, request, *args, **kwargs):
        """
        List documents with optional generation details.
        
        GET /api/documents/
        GET /api/documents/?source=generated  (only template-generated documents)
        GET /api/documents/?include_generation=true  (include generation details)
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if generation details should be included
        include_generation = request.query_params.get('include_generation', 'false').lower() == 'true'
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            
            if include_generation:
                data = self._add_generation_details(data)
            
            return self.get_paginated_response(data)
        
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        if include_generation:
            data = self._add_generation_details(data)
        
        return Response(data)
    
    def _add_generation_details(self, documents_data):
        """Add generation details to document data"""
        # Get all document IDs
        doc_ids = [doc['id'] for doc in documents_data]
        
        # Fetch all generations for these documents
        generations = DocumentGeneration.objects.filter(
            generated_document_id__in=doc_ids
        ).select_related('template', 'generated_by')
        
        # Create a lookup dict
        gen_lookup = {}
        for gen in generations:
            gen_lookup[gen.generated_document_id] = {
                'generation_id': gen.id,
                'template_id': gen.template.id,
                'template_name': gen.template.name,
                'template_version': gen.template.version,
                'template_category': gen.template.category,
                'generation_data': gen.generation_data,
                'generated_by': {
                    'id': gen.generated_by.id,
                    'username': gen.generated_by.username,
                    'email': gen.generated_by.email,
                },
                'generated_at': gen.generated_at.isoformat() if gen.generated_at else None,
                'has_pdf': bool(gen.generated_pdf),
            }
        
        # Add generation info to each document
        for doc in documents_data:
            doc['is_generated'] = doc['id'] in gen_lookup
            doc['generation_info'] = gen_lookup.get(doc['id'], None)
        
        return documents_data
    
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
    
    @action(detail=True, methods=['get'])
    def view(self, request, pk=None):
        """
        View document file in browser (for PDFs)
        GET /api/documents/{id}/view/
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
            # Use 'inline' instead of 'attachment' to view in browser
            response['Content-Disposition'] = f'inline; filename="{document.original_filename}"'
            return response
        except Exception as e:
            return Response({
                'error': f'Error viewing file: {str(e)}'
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
        """
        Filter templates based on query parameters.
        
        Query Parameters:
        - scope: Filter by scope (spv, investor) - use ?scope=spv for Generate Documents screen
        - jurisdiction: Filter by jurisdiction_scope
        - category: Filter by category
        - search: Search in name and description
        """
        queryset = DocumentTemplate.objects.filter(is_active=True)
        
        # Filter by scope (NEW - for SPV-only screen, use ?scope=spv)
        scope = self.request.query_params.get('scope', None)
        if scope:
            queryset = queryset.filter(scope=scope)
        
        # Filter by jurisdiction
        jurisdiction = self.request.query_params.get('jurisdiction', None)
        if jurisdiction:
            queryset = queryset.filter(jurisdiction_scope=jurisdiction)
        
        # Filter by content type
        content_type = self.request.query_params.get('content_type', None)
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
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
    
    @action(detail=True, methods=['get'])
    def configurable_fields(self, request, pk=None):
        """
        Get configurable fields for a template (for Syndicate Document Defaults).
        
        Returns fields from template.configurable_fields[] (NOT required_fields[]).
        These are used for saving syndicate-level defaults, not for document generation.
        
        GET /api/document-templates/{id}/configurable_fields/
        """
        template = self.get_object()
        
        # Ensure configurable_fields is a list
        configurable_fields = template.configurable_fields or []
        if isinstance(configurable_fields, str):
            import json
            try:
                configurable_fields = json.loads(configurable_fields)
            except json.JSONDecodeError:
                configurable_fields = []
        
        return Response({
            'template_id': template.id,
            'template_name': template.name,
            'description': template.description,
            'configurable_fields': configurable_fields,
            'message': 'Documents generated here are SPV-level templates or reference documents. Investor-specific documents are generated automatically during allocations, capital calls, or transfers.',
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
            configurable_fields=template.configurable_fields,  # Include configurable_fields
            enable_digital_signature=template.enable_digital_signature,
            is_active=True,
            created_by=request.user,
        )
        
        serializer = DocumentTemplateSerializer(new_template)
        return Response({
            'message': 'Template duplicated successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class SyndicateDocumentDefaultsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Syndicate Document Defaults.
    
    "Syndicate Document Defaults" section in the UI.
    Template-driven defaults only: Render fields from template.configurable_fields[]
    (NOT from required_fields[] used for document generation).
    The goal is to save syndicate-level defaults, not generate a specific PDF.
    
    Documents generated here are SPV-level templates or reference documents.
    Investor-specific documents are generated automatically during allocations,
    capital calls, or transfers.
    """
    queryset = SyndicateDocumentDefaults.objects.all()
    serializer_class = SyndicateDocumentDefaultsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action in ['create', 'update', 'partial_update']:
            return SyndicateDocumentDefaultsCreateSerializer
        return SyndicateDocumentDefaultsSerializer
    
    def get_queryset(self):
        """Filter defaults based on user role and query parameters"""
        user = self.request.user
        queryset = SyndicateDocumentDefaults.objects.all()
        
        # Filter by user's syndicate if not admin
        if not (user.is_staff or user.role == 'admin'):
            # Get user's syndicate profile
            if hasattr(user, 'syndicateprofile'):
                queryset = queryset.filter(syndicate=user.syndicateprofile)
            else:
                queryset = queryset.filter(created_by=user)
        
        # Filter by syndicate
        syndicate_id = self.request.query_params.get('syndicate', None)
        if syndicate_id:
            queryset = queryset.filter(syndicate_id=syndicate_id)
        
        # Filter by template
        template_id = self.request.query_params.get('template', None)
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        return queryset.select_related('syndicate', 'template', 'created_by')
    
    def perform_create(self, serializer):
        """Set the creator when creating defaults"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_defaults(self, request):
        """
        Get current user's syndicate document defaults.
        GET /api/syndicate-document-defaults/my_defaults/
        """
        user = request.user
        
        if hasattr(user, 'syndicateprofile'):
            defaults = SyndicateDocumentDefaults.objects.filter(
                syndicate=user.syndicateprofile
            ).select_related('template')
            
            serializer = SyndicateDocumentDefaultsSerializer(defaults, many=True)
            return Response({
                'message': 'Syndicate document defaults retrieved successfully',
                'data': serializer.data
            })
        
        return Response({
            'message': 'No syndicate profile found for user',
            'data': []
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def save_defaults(self, request):
        """
        Create or update syndicate document defaults for a template.
        POST /api/syndicate-document-defaults/save_defaults/
        
        Body: {
            "template_id": 1,
            "default_values": {"field_name": "value", ...}
        }
        """
        user = request.user
        template_id = request.data.get('template_id')
        default_values = request.data.get('default_values', {})
        
        if not template_id:
            return Response({
                'error': 'template_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate template exists
        try:
            template = DocumentTemplate.objects.get(id=template_id, is_active=True)
        except DocumentTemplate.DoesNotExist:
            return Response({
                'error': 'Template not found or is not active'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get user's syndicate
        if not hasattr(user, 'syndicateprofile'):
            return Response({
                'error': 'No syndicate profile found for user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        syndicate = user.syndicateprofile
        
        # Create or update defaults
        defaults, created = SyndicateDocumentDefaults.objects.update_or_create(
            syndicate=syndicate,
            template=template,
            defaults={
                'default_values': default_values,
                'created_by': user,
            }
        )
        
        serializer = SyndicateDocumentDefaultsSerializer(defaults)
        return Response({
            'message': f'Syndicate document defaults {"created" if created else "updated"} successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def template_details(self, request, pk=None):
        """
        Screen 3: Get all details for a saved default (template details, required fields, configurable fields, saved defaults)
        GET /api/syndicate-document-defaults/{id}/template_details/
        """
        defaults_obj = self.get_object()
        template = defaults_obj.template
        
        # Get required fields
        required_fields = template.required_fields or []
        if isinstance(required_fields, str):
            import json
            try:
                required_fields = json.loads(required_fields)
            except json.JSONDecodeError:
                required_fields = []
        
        # Get configurable fields
        configurable_fields = template.configurable_fields or []
        if isinstance(configurable_fields, str):
            import json
            try:
                configurable_fields = json.loads(configurable_fields)
            except json.JSONDecodeError:
                configurable_fields = []
        
        # Get saved default values
        saved_defaults = defaults_obj.default_values or {}
        
        return Response({
            'template_id': template.id,
            'template_name': template.name,
            'version': template.version,
            'category': template.category,
            'scope': template.scope,
            'jurisdiction_scope': template.jurisdiction_scope,
            'description': template.description,
            'required_fields': required_fields,
            'configurable_fields': configurable_fields,
            'saved_default_values': saved_defaults,
            'enable_digital_signature': template.enable_digital_signature,
            'defaults_id': defaults_obj.id,
            'syndicate_id': defaults_obj.syndicate.id if defaults_obj.syndicate else None,
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['put'])
    def generate_from_defaults(self, request, pk=None):
        """
        Screen 3: Generate document from template using saved defaults
        PUT /api/syndicate-document-defaults/{id}/generate_from_defaults/
        
        Body (optional - to override defaults or add required fields):
        {
            "field_data": {"field_name": "value", ...},  // Optional: override defaults or add required fields
            "enable_digital_signature": false,
            "title": "Custom Title",  // Optional
            "description": "Custom Description",  // Optional
            "spv_id": 1  // Optional
        }
        """
        defaults_obj = self.get_object()
        template = defaults_obj.template
        
        # Get saved defaults
        saved_defaults = defaults_obj.default_values or {}
        
        # Get additional field_data from request (optional - to override or add required fields)
        additional_field_data = request.data.get('field_data', {})
        
        # Merge saved defaults with additional field_data (additional_field_data takes precedence)
        merged_field_data = {**saved_defaults, **additional_field_data}
        
        # Helper function to normalize field names for matching
        def normalize_field_name(name):
            """Normalize field name for comparison (lowercase, replace spaces/underscores)"""
            if not name:
                return ''
            return str(name).lower().replace(' ', '_').replace('-', '_')
        
        # Validate required fields
        required_fields = template.required_fields or []
        if isinstance(required_fields, str):
            import json
            try:
                required_fields = json.loads(required_fields)
            except json.JSONDecodeError:
                required_fields = []
        
        # Create a normalized map of merged_field_data keys
        normalized_field_data = {normalize_field_name(k): v for k, v in merged_field_data.items()}
        
        missing_fields = []
        for field_def in required_fields:
            if not isinstance(field_def, dict):
                continue
            field_name = field_def.get('name')
            field_label = field_def.get('label', field_name)
            
            if field_def.get('required', False):
                # Check both original field_name and normalized version
                normalized_name = normalize_field_name(field_name)
                
                # Check if field exists in merged_field_data (exact match or normalized match)
                field_found = (
                    field_name in merged_field_data or
                    normalized_name in normalized_field_data or
                    any(normalize_field_name(k) == normalized_name for k in merged_field_data.keys())
                )
                
                if not field_found:
                    missing_fields.append(field_label)
        
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get optional parameters
        enable_digital_signature = request.data.get('enable_digital_signature', False)
        title = request.data.get('title')
        description = request.data.get('description', '')
        spv_id = request.data.get('spv_id')
        
        # Generate document title if not provided
        if not title:
            title = f"{template.name} - {merged_field_data.get('investor_name', merged_field_data.get('spv_name', 'Document'))}"
        
        # Create the document first (needed for document_id generation)
        document = Document.objects.create(
            title=title,
            description=description or template.description,
            document_type='other',
            version='1.0',
            status='draft',
            created_by=request.user,
            spv_id=spv_id if spv_id else None,
            syndicate_id=defaults_obj.syndicate.id if defaults_obj.syndicate else None,
        )
        
        # Generate PDF from template content (or create default template if empty)
        pdf_file = None
        pdf_generated = False
        original_filename = f"{title.replace(' ', '_').replace('/', '_')}.pdf"
        try:
            pdf_file = generate_pdf_from_template(template, merged_field_data, title)
            if pdf_file:
                # Generate filename with document_id
                filename = f"{document.document_id}_{uuid.uuid4().hex[:8]}.pdf"
                # Save PDF file to document
                document.file.save(filename, pdf_file, save=False)
                document.original_filename = original_filename
                document.mime_type = 'application/pdf'
                pdf_generated = True
        except Exception as e:
            # Log error but don't fail the request - document will be created without PDF
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating PDF for document {document.document_id}: {str(e)}", exc_info=True)
        
        # Save document with PDF file if generated
        document.save()
        
        # Create generation record
        generation = DocumentGeneration.objects.create(
            template=template,
            generated_document=document,
            generation_data=merged_field_data,
            generated_by=request.user,
            enable_digital_signature=enable_digital_signature,
        )
        
        # Also save PDF to generation record
        if pdf_generated:
            try:
                pdf_file_for_generation = generate_pdf_from_template(template, merged_field_data, title)
                if pdf_file_for_generation:
                    gen_filename = f"gen_{document.document_id}_{uuid.uuid4().hex[:8]}.pdf"
                    generation.generated_pdf.save(gen_filename, pdf_file_for_generation, save=False)
                    generation.pdf_filename = original_filename
                    generation.pdf_file_size = pdf_file_for_generation.size if hasattr(pdf_file_for_generation, 'size') else len(pdf_file_for_generation.read())
                    generation.save()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not save PDF to generation record: {str(e)}")
        
        # If digital signature is enabled, set status to pending_signatures
        if enable_digital_signature:
            document.status = 'pending_signatures'
            document.save()
        
        # Refresh document
        document.refresh_from_db()
        
        # Prepare response with PDF generation status
        response_data = {
            'message': 'Document generated successfully from template defaults',
            'pdf_generated': pdf_generated,
            'data': {
                'document': DocumentSerializer(document, context={'request': request}).data,
                'generation': DocumentGenerationSerializer(generation, context={'request': request}).data,
            }
        }
        
        if not pdf_generated and template.template_content:
            response_data['warning'] = 'PDF could not be generated. Please check template content and ensure WeasyPrint is installed.'
        
        return Response(response_data, status=status.HTTP_201_CREATED)
# takes a document template/Creates a new Document record
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_document_from_template(request):
    """
    Generate a document from a template
    POST /api/documents/generate-from-template/
    
    Screen 2: When syndicate fills details and clicks "Generate Document"
    - Accepts template_id and field_data (required_fields + configurable_fields)
    - Supports investor_id and spv_id to auto-resolve names
    - Merges with saved syndicate defaults if available
    - Generates document
    
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
    serializer = DocumentGenerationRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    template_id = serializer.validated_data['template_id']
    field_data = serializer.validated_data['field_data'].copy()  # Make a copy to modify
    enable_digital_signature = serializer.validated_data.get('enable_digital_signature', False)
    title = serializer.validated_data.get('title')
    description = serializer.validated_data.get('description', '')
    spv_id = serializer.validated_data.get('spv_id')
    syndicate_id = serializer.validated_data.get('syndicate_id')
    investor_id = serializer.validated_data.get('investor_id')
    
    # Resolve investor_name from investor_id if provided
    if investor_id and 'investor_name' not in field_data:
        try:
            investor_user = CustomUser.objects.get(id=investor_id, role='investor')
            investor_name = investor_user.get_full_name()
            if not investor_name:
                investor_name = investor_user.username
            field_data['investor_name'] = investor_name
            field_data['investor_id'] = investor_id  # Also store the ID for reference
        except CustomUser.DoesNotExist:
            return Response({
                'error': f'Investor with ID {investor_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Resolve spv_name from spv_id if provided
    if spv_id and 'spv_name' not in field_data:
        try:
            spv = SPV.objects.get(id=spv_id)
            field_data['spv_name'] = spv.display_name
            field_data['spv_id'] = spv_id  # Also store the ID for reference
        except SPV.DoesNotExist:
            return Response({
                'error': f'SPV with ID {spv_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        template = DocumentTemplate.objects.get(id=template_id, is_active=True)
    except DocumentTemplate.DoesNotExist:
        return Response({
            'error': 'Template not found or is not active'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get syndicate defaults if available (for merging with field_data)
    saved_defaults = {}
    if hasattr(request.user, 'syndicateprofile'):
        try:
            defaults_obj = SyndicateDocumentDefaults.objects.get(
                syndicate=request.user.syndicateprofile,
                template=template
            )
            saved_defaults = defaults_obj.default_values or {}
        except SyndicateDocumentDefaults.DoesNotExist:
            pass
    
    # Get configurable fields to check which fields can come from defaults
    configurable_fields = template.configurable_fields or []
    if isinstance(configurable_fields, str):
        import json
        try:
            configurable_fields = json.loads(configurable_fields)
        except json.JSONDecodeError:
            configurable_fields = []
    
    # Create a set of configurable field names (normalized) for quick lookup
    configurable_field_names = set()
    for cfg_field in configurable_fields:
        if isinstance(cfg_field, dict):
            cfg_name = cfg_field.get('name')
            if cfg_name:
                # Normalize the name
                normalized_cfg = str(cfg_name).lower().replace(' ', '_').replace('-', '_')
                configurable_field_names.add(normalized_cfg)
    
    # Merge saved defaults with provided field_data (field_data takes precedence)
    merged_field_data = {**saved_defaults, **field_data}
    
    # Validate required fields
    required_fields = template.required_fields or []
    
    # Ensure required_fields is a list (parse if it's a string)
    if isinstance(required_fields, str):
        import json
        try:
            required_fields = json.loads(required_fields)
        except json.JSONDecodeError:
            required_fields = []
    
    # Helper function to normalize field names for matching
    def normalize_field_name(name):
        """Normalize field name for comparison (lowercase, replace spaces/underscores)"""
        if not name:
            return ''
        return str(name).lower().replace(' ', '_').replace('-', '_')
    
    # Create a normalized map of merged_field_data keys for easier lookup
    normalized_field_data = {}
    for key, value in merged_field_data.items():
        normalized_key = normalize_field_name(key)
        normalized_field_data[normalized_key] = value
        # Also keep original key
        if key not in merged_field_data:
            normalized_field_data[key] = value
    
    missing_fields = []
    for field_def in required_fields:
        # Skip if field_def is not a dict
        if not isinstance(field_def, dict):
            continue
            
        field_name = field_def.get('name')
        field_label = field_def.get('label', field_name)
        
        if field_def.get('required', False):
            # Normalize the field name for comparison
            normalized_name = normalize_field_name(field_name)
            
            # Check if this field is in configurable_fields
            is_configurable = normalized_name in configurable_field_names
            
            # Check if field exists in merged_field_data (check both original and normalized)
            field_value = None
            field_found = False
            
            # First try exact match
            if field_name in merged_field_data:
                field_value = merged_field_data[field_name]
                field_found = True
            # Then try normalized match in original keys
            else:
                for key in merged_field_data.keys():
                    if normalize_field_name(key) == normalized_name:
                        field_value = merged_field_data[key]
                        field_found = True
                        break
                # Also check normalized_field_data
                if not field_found and normalized_name in normalized_field_data:
                    field_value = normalized_field_data[normalized_name]
                    field_found = True
            
            # Check if value is not empty (None, empty string, etc.)
            if field_found:
                if field_value is None or (isinstance(field_value, str) and field_value.strip() == ''):
                    field_found = False
            
            # If field is not found
            if not field_found:
                # Check if field is in saved_defaults (even if not in merged_field_data due to normalization issues)
                in_saved_defaults = False
                if saved_defaults:
                    for key in saved_defaults.keys():
                        if normalize_field_name(key) == normalized_name:
                            saved_value = saved_defaults[key]
                            if saved_value is not None and (not isinstance(saved_value, str) or saved_value.strip() != ''):
                                in_saved_defaults = True
                                break
                
                # If field is in configurable_fields and in saved_defaults, it's optional
                # If field is in configurable_fields but NOT in saved_defaults, it's still required
                # If field is NOT in configurable_fields, it's required
                if is_configurable and in_saved_defaults:
                    # Configurable field with saved default - optional
                    pass
                else:
                    # Required field - must be provided
                    missing_fields.append(field_label)
    
    if missing_fields:
        return Response({
            'error': f'Missing required fields: {", ".join(missing_fields)}',
            'details': {
                'provided_fields': list(field_data.keys()),
                'saved_defaults': list(saved_defaults.keys()) if saved_defaults else [],
                'required_fields': [f.get('label', f.get('name')) for f in required_fields if isinstance(f, dict) and f.get('required', False)],
                'suggestion': 'If these fields are configurable defaults, please save them first using the save_defaults API, or provide them in field_data.'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Use syndicate_id from user's syndicate profile if not provided
    if not syndicate_id and hasattr(request.user, 'syndicateprofile'):
        syndicate_id = request.user.syndicateprofile.id
    
    # Generate document title if not provided
    if not title:
        title = f"{template.name} - {merged_field_data.get('investor_name', merged_field_data.get('spv_name', 'Document'))}"
    
    # Create the document first (needed for document_id generation)
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
    
    # Generate PDF from template content (or create default template if empty)
    pdf_file = None
    pdf_generated = False
    try:
        pdf_file = generate_pdf_from_template(template, merged_field_data, title)
        if pdf_file:
            # Generate filename with document_id
            filename = f"{document.document_id}_{uuid.uuid4().hex[:8]}.pdf"
            original_filename = f"{title.replace(' ', '_').replace('/', '_')}.pdf"
            
            # Save PDF file to document
            document.file.save(filename, pdf_file, save=False)
            document.original_filename = original_filename
            document.mime_type = 'application/pdf'
            pdf_generated = True
    except Exception as e:
        # Log error but don't fail the request - document will be created without PDF
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating PDF for document {document.document_id}: {str(e)}", exc_info=True)
    
    # Save document with PDF file if generated
    document.save()
    
    # Create generation record with merged field data
    generation = DocumentGeneration.objects.create(
        template=template,
        generated_document=document,
        generation_data=merged_field_data,
        generated_by=request.user,
        enable_digital_signature=enable_digital_signature,
    )
    
    # Also save PDF to generation record
    if pdf_generated and document.file:
        try:
            # Re-generate PDF for generation record (or copy from document)
            pdf_file_for_generation = generate_pdf_from_template(template, merged_field_data, title)
            if pdf_file_for_generation:
                gen_filename = f"gen_{document.document_id}_{uuid.uuid4().hex[:8]}.pdf"
                generation.generated_pdf.save(gen_filename, pdf_file_for_generation, save=False)
                generation.pdf_filename = original_filename
                generation.pdf_file_size = pdf_file_for_generation.size if hasattr(pdf_file_for_generation, 'size') else len(pdf_file_for_generation.read())
                generation.save()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not save PDF to generation record: {str(e)}")
    
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
    
    # Prepare response with PDF generation status
    response_data = {
        'message': 'Document generated successfully',
        'pdf_generated': pdf_generated,
        'data': {
            'document': DocumentSerializer(document, context={'request': request}).data,
            'generation': DocumentGenerationSerializer(generation).data,
        }
    }
    
    if not pdf_generated and template.template_content:
        response_data['warning'] = 'PDF could not be generated. Please check template content and ensure WeasyPrint is installed.'
    
    return Response(response_data, status=status.HTTP_201_CREATED)


def generate_pdf_from_template(template, field_data, title=None):
    """
    Generate PDF from template content by replacing placeholders with field data.
    If template_content is empty, creates a default document with field data.
    
    Args:
        template: DocumentTemplate instance
        field_data: Dictionary of field values to replace in template
        title: Optional title for the document
        
    Returns:
        ContentFile: PDF file content
    """
    # Get template content
    template_content = template.template_content or ''
    content_type = template.content_type or 'html'
    
    # If template_content is empty, create a default template
    if not template_content.strip():
        template_content = create_default_template(template, field_data, title)
    
    # Replace placeholders in template content
    # Support both {{field_name}} and {field_name} formats
    processed_content = template_content
    
    # Replace all placeholders with field values
    for key, value in field_data.items():
        if value is None:
            value = ''
        else:
            value = str(value)
        
        # Replace {{field_name}} format
        placeholder_pattern = r'\{\{' + re.escape(key) + r'\}\}'
        processed_content = re.sub(placeholder_pattern, value, processed_content, flags=re.IGNORECASE)
        
        # Replace {field_name} format
        placeholder_pattern2 = r'\{' + re.escape(key) + r'\}'
        processed_content = re.sub(placeholder_pattern2, value, processed_content, flags=re.IGNORECASE)
    
    # Generate PDF based on content type
    if content_type == 'html' or content_type == 'jsx':
        return generate_pdf_from_html(processed_content)
    elif content_type == 'markdown':
        # Convert markdown to HTML first
        try:
            import markdown
            processed_content = markdown.markdown(processed_content)
        except ImportError:
            # If markdown not available, treat as plain text
            processed_content = f"<html><body><pre>{processed_content}</pre></body></html>"
        return generate_pdf_from_html(processed_content)
    else:
        # Default to HTML
        return generate_pdf_from_html(processed_content)


def create_default_template(template, field_data, title=None):
    """
    Create a default HTML template when template_content is empty.
    
    Args:
        template: DocumentTemplate instance
        field_data: Dictionary of field values
        title: Optional title for the document
        
    Returns:
        str: HTML content
    """
    from datetime import datetime
    
    doc_title = title or template.name
    
    # Build fields table HTML
    fields_html = ""
    for key, value in field_data.items():
        # Convert key to readable label
        label = key.replace('_', ' ').title()
        fields_html += f"""
        <tr>
            <td style="font-weight: bold; padding: 10px; border: 1px solid #ddd; background-color: #f9f9f9;">{label}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{value if value else '-'}</td>
        </tr>
        """
    
    # Create default HTML template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{doc_title}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                border-bottom: 2px solid #2c5f2d;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2c5f2d;
                margin: 0;
                font-size: 24px;
            }}
            .header p {{
                color: #666;
                margin: 5px 0 0 0;
            }}
            .section {{
                margin-bottom: 30px;
            }}
            .section-title {{
                color: #2c5f2d;
                font-size: 18px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .meta-info {{
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
            .meta-info p {{
                margin: 5px 0;
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{doc_title}</h1>
            <p>{template.description or 'Generated Document'}</p>
        </div>
        
        <div class="meta-info">
            <p><strong>Template:</strong> {template.name} (v{template.version})</p>
            <p><strong>Category:</strong> {template.get_category_display() if hasattr(template, 'get_category_display') else template.category}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="section">
            <h2 class="section-title">Document Details</h2>
            <table>
                {fields_html}
            </table>
        </div>
        
        <div class="footer">
            <p>This document was automatically generated.</p>
            <p>Document ID will be assigned upon finalization.</p>
        </div>
    </body>
    </html>
    """
    
    return html_content


def generate_pdf_from_html(html_content):
    """
    Generate PDF from HTML content using xhtml2pdf (Windows-friendly), WeasyPrint, or ReportLab.
    
    Args:
        html_content: HTML content as string
        
    Returns:
        ContentFile: PDF file content
    """
    # Create a complete HTML document if not already complete
    if '<html' not in html_content.lower():
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    line-height: 1.6;
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
    
    # Try xhtml2pdf first (best for Windows, no external dependencies)
    if XHTML2PDF_AVAILABLE:
        try:
            buffer = BytesIO()
            result = pisa.CreatePDF(
                html_content,
                dest=buffer,
                encoding='utf-8'
            )
            
            if not result.err:
                buffer.seek(0)
                return ContentFile(buffer.read(), name='document.pdf')
            else:
                raise Exception(f"xhtml2pdf PDF generation failed: {result.err}")
        except Exception as e:
            # If xhtml2pdf fails, try next option
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"xhtml2pdf failed, trying alternative: {str(e)}")
    
    # Try WeasyPrint (good for Linux/Mac)
    if WEASYPRINT_AVAILABLE:
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
            return ContentFile(pdf_bytes, name='document.pdf')
        except Exception as e:
            # If WeasyPrint fails, try next option
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"WeasyPrint failed, trying alternative: {str(e)}")
    
    # Fallback to ReportLab (basic text rendering)
    if REPORTLAB_AVAILABLE:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Simple HTML to text conversion for ReportLab
            # Remove HTML tags and create paragraphs
            text_content = re.sub(r'<[^>]+>', '', html_content)
            paragraphs = text_content.split('\n\n')
            
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))
            
            doc.build(story)
            buffer.seek(0)
            return ContentFile(buffer.read(), name='document.pdf')
        except Exception as e:
            raise Exception(f"ReportLab PDF generation failed: {str(e)}")
    
    # No PDF library available - raise error
    raise ImportError(
        "No PDF generation library available. Please install xhtml2pdf (recommended for Windows) or WeasyPrint. "
        "Install with: pip install xhtml2pdf"
    )


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
    
    serializer = DocumentGenerationSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_investors_list(request):
    """
    Get list of all investors for document generation dropdown.
    GET /api/documents/investors/
    
    Query Parameters:
    - search: Search by name, username, or email
    - spv_id: Filter investors by SPV ID
    - limit: Limit the number of results (default: 100)
    
    Response:
    {
        "count": 10,
        "results": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "username": "johndoe",
                "first_name": "John",
                "last_name": "Doe",
                "spvs": [
                    {
                        "id": 3,
                        "display_name": "Tech Startup Fund I",
                        "status": "active",
                        "invested_amount": "100000.00"
                    }
                ]
            },
            ...
        ]
    }
    """
    from investors.dashboard_models import Investment
    
    # Get all users with role='investor'
    queryset = CustomUser.objects.filter(role='investor', is_active=True)
    
    # Filter by SPV if provided
    spv_filter_id = request.query_params.get('spv_id', None)
    if spv_filter_id:
        # Get investors who have invested in this SPV
        investor_ids = Investment.objects.filter(spv_id=spv_filter_id).values_list('investor_id', flat=True)
        queryset = queryset.filter(id__in=investor_ids)
    
    # Search functionality
    search = request.query_params.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Limit results
    limit = request.query_params.get('limit', 100)
    try:
        limit = int(limit)
    except ValueError:
        limit = 100
    
    queryset = queryset[:limit]
    
    # Format response with SPVs
    investors = []
    for user in queryset:
        full_name = user.get_full_name()
        if not full_name:
            full_name = user.username
        
        # Get SPVs this investor has invested in
        investments = Investment.objects.filter(investor=user).select_related('spv')
        spvs_list = []
        for investment in investments:
            if investment.spv:
                spvs_list.append({
                    'id': investment.spv.id,
                    'display_name': investment.spv.display_name,
                    'status': investment.spv.status,
                    'invested_amount': str(investment.invested_amount) if investment.invested_amount else '0',
                })
        
        investors.append({
            'id': user.id,
            'name': full_name,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'spvs': spvs_list,
        })
    
    return Response({
        'count': len(investors),
        'results': investors
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_spvs_list(request):
    """
    Get list of all SPVs for document generation dropdown.
    GET /api/documents/spvs/
    
    Query Parameters:
    - search: Search by display_name or portfolio_company_name
    - status: Filter by status (active, approved, etc.)
    - limit: Limit the number of results (default: 100)
    
    Response:
    [
        {
            "id": 1,
            "display_name": "Tech Startup Fund I",
            "portfolio_company_name": "XYZ Tech",
            "status": "active"
        },
        ...
    ]
    """
    user = request.user
    queryset = SPV.objects.all()
    
    # Filter by user role - non-admin users only see their own SPVs or SPVs they're associated with
    if not (user.is_staff or user.role == 'admin'):
        # Get SPVs created by user or associated with user's syndicate
        from django.db.models import Q
        filter_q = Q(created_by=user)
        
        if hasattr(user, 'syndicateprofile'):
            # Also include SPVs from deals where user is the syndicate
            filter_q |= Q(created_by__syndicateprofile=user.syndicateprofile)
        
        queryset = queryset.filter(filter_q)
    
    # Search functionality
    search = request.query_params.get('search', None)
    if search:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(display_name__icontains=search) |
            Q(portfolio_company_name__icontains=search)
        )
    
    # Filter by status
    status_filter = request.query_params.get('status', None)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Limit results
    limit = request.query_params.get('limit', 100)
    try:
        limit = int(limit)
    except ValueError:
        limit = 100
    
    queryset = queryset.order_by('-created_at')[:limit]
    
    # Format response
    spvs = []
    for spv in queryset:
        spvs.append({
            'id': spv.id,
            'display_name': spv.display_name,
            'portfolio_company_name': spv.portfolio_company_name or '',
            'status': spv.status,
            'created_at': spv.created_at.isoformat() if spv.created_at else None,
        })
    
    return Response({
        'count': len(spvs),
        'results': spvs
    }, status=status.HTTP_200_OK)


class DocumentGenerationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing generated documents with PDF files.
    GET /api/document-generations/ - List all generated documents
    GET /api/document-generations/{id}/ - Get specific generation details
    GET /api/document-generations/{id}/download/ - Download generated PDF
    GET /api/document-generations/{id}/view/ - View PDF in browser
    """
    queryset = DocumentGeneration.objects.all()
    serializer_class = DocumentGenerationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter generations based on user role and query parameters"""
        user = self.request.user
        queryset = DocumentGeneration.objects.all()
        
        # Filter by user role
        if not (user.is_staff or user.role == 'admin'):
            queryset = queryset.filter(generated_by=user)
        
        # Filter by template
        template_id = self.request.query_params.get('template', None)
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        
        # Filter by document
        document_id = self.request.query_params.get('document', None)
        if document_id:
            queryset = queryset.filter(generated_document_id=document_id)
        
        # Filter by has_pdf
        has_pdf = self.request.query_params.get('has_pdf', None)
        if has_pdf is not None:
            if has_pdf.lower() in ['true', '1', 'yes']:
                queryset = queryset.exclude(generated_pdf='').exclude(generated_pdf__isnull=True)
            elif has_pdf.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(Q(generated_pdf='') | Q(generated_pdf__isnull=True))
        
        return queryset.select_related('template', 'generated_document', 'generated_by')
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download generated PDF file
        GET /api/document-generations/{id}/download/
        """
        generation = self.get_object()
        
        if not generation.generated_pdf:
            return Response({
                'error': 'Generated PDF file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = FileResponse(
                generation.generated_pdf.open('rb'),
                content_type='application/pdf'
            )
            filename = generation.pdf_filename or f'{generation.generated_document.document_id}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                'error': f'Error downloading PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def view(self, request, pk=None):
        """
        View generated PDF file in browser
        GET /api/document-generations/{id}/view/
        """
        generation = self.get_object()
        
        if not generation.generated_pdf:
            return Response({
                'error': 'Generated PDF file not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            response = FileResponse(
                generation.generated_pdf.open('rb'),
                content_type='application/pdf'
            )
            filename = generation.pdf_filename or f'{generation.generated_document.document_id}.pdf'
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        except Exception as e:
            return Response({
                'error': f'Error viewing PDF: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



