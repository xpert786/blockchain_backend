from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .email_utils import send_verification_email, send_sms_verification


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_test_email(request):
    """
    Send a test verification email
    POST /api/test-email/send_test_email/
    """
    email = request.data.get('email')
    code = request.data.get('code', '123456')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Send test email
        success = send_verification_email(email, code, 'Test User')
        
        if success:
            return Response({
                'success': True,
                'message': f'Test email sent to {email} with code {code}',
                'email': email,
                'code': code
            })
        else:
            return Response({
                'error': 'Failed to send email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'Error sending email: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_verification_email(request):
    """
    Send a test verification email
    POST /api/test-email/send_verification_email/
    """
    email = request.data.get('email')
    code = request.data.get('code', '123456')
    name = request.data.get('name', 'Test User')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Send test email
        success = send_verification_email(email, code, name)
        
        if success:
            return Response({
                'success': True,
                'message': f'Verification email sent to {email} with code {code}',
                'email': email,
                'code': code
            })
        else:
            return Response({
                'error': 'Failed to send email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'Error sending email: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_2fa_email(request):
    """
    Send a test 2FA email
    POST /api/test-email/send_2fa_email/
    """
    email = request.data.get('email')
    code = request.data.get('code', '123456')
    name = request.data.get('name', 'Test User')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Send test 2FA email
        from .email_utils import send_2fa_code_email
        success = send_2fa_code_email(email, code, name)
        
        if success:
            return Response({
                'success': True,
                'message': f'2FA email sent to {email} with code {code}',
                'email': email,
                'code': code
            })
        else:
            return Response({
                'error': 'Failed to send email'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'Error sending email: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_test_sms(request):
    """
    Send a test SMS (will just log to console)
    POST /api/test-email/send_test_sms/
    """
    phone_number = request.data.get('phone_number')
    code = request.data.get('code', '123456')
    
    if not phone_number:
        return Response({
            'error': 'Phone number is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Send test SMS (will log to console)
        success = send_sms_verification(phone_number, code)
        
        if success:
            return Response({
                'success': True,
                'message': f'Test SMS sent to {phone_number} with code {code}',
                'phone_number': phone_number,
                'code': code
            })
        else:
            return Response({
                'error': 'Failed to send SMS'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'Error sending SMS: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)