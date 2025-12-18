from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_verification_email(email, code, user_name=None):
    """
    Send verification code via email
    """
    try:
        subject = 'Your Verification Code - Blockchain Admin'
        
        # Create HTML email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Email Verification</h2>
                
                <p>Hello {user_name or 'User'},</p>
                
                <p>Thank you for registering with Blockchain Admin. To complete your registration, please use the verification code below:</p>
                
                <div style="background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #2c3e50; font-size: 32px; letter-spacing: 5px; margin: 0;">{code}</h1>
                </div>
                
                <p><strong>Important:</strong></p>
                <ul>
                    <li>This code will expire in 15 minutes</li>
                    <li>Enter this code exactly as shown</li>
                    <li>If you didn't request this code, please ignore this email</li>
                </ul>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="text-align: center; color: #666; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_message = f"""
        Email Verification
        
        Hello {user_name or 'User'},
        
        Thank you for registering with Blockchain Admin. To complete your registration, please use the verification code below:
        
        Verification Code: {code}
        
        Important:
        - This code will expire in 15 minutes
        - Enter this code exactly as shown
        - If you didn't request this code, please ignore this email
        
        If you have any questions, please contact our support team.
        
        This is an automated message. Please do not reply to this email.
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_sms_verification(phone_number, code):
    """
    Send verification code via SMS
    Note: This is a placeholder. You'll need to integrate with an SMS service like Twilio
    """
    try:
        # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
        print(f"SMS would be sent to {phone_number} with code: {code}")
        
        # For now, just log the SMS
        print(f"📱 SMS Code: {code} sent to {phone_number}")
        return True
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


def send_2fa_code_email(email, code, user_name=None):
    """
    Send 2FA verification code via email
    """
    try:
        subject = 'Your 2FA Verification Code - Blockchain Admin'
        
        # Create HTML email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Two-Factor Authentication</h2>
                
                <p>Hello {user_name or 'User'},</p>
                
                <p>You requested a two-factor authentication code. Use the code below to complete your login:</p>
                
                <div style="background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #2c3e50; font-size: 32px; letter-spacing: 5px; margin: 0;">{code}</h1>
                </div>
                
                <p><strong>Security Notice:</strong></p>
                <ul>
                    <li>This code will expire in 15 minutes</li>
                    <li>Never share this code with anyone</li>
                    <li>If you didn't request this code, please secure your account immediately</li>
                </ul>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="text-align: center; color: #666; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_message = f"""
        Two-Factor Authentication
        
        Hello {user_name or 'User'},
        
        You requested a two-factor authentication code. Use the code below to complete your login:
        
        Verification Code: {code}
        
        Security Notice:
        - This code will expire in 15 minutes
        - Never share this code with anyone
        - If you didn't request this code, please secure your account immediately
        
        If you have any questions, please contact our support team.
        
        This is an automated message. Please do not reply to this email.
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending 2FA email: {e}")
        return False


def send_password_reset_otp(email, otp, user_name=None):
    """
    Send password reset OTP via email
    """
    try:
        subject = 'Password Reset OTP - Blockchain Admin'
        
        # Create HTML email content
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; text-align: center;">Password Reset Request</h2>
                
                <p>Hello {user_name or 'User'},</p>
                
                <p>We received a request to reset your password. Use the 4-digit OTP below to proceed with resetting your password:</p>
                
                <div style="background-color: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                    <h1 style="color: #2c3e50; font-size: 48px; letter-spacing: 10px; margin: 0;">{otp}</h1>
                </div>
                
                <p><strong>Security Notice:</strong></p>
                <ul>
                    <li>This OTP will expire in 15 minutes</li>
                    <li>Never share this OTP with anyone</li>
                    <li>If you didn't request a password reset, please ignore this email and secure your account</li>
                    <li>Your password will not change until you complete the reset process</li>
                </ul>
                
                <p>If you have any questions or concerns, please contact our support team immediately.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="text-align: center; color: #666; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create plain text version
        plain_message = f"""
        Password Reset Request
        
        Hello {user_name or 'User'},
        
        We received a request to reset your password. Use the 4-digit OTP below to proceed with resetting your password:
        
        OTP: {otp}
        
        Security Notice:
        - This OTP will expire in 15 minutes
        - Never share this OTP with anyone
        - If you didn't request a password reset, please ignore this email and secure your account
        - Your password will not change until you complete the reset process
        
        If you have any questions or concerns, please contact our support team immediately.
        
        This is an automated message. Please do not reply to this email.
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False
