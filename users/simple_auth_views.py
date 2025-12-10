from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import string

from .models import CustomUser, TwoFactorAuth, EmailVerification
from .serializers import CustomUserSerializer
from .email_utils import send_verification_email, send_sms_verification, send_2fa_code_email


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def auth_login(request):
    """
    Login with email and password
    POST /api/auth/login/
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
    
    if not user.is_active:
        return Response({
            'error': 'Account is deactivated'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Check if 2FA is enabled
    if user.two_factor_enabled:
        return Response({
            'requires_2fa': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'two_factor_method': user.two_factor_method,
            'message': f'Please verify your {user.two_factor_method.upper()} code'
        }, status=status.HTTP_200_OK)
    
    # Generate tokens for users without 2FA
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': CustomUserSerializer(user).data,
        'requires_2fa': False
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_2fa_login(request):
    """
    Verify 2FA code during login
    POST /api/auth/verify_2fa_login/
    """
    user_id = request.data.get('user_id')
    code = request.data.get('code')
    two_factor_method = request.data.get('two_factor_method', 'sms')
    
    if not user_id or not code:
        return Response({
            'error': 'user_id and code are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not user.two_factor_enabled:
        return Response({
            'error': 'Two-factor authentication is not enabled for this user'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify code based on method
    if two_factor_method == 'sms':
        is_valid = _verify_sms_code(user, code)
    elif two_factor_method == 'email':
        is_valid = _verify_email_code(user, code)
    else:
        return Response({
            'error': 'Invalid two-factor method'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if is_valid:
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': CustomUserSerializer(user).data,
            'message': 'Login successful'
        })
    else:
        return Response({
            'error': 'Invalid or expired verification code'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def setup_2fa(request):
    """
    Setup two-factor authentication - choose method (email or mobile)
    POST /api/auth/setup_2fa/
    """
    user = request.user
    method = request.data.get('method')  # 'email' or 'sms'
    
    if method not in ['sms', 'email']:
        return Response({
            'error': 'Invalid method. Choose from: sms, email'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if method == 'sms':
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({
                'error': 'Phone number is required for SMS 2FA'
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
            'message': f'Verification code sent to {phone_number}',
            'phone_number': phone_number,
            'method': 'sms',
            'next_step': 'verify_setup'
        })
    
    elif method == 'email':
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
        send_2fa_code_email(user.email, code, user.first_name)
        
        return Response({
            'success': True,
            'message': f'Verification code sent to {user.email}',
            'email': user.email,
            'method': 'email',
            'next_step': 'verify_setup'
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_setup(request):
    """
    Verify 2FA setup code
    POST /api/auth/verify_setup/
    """
    user = request.user
    code = request.data.get('code')
    method = request.data.get('method', 'sms')
    
    if not code:
        return Response({
            'error': 'Verification code is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify code based on method
    if method == 'sms':
        is_valid = _verify_sms_code(user, code)
    elif method == 'email':
        is_valid = _verify_email_code(user, code)
    else:
        return Response({
            'error': 'Invalid method'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if is_valid:
        # Enable 2FA for user
        user.two_factor_enabled = True
        user.two_factor_method = method
        if method == 'sms':
            # Get phone number from the verification record
            try:
                two_fa = TwoFactorAuth.objects.get(user=user, code=code)
                user.phone_number = two_fa.phone_number
            except TwoFactorAuth.DoesNotExist:
                pass
        user.save()
        
        return Response({
            'success': True,
            'message': 'Two-factor authentication enabled successfully',
            'two_factor_enabled': True,
            'two_factor_method': method
        })
    else:
        return Response({
            'error': 'Invalid verification code'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resend_code(request):
    """
    Resend 2FA verification code
    POST /api/auth/resend_code/
    """
    user = request.user
    method = request.data.get('method', user.two_factor_method)
    
    if method == 'sms':
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
    
    elif method == 'email':
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
        send_2fa_code_email(user.email, code, user.first_name)
        
        return Response({
            'success': True,
            'message': f'New verification code sent to {user.email}'
        })
    
    else:
        return Response({
            'error': 'Invalid method'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def disable_2fa(request):
    """
    Disable two-factor authentication
    POST /api/auth/disable_2fa/
    """
    user = request.user
    password = request.data.get('password')
    
    if not password:
        return Response({
            'error': 'Password is required to disable 2FA'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not user.check_password(password):
        return Response({
            'error': 'Invalid password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Disable 2FA
    user.two_factor_enabled = False
    user.two_factor_method = None
    user.save()
    
    # Delete existing 2FA records
    TwoFactorAuth.objects.filter(user=user).delete()
    EmailVerification.objects.filter(user=user).delete()
    
    return Response({
        'success': True,
        'message': 'Two-factor authentication disabled successfully'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_2fa_status(request):
    """
    Get current 2FA status for the user
    GET /api/auth/get_2fa_status/
    """
    user = request.user
    
    return Response({
        'two_factor_enabled': user.two_factor_enabled,
        'two_factor_method': user.two_factor_method,
        'phone_number': user.phone_number if user.two_factor_enabled and user.two_factor_method == 'sms' else None,
        'email': user.email if user.two_factor_enabled and user.two_factor_method == 'email' else None
    })


def _verify_sms_code(user, code):
    """Verify SMS 2FA code"""
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


def _verify_email_code(user, code):
    """Verify Email 2FA code"""
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