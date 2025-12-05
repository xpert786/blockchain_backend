# sms_utils.py
from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

logger = logging.getLogger(__name__)

def send_twilio_sms(to_number, code):
    """
    Sends a 4-digit verification code via Twilio.
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        message = client.messages.create(
            body=f"Your verification code is: {code}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return True, message.sid
    except TwilioRestException as e:
        logger.error(f"Twilio Error: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return False, str(e)