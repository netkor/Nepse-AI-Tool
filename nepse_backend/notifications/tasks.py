from celery import shared_task
import logging
from notifications.models import NotificationHistory
from notifications.providers.telegram_provider import TelegramProvider
from notifications.providers.email_provider import EmailProvider
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_task(self, notification_id: str, payload: dict):
    """Payload example: {'provider':'telegram','chat_id':..., 'text':...}
    or {'provider':'email','recipients': [...], 'subject':..., 'body':...}
    """
    try:
        nh = NotificationHistory.objects.get(id=notification_id)
    except NotificationHistory.DoesNotExist:
        logger.error('NotificationHistory %s not found', notification_id)
        return {'ok': False, 'reason': 'not_found'}

    provider = payload.get('provider')
    try:
        if provider == 'telegram':
            tg = TelegramProvider()
            resp = tg.send(payload['chat_id'], payload['text'])
            with transaction.atomic():
                nh.mark_sent(provider_ref=resp.get('result', {}).get('message_id'))
            return {'ok': True}

        if provider == 'email':
            ep = EmailProvider()
            resp = ep.send(payload.get('subject',''), payload.get('body',''), payload.get('recipients', []), html_message=payload.get('html'))
            with transaction.atomic():
                nh.mark_sent(provider_ref='email_sent')
            return {'ok': True}

        logger.error('Unknown provider: %s', provider)
        nh.mark_failed(f'unknown_provider:{provider}')
        return {'ok': False}

    except Exception as exc:
        logger.exception('Sending notification failed')
        nh.mark_failed(str(exc))
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error('Max retries exceeded for notification %s', notification_id)
            return {'ok': False, 'reason': 'max_retries'}
