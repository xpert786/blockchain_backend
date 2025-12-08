from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import string
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, Sector, Geography, EmailVerification, TwoFactorAuth, TermsAcceptance
from .email_utils import send_verification_email, send_sms_verification, send_2fa_code_email
from .sms_utils import send_twilio_sms
from .serializers import (
    CustomUserSerializer, 
    UserRegistrationSerializer,
    SectorSerializer,
    GeographySerializer,
    RegistrationSerializer,
    EmailVerificationSerializer,
    TwoFactorAuthSerializer,
    TermsAcceptanceSerializer,
    VerifyEmailSerializer,
    VerifyTwoFactorSerializer,
    QuickProfileSerializer
)
from investors.models import InvestorProfile
from rest_framework import generics, permissions, authentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings



# ================== Welcome Message ==================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def welcome_message(request):
    """
    Welcome message
    GET /api/users/welcome/
    """
    return Response({"message": "Welcome to the User Management API!"}, status=status.HTTP_200_OK)

# ==================== USER MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_list(request):
    """
    Get list of all users
    GET /api/users/
    """
    users = CustomUser.objects.all()
    serializer = CustomUserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_detail(request, pk):
    """
    Get specific user details
    GET /api/users/<id>/
    """
    user = get_object_or_404(CustomUser, pk=pk)
    serializer = CustomUserSerializer(user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
@csrf_exempt
def user_register(request):
    """
    Register a new user
    POST /api/users/register/
    """
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = Response({}, status=status.HTTP_200_OK)
        # Add CORS headers
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
        else:
            response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        return response
    
    # Handle registration request
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'message': 'User registered successfully',
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        }, status=status.HTTP_201_CREATED)
        
        # Add CORS headers to response
        origin = request.META.get('HTTP_ORIGIN')
        if origin:
            response['Access-Control-Allow-Origin'] = origin
        else:
            response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
@csrf_exempt
def user_login(request):
    """
    Login user and return JWT tokens
    POST /api/users/login/
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = CustomUser.objects.filter(email__iexact=email).first()
    if not user:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user = authenticate(request, username=user.username, password=password)
    if not user:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': CustomUserSerializer(user).data
    })


# ==================== SYNDICATE MANAGEMENT ====================







# ==================== SECTOR MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sector_list(request):
    """
    Get list of sectors
    GET /api/sectors/
    """
    sectors = Sector.objects.all()
    name = request.query_params.get('name', None)
    if name:
        sectors = sectors.filter(name__icontains=name)
    sectors = sectors.order_by('name')
    
    serializer = SectorSerializer(sectors, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sector_detail(request, pk):
    """
    Get specific sector details
    GET /api/sectors/<id>/
    """
    sector = get_object_or_404(Sector, pk=pk)
    serializer = SectorSerializer(sector)
    return Response(serializer.data)


# ==================== GEOGRAPHY MANAGEMENT ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def geography_list(request):
    """
    Get list of geographies
    GET /api/geographies/
    """
    geographies = Geography.objects.all()
    region = request.query_params.get('region', None)
    name = request.query_params.get('name', None)
    
    if region:
        geographies = geographies.filter(region__icontains=region)
    if name:
        geographies = geographies.filter(name__icontains=name)
        
    geographies = geographies.order_by('region', 'name')
    
    serializer = GeographySerializer(geographies, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def geography_detail(request, pk):
    """
    Get specific geography details
    GET /api/geographies/<id>/
    """
    geography = get_object_or_404(Geography, pk=pk)
    serializer = GeographySerializer(geography)
    return Response(serializer.data)




# ==================== REGISTRATION FLOW ====================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def registration_register(request):
    """
    Step 1: Register user with basic information
    POST /api/registration/register/
    """
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        return Response({
            'success': True,
            'message': 'User registered successfully. Please verify your email.',
            'user_id': user.id,
            'next_step': 'verify_email'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_email_verification(request):
    """
    Step 2: Send email verification code
    POST /api/registration/send_email_verification/
    """
    user_id = request.data.get('user_id')
    email = request.data.get('email')
    
    if not user_id or not email:
        return Response({
            'error': 'user_id and email are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = EmailVerificationSerializer(
        data={'email': email, 'code': ''},  # Code will be generated in create method
        context={'user': user}
    )
    
    if serializer.is_valid():
        verification = serializer.save()
        
        return Response({
            'success': True,
            'message': f'Verification code sent to {email}',
            'verification_id': verification.id,
            'next_step': 'verify_email_code'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email(request):
    """
    Step 3: Verify email with 6-digit code
    POST /api/registration/verify_email/
    """
    serializer = VerifyEmailSerializer(data=request.data)
    if serializer.is_valid():
        verification = serializer.validated_data['verification']
        user = verification.user
        
        # Mark email as verified
        verification.is_verified = True
        verification.save()
        
        # Update user email verification status
        user.email_verified = True
        user.save()
        
        return Response({
            'success': True,
            'message': 'Email verified successfully',
            'user_id': user.id,
            'next_step': 'send_two_factor'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def send_two_factor(request):
    """
    Step 4: Send two-factor authentication code
    POST /api/registration/send_two_factor/
    """
    user_id = request.data.get('user_id')
    phone_number = request.data.get('phone_number')
    
    if not user_id or not phone_number:
        return Response({
            'error': 'user_id and phone_number are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Generate code and create TwoFactorAuth record directly to avoid
    # serializer-level validation issues on some deployments.
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"send_two_factor called with user_id={user_id}, phone_number={phone_number}")
        
        code = ''.join(random.choices(string.digits, k=4))
        expires_at = timezone.now() + timedelta(minutes=10)

        logger.info(f"Generated code: {code}, expires_at: {expires_at}")

        two_fa, created = TwoFactorAuth.objects.update_or_create(
            user=user,
            phone_number=phone_number,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )

        logger.info(f"Created/updated TwoFactorAuth record: {two_fa.id}")

        # Send SMS
        success, msg = send_twilio_sms(phone_number, code)
        logger.info(f"SMS send result: success={success}, msg={msg}")
        
        if not success:
            logger.error(f"Failed to send SMS: {msg}")
            return Response({'error': f'Failed to send SMS: {msg}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(f"SMS sent successfully to {phone_number}")
        
        return Response({
            'success': True,
            'message': f'4-digit verification code sent to {phone_number}',
            'two_fa_id': two_fa.id,
            'next_step': 'verify_two_factor'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Exception in send_two_factor: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def verify_two_factor(request):
    """
    Step 5: Verify 4-digit two-factor authentication code
    POST /api/registration/verify_two_factor/
    """
    serializer = VerifyTwoFactorSerializer(data=request.data)
    if serializer.is_valid():
        two_fa = serializer.validated_data['two_fa']
        user = two_fa.user
        
        # Mark 2FA as verified
        two_fa.is_verified = True
        two_fa.save()
        
        # Update user phone verification status
        user.phone_verified = True
        user.phone_number = two_fa.phone_number
        user.save()
        
        return Response({
            'success': True,
            'message': 'Phone number verified successfully',
            'user_id': user.id,
            'next_step': 'accept_terms'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def accept_terms(request):
    """
    Step 6: Accept terms of service
    POST /api/registration/accept_terms/
    """
    user_id = request.data.get('user_id')
    terms_acceptances = request.data.get('terms_acceptances', [])
    
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
    
    # Accept all terms
    accepted_terms = []
    for term_data in terms_acceptances:
        serializer = TermsAcceptanceSerializer(
            data=term_data,
            context={'user': user, 'request': request}
        )
        if serializer.is_valid():
            terms_acceptance = serializer.save()
            accepted_terms.append(terms_acceptance)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': 'Terms of service accepted successfully',
        'user_id': user.id,
        'accepted_terms': len(accepted_terms),
        'next_step': 'complete_registration'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def complete_registration(request):
    """
    Step 7: Complete registration and generate tokens
    POST /api/registration/complete_registration/
    """
    user_id = request.data.get('user_id')
    
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
    
    # Check if all verifications are complete
    if not user.email_verified:
        return Response({
            'error': 'Email verification required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.phone_verified:
        return Response({
            'error': 'Phone verification required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if all required terms are accepted
    required_terms = ['general_terms', 'investing_banking_terms', 'e_sign_consent', 'infrafi_deposit', 'cookie_consent']
    accepted_terms = TermsAcceptance.objects.filter(
        user=user,
        terms_type__in=required_terms,
        accepted=True
    ).values_list('terms_type', flat=True)
    
    missing_terms = set(required_terms) - set(accepted_terms)
    if missing_terms:
        return Response({
            'error': f'Missing terms acceptance: {", ".join(missing_terms)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'success': True,
        'message': 'Registration completed successfully!',
        'user': CustomUserSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_registration_status(request):
    """
    Get registration status for a user
    GET /api/registration/get_registration_status/?user_id=1
    """
    user_id = request.query_params.get('user_id')
    
    if not user_id:
        return Response({
            'error': 'user_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check registration progress
    progress = {
        'user_created': True,
        'email_verified': user.email_verified,
        'phone_verified': user.phone_verified,
        'terms_accepted': False,
        'registration_complete': False
    }
    
    # Check terms acceptance
    required_terms = ['general_terms', 'investing_banking_terms', 'e_sign_consent', 'infrafi_deposit', 'cookie_consent']
    accepted_terms = TermsAcceptance.objects.filter(
        user=user,
        terms_type__in=required_terms,
        accepted=True
    ).values_list('terms_type', flat=True)
    
    progress['terms_accepted'] = len(accepted_terms) == len(required_terms)
    progress['registration_complete'] = (
        progress['email_verified'] and 
        progress['phone_verified'] and 
        progress['terms_accepted']
    )
    
    # Determine current step
    if not progress['email_verified']:
        current_step = 'verify_email'
    elif not progress['phone_verified']:
        current_step = 'verify_two_factor'
    elif not progress['terms_accepted']:
        current_step = 'accept_terms'
    else:
        current_step = 'complete_registration'
    
    return Response({
        'user_id': user.id,
        'progress': progress,
        'current_step': current_step,
        'user_data': CustomUserSerializer(user).data
    }, status=status.HTTP_200_OK)

##############=====================Google Login With Role=====================
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.permissions import AllowAny


class GoogleLoginWithRoleView(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    permission_classes = (AllowAny,)
    authentication_classes = []
    callback_url = settings.CALLBACK_URL  

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code != 200:
            return response

        user = self.user 
        
        requested_role = request.data.get('role')

        if not user.role and requested_role:
            
            allowed_roles = ['investor', 'syndicate']
            
            if requested_role in allowed_roles:
                user.role = requested_role
                user.save()
            else:
                pass 

        return response
    

class QuickProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = QuickProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Support JWT, Basic, and Token authentication
    authentication_classes = [JWTAuthentication, authentication.BasicAuthentication, authentication.TokenAuthentication]

    def get_object(self):
        profile, created = InvestorProfile.objects.get_or_create(user=self.request.user)
        return profile