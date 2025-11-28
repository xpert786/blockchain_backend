from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import logging

from .models import SyndicateProfile
from .serializers import (
    SyndicateProfileSerializer,
    SyndicateSettingsGeneralInfoSerializer,
    SyndicateSettingsKYBVerificationSerializer,
    SyndicateSettingsComplianceSerializer,
    SyndicateSettingsJurisdictionalSerializer,
    SyndicateSettingsPortfolioSerializer,
    SyndicateSettingsNotificationsSerializer
)

logger = logging.getLogger(__name__)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_general_info(request):
    """
    Settings: General Information
    GET /api/syndicate/settings/general-info/ - Get general info
    PATCH /api/syndicate/settings/general-info/ - Update general info
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = SyndicateSettingsGeneralInfoSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    # Handle PATCH request
    # Handle file upload for logo if present
    file_uploaded = False
    if hasattr(request, 'FILES') and 'logo' in request.FILES:
        file = request.FILES['logo']
        profile.logo = file
        profile.save()
        file_uploaded = True
    
    # Prepare clean data for serializer (exclude file fields)
    serializer_data = {}
    if hasattr(request, 'data'):
        from django.http import QueryDict
        if isinstance(request.data, QueryDict):
            for key in request.data.keys():
                if key != 'logo':
                    serializer_data[key] = request.data[key]
        elif isinstance(request.data, dict):
            for key, value in request.data.items():
                if key != 'logo':
                    serializer_data[key] = value
    
    serializer = SyndicateSettingsGeneralInfoSerializer(
        profile,
        data=serializer_data,
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        profile.refresh_from_db()
        
        # Return updated profile
        response_serializer = SyndicateSettingsGeneralInfoSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'message': 'General information updated successfully',
            'data': response_serializer.data
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_team_management(request):
    """
    Settings: Team Management
    GET /api/syndicate/settings/team-management/ - Get team members
    PATCH /api/syndicate/settings/team-management/ - Update RBAC settings
    
    Note: Team member CRUD operations are handled by /api/team-members/ endpoints
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Import here to avoid circular import
        from .models import TeamMember
        from .serializers import TeamMemberListSerializer
        
        team_members = TeamMember.objects.filter(syndicate=profile).select_related('user')
        team_members_data = TeamMemberListSerializer(team_members, many=True).data
        
        return Response({
            'success': True,
            'data': {
                'syndicate_id': profile.id,
                'firm_name': profile.firm_name,
                'enable_role_based_access_controls': profile.enable_role_based_access_controls,
                'team_members_count': team_members.count(),
                'team_members': team_members_data
            }
        })
    
    # Handle PATCH request for RBAC settings
    enable_rbac = request.data.get('enable_role_based_access_controls')
    if enable_rbac is not None:
        profile.enable_role_based_access_controls = enable_rbac
        profile.save()
        
        return Response({
            'success': True,
            'message': 'Role-based access controls updated successfully',
            'data': {
                'enable_role_based_access_controls': profile.enable_role_based_access_controls
            }
        })
    
    return Response({
        'error': 'No valid data provided'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_kyb_verification(request):
    """
    Settings: KYB Verification
    GET /api/syndicate/settings/kyb-verification/ - Get KYB verification data
    PATCH /api/syndicate/settings/kyb-verification/ - Update KYB verification data
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = SyndicateSettingsKYBVerificationSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    # Handle PATCH request
    serializer = SyndicateSettingsKYBVerificationSerializer(
        profile,
        data=request.data,
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        profile.refresh_from_db()
        
        # Return updated profile
        response_serializer = SyndicateSettingsKYBVerificationSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'message': 'KYB verification data updated successfully',
            'data': response_serializer.data
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_compliance(request):
    """
    Settings: Compliance & Accreditation
    GET /api/syndicate/settings/compliance/ - Get compliance documents
    PATCH /api/syndicate/settings/compliance/ - Update compliance documents
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = SyndicateSettingsComplianceSerializer(profile, context={'request': request})
        
        # Get compliance document URL if exists
        compliance_file_url = None
        if profile.additional_compliance_policies:
            compliance_file_url = request.build_absolute_uri(profile.additional_compliance_policies.url)
        
        return Response({
            'success': True,
            'data': {
                **serializer.data,
                'compliance_file_url': compliance_file_url
            }
        })
    
    # Handle PATCH request
    # Handle file upload if present
    file_uploaded = False
    if hasattr(request, 'FILES') and 'additional_compliance_policies' in request.FILES:
        file = request.FILES['additional_compliance_policies']
        profile.additional_compliance_policies = file
        profile.save()
        file_uploaded = True
    
    # Prepare clean data for serializer (exclude file fields)
    serializer_data = {}
    if hasattr(request, 'data'):
        from django.http import QueryDict
        if isinstance(request.data, QueryDict):
            for key in request.data.keys():
                if key != 'additional_compliance_policies':
                    serializer_data[key] = request.data[key]
        elif isinstance(request.data, dict):
            for key, value in request.data.items():
                if key != 'additional_compliance_policies':
                    serializer_data[key] = value
    
    serializer = SyndicateSettingsComplianceSerializer(
        profile,
        data=serializer_data,
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        profile.refresh_from_db()
        
        # Get updated compliance file URL
        compliance_file_url = None
        if profile.additional_compliance_policies:
            compliance_file_url = request.build_absolute_uri(profile.additional_compliance_policies.url)
        
        # Return updated profile
        response_serializer = SyndicateSettingsComplianceSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'message': 'Compliance data updated successfully',
            'data': {
                **response_serializer.data,
                'compliance_file_url': compliance_file_url
            }
        })
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_jurisdictional(request):
    """
    Settings: Jurisdictional Settings
    GET /api/syndicate/settings/jurisdictional/ - Get jurisdictional settings
    PATCH /api/syndicate/settings/jurisdictional/ - Update jurisdictional settings
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        return Response({
            'success': True,
            'message': 'Jurisdictional settings endpoint',
            'data': {
                'jurisdictional_compliance_acknowledged': profile.jurisdictional_compliance_acknowledged,
                'geographies': [
                    {
                        'id': geo.id,
                        'name': geo.name,
                        'region': geo.region,
                        'country_code': geo.country_code
                    }
                    for geo in profile.geographies.all()
                ]
            }
        })
    
    elif request.method == 'PATCH':
        serializer = SyndicateSettingsJurisdictionalSerializer(
            profile, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Jurisdictional settings updated successfully',
                'data': {
                    'jurisdictional_compliance_acknowledged': profile.jurisdictional_compliance_acknowledged,
                    'geographies': [
                        {
                            'id': geo.id,
                            'name': geo.name,
                            'region': geo.region,
                            'country_code': geo.country_code
                        }
                        for geo in profile.geographies.all()
                    ]
                }
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_portfolio(request):
    """
    Settings: Portfolio Company Outreach
    GET /api/syndicate/settings/portfolio/ - Get portfolio settings
    PATCH /api/syndicate/settings/portfolio/ - Update portfolio settings
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        return Response({
            'success': True,
            'message': 'Portfolio company outreach settings endpoint',
            'data': {
                'sectors': [
                    {
                        'id': sector.id,
                        'name': sector.name,
                        'description': sector.description
                    }
                    for sector in profile.sectors.all()
                ],
                'enable_platform_lp_access': profile.enable_platform_lp_access,
                'existing_lp_count': profile.existing_lp_count
            }
        })
    
    elif request.method == 'PATCH':
        serializer = SyndicateSettingsPortfolioSerializer(
            profile,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Portfolio settings updated successfully',
                'data': {
                    'sectors': [
                        {
                            'id': sector.id,
                            'name': sector.name,
                            'description': sector.description
                        }
                        for sector in profile.sectors.all()
                    ],
                    'enable_platform_lp_access': profile.enable_platform_lp_access,
                    'existing_lp_count': profile.existing_lp_count
                }
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_notifications(request):
    """
    Settings: Notifications & Communication
    GET /api/syndicate/settings/notifications/ - Get notification settings
    PATCH /api/syndicate/settings/notifications/ - Update notification settings
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        return Response({
            'success': True,
            'message': 'Notifications & communication settings',
            'data': {
                'email': user.email,
                'phone_number': user.phone_number,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified,
                'two_factor_enabled': user.two_factor_enabled,
                'two_factor_method': user.two_factor_method,
                'notification_preference': user.notification_preference,
                'notify_email_preference': user.notify_email_preference,
                'notify_new_lp_alerts': user.notify_new_lp_alerts,
                'notify_deal_updates': user.notify_deal_updates
            }
        })
    
    elif request.method == 'PATCH':
        serializer = SyndicateSettingsNotificationsSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Notification settings updated successfully',
                'data': {
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'email_verified': user.email_verified,
                    'phone_verified': user.phone_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                    'two_factor_method': user.two_factor_method,
                    'notification_preference': user.notification_preference,
                    'notify_email_preference': user.notify_email_preference,
                    'notify_new_lp_alerts': user.notify_new_lp_alerts,
                    'notify_deal_updates': user.notify_deal_updates
                }
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_fee_recipient(request):
    """
    Settings: Fee Recipient Setup
    GET /api/syndicate/settings/fee-recipient/ - Get fee recipient settings
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'message': 'Fee recipient setup endpoint - to be implemented',
        'data': {
            'syndicate_id': profile.id,
            'firm_name': profile.firm_name
            # TODO: Add fee recipient fields when implemented
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_bank_details(request):
    """
    Settings: Bank Details
    GET /api/syndicate/settings/bank-details/ - Get bank details
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'message': 'Bank details endpoint - to be implemented',
        'data': {
            'syndicate_id': profile.id,
            'firm_name': profile.firm_name
            # TODO: Add bank details fields when implemented
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_overview(request):
    """
    Settings: Overview - Get all settings at once
    GET /api/syndicate/settings/overview/ - Get complete settings overview
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get all settings data
    general_info_serializer = SyndicateSettingsGeneralInfoSerializer(profile, context={'request': request})
    kyb_serializer = SyndicateSettingsKYBVerificationSerializer(profile, context={'request': request})
    compliance_serializer = SyndicateSettingsComplianceSerializer(profile, context={'request': request})
    
    return Response({
        'success': True,
        'data': {
            'general_info': general_info_serializer.data,
            'kyb_verification': kyb_serializer.data,
            'compliance': compliance_serializer.data,
            'team_management': {
                'enable_role_based_access_controls': profile.enable_role_based_access_controls
            },
            'jurisdictional': {
                'jurisdictional_compliance_acknowledged': profile.jurisdictional_compliance_acknowledged,
                'geographies': [
                    {'id': geo.id, 'name': geo.name, 'region': geo.region}
                    for geo in profile.geographies.all()
                ]
            },
            'portfolio': {
                'sectors': [
                    {'id': sector.id, 'name': sector.name}
                    for sector in profile.sectors.all()
                ],
                'enable_platform_lp_access': profile.enable_platform_lp_access,
                'existing_lp_count': profile.existing_lp_count
            },
            'user': {
                'email': user.email,
                'phone_number': user.phone_number,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified
            }
        }
    })
