from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailProvider:
    """Email provider using Django's email backend."""

    def is_enabled(self) -> bool:
        # consider SMTP settings or EMAIL_BACKEND presence
        return bool(getattr(settings, 'EMAIL_HOST', None))

    def send(self, subject: str, body: str, recipient_list, html_message: str = None) -> dict:
        try:
            send_mail(subject, body, getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list, html_message=html_message)
            return {'ok': True}
        except Exception as e:
            logger.exception('Email send failed')
            raise
