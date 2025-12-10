from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import ParseError
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging

from .models import CustomUser, SyndicateProfile, Sector, Geography, BeneficialOwner
from .serializers import (
    SyndicateProfileSerializer, SyndicateStep1Serializer, 
    SyndicateStep1InvestmentFocusSerializer,
    SyndicateStep2Serializer, SyndicateStep3Serializer, SyndicateStep4Serializer,
    EntityKYBDetailsSerializer,
    BeneficialOwnerSerializer, BeneficialOwnerListSerializer,
    BeneficialOwnerCreateSerializer, BeneficialOwnerUpdateSerializer
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_syndicate_profile(request):
    """
    Get current user's syndicate profile
    GET /api/syndicate/profile/
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
        serializer = SyndicateProfileSerializer(profile)
        return Response(serializer.data)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found. Please start the onboarding process.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_syndicate_profile(request):
    """
    Create syndicate profile for current user
    POST /api/syndicate/profile/
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can create syndicate profiles'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Check if profile already exists
    if SyndicateProfile.objects.filter(user=user).exists():
        return Response({
            'error': 'Syndicate profile already exists. Use update endpoints instead.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = SyndicateProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step1(request):
    """
    Step 1: Lead Info - Personal and accreditation details
    GET /api/syndicate/step1/ - Get step 1 data
    POST /api/syndicate/step1/ - Create or update step 1
    PATCH /api/syndicate/step1/ - Update step 1 (for editing when going back)
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get or create syndicate profile
    profile, created = SyndicateProfile.objects.get_or_create(user=user)
    
    # Handle GET request
    if request.method == 'GET':
        serializer = SyndicateStep1Serializer(profile)
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'message': 'Personal and accreditation info retrieved',
            'data': serializer.data,
            'profile': profile_serializer.data,
            'step_completed': profile.step1_completed,
        }, status=status.HTTP_200_OK)
    
    # Handle POST/PATCH request
    serializer = SyndicateStep1Serializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        # Return updated profile with step completion status
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'message': 'Personal and accreditation info updated successfully',
            'data': serializer.data,
            'profile': profile_serializer.data,
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step1_investment_focus(request):
    """
    Step 1: Lead Info - Investment Focus and LP Network
    GET /api/syndicate/step1/investment-focus/ - Get investment focus data
    POST /api/syndicate/step1/investment-focus/ - Create or update investment focus
    PATCH /api/syndicate/step1/investment-focus/ - Update investment focus
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get or create syndicate profile
    profile, created = SyndicateProfile.objects.get_or_create(user=user)
    
    # Handle GET request
    if request.method == 'GET':
        serializer = SyndicateStep1InvestmentFocusSerializer(profile)
        return Response({
            'success': True,
            'message': 'Investment focus info retrieved',
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    
    # Handle POST/PATCH request
    serializer = SyndicateStep1InvestmentFocusSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        # Return updated data
        updated_serializer = SyndicateStep1InvestmentFocusSerializer(profile)
        return Response({
            'success': True,
            'message': 'Investment focus info updated successfully',
            'data': updated_serializer.data,
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step2(request):
    """
    Step 2: Entity Profile - Company information and structure
    GET /api/syndicate/step2/ - Get step 2 data
    POST /api/syndicate/step2/ - Create or update step 2
    PATCH /api/syndicate/step2/ - Update step 2 (for editing when going back)
    
    Fields supported:
    - firm_name: string (required)
    - description: text (required)
    - logo: file upload
    - sector_ids: array of sector IDs
    - geography_ids: array of geography IDs
    - existing_lp_count: string ("0", "1-10", etc.)
    - enable_platform_lp_access: boolean
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get or create syndicate profile
    profile, created = SyndicateProfile.objects.get_or_create(user=user)
    
    # Handle GET request
    if request.method == 'GET':
        step2_serializer = SyndicateStep2Serializer(profile)
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'message': 'Entity profile data retrieved successfully',
            'data': step2_serializer.data,
            'profile': profile_serializer.data,
            'step_completed': profile.step2_completed,
            'next_step': 'step3' if profile.step2_completed else 'step2'
        }, status=status.HTTP_200_OK)
    
    # Handle POST/PATCH request
    serializer = SyndicateStep2Serializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        # Refresh profile to get updated data
        profile.refresh_from_db()
        
        # Return updated profile with step completion status
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'message': 'Entity profile updated successfully',
            'data': serializer.data,
            'profile': profile_serializer.data,
            'step_completed': profile.step2_completed,
            'next_step': 'step3' if profile.step2_completed else 'step2'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step3a_kyb_details(request):
    """
    Step 3a: Entity KYB Details - Required Business Info
    GET /api/syndicate/step3a/ - Get entity KYB details
    POST /api/syndicate/step3a/ - Create or update entity KYB details
    PATCH /api/syndicate/step3a/ - Update entity KYB details (partial)
    
    Supports multipart/form-data for document uploads.
    
    Fields:
    - entity_legal_name: string (required)
    - entity_type: string (trust, individual, company, partnership) (required)
    - country_of_incorporation: string
    - registration_number: string
    - Registered Address: registered_street_address, registered_area_landmark, etc.
    - Operating Address: operating_street_address, operating_area_landmark, etc.
    - Documents: certificate_of_incorporation, registered_address_proof, directors_register, trust_deed, partnership_agreement
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get or create syndicate profile
    profile, created = SyndicateProfile.objects.get_or_create(user=user)
    
    # Handle GET request
    if request.method == 'GET':
        serializer = EntityKYBDetailsSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'message': 'Entity KYB details retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    # Handle POST/PATCH request
    # Handle file uploads
    file_fields = [
        'certificate_of_incorporation', 'registered_address_proof', 
        'directors_register', 'trust_deed', 'partnership_agreement'
    ]
    
    files_uploaded = {}
    if hasattr(request, 'FILES'):
        for field in file_fields:
            if field in request.FILES:
                files_uploaded[field] = request.FILES[field]
    
    # Prepare data for serializer (exclude file fields as they're handled separately)
    serializer_data = {}
    if hasattr(request, 'data'):
        from django.http import QueryDict
        if isinstance(request.data, QueryDict):
            for key in request.data.keys():
                if key not in file_fields:
                    serializer_data[key] = request.data[key]
        elif isinstance(request.data, dict):
            for key, value in request.data.items():
                if key not in file_fields:
                    serializer_data[key] = value
    
    serializer = EntityKYBDetailsSerializer(
        profile, 
        data=serializer_data, 
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        # Save files first
        for field, file in files_uploaded.items():
            setattr(profile, field, file)
        
        serializer.save()
        profile.refresh_from_db()
        
        # Return updated data
        response_serializer = EntityKYBDetailsSerializer(profile, context={'request': request})
        return Response({
            'success': True,
            'message': 'Entity KYB details updated successfully',
            'data': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step3b_beneficial_owners(request, owner_id=None):
    """
    Step 3b: Beneficial Owners (UBOs)
    GET /api/syndicate/step3b/ - List all beneficial owners
    GET /api/syndicate/step3b/<id>/ - Get single beneficial owner
    POST /api/syndicate/step3b/ - Add new beneficial owner
    PATCH /api/syndicate/step3b/<id>/ - Update beneficial owner
    DELETE /api/syndicate/step3b/<id>/ - Remove beneficial owner
    
    Supports multipart/form-data for document uploads.
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get or create syndicate profile
    profile, created = SyndicateProfile.objects.get_or_create(user=user)
    
    # Handle GET request
    if request.method == 'GET':
        if owner_id:
            # Get single beneficial owner
            try:
                owner = BeneficialOwner.objects.get(id=owner_id, syndicate=profile)
                serializer = BeneficialOwnerSerializer(owner, context={'request': request})
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except BeneficialOwner.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Beneficial owner not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # List all beneficial owners
            owners = BeneficialOwner.objects.filter(syndicate=profile)
            serializer = BeneficialOwnerListSerializer(owners, many=True)
            return Response({
                'success': True,
                'message': 'Beneficial owners retrieved successfully',
                'count': owners.count(),
                'data': serializer.data
            }, status=status.HTTP_200_OK)
    
    # Handle POST request - Create new beneficial owner
    elif request.method == 'POST':
        serializer = BeneficialOwnerCreateSerializer(
            data=request.data,
            context={'syndicate': profile, 'added_by': user, 'request': request}
        )
        
        if serializer.is_valid():
            owner = serializer.save()
            
            # Handle file uploads
            if hasattr(request, 'FILES'):
                if 'identity_document' in request.FILES:
                    owner.identity_document = request.FILES['identity_document']
                if 'proof_of_address' in request.FILES:
                    owner.proof_of_address = request.FILES['proof_of_address']
                owner.save()
            
            response_serializer = BeneficialOwnerSerializer(owner, context={'request': request})
            return Response({
                'success': True,
                'message': 'Beneficial owner added successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle PATCH request - Update beneficial owner
    elif request.method == 'PATCH':
        # Get owner_id from URL or request data
        target_id = owner_id or request.data.get('id') or request.data.get('owner_id')
        
        if not target_id:
            return Response({
                'success': False,
                'error': 'Beneficial owner ID is required for update. Provide id in URL or request body.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            owner = BeneficialOwner.objects.get(id=target_id, syndicate=profile)
        except BeneficialOwner.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Beneficial owner not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BeneficialOwnerUpdateSerializer(owner, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Handle file uploads
            if hasattr(request, 'FILES'):
                if 'identity_document' in request.FILES:
                    owner.identity_document = request.FILES['identity_document']
                if 'proof_of_address' in request.FILES:
                    owner.proof_of_address = request.FILES['proof_of_address']
            
            serializer.save()
            owner.refresh_from_db()
            
            response_serializer = BeneficialOwnerSerializer(owner, context={'request': request})
            return Response({
                'success': True,
                'message': 'Beneficial owner updated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle DELETE request
    elif request.method == 'DELETE':
        target_id = owner_id or request.data.get('id') or request.data.get('owner_id')
        
        if not target_id:
            return Response({
                'success': False,
                'error': 'Beneficial owner ID is required for deletion.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            owner = BeneficialOwner.objects.get(id=target_id, syndicate=profile)
            owner_name = owner.full_name
            owner.delete()
            return Response({
                'success': True,
                'message': f'Beneficial owner "{owner_name}" removed successfully'
            }, status=status.HTTP_200_OK)
        except BeneficialOwner.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Beneficial owner not found'
            }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step3(request):
    """
    Step 3: Compliance & Attestation - Regulatory requirements
    GET /api/syndicate/step3/ - Get step 3 data
    POST /api/syndicate/step3/ - Create or update step 3
    PATCH /api/syndicate/step3/ - Update step 3 (for editing when going back)
    
    Supports both JSON and multipart/form-data for file uploads.
    When uploading files (additional_compliance_policies), use multipart/form-data.
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
            'error': 'Syndicate profile not found. Please complete previous steps first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if Step 2 is completed (only for POST/PATCH, allow GET even if step2 not completed)
    if request.method != 'GET' and not profile.step2_completed:
        return Response({
            'error': 'Step 2 must be completed before proceeding to Step 3'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle GET request
    if request.method == 'GET':
        step3_serializer = SyndicateStep3Serializer(profile, context={'request': request})
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'step_data': step3_serializer.data,
            'profile': profile_serializer.data,
            'step_completed': profile.step3_completed,
            'next_step': 'step4' if profile.step3_completed else 'step3'
        }, status=status.HTTP_200_OK)
    
    # Handle parser selection based on Content-Type for POST/PATCH
    content_type = request.content_type or request.META.get('CONTENT_TYPE', '')
    
    # If Content-Type is JSON but request has files, provide helpful error
    if 'application/json' in content_type and hasattr(request, 'FILES') and request.FILES:
        return Response({
            'detail': 'File uploads require Content-Type: multipart/form-data, not application/json. '
                     'Please remove the Content-Type: application/json header when uploading files, '
                     'or use multipart/form-data instead.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle file upload if present (do this first to avoid pickling issues)
    file_uploaded = False
    if hasattr(request, 'FILES') and 'additional_compliance_policies' in request.FILES:
        file = request.FILES['additional_compliance_policies']
        profile.additional_compliance_policies = file
        profile.save()
        file_uploaded = True
    
    # Prepare clean data for serializer (only non-file fields)
    # This avoids pickling issues with file objects
    serializer_data = {}
    
    # Extract only the fields we need, avoiding file objects
    if hasattr(request, 'data'):
        from django.http import QueryDict
        if isinstance(request.data, QueryDict):
            # For QueryDict, get only the non-file fields
            for key in request.data.keys():
                if key != 'additional_compliance_policies':  # Skip file field
                    value = request.data.get(key)
                    # Convert string boolean values
                    if value in ['true', 'True', '1']:
                        serializer_data[key] = True
                    elif value in ['false', 'False', '0']:
                        serializer_data[key] = False
                    else:
                        serializer_data[key] = value
        elif isinstance(request.data, dict):
            # For dict, copy only non-file fields
            for key, value in request.data.items():
                if key != 'additional_compliance_policies':  # Skip file field
                    serializer_data[key] = value
    
    # Add file field to serializer data only if it was uploaded and needs to be validated
    # But actually, since we already saved it, we don't need to include it
    serializer = SyndicateStep3Serializer(
        profile, 
        data=serializer_data, 
        partial=True, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # Refresh profile to get updated file information
        profile.refresh_from_db()
        
        # Return updated profile with step completion status
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'message': 'Step 3 completed successfully',
            'profile': profile_serializer.data,
            'next_step': 'step4' if profile.step3_completed else 'step3'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_step4(request):
    """
    Step 4: Final Review & Submit - Submit application for review
    GET /api/syndicate/step4/ - Get step 4 data
    POST /api/syndicate/step4/ - Create or update step 4
    PATCH /api/syndicate/step4/ - Update step 4 (for editing when going back)
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
            'error': 'Syndicate profile not found. Please complete previous steps first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if Step 3 is completed (only for POST/PATCH, allow GET even if step3 not completed)
    if request.method != 'GET' and not profile.step3_completed:
        return Response({
            'error': 'Step 3 must be completed before proceeding to Step 4'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle GET request
    if request.method == 'GET':
        step4_serializer = SyndicateStep4Serializer(profile)
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'step_data': step4_serializer.data,
            'profile': profile_serializer.data,
            'step_completed': profile.step4_completed,
            'application_status': profile.application_status,
            'submitted_at': profile.submitted_at
        }, status=status.HTTP_200_OK)
    
    # Handle POST/PATCH request
    serializer = SyndicateStep4Serializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        # Return updated profile with submission status
        profile_serializer = SyndicateProfileSerializer(profile)
        return Response({
            'success': True,
            'message': 'Syndicate application submitted successfully! Your application is now under review.',
            'profile': profile_serializer.data,
            'application_status': profile.application_status,
            'submitted_at': profile.submitted_at
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def syndicate_progress(request):
    """
    Get syndicate onboarding progress
    GET /api/syndicate/progress/
    """
    user = request.user
    
    # Check if user has syndicate role
    if user.role != 'syndicate':
        return Response({
            'error': 'Only users with syndicate role can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        profile = SyndicateProfile.objects.get(user=user)
        
        progress = {
            'step1_completed': profile.step1_completed,
            'step2_completed': profile.step2_completed,
            'step3_completed': profile.step3_completed,
            'step4_completed': profile.step4_completed,
            'current_step': profile.current_step,
            'application_status': profile.application_status,
            'submitted_at': profile.submitted_at
        }
        
        return Response({
            'progress': progress,
            'profile': SyndicateProfileSerializer(profile).data
        })
        
    except SyndicateProfile.DoesNotExist:
        return Response({
            'progress': {
                'step1_completed': False,
                'step2_completed': False,
                'step3_completed': False,
                'step4_completed': False,
                'current_step': 1,
                'application_status': 'not_started',
                'submitted_at': None
            },
            'message': 'Syndicate profile not found. Please start the onboarding process.'
        })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_sectors_and_geographies(request):
    """
    Get available sectors and geographies for syndicate onboarding
    GET /api/syndicate/sectors-geographies/
    """
    sectors = Sector.objects.all()
    geographies = Geography.objects.all()
    
    from .serializers import SectorSerializer, GeographySerializer
    
    return Response({
        'sectors': SectorSerializer(sectors, many=True).data,
        'geographies': GeographySerializer(geographies, many=True).data
    })


@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_syndicate_profile(request):
    """
    Update syndicate profile (admin only)
    PUT /api/syndicate/profile/<id>/
    """
    user = request.user
    
    # Check if user is admin
    if not user.is_staff and user.role != 'admin':
        return Response({
            'error': 'Only administrators can update syndicate profiles'
        }, status=status.HTTP_403_FORBIDDEN)
    
    profile_id = request.data.get('profile_id')
    if not profile_id:
        return Response({
            'error': 'profile_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        profile = SyndicateProfile.objects.get(id=profile_id)
    except SyndicateProfile.DoesNotExist:
        return Response({
            'error': 'Syndicate profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SyndicateProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Syndicate profile updated successfully',
            'profile': serializer.data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
