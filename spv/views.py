from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum, Count, Q as DjangoQ
from django.db import models
from django.utils import timezone

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from kyc.models import KYC

from .models import (
    SPV, PortfolioCompany, CompanyStage, IncorporationType,
    InstrumentType, ShareClass, Round, MasterPartnershipEntity
)
from users.models import CustomUser
from users.serializers import CustomUserSerializer
from .serializers import (
    SPVSerializer,
    SPVCreateSerializer,
    SPVListSerializer,
    SPVStep1CreateSerializer,
    SPVStep1Serializer,
    SPVStep2Serializer,
    SPVStep3Serializer,
    SPVStep4Serializer,
    SPVStep5Serializer,
    SPVStep6Serializer,
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
        elif self.action == 'update_step6':
            return SPVStep6Serializer
        return SPVSerializer
    
    def get_queryset(self):
        """Filter SPVs based on user role"""
        user = self.request.user
        print(user, "--------user info ---------")
        if user.role == 'admin':
            # Admins can see all SPVs
            spv_data = SPV.objects.all()
            print(spv_data, "-------all spv data------")
            return spv_data
        else:
            # Users can only see their own SPVs
            user_spvs = SPV.objects.filter(created_by=user)
            print(user_spvs, "-------user spv data------")
            return user_spvs
    
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
        if not (request.user.role == 'admin'):
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
    

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_step1(self, request):
        serializer = SPVStep1CreateSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            spv = serializer.save()
            return Response({
                "message": "SPV Step 1 created successfully",
                "data": SPVSerializer(spv).data,
                "step": 1
            }, status=201)

        return Response(serializer.errors, status=400)


    
    @action(detail=True, methods=['get', 'post', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step1(self, request, pk=None):
        """
        Get, Create or Update SPV Step 1 (Basic Information) fields
        GET /api/spv/{id}/update_step1/ - Get step 1 data
        POST /api/spv/{id}/update_step1/ - Create or update step 1
        PATCH /api/spv/{id}/update_step1/ - Update step 1 (for editing when going back)
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle GET request
        if request.method == 'GET':
            step1_serializer = SPVStep1Serializer(spv)
            spv_serializer = SPVSerializer(spv)
            return Response({
                'success': True,
                'step_data': step1_serializer.data,
                'spv': spv_serializer.data,
                'step': 1,
                'step_name': 'Basic Information'
            }, status=status.HTTP_200_OK)
        
        # Handle POST/PATCH request
        serializer = SPVStep1Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 1 (Basic Information) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step2(self, request, pk=None):
        """
        Get, Create or Update SPV Step 2 (Terms) fields
        GET /api/spv/{id}/update_step2/ - Get step 2 data
        POST /api/spv/{id}/update_step2/ - Create or update step 2
        PATCH /api/spv/{id}/update_step2/ - Update step 2 (for editing when going back)
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle GET request
        if request.method == 'GET':
            step2_serializer = SPVStep2Serializer(spv)
            spv_serializer = SPVSerializer(spv)
            return Response({
                'success': True,
                'step_data': step2_serializer.data,
                'spv': spv_serializer.data,
                'step': 2,
                'step_name': 'Terms'
            }, status=status.HTTP_200_OK)
        
        # Handle POST/PATCH request
        serializer = SPVStep2Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 2 (Terms) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step3(self, request, pk=None):
        """
        Get, Create or Update SPV Step 3 (Adviser & Legal Structure) fields
        GET /api/spv/{id}/update_step3/ - Get step 3 data
        POST /api/spv/{id}/update_step3/ - Create or update step 3
        PATCH /api/spv/{id}/update_step3/ - Update step 3 (for editing when going back)
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle GET request
        if request.method == 'GET':
            step3_serializer = SPVStep3Serializer(spv)
            spv_serializer = SPVSerializer(spv)
            return Response({
                'success': True,
                'step_data': step3_serializer.data,
                'spv': spv_serializer.data,
                'step': 3,
                'step_name': 'Adviser & Legal Structure'
            }, status=status.HTTP_200_OK)
        
        # Handle POST/PATCH request
        serializer = SPVStep3Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 3 (Adviser & Legal Structure) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step4(self, request, pk=None):
        """
        Get, Create or Update SPV Step 4 (Fundraising & Jurisdiction) fields
        GET /api/spv/{id}/update_step4/ - Get step 4 data
        POST /api/spv/{id}/update_step4/ - Create or update step 4
        PATCH /api/spv/{id}/update_step4/ - Update step 4 (for editing when going back)
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle GET request
        if request.method == 'GET':
            step4_serializer = SPVStep4Serializer(spv)
            spv_serializer = SPVSerializer(spv)
            return Response({
                'success': True,
                'step_data': step4_serializer.data,
                'spv': spv_serializer.data,
                'step': 4,
                'step_name': 'Fundraising & Jurisdiction'
            }, status=status.HTTP_200_OK)
        
        # Handle POST/PATCH request
        serializer = SPVStep4Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 4 (Fundraising & Jurisdiction) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step5(self, request, pk=None):
        """
        Get, Create or Update SPV Step 5 (Invite LPs & Additional Information) fields
        GET /api/spv/{id}/update_step5/ - Get step 5 data
        POST /api/spv/{id}/update_step5/ - Create or update step 5
        PATCH /api/spv/{id}/update_step5/ - Update step 5 (for editing when going back)
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle GET request
        if request.method == 'GET':
            step5_serializer = SPVStep5Serializer(spv)
            spv_serializer = SPVSerializer(spv)
            return Response({
                'success': True,
                'step_data': step5_serializer.data,
                'spv': spv_serializer.data,
                'step': 5,
                'step_name': 'Invite LPs & Additional Information'
            }, status=status.HTTP_200_OK)
        
        # Handle POST/PATCH request
        serializer = SPVStep5Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 5 (Invite LPs & Additional Information) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'post', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_step6(self, request, pk=None):
        """
        Get, Create or Update SPV Step 6 (Additional Information) fields
        GET /api/spv/{id}/update_step6/ - Get step 6 data
        POST /api/spv/{id}/update_step6/ - Create or update step 6
        PATCH /api/spv/{id}/update_step6/ - Update step 6 (for editing when going back)
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Handle GET request
        if request.method == 'GET':
            step6_serializer = SPVStep6Serializer(spv)
            spv_serializer = SPVSerializer(spv)
            return Response({
                'success': True,
                'step_data': step6_serializer.data,
                'spv': spv_serializer.data,
                'step': 6,
                'step_name': 'Additional Information'
            }, status=status.HTTP_200_OK)
        
        # Handle POST/PATCH request
        serializer = SPVStep6Serializer(spv, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'SPV Step 6 (Additional Information) updated successfully',
                'data': SPVSerializer(spv).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def final_review(self, request, pk=None):
        """
        Get all SPV data from all steps (1-6) for Final Review
        GET /api/spv/{id}/final_review/
        """
        spv = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to access this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get data from all steps
        step1_data = SPVStep1Serializer(spv).data
        step2_data = SPVStep2Serializer(spv).data
        step3_data = SPVStep3Serializer(spv).data
        step4_data = SPVStep4Serializer(spv).data
        step5_data = SPVStep5Serializer(spv).data
        step6_data = SPVStep6Serializer(spv).data
        
        # Get full SPV data
        full_spv_data = SPVSerializer(spv).data
        
        return Response({
            'success': True,    
            'spv_id': spv.id,
            'spv_status': spv.status,
            'steps': {
                'step_1': {
                    'step_name': 'Basic Information',
                    'data': step1_data
                },
                'step_2': {
                    'step_name': 'Terms',
                    'data': step2_data
                },
                'step_3': {
                    'step_name': 'Adviser & Legal Structure',
                    'data': step3_data
                },
                'step_4': {
                    'step_name': 'Fundraising & Jurisdiction',
                    'data': step4_data
                },
                'step_5': {
                    'step_name': 'Invite LPs & Additional Information',
                    'data': step5_data
                },
                'step_6': {
                    'step_name': 'Additional Information',
                    'data': step6_data
                }
            },
            'full_spv_data': full_spv_data,
            'created_at': spv.created_at.isoformat(),
            'updated_at': spv.updated_at.isoformat(),
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def final_submit(self, request, pk=None):
        """
        Final submit the SPV after completing all 6 steps.
        Saves the SPV and changes status to 'pending_review'.
        POST /api/spv/{id}/final_submit/
        """
        spv = self.get_object()

        # Permission check
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': 'You do not have permission to submit this SPV'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # validation added
        serializer = SPVStep6Serializer(spv, data=request.data, partial=True,context={'final_submit': True})
        serializer.is_valid(raise_exception=True)
        serializer.save()


        # REQUIRED FIELDS CHECK (based on all steps)
        required_fields = [
            'deal_name',
            'syndicate_selection',
            'jurisdiction',
            'entity_type',
            'minimum_lp_investment'
        ]

        missing = [f for f in required_fields if not getattr(spv, f)]
        if missing:
            return Response({
                'error': 'Cannot submit SPV. Missing required fields.',
                'missing_fields': missing
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update status
        spv.status = 'pending_review'
        spv.save()

        return Response({
            'message': 'SPV submitted successfully and is now pending admin review.',
            'spv': SPVSerializer(spv).data
        }, status=status.HTTP_200_OK)



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
    # Get fund leads - typically staff/admin users or users with specific roles
    fund_leads = CustomUser.objects.filter(
        DjangoQ(is_staff=True) | DjangoQ(role__in=['admin', 'syndicate'])
    ).order_by('first_name', 'last_name', 'username')
    
    return Response({
        'company_stages': CompanyStageSerializer(CompanyStage.objects.all(), many=True).data,
        'incorporation_types': IncorporationTypeSerializer(IncorporationType.objects.all(), many=True).data,
        'portfolio_companies': PortfolioCompanySerializer(PortfolioCompany.objects.all()[:50], many=True).data,
        'instrument_types': InstrumentTypeSerializer(InstrumentType.objects.all(), many=True).data,
        'share_classes': ShareClassSerializer(ShareClass.objects.all(), many=True).data,
        'rounds': RoundSerializer(Round.objects.all(), many=True).data,
        'master_partnership_entities': MasterPartnershipEntitySerializer(MasterPartnershipEntity.objects.all(), many=True).data,
        'fund_leads': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name() or user.username,
            }
            for user in fund_leads
        ],
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


def _safe_decimal(value):
    """Safely convert value to Decimal, handling edge cases"""
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    
    # Handle string values
    value_str = str(value).strip()
    if not value_str or value_str.lower() in ['none', 'null', '']:
        return Decimal('0')
    
    try:
        return Decimal(value_str)
    except Exception:
        # If conversion fails, return 0
        return Decimal('0')


def _decimal_to_float(value, precision='0.01'):
    """Safely convert Decimal to float with precision"""
    value = _safe_decimal(value)
    try:
        quantizer = Decimal(precision)
        if quantizer != 0:
            return float(value.quantize(quantizer, rounding=ROUND_HALF_UP))
        return float(value)
    except Exception:
        # If quantize fails, return float directly
        return float(value) if value else 0.0


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_dashboard_summary(request):
    """
    Dashboard summary for syndicate managers.
    GET /api/spv/dashboard/
    """
    from investors.dashboard_models import Investment
    
    user = request.user
    if user.is_staff or getattr(user, 'role', '') == 'admin':
        queryset = SPV.objects.all()
    else:
        queryset = SPV.objects.filter(created_by=user)

    queryset = queryset.select_related('company_stage', 'round')

    totals = queryset.aggregate(
        total_allocation=Sum('allocation'),
        total_round_size=Sum('round_size'),
        spv_count=Count('id')
    )

    total_aum = _safe_decimal(totals.get('total_allocation'))
    total_target = _safe_decimal(totals.get('total_round_size'))
    spv_count = totals.get('spv_count', 0) or 0

    # Count active investors (those who have actually invested, not just invited)
    # Only count investments with active/committed/approved status
    invested_statuses = ['active', 'committed', 'approved', 'pending_payment', 'payment_processing']
    try:
        spv_ids = list(queryset.values_list('id', flat=True))
        active_investors = Investment.objects.filter(
            spv_id__in=spv_ids,
            status__in=invested_statuses
        ).values('investor').distinct().count()
    except Exception:
        active_investors = 0
        
    average_investment = Decimal('0')
    if active_investors:
        average_investment = (total_aum / active_investors).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    my_spv_cards = []
    total_progress = Decimal('0')
    
    # Use .values() to avoid SQLite Decimal conversion errors
    try:
        spvs_values = queryset.values(
            'id', 'display_name', 'status', 'created_at', 'updated_at',
            'lp_invite_emails', 'round__name', 'company_stage__name'
        )
        
        for spv in spvs_values:
            try:
                # Get decimal fields separately with error handling
                allocation_obj = queryset.filter(id=spv['id']).values('allocation', 'round_size').first()
                
                if allocation_obj:
                    my_commitment = _safe_decimal(allocation_obj.get('allocation'))
                    target_amount = _safe_decimal(allocation_obj.get('round_size'))
                else:
                    my_commitment = Decimal('0')
                    target_amount = Decimal('0')
            except Exception:
                my_commitment = Decimal('0')
                target_amount = Decimal('0')

            # Count actual investors for this SPV (not just invited)
            spv_investor_count = Investment.objects.filter(
                spv_id=spv['id'],
                status__in=invested_statuses
            ).values('investor').distinct().count()
            
            # Get total raised amount from actual investors
            total_raised = Investment.objects.filter(
                spv_id=spv['id'],
                status__in=invested_statuses
            ).aggregate(total=Sum('invested_amount'))['total'] or Decimal('0')
            
            total_raised = _safe_decimal(total_raised)
                
            # Calculate progress based on total amount raised vs target (round_size)
            progress_percent = Decimal('0')
            if target_amount > 0:
                progress_percent = (total_raised / target_amount) * Decimal('100')
            progress_percent = min(progress_percent, Decimal('100'))
            total_progress += progress_percent
            
            my_spv_cards.append({
                'id': spv['id'],
                'code': f"SPV-{spv['id']:03d}",
                'name': spv['display_name'],
                'status': spv['status'],
                'status_label': dict(SPV.STATUS_CHOICES).get(spv['status'], spv['status']),
                'my_commitment': _decimal_to_float(my_commitment),
                'amount_raised': _decimal_to_float(total_raised),
                'target_amount': _decimal_to_float(target_amount),
                'target_currency': 'USD',
                'investor_count': spv_investor_count,
                'invited_count': len(spv['lp_invite_emails'] or []),  # Also include invited count separately
                'round': spv['round__name'],
                'stage': spv['company_stage__name'],
                'progress_percent': float(progress_percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)),
                'created_at': spv['created_at'].isoformat() if spv['created_at'] else None,
                'updated_at': spv['updated_at'].isoformat() if spv['updated_at'] else None,
            })
    except Exception:
        # Fallback: empty list if iteration fails
        my_spv_cards = []

    average_progress = float((total_progress / spv_count).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if spv_count else 0.0

    # Pending actions (KYC, document upload, review statuses)
    pending_actions = []
    kyc_record = KYC.objects.filter(user=user).order_by('-id').first()
    if not kyc_record or kyc_record.status != 'Approved':
        pending_actions.append({
            'id': 'kyc-verification',
            'title': 'Complete Your Business Verification',
            'description': 'To continue creating SPVs and managing investors, please verify your business details.',
            'status': kyc_record.status if kyc_record else 'missing',
            'action_required': 'kyc_verification',
            'updated_at': kyc_record.updated_at.isoformat() if kyc_record and hasattr(kyc_record, 'updated_at') and kyc_record.updated_at else None
        })

    now = timezone.now().date()
    
    # Use .values() to safely iterate SPVs without Decimal conversion
    try:
        for spv in queryset.values('id', 'status', 'display_name', 'pitch_deck', 'supporting_document', 'target_closing_date', 'updated_at'):
            if spv['status'] == 'pending_review':
                pending_actions.append({
                    'id': f'spv-review-{spv["id"]}',
                    'title': f'{spv["display_name"]} pending review',
                    'description': 'Review and approve deal terms to continue fundraising.',
                    'status': spv['status'],
                    'action_required': 'review_spv',
                    'spv_id': spv['id'],
                    'updated_at': spv['updated_at'].isoformat() if spv['updated_at'] else None,
                })
            if not spv['pitch_deck'] or not spv['supporting_document']:
                pending_actions.append({
                    'id': f'spv-docs-{spv["id"]}',
                    'title': f'Upload documents for {spv["display_name"]}',
                    'description': 'Pitch deck or supporting documents are missing.',
                    'status': 'documents_pending',
                    'action_required': 'upload_documents',
                    'spv_id': spv['id'],
                    'updated_at': spv['updated_at'].isoformat() if spv['updated_at'] else None,
                })
            if spv['target_closing_date'] and spv['target_closing_date'] <= now + timedelta(days=14) and spv['status'] not in ('closed', 'cancelled'):
                pending_actions.append({
                    'id': f'spv-closing-{spv["id"]}',
                    'title': f'{spv["display_name"]} closing soon',
                    'description': f'Target closing date {spv["target_closing_date"].isoformat()} is approaching.',
                    'status': 'closing_soon',
                    'action_required': 'close_out_spv',
                    'spv_id': spv['id'],
                    'updated_at': spv['updated_at'].isoformat() if spv['updated_at'] else None,
                })
    except Exception:
        pass  # Silently continue if pending actions fail

    status_breakdown = []
    status_totals = queryset.values('status').annotate(
        count=Count('id'),
        total_allocation=Sum('allocation')
    )
    status_labels = dict(SPV.STATUS_CHOICES)
    for entry in status_totals:
        status_breakdown.append({
            'status': entry['status'],
            'label': status_labels.get(entry['status'], entry['status']),
            'count': entry['count'],
            'total_allocation': _decimal_to_float(entry['total_allocation']),
        })

    analytics = {
        'performance_overview': {
            'total_funds_raised': _decimal_to_float(total_aum),
            'total_target': _decimal_to_float(total_target),
            'average_progress_percent': average_progress,
            'success_rate_percent': float(
                ((total_aum / total_target) * Decimal('100')).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            ) if total_target > 0 else 0.0,
        },
        'status_breakdown': status_breakdown,
        'active_investors': active_investors,
    }

    response_data = {
        'summary': {
            'my_spvs_count': spv_count,
            'total_aum': _decimal_to_float(total_aum),
            'total_target': _decimal_to_float(total_target),
            'active_investors': active_investors,
            'average_investment': _decimal_to_float(average_investment),
            'last_updated': timezone.now().isoformat(),
        },
        'sections': {
            'my_spvs': my_spv_cards,
            'pending_actions': pending_actions,
            'analytics': analytics,
        }
    }

    return Response(response_data)


STATUS_TABS = {
    'all': {
        'label': 'All',
        'statuses': None,
    },
    'ready_to_launch': {
        'label': 'Ready to launch',
        'statuses': ['approved', 'pending_review'],
    },
    'fundraising': {
        'label': 'Fundraising',
        'statuses': ['active'],
    },
    'closed': {
        'label': 'Closed',
        'statuses': ['closed', 'cancelled'],
    },
}


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_management_overview(request):
    """
    SPV management overview list with status filters.
    GET /api/spv/management/
    """
    from investors.dashboard_models import Investment
    
    user = request.user
    if user.is_staff or getattr(user, 'role', '') == 'admin':
        base_queryset = SPV.objects.all()
    else:
        base_queryset = SPV.objects.filter(created_by=user)

    base_queryset = base_queryset.select_related('company_stage', 'round', 'portfolio_company')

    status_key = request.query_params.get('status', 'all')
    if status_key not in STATUS_TABS:
        status_key = 'all'

    status_filter = STATUS_TABS[status_key]['statuses']
    queryset = base_queryset
    if status_filter:
        queryset = queryset.filter(status__in=status_filter)

    totals = base_queryset.aggregate(
        total_allocation=Sum('allocation'),
        total_round_size=Sum('round_size'),
        spv_count=Count('id')
    )

    total_aum = _safe_decimal(totals.get('total_allocation'))
    total_target = _safe_decimal(totals.get('total_round_size'))
    spv_count = totals.get('spv_count', 0) or 0

    # Count active investors (those who have actually invested, not just invited)
    invested_statuses = ['active', 'committed', 'approved', 'pending_payment', 'payment_processing']
    try:
        spv_ids = list(base_queryset.values_list('id', flat=True))
        active_investors = Investment.objects.filter(
            spv_id__in=spv_ids,
            status__in=invested_statuses
        ).values('investor').distinct().count()
    except Exception:
        active_investors = 0
    
    success_rate = Decimal('0')
    if total_target > 0:
        success_rate = (total_aum / total_target) * Decimal('100')

    spv_cards = []
    
    # Use .values() to avoid SQLite Decimal conversion errors
    try:
        queryset_values = queryset.values(
            'id', 'display_name', 'status', 'jurisdiction', 'deal_tags',
            'created_at', 'lp_invite_emails', 'pitch_deck', 'supporting_document',
            'portfolio_company_name', 'round__name', 'company_stage__name',
            'portfolio_company__name'
        )
        
        for spv in queryset_values:
            try:
                # Get decimal fields from database with error handling
                allocation_obj = base_queryset.filter(id=spv['id']).values('allocation', 'round_size', 'minimum_lp_investment').first()
                
                if allocation_obj:
                    my_commitment = _safe_decimal(allocation_obj.get('allocation'))
                    target_amount = _safe_decimal(allocation_obj.get('round_size'))
                    min_investment = _safe_decimal(allocation_obj.get('minimum_lp_investment'))
                else:
                    my_commitment = Decimal('0')
                    target_amount = Decimal('0')
                    min_investment = Decimal('0')
            except Exception:
                my_commitment = Decimal('0')
                target_amount = Decimal('0')
                min_investment = Decimal('0')

            # Count actual investors for this SPV (not just invited)
            spv_investor_count = Investment.objects.filter(
                spv_id=spv['id'],
                status__in=invested_statuses
            ).values('investor').distinct().count()
            
            # Get total raised amount from actual investors
            total_raised = Investment.objects.filter(
                spv_id=spv['id'],
                status__in=invested_statuses
            ).aggregate(total=Sum('invested_amount'))['total'] or Decimal('0')
            
            total_raised = _safe_decimal(total_raised)
            
            # Calculate progress based on total amount raised vs target (round_size)
            progress_percent = Decimal('0')
            if target_amount > 0:
                progress_percent = (total_raised / target_amount) * Decimal('100')
            progress_percent = min(progress_percent, Decimal('100'))
            
            spv_cards.append({
                'id': spv['id'],
                'code': f"SPV-{spv['id']:03d}",
                'name': spv['display_name'],
                'status': spv['status'],
                'status_label': dict(SPV.STATUS_CHOICES).get(spv['status'], spv['status']),
                'jurisdiction': spv['jurisdiction'],
                'sector': spv['deal_tags'][0] if isinstance(spv['deal_tags'], list) and spv['deal_tags'] else None,
                'industry_tags': spv['deal_tags'] or [],
                'created_at': spv['created_at'].isoformat() if spv['created_at'] else None,
                'target_amount': _decimal_to_float(target_amount),
                'amount_raised': _decimal_to_float(total_raised),
                'my_commitment': _decimal_to_float(my_commitment),
                'investor_count': spv_investor_count,
                'invited_count': len(spv['lp_invite_emails'] or []),  # Also include invited count separately
                'minimum_investment': _decimal_to_float(min_investment),
                'round': spv['round__name'],
                'stage': spv['company_stage__name'],
                'portfolio_company': spv['portfolio_company__name'] or spv['portfolio_company_name'],
                'funding_progress_percent': float(progress_percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)),
                'actions': {
                    'manage_investors': True,
                    'documents': spv['pitch_deck'] is not None or spv['supporting_document'] is not None,
                    'analytics': True,
                }
            })
    except Exception as e:
        # Fallback: return empty list if queryset iteration fails
        spv_cards = []

    tab_summary = []
    for key, config in STATUS_TABS.items():
        tab_queryset = base_queryset
        if config['statuses']:
            tab_queryset = tab_queryset.filter(status__in=config['statuses'])

        tab_data = tab_queryset.aggregate(
            count=Count('id'),
            total_allocation=Sum('allocation')
        )
        tab_summary.append({
            'key': key,
            'label': config['label'],
            'count': tab_data.get('count', 0) or 0,
            'total_allocation': _decimal_to_float(tab_data.get('total_allocation')),
            'active': key == status_key,
        })

    response_data = {
        'filters': {
            'selected_status': status_key,
            'available_statuses': tab_summary,
        },
        'summary': {
            'total_spvs': spv_count,
            'total_aum': _decimal_to_float(total_aum),
            'total_target': _decimal_to_float(total_target),
            'active_investors': active_investors,
            'success_rate_percent': float(success_rate.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if success_rate else 0.0,
            'last_updated': timezone.now().isoformat(),
        },
        'spvs': spv_cards,
    }

    return Response(response_data)
