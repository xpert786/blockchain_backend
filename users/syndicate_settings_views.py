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
    SyndicateSettingsNotificationsSerializer,
    FeeRecipientSerializer
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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_jurisdictional_detail(request, geography_id):
    """
    Settings: Specific Jurisdictional Geography
    GET /api/syndicate/settings/jurisdictional/<id>/ - Get specific geography details
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
    
    # Check if geography is associated with the syndicate profile
    from .models import Geography
    geography = get_object_or_404(Geography, id=geography_id)
    
    # Verify this geography is in the user's syndicate geographies
    if not profile.geographies.filter(id=geography_id).exists():
        return Response({
            'error': 'This geography is not associated with your syndicate profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'success': True,
        'message': 'Geography details retrieved successfully',
        'data': {
            'id': geography.id,
            'name': geography.name,
            'region': geography.region,
            'country_code': geography.country_code,
            'created_at': geography.created_at
        }
    })


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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_portfolio_detail(request, sector_id):
    """
    Settings: Specific Portfolio Sector
    GET /api/syndicate/settings/portfolio/<id>/ - Get specific sector details
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
    
    # Check if sector is associated with the syndicate profile
    from .models import Sector
    sector = get_object_or_404(Sector, id=sector_id)
    
    # Verify this sector is in the user's syndicate sectors
    if not profile.sectors.filter(id=sector_id).exists():
        return Response({
            'error': 'This sector is not associated with your syndicate profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        'success': True,
        'message': 'Sector details retrieved successfully',
        'data': {
            'id': sector.id,
            'name': sector.name,
            'description': sector.description,
            'created_at': sector.created_at
        }
    })


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
def syndicate_settings_notifications_detail(request, preference_type):
    """
    Settings: Specific Notification Preference
    GET /api/syndicate/settings/notifications/<preference_type>/ - Get specific notification preference details
    
    Supported preference_types:
    - email_preference
    - lp_alerts
    - deal_updates
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
    
    # Valid preference types
    preference_map = {
        'email_preference': {
            'key': 'notify_email_preference',
            'label': 'Email Preference',
            'description': 'Receive email notifications'
        },
        'lp_alerts': {
            'key': 'notify_new_lp_alerts',
            'label': 'New LP Alerts',
            'description': 'Receive alerts for new LP activities'
        },
        'deal_updates': {
            'key': 'notify_deal_updates',
            'label': 'Deal Status Updates',
            'description': 'Receive updates on deal status changes'
        }
    }
    
    if preference_type not in preference_map:
        return Response({
            'error': f'Invalid preference type. Valid options are: {", ".join(preference_map.keys())}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    pref_info = preference_map[preference_type]
    pref_value = getattr(user, pref_info['key'], False)
    
    return Response({
        'success': True,
        'message': f'{pref_info["label"]} notification preference retrieved',
        'data': {
            'type': preference_type,
            'label': pref_info['label'],
            'description': pref_info['description'],
            'enabled': pref_value,
            'user_email': user.email,
            'user_phone_number': user.phone_number
        }
    })


@api_view(['GET', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_fee_recipient(request):
    """
    Settings: Fee Recipient Setup
    GET /api/syndicate/settings/fee-recipient/ - Get fee recipient settings
    PATCH /api/syndicate/settings/fee-recipient/ - Update fee recipient settings
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
        # Get or create fee recipient
        from .models import FeeRecipient
        fee_recipient, created = FeeRecipient.objects.get_or_create(syndicate=profile)
        
        serializer = FeeRecipientSerializer(fee_recipient, context={'request': request})
        return Response({
            'success': True,
            'message': 'Fee recipient setup',
            'data': serializer.data
        })
    
    elif request.method == 'PATCH':
        from .models import FeeRecipient
        
        # Get or create fee recipient
        fee_recipient, created = FeeRecipient.objects.get_or_create(syndicate=profile)
        
        # Handle file uploads if present
        if hasattr(request, 'FILES') and 'id_document' in request.FILES:
            fee_recipient.id_document = request.FILES['id_document']
        
        if hasattr(request, 'FILES') and 'proof_of_address' in request.FILES:
            fee_recipient.proof_of_address = request.FILES['proof_of_address']
        
        # Prepare clean data for serializer (exclude file fields)
        serializer_data = {}
        if hasattr(request, 'data'):
            from django.http import QueryDict
            if isinstance(request.data, QueryDict):
                for key in request.data.keys():
                    if key not in ['id_document', 'proof_of_address']:
                        serializer_data[key] = request.data[key]
            elif isinstance(request.data, dict):
                for key, value in request.data.items():
                    if key not in ['id_document', 'proof_of_address']:
                        serializer_data[key] = value
        
        serializer = FeeRecipientSerializer(
            fee_recipient,
            data=serializer_data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Save files first
            if hasattr(request, 'FILES') and 'id_document' in request.FILES:
                fee_recipient.id_document = request.FILES['id_document']
            if hasattr(request, 'FILES') and 'proof_of_address' in request.FILES:
                fee_recipient.proof_of_address = request.FILES['proof_of_address']
            
            serializer.save()
            fee_recipient.refresh_from_db()
            
            # Return updated fee recipient
            response_serializer = FeeRecipientSerializer(fee_recipient, context={'request': request})
            return Response({
                'success': True,
                'message': 'Fee recipient settings updated successfully',
                'data': response_serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_settings_fee_recipient_detail(request, recipient_id):
    """
    Settings: Specific Fee Recipient
    GET /api/syndicate/settings/fee-recipient/<id>/ - Get specific fee recipient details
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
    
    from .models import FeeRecipient
    fee_recipient = get_object_or_404(FeeRecipient, id=recipient_id)
    
    # Verify this fee recipient belongs to user's syndicate
    if fee_recipient.syndicate != profile:
        return Response({
            'error': 'This fee recipient is not associated with your syndicate profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = FeeRecipientSerializer(fee_recipient, context={'request': request})
    return Response({
        'success': True,
        'message': 'Fee recipient details retrieved successfully',
        'data': serializer.data
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
