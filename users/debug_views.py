from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from .models import CustomUser, EmailVerification, TwoFactorAuth


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def server_status(request):
    """
    Check server status
    GET /api/debug/server_status/
    """
    return Response({
        'status': 'OK',
        'message': 'Server is running',
        'timestamp': timezone.now()
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def database_status(request):
    """
    Check database status
    GET /api/debug/database_status/
    """
    try:
        # Test database connection
        user_count = CustomUser.objects.count()
        return Response({
            'status': 'OK',
            'message': 'Database is accessible',
            'user_count': user_count,
            'timestamp': timezone.now()
        })
    except Exception as e:
        return Response({
            'status': 'ERROR',
            'message': f'Database error: {str(e)}',
            'timestamp': timezone.now()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def email_status(request):
    """
    Check email configuration status
    GET /api/debug/email_status/
    """
    try:
        from django.conf import settings
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not configured')
        email_host = getattr(settings, 'EMAIL_HOST', 'Not configured')
        email_port = getattr(settings, 'EMAIL_PORT', 'Not configured')
        
        return Response({
            'status': 'OK',
            'message': 'Email configuration loaded',
            'email_backend': email_backend,
            'email_host': email_host,
            'email_port': email_port,
            'timestamp': timezone.now()
        })
    except Exception as e:
        return Response({
            'status': 'ERROR',
            'message': f'Email configuration error: {str(e)}',
            'timestamp': timezone.now()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def cors_status(request):
    """
    Check CORS configuration status
    GET /api/debug/cors_status/
    """
    try:
        from django.conf import settings
        cors_allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        cors_allow_all_origins = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
        
        return Response({
            'status': 'OK',
            'message': 'CORS configuration loaded',
            'cors_allowed_origins': cors_allowed_origins,
            'cors_allow_all_origins': cors_allow_all_origins,
            'timestamp': timezone.now()
        })
    except Exception as e:
        return Response({
            'status': 'ERROR',
            'message': f'CORS configuration error: {str(e)}',
            'timestamp': timezone.now()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_user_verifications(request):
    """
    Check all verification records for a user
    POST /api/debug/check_user_verifications/
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
    
    # Get all email verifications
    email_verifications = EmailVerification.objects.filter(user=user).order_by('-created_at')
    email_data = []
    for ev in email_verifications:
        email_data.append({
            'id': ev.id,
            'email': ev.email,
            'code': ev.code,
            'is_verified': ev.is_verified,
            'created_at': ev.created_at,
            'expires_at': ev.expires_at,
            'is_expired': ev.expires_at < timezone.now()
        })
    
    # Get all SMS verifications
    sms_verifications = TwoFactorAuth.objects.filter(user=user).order_by('-created_at')
    sms_data = []
    for sv in sms_verifications:
        sms_data.append({
            'id': sv.id,
            'phone_number': sv.phone_number,
            'code': sv.code,
            'is_verified': sv.is_verified,
            'created_at': sv.created_at,
            'expires_at': sv.expires_at,
            'is_expired': sv.expires_at < timezone.now()
        })
    
    return Response({
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'email_verified': user.email_verified,
        'phone_verified': user.phone_verified,
        'email_verifications': email_data,
        'sms_verifications': sms_data
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_code_debug(request):
    """
    Debug version of verify code with detailed response
    POST /api/debug/verify_code_debug/
    """
    user_id = request.data.get('user_id')
    code = request.data.get('code')
    method = request.data.get('method', 'email')
    
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
    
    debug_info = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'method': method,
        'code_provided': code,
        'current_time': timezone.now()
    }
    
    if method == 'email':
        # Check email verifications
        verifications = EmailVerification.objects.filter(
            user=user,
            email=user.email,
            code=code
        )
        
        debug_info['verifications_found'] = verifications.count()
        debug_info['verifications'] = []
        
        for verification in verifications:
            debug_info['verifications'].append({
                'id': verification.id,
                'code': verification.code,
                'is_verified': verification.is_verified,
                'expires_at': verification.expires_at,
                'is_expired': verification.expires_at < timezone.now(),
                'matches_code': verification.code == code
            })
        
        # Find valid verification
        valid_verification = EmailVerification.objects.filter(
            user=user,
            email=user.email,
            code=code,
            is_verified=False,
            expires_at__gt=timezone.now()
        ).first()
        
        debug_info['valid_verification_found'] = valid_verification is not None
        
        if valid_verification:
            debug_info['verification_result'] = 'SUCCESS'
            # Mark as verified
            valid_verification.is_verified = True
            valid_verification.save()
            user.email_verified = True
            user.save()
            debug_info['user_updated'] = True
        else:
            debug_info['verification_result'] = 'FAILED'
            debug_info['failure_reason'] = 'No valid verification found'
    
    elif method == 'sms':
        # Check SMS verifications
        verifications = TwoFactorAuth.objects.filter(
            user=user,
            code=code
        )
        
        debug_info['verifications_found'] = verifications.count()
        debug_info['verifications'] = []
        
        for verification in verifications:
            debug_info['verifications'].append({
                'id': verification.id,
                'phone_number': verification.phone_number,
                'code': verification.code,
                'is_verified': verification.is_verified,
                'expires_at': verification.expires_at,
                'is_expired': verification.expires_at < timezone.now(),
                'matches_code': verification.code == code
            })
        
        # Find valid verification
        valid_verification = TwoFactorAuth.objects.filter(
            user=user,
            code=code,
            is_verified=False,
            expires_at__gt=timezone.now()
        ).first()
        
        debug_info['valid_verification_found'] = valid_verification is not None
        
        if valid_verification:
            debug_info['verification_result'] = 'SUCCESS'
            # Mark as verified
            valid_verification.is_verified = True
            valid_verification.save()
            user.phone_verified = True
            user.phone_number = valid_verification.phone_number
            user.save()
            debug_info['user_updated'] = True
        else:
            debug_info['verification_result'] = 'FAILED'
            debug_info['failure_reason'] = 'No valid verification found'
    
    return Response(debug_info)