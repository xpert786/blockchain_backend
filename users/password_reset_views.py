from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import random
import string

from .models import CustomUser, PasswordReset
from .email_utils import send_password_reset_otp


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """
    Step 1: Request password reset OTP
    POST /api/auth/forgot_password/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email__iexact=email)
    except CustomUser.DoesNotExist:
        return Response({
            'success': True,
            'message': 'If an account with this email exists, a password reset OTP has been sent.'
        }, status=status.HTTP_200_OK)
    
    otp = ''.join(random.choices(string.digits, k=4))
    expires_at = timezone.now() + timedelta(minutes=15)
    
    PasswordReset.objects.filter(
        user=user,
        is_used=False,
        is_verified=False
    ).update(is_used=True)
    
    password_reset = PasswordReset.objects.create(
        user=user,
        email=user.email,
        otp=otp,
        expires_at=expires_at
    )
    
    send_password_reset_otp(user.email, otp, user.first_name or user.username)
    
    return Response({
        'success': True,
        'message': 'If an account with this email exists, a password reset OTP has been sent.',
        'email': user.email
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_reset_otp(request):
    """
    Step 2: Verify the password reset OTP
    POST /api/auth/verify_reset_otp/
    Body: { "email": "user@example.com", "otp": "1234" }
    """
    email = request.data.get('email')
    otp = request.data.get('otp')
    
    if not email or not otp:
        return Response({
            'error': 'Email and OTP are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(otp) != 4 or not otp.isdigit():
        return Response({
            'error': 'OTP must be a 4-digit number'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email__iexact=email)
    except CustomUser.DoesNotExist:
        return Response({
            'error': 'Invalid email or OTP'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        password_reset = PasswordReset.objects.filter(
            user=user,
            email__iexact=email,
            otp=otp,
            is_used=False,
            is_verified=False
        ).latest('created_at')
    except PasswordReset.DoesNotExist:
        return Response({
            'error': 'Invalid or expired OTP'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if timezone.now() > password_reset.expires_at:
        return Response({
            'error': 'OTP has expired. Please request a new one.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    password_reset.is_verified = True
    password_reset.save()
    
    return Response({
        'success': True,
        'message': 'OTP verified successfully. You can now reset your password.',
        'reset_token': password_reset.id
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """
    Step 3: Reset password with verified OTP
    POST /api/auth/reset_password/
    Body: { 
        "email": "user@example.com", 
        "otp": "1234",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }
    """
    email = request.data.get('email')
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')
    
    if not all([email, otp, new_password, confirm_password]):
        return Response({
            'error': 'All fields are required (email, otp, new_password, confirm_password)'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_password != confirm_password:
        return Response({
            'error': 'Passwords do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        validate_password(new_password)
    except ValidationError as e:
        return Response({
            'error': 'Password validation failed',
            'details': list(e.messages)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email__iexact=email)
    except CustomUser.DoesNotExist:
        return Response({
            'error': 'Invalid request'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        password_reset = PasswordReset.objects.filter(
            user=user,
            email__iexact=email,
            otp=otp,
            is_verified=True,
            is_used=False
        ).latest('created_at')
    except PasswordReset.DoesNotExist:
        return Response({
            'error': 'Invalid or expired OTP. Please verify your OTP first.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if timezone.now() > password_reset.expires_at:
        return Response({
            'error': 'OTP has expired. Please request a new one.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user.set_password(new_password)
    user.save()
    
    password_reset.is_used = True
    password_reset.save()
    
    PasswordReset.objects.filter(
        user=user,
        is_used=False
    ).update(is_used=True)
    
    return Response({
        'success': True,
        'message': 'Password has been reset successfully. You can now login with your new password.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_reset_otp(request):
    """
    Resend password reset OTP
    POST /api/auth/resend_reset_otp/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email__iexact=email)
    except CustomUser.DoesNotExist:
        return Response({
            'success': True,
            'message': 'If an account with this email exists, a new OTP has been sent.'
        }, status=status.HTTP_200_OK)
    
    PasswordReset.objects.filter(
        user=user,
        is_used=False,
        is_verified=False
    ).update(is_used=True)
    
    otp = ''.join(random.choices(string.digits, k=4))
    expires_at = timezone.now() + timedelta(minutes=15)
    
    password_reset = PasswordReset.objects.create(
        user=user,
        email=user.email,
        otp=otp,
        expires_at=expires_at
    )
    
    send_password_reset_otp(user.email, otp, user.first_name or user.username)
    
    return Response({
        'success': True,
        'message': 'If an account with this email exists, a new OTP has been sent.',
        'email': user.email
    }, status=status.HTTP_200_OK)
