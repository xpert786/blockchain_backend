from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .email_utils import send_verification_email, send_sms_verification


class TestEmailViewSet(viewsets.ViewSet):
    """
    Test endpoints for email functionality
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def send_test_email(self, request):
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
    
    @action(detail=False, methods=['post'])
    def send_test_sms(self, request):
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
