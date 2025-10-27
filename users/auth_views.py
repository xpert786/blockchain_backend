from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import random
import string
import pyotp
import qrcode
import io
import base64

from .models import CustomUser, TwoFactorAuth, EmailVerification
from .serializers import (
    CustomUserSerializer,
    TwoFactorAuthSerializer,
    VerifyTwoFactorSerializer,
    VerifyEmailSerializer
)


class AuthenticationViewSet(viewsets.ViewSet):
    """
    Comprehensive authentication API with 2FA support
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login with username/password
        POST /api/auth/login/
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
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
    
    @action(detail=False, methods=['post'])
    def verify_2fa_login(self, request):
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
            is_valid = self._verify_sms_code(user, code)
        elif two_factor_method == 'totp':
            is_valid = self._verify_totp_code(user, code)
        elif two_factor_method == 'email':
            is_valid = self._verify_email_code(user, code)
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
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enable_2fa(self, request):
        """
        Enable two-factor authentication for the current user
        POST /api/auth/enable_2fa/
        """
        user = request.user
        method = request.data.get('method', 'sms')
        phone_number = request.data.get('phone_number')
        
        if method not in ['sms', 'totp', 'email']:
            return Response({
                'error': 'Invalid method. Choose from: sms, totp, email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if method == 'sms' and not phone_number:
            return Response({
                'error': 'Phone number is required for SMS 2FA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if method == 'sms':
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
            
            # TODO: Send actual SMS
            # send_sms(phone_number, f"Your 2FA verification code is: {code}")
            
            return Response({
                'message': f'Verification code sent to {phone_number}',
                'phone_number': phone_number,
                'next_step': 'verify_2fa_setup'
            })
        
        elif method == 'totp':
            # Generate TOTP secret
            secret = pyotp.random_base32()
            user.totp_secret = secret
            user.save()
            
            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name="Blockchain Admin"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return Response({
                'message': 'Scan the QR code with your authenticator app',
                'qr_code': f"data:image/png;base64,{qr_code_base64}",
                'secret': secret,  # For manual entry
                'next_step': 'verify_totp_setup'
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
            
            # TODO: Send actual email
            # send_email(user.email, f"Your 2FA verification code is: {code}")
            
            return Response({
                'message': f'Verification code sent to {user.email}',
                'email': user.email,
                'next_step': 'verify_2fa_setup'
            })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_2fa_setup(self, request):
        """
        Verify 2FA setup code
        POST /api/auth/verify_2fa_setup/
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
            is_valid = self._verify_sms_code(user, code)
        elif method == 'totp':
            is_valid = self._verify_totp_code(user, code)
        elif method == 'email':
            is_valid = self._verify_email_code(user, code)
        else:
            return Response({
                'error': 'Invalid method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if is_valid:
            # Enable 2FA for user
            user.two_factor_enabled = True
            user.two_factor_method = method
            user.save()
            
            # Generate backup codes
            backup_codes = [''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) for _ in range(10)]
            user.backup_codes = backup_codes
            user.save()
            
            return Response({
                'message': 'Two-factor authentication enabled successfully',
                'backup_codes': backup_codes,
                'warning': 'Save these backup codes in a secure location'
            })
        else:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def disable_2fa(self, request):
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
        user.totp_secret = None
        user.backup_codes = []
        user.save()
        
        # Delete existing 2FA records
        TwoFactorAuth.objects.filter(user=user).delete()
        
        return Response({
            'message': 'Two-factor authentication disabled successfully'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def resend_2fa_code(self, request):
        """
        Resend 2FA verification code
        POST /api/auth/resend_2fa_code/
        """
        user = request.user
        method = request.data.get('method', user.two_factor_method)
        
        if not user.two_factor_enabled:
            return Response({
                'error': 'Two-factor authentication is not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
            
            # TODO: Send actual SMS
            # send_sms(phone_number, f"Your 2FA verification code is: {code}")
            
            return Response({
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
            
            # TODO: Send actual email
            # send_email(user.email, f"Your 2FA verification code is: {code}")
            
            return Response({
                'message': f'New verification code sent to {user.email}'
            })
        
        else:
            return Response({
                'error': 'Invalid method'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def get_2fa_status(self, request):
        """
        Get current 2FA status for the user
        GET /api/auth/get_2fa_status/
        """
        user = request.user
        
        return Response({
            'two_factor_enabled': user.two_factor_enabled,
            'two_factor_method': user.two_factor_method,
            'phone_number': user.phone_number if user.two_factor_enabled else None,
            'email': user.email if user.two_factor_enabled else None,
            'backup_codes_count': len(user.backup_codes) if user.backup_codes else 0
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def regenerate_backup_codes(self, request):
        """
        Regenerate backup codes for 2FA
        POST /api/auth/regenerate_backup_codes/
        """
        user = request.user
        password = request.data.get('password')
        
        if not user.two_factor_enabled:
            return Response({
                'error': 'Two-factor authentication is not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not password:
            return Response({
                'error': 'Password is required to regenerate backup codes'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(password):
            return Response({
                'error': 'Invalid password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate new backup codes
        backup_codes = [''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) for _ in range(10)]
        user.backup_codes = backup_codes
        user.save()
        
        return Response({
            'message': 'Backup codes regenerated successfully',
            'backup_codes': backup_codes,
            'warning': 'Save these backup codes in a secure location'
        })
    
    def _verify_sms_code(self, user, code):
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
    
    def _verify_totp_code(self, user, code):
        """Verify TOTP 2FA code"""
        if not user.totp_secret:
            return False
        
        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code, valid_window=1)  # Allow 1 time step tolerance
    
    def _verify_email_code(self, user, code):
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
