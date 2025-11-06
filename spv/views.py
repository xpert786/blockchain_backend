from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import SPV, PortfolioCompany, CompanyStage, IncorporationType
from .serializers import (
    SPVSerializer,
    SPVCreateSerializer,
    SPVListSerializer,
    PortfolioCompanySerializer,
    CompanyStageSerializer,
    IncorporationTypeSerializer,
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


class CompanyStageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Company Stages (read-only)
    """
    queryset = CompanyStage.objects.all()
    serializer_class = CompanyStageSerializer
    permission_classes = [permissions.IsAuthenticated]


class IncorporationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Incorporation Types (read-only)
    """
    queryset = IncorporationType.objects.all()
    serializer_class = IncorporationTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


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
    })
