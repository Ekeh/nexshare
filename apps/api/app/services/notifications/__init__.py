from app.core.config import get_settings
from app.services.notifications.base import EmailSender, SmsSender
from app.services.notifications.console import ConsoleEmailSender, ConsoleSmsSender
from app.services.notifications.resend_email import ResendEmailSender
from app.services.notifications.termii_sms import TermiiSmsSender

settings = get_settings()


def get_email_sender() -> EmailSender:
    if settings.resend_api_key:
        return ResendEmailSender(api_key=settings.resend_api_key, from_address=settings.resend_from_email)
    return ConsoleEmailSender()


def get_sms_sender() -> SmsSender:
    if settings.termii_api_key:
        return TermiiSmsSender(api_key=settings.termii_api_key, sender_id=settings.termii_sender_id)
    return ConsoleSmsSender()
