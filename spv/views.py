from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import (
    SPV, PortfolioCompany, CompanyStage, IncorporationType,
    InstrumentType, ShareClass, Round, MasterPartnershipEntity
)
from .serializers import (
    SPVSerializer,
    SPVCreateSerializer,
    SPVListSerializer,
    SPVStep2Serializer,
    SPVStep3Serializer,
    SPVStep4Serializer,
    SPVStep5Serializer,
    PortfolioCompanySerializer,
    CompanyStageSerializer,
    IncorporationTypeSerializer,
    InstrumentTypeSerializer,
    ShareClassSerializer,
    RoundSerializer,
    MasterPartnershipEntitySerializer,
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Custom permission to only allow owners of SPV or admins to view/edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Admin can access all SPVs
        if request.user.is_staff or request.user.role == 'admin':
            return True
        # Users can only access their own SPVs
        return obj.created_by == request.user


class SPVViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SPV deals
    Provides CRUD operations for SPV model
    """
    queryset = SPV.objects.all()
    serializer_class = SPVSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return SPVCreateSerializer
        elif self.action == 'list':
            return SPVListSerializer
        elif self.action == 'update_step2':
            return SPVStep2Serializer
        elif self.action == 'update_step3':
            return SPVStep3Serializer
        elif self.action == 'update_step4':
            return SPVStep4Serializer
        elif self.action == 'update_step5':
            return SPVStep5Serializer
        return SPVSerializer
    
    def get_queryset(self):
        """Filter SPVs based on user role"""
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            # Admins can see all SPVs
            return SPV.objects.all()
        else:
            # Users can only see their own SPVs
            return SPV.objects.filter(created_by=user)
    
    def perform_create(self, serializer):
        """Set the creator to current user when creating SPV"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_spvs(self, request):
        """
        Get current user's SPV records
        GET /api/spv/my_spvs/
        """
        spv_records = SPV.objects.filter(created_by=request.user)
        serializer = SPVListSerializer(spv_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        """
        Update SPV status (Admin only)
        PATCH /api/spv/{id}/update_status/
        """
        # Check if user is admin
        if not (request.user.is_staff or request.user.role == 'admin'):
            return Response({
                'error': 'Only admins can update SPV status'
            }, status=status.HTTP_403_FORBIDDEN)
        
        spv = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(SPV.STATUS_CHOICES):
            return Response({
                'error': f'Invalid status. Must be one of: {", ".join([choice[0] for choice in SPV.STATUS_CHOICES])}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        spv.status = new_status
        spv.save()
        
        return Response({
            'message': 'SPV status updated successfully',
            'data': SPVSerializer(spv).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step2(self, request, pk=None):
        """
        Update SPV Step 2 (Terms) fields
        PATCH /api/spv/{id}/update_step2/
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to update this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SPVStep2Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 2 (Terms) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step3(self, request, pk=None):
        """
        Update SPV Step 3 (Adviser & Legal Structure) fields
        PATCH /api/spv/{id}/update_step3/
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to update this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SPVStep3Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 3 (Adviser & Legal Structure) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step4(self, request, pk=None):
        """
        Update SPV Step 4 (Fundraising & Jurisdiction) fields
        PATCH /api/spv/{id}/update_step4/
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to update this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SPVStep4Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 4 (Fundraising & Jurisdiction) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step5(self, request, pk=None):
        """
        Update SPV Step 5 (Invite LPs & Additional Information) fields
        PATCH /api/spv/{id}/update_step5/
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to update this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SPVStep5Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 5 (Invite LPs & Additional Information) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PortfolioCompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Portfolio Companies
    """
    queryset = PortfolioCompany.objects.all()
    serializer_class = PortfolioCompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter portfolio companies"""
        search = self.request.query_params.get('search', None)
        queryset = PortfolioCompany.objects.all()
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('name')


class StaffCreateMixin:
    """
    Mixin to allow only staff/admin users to create reference data entries.
    """

    def create(self, request, *args, **kwargs):
        user = request.user
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            return Response(
                {'error': 'Only staff or admin users can create entries.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class CompanyStageViewSet(StaffCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating Company Stages
    """
    queryset = CompanyStage.objects.all()
    serializer_class = CompanyStageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']


class IncorporationTypeViewSet(StaffCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating Incorporation Types
    """
    queryset = IncorporationType.objects.all()
    serializer_class = IncorporationTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']


class InstrumentTypeViewSet(StaffCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating Instrument Types
    """
    queryset = InstrumentType.objects.all()
    serializer_class = InstrumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']


class ShareClassViewSet(StaffCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating Share Classes
    """
    queryset = ShareClass.objects.all()
    serializer_class = ShareClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']


class RoundViewSet(StaffCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating Rounds
    """
    queryset = Round.objects.all()
    serializer_class = RoundSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']


class MasterPartnershipEntityViewSet(StaffCreateMixin, viewsets.ModelViewSet):
    """
    ViewSet for viewing and creating Master Partnership Entities
    """
    queryset = MasterPartnershipEntity.objects.all()
    serializer_class = MasterPartnershipEntitySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_spv_options(request):
    """
    Get all options needed for SPV creation form
    GET /api/spv/options/
    """
    return Response({
        'company_stages': CompanyStageSerializer(CompanyStage.objects.all(), many=True).data,
        'incorporation_types': IncorporationTypeSerializer(IncorporationType.objects.all(), many=True).data,
        'portfolio_companies': PortfolioCompanySerializer(PortfolioCompany.objects.all()[:50], many=True).data,
        'instrument_types': InstrumentTypeSerializer(InstrumentType.objects.all(), many=True).data,
        'share_classes': ShareClassSerializer(ShareClass.objects.all(), many=True).data,
        'rounds': RoundSerializer(Round.objects.all(), many=True).data,
        'master_partnership_entities': MasterPartnershipEntitySerializer(MasterPartnershipEntity.objects.all(), many=True).data,
        'transaction_types': [{'value': choice[0], 'label': choice[1]} for choice in SPV.TRANSACTION_TYPE_CHOICES],
        'valuation_types': [{'value': choice[0], 'label': choice[1]} for choice in SPV.VALUATION_TYPE_CHOICES],
        'adviser_entities': [{'value': choice[0], 'label': choice[1]} for choice in SPV.ADVISER_ENTITY_CHOICES],
        'access_modes': [{'value': choice[0], 'label': choice[1]} for choice in SPV.ACCESS_MODE_CHOICES],
        'investment_visibility_options': [{'value': choice[0], 'label': choice[1]} for choice in SPV.INVESTMENT_VISIBILITY_CHOICES],
    })


def _build_lookup_response(serializer_class, queryset):
    """
    Helper to serialize lookup querysets consistently.
    """
    serializer = serializer_class(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_company_stages(request):
    """
    Lookup endpoint: GET /api/lookups/company-stages/
    """
    return _build_lookup_response(CompanyStageSerializer, CompanyStage.objects.all())


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_incorporation_types(request):
    """
    Lookup endpoint: GET /api/lookups/incorporation-types/
    """
    return _build_lookup_response(IncorporationTypeSerializer, IncorporationType.objects.all())


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_instrument_types(request):
    """
    Lookup endpoint: GET /api/lookups/instrument-types/
    """
    return _build_lookup_response(InstrumentTypeSerializer, InstrumentType.objects.all())


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_share_classes(request):
    """
    Lookup endpoint: GET /api/lookups/share-classes/
    """
    return _build_lookup_response(ShareClassSerializer, ShareClass.objects.all())


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_rounds(request):
    """
    Lookup endpoint: GET /api/lookups/rounds/
    """
    return _build_lookup_response(RoundSerializer, Round.objects.all())


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_master_partnership_entities(request):
    """
    Lookup endpoint: GET /api/lookups/master-partnership-entities/
    """
    return _build_lookup_response(
        MasterPartnershipEntitySerializer,
        MasterPartnershipEntity.objects.all()
    )
