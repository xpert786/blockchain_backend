from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
import logging

from .models import SyndicateProfile, TeamMember
from .serializers import (
    TeamMemberSerializer,
    TeamMemberListSerializer,
    TeamMemberCreateSerializer,
    TeamMemberUpdateSerializer,
    TeamMemberRoleUpdateSerializer,
    TeamMemberPermissionsUpdateSerializer
)

logger = logging.getLogger(__name__)


class IsSyndicateOwnerOrTeamManager(permissions.BasePermission):
    """
    Permission: Only syndicate owner or team members with can_manage_team permission
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Must have syndicate role
        if request.user.role != 'syndicate':
            return False
        
        # Check if user has syndicate profile
        try:
            syndicate = SyndicateProfile.objects.get(user=request.user)
        except SyndicateProfile.DoesNotExist:
            return False
        
        # Syndicate owner always has permission
        if syndicate.user == request.user:
            return True
        
        # Check if user is a team member with can_manage_team permission
        team_member = TeamMember.objects.filter(
            syndicate=syndicate,
            user=request.user,
            is_active=True,
            can_manage_team=True
        ).first()
        
        return team_member is not None


class TeamMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing team members
    """
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsSyndicateOwnerOrTeamManager]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return TeamMemberListSerializer
        elif self.action == 'create':
            return TeamMemberCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TeamMemberUpdateSerializer
        return TeamMemberSerializer
    
    def get_queryset(self):
        """Filter team members by current user's syndicate"""
        user = self.request.user
        
        # Get user's syndicate profile
        try:
            syndicate = SyndicateProfile.objects.get(user=user)
        except SyndicateProfile.DoesNotExist:
            return TeamMember.objects.none()
        
        queryset = TeamMember.objects.filter(syndicate=syndicate)
        
        # Filter by search query
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(role__icontains=search)
            )
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.select_related('user', 'added_by')
    
    def create(self, request, *args, **kwargs):
        """Create a new team member"""
        # Get syndicate profile
        try:
            syndicate = SyndicateProfile.objects.get(user=request.user)
        except SyndicateProfile.DoesNotExist:
            return Response({
                'error': 'Syndicate profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(
            data=request.data,
            context={
                'syndicate': syndicate,
                'added_by': request.user
            }
        )
        serializer.is_valid(raise_exception=True)
        team_member = serializer.save()
        
        # Return full details
        response_serializer = TeamMemberSerializer(team_member)
        return Response({
            'message': 'Team member added successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update team member"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        team_member = serializer.save()
        
        # Return full details
        response_serializer = TeamMemberSerializer(team_member)
        return Response({
            'message': 'Team member updated successfully',
            'data': response_serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete/remove team member"""
        instance = self.get_object()
        instance.delete()
        
        return Response({
            'message': 'Team member removed successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def update_role(self, request, pk=None):
        """
        Update team member role
        PATCH /api/team-members/{id}/update_role/
        """
        team_member = self.get_object()
        serializer = TeamMemberRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_role = serializer.validated_data['role']
        apply_permissions = serializer.validated_data['apply_role_permissions']
        
        team_member.role = new_role
        
        # Apply role-based permissions if requested and RBAC is enabled
        if apply_permissions and team_member.syndicate.enable_role_based_access_controls:
            team_member.apply_role_permissions()
        
        team_member.save()
        
        # Return updated team member
        response_serializer = TeamMemberSerializer(team_member)
        return Response({
            'message': 'Role updated successfully',
            'data': response_serializer.data
        })
    
    @action(detail=True, methods=['patch'])
    def update_permissions(self, request, pk=None):
        """
        Update team member permissions
        PATCH /api/team-members/{id}/update_permissions/
        """
        team_member = self.get_object()
        serializer = TeamMemberPermissionsUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Update permissions
        for field, value in serializer.validated_data.items():
            setattr(team_member, field, value)
        
        team_member.save()
        
        # Return updated team member
        response_serializer = TeamMemberSerializer(team_member)
        return Response({
            'message': 'Permissions updated successfully',
            'data': response_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate team member
        POST /api/team-members/{id}/deactivate/
        """
        team_member = self.get_object()
        team_member.is_active = False
        team_member.save()
        
        response_serializer = TeamMemberSerializer(team_member)
        return Response({
            'message': 'Team member deactivated successfully',
            'data': response_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate team member
        POST /api/team-members/{id}/activate/
        """
        team_member = self.get_object()
        team_member.is_active = True
        team_member.save()
        
        response_serializer = TeamMemberSerializer(team_member)
        return Response({
            'message': 'Team member activated successfully',
            'data': response_serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def roles(self, request):
        """
        Get available roles
        GET /api/team-members/roles/
        """
        return Response({
            'success': True,
            'data': {
                'roles': [
                    {'value': role[0], 'label': role[1]}
                    for role in TeamMember.ROLE_CHOICES
                ]
            }
        })
    
    @action(detail=False, methods=['get'])
    def permissions_list(self, request):
        """
        Get list of all available permissions
        GET /api/team-members/permissions_list/
        """
        return Response({
            'success': True,
            'data': {
                'permissions': [
                    {'key': 'can_access_dashboard', 'label': 'Access Dashboard'},
                    {'key': 'can_manage_spvs', 'label': 'Manage SPVs'},
                    {'key': 'can_manage_documents', 'label': 'Manage Documents'},
                    {'key': 'can_manage_investors', 'label': 'Manage Investors'},
                    {'key': 'can_view_reports', 'label': 'View Reports'},
                    {'key': 'can_manage_transfers', 'label': 'Manage Transfers'},
                    {'key': 'can_manage_team', 'label': 'Manage Team'},
                    {'key': 'can_manage_settings', 'label': 'Manage Settings'},
                ]
            }
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get team statistics
        GET /api/team-members/statistics/
        """
        # Get user's syndicate
        try:
            syndicate = SyndicateProfile.objects.get(user=request.user)
        except SyndicateProfile.DoesNotExist:
            return Response({
                'error': 'Syndicate profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        queryset = TeamMember.objects.filter(syndicate=syndicate)
        
        return Response({
            'success': True,
            'data': {
                'total_members': queryset.count(),
                'active_members': queryset.filter(is_active=True).count(),
                'inactive_members': queryset.filter(is_active=False).count(),
                'registered_members': queryset.filter(user__isnull=False).count(),
                'pending_invitations': queryset.filter(
                    invitation_sent=True,
                    invitation_accepted=False
                ).count(),
                'role_distribution': {
                    role[0]: queryset.filter(role=role[0]).count()
                    for role in TeamMember.ROLE_CHOICES
                }
            }
        })
