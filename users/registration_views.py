from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
import random
import string

from .models import CustomUser, TwoFactorAuth, EmailVerification, TermsAcceptance
from .serializers import CustomUserSerializer
from .email_utils import send_verification_email, send_sms_verification


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
@csrf_exempt
def registration_flow_register(request):
    """
    Step 1: Register user with basic information
    POST /api/registration-flow/register/
    """
    data = request.data
    
    # Validate required fields
    required_fields = ['email', 'password', 'confirm_password', 'full_name', 'phone_number']
    for field in required_fields:
        if field not in data:
            return Response({
                'error': f'Field "{field}" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate password match
    if data['password'] != data['confirm_password']:
        return Response({
            'error': 'Passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if email already exists
    if CustomUser.objects.filter(email=data['email']).exists():
        return Response({
            'error': 'A user with this email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if phone number already exists
    if CustomUser.objects.filter(phone_number=data['phone_number']).exists():
        return Response({
            'error': 'A user with this phone number already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Split full name into first and last name
        full_name = data['full_name']
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Generate username from email (part before @)
        email = data['email']
        base_username = email.split('@')[0]
        username = base_username
        
        # Ensure username is unique
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = CustomUser.objects.create(
            username=username,
            email=data['email'],
            phone_number=data['phone_number'],
            first_name=first_name,
            last_name=last_name,
            role=data.get('role', 'investor'),
            is_active=True
        )
        user.set_password(data['password'])
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user_id': user.id,
            'email': user.email,
            'phone_number': user.phone_number,
            'full_name': full_name,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            },
            'next_step': 'choose_verification_method'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def choose_verification_method(request):
    """
    Step 2: Choose verification method (email or mobile)
    POST /api/registration-flow/choose_verification_method/
    """
    user = request.user
    method = request.data.get('method')  # 'email' or 'sms'
    
    if method not in ['email', 'sms']:
        return Response({
            'error': 'Invalid method. Choose from: email, sms'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if method == 'email':
        # Send email verification code
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=15)
        
        EmailVerification.objects.update_or_create(
            user=user,
            email=user.email,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )
        
        # Send actual email
        send_verification_email(user.email, code, user.first_name)
        
        return Response({
            'success': True,
            'message': f'A verification code has been sent to {user.email}',
            'email': user.email,
            'method': 'email',
            'next_step': 'verify_code'
        })
    
    elif method == 'sms':
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({
                'error': 'Phone number is required for SMS verification'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send SMS verification code
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)
        
        TwoFactorAuth.objects.update_or_create(
            user=user,
            phone_number=phone_number,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )
        
        # Send actual SMS
        send_sms_verification(phone_number, code)
        
        return Response({
            'success': True,
            'message': f'A verification code has been sent to {phone_number}',
            'phone_number': phone_number,
            'method': 'sms',
            'next_step': 'verify_code'
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_code(request):
    """
    Step 3: Verify the code received via email or SMS
    POST /api/registration-flow/verify_code/
    """
    user = request.user
    code = request.data.get('code')
    method = request.data.get('method', 'email')
    
    if not code:
        return Response({
            'error': 'Verification code is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify code based on method
    if method == 'email':
        is_valid = _verify_email_code(user, code)
    elif method == 'sms':
        is_valid = _verify_sms_code(user, code)
    else:
        return Response({
            'error': 'Invalid method'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if is_valid:
        # Mark verification as complete
        if method == 'email':
            user.email_verified = True
        elif method == 'sms':
            user.phone_verified = True
            # Get phone number from the verification record
            try:
                two_fa = TwoFactorAuth.objects.get(user=user, code=code)
                user.phone_number = two_fa.phone_number
            except TwoFactorAuth.DoesNotExist:
                pass
        
        user.save()
        
        return Response({
            'success': True,
            'message': 'Verification successful! Your account is now active.',
            'user': CustomUserSerializer(user).data,
            'next_step': 'accept_terms'
        })
    else:
        return Response({
            'error': 'Invalid or expired verification code'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resend_code(request):
    """
    Resend verification code
    POST /api/registration-flow/resend_code/
    """
    user = request.user
    method = request.data.get('method', 'email')
    
    if method == 'email':
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=15)
        
        EmailVerification.objects.update_or_create(
            user=user,
            email=user.email,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )
        
        # Send actual email
        send_verification_email(user.email, code, user.first_name)
        
        return Response({
            'success': True,
            'message': f'New verification code sent to {user.email}'
        })
    
    elif method == 'sms':
        phone_number = user.phone_number
        if not phone_number:
            return Response({
                'error': 'Phone number not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)
        
        TwoFactorAuth.objects.update_or_create(
            user=user,
            phone_number=phone_number,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )
        
        # Send actual SMS
        send_sms_verification(phone_number, code)
        
        return Response({
            'success': True,
            'message': f'New verification code sent to {phone_number}'
        })
    
    else:
        return Response({
            'error': 'Invalid method'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_registration_status(request):
    """
    Get registration status for the current user
    GET /api/registration-flow/get_registration_status/
    """
    user = request.user
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'email_verified': user.email_verified,
        'phone_verified': user.phone_verified,
        'registration_complete': user.email_verified or user.phone_verified
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_terms(request):
    """
    Get available terms of service
    GET /api/registration-flow/get_terms/
    """
    terms_list = [
        {
            'id': 'general_terms',
            'title': 'General terms of services',
            'description': 'General terms and conditions for using the platform'
        },
        {
            'id': 'investing_banking_terms',
            'title': 'Investing banking Terms',
            'description': 'Terms specific to investment banking services'
        },
        {
            'id': 'e_sign_consent',
            'title': 'E-Sign Consent',
            'description': 'Electronic signature consent agreement'
        },
        {
            'id': 'infrafi_deposit',
            'title': 'Short Deposit Repayment and Custodial Agreement',
            'description': 'Deposit placement and custodial agreement terms'
        },
        {
            'id': 'cookie_consent',
            'title': 'Cookie consent preferences',
            'description': 'Cookie usage and privacy preferences'
        }
    ]
    
    return Response({
        'terms': terms_list,
        'message': 'Terms of service documents available for review'
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def accept_terms(request):
    """
    Accept terms of service
    POST /api/registration-flow/accept_terms/
    """
    user = request.user
    terms_data = request.data.get('terms', [])
    
    if not terms_data:
        return Response({
            'error': 'Terms acceptance data is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get request info for audit trail
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    accepted_terms = []
    errors = []
    
    for term_item in terms_data:
        terms_type = term_item.get('terms_type')
        accepted = term_item.get('accepted', False)
        
        if not terms_type:
            errors.append('terms_type is required for each term')
            continue
        
        # Validate terms_type
        valid_terms = ['general_terms', 'investing_banking_terms', 'e_sign_consent', 'infrafi_deposit', 'cookie_consent']
        if terms_type not in valid_terms:
            errors.append(f'Invalid terms_type: {terms_type}')
            continue
        
        try:
            # Create or update terms acceptance
            terms_acceptance, created = TermsAcceptance.objects.update_or_create(
                user=user,
                terms_type=terms_type,
                defaults={
                    'accepted': accepted,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                }
            )
            accepted_terms.append({
                'terms_type': terms_type,
                'accepted': accepted,
                'accepted_at': terms_acceptance.accepted_at
            })
        except Exception as e:
            errors.append(f'Error accepting {terms_type}: {str(e)}')
    
    if errors:
        return Response({
            'error': 'Some terms could not be accepted',
            'errors': errors,
            'accepted_terms': accepted_terms
        }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'success': True,
        'message': 'Terms of service accepted successfully',
        'accepted_terms': accepted_terms,
        'next_step': 'registration_complete'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_terms_status(request):
    """
    Get terms acceptance status for the current user
    GET /api/registration-flow/get_terms_status/
    """
    user = request.user
    
    # Get all terms acceptances for the user
    terms_acceptances = TermsAcceptance.objects.filter(user=user)
    
    terms_status = {}
    for acceptance in terms_acceptances:
        terms_status[acceptance.terms_type] = {
            'accepted': acceptance.accepted,
            'accepted_at': acceptance.accepted_at,
            'ip_address': acceptance.ip_address
        }
    
    # Check if all required terms are accepted
    required_terms = ['general_terms', 'investing_banking_terms', 'e_sign_consent', 'infrafi_deposit', 'cookie_consent']
    all_terms_accepted = all(
        terms_status.get(term, {}).get('accepted', False) for term in required_terms
    )
    
    return Response({
        'user_id': user.id,
        'terms_status': terms_status,
        'all_terms_accepted': all_terms_accepted,
        'required_terms': required_terms
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def complete_registration(request):
    """
    Complete the registration process
    POST /api/registration-flow/complete_registration/
    """
    user = request.user
    
    # Check if email or phone is verified
    if not user.email_verified and not user.phone_verified:
        return Response({
            'error': 'Email or phone verification is required'
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
    
    # Registration is complete
    return Response({
        'success': True,
        'message': 'Registration completed successfully! Welcome to the platform.',
        'user': CustomUserSerializer(user).data,
        'registration_complete': True
    })


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _verify_email_code(user, code):
    """Verify Email verification code"""
    try:
        verification = EmailVerification.objects.get(
            user=user,
            email=user.email,
            code=code,
            is_verified=False,
            expires_at__gt=timezone.now()
        )
        verification.is_verified = True
        verification.save()
        return True
    except EmailVerification.DoesNotExist:
        return False


def _verify_sms_code(user, code):
    """Verify SMS verification code"""
    try:
        two_fa = TwoFactorAuth.objects.get(
            user=user,
            code=code,
            is_verified=False,
            expires_at__gt=timezone.now()
        )
        two_fa.is_verified = True
        two_fa.save()
        return True
    except TwoFactorAuth.DoesNotExist:
        return False