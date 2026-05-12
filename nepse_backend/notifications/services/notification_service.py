import logging
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any
from notifications.models import NotificationHistory, NotificationTemplate
from notifications.providers.telegram_provider import TelegramProvider
from notifications.providers.email_provider import EmailProvider
from notifications.utils.rate_limiter import RedisRateLimiter

logger = logging.getLogger(__name__)


class NotificationService:
    """High-level notification service used by application code.

    Responsibilities:
    - Render templates into payloads
    - Enforce per-user and global rate limits
    - Persist NotificationHistory records
    - Queue Celery tasks (tasks.send_notification_task)
    """

    def __init__(self):
        self.telegram = TelegramProvider()
        self.email = EmailProvider()
        self.rate_limiter = RedisRateLimiter()

    def send_telegram(self, user_chat_id: str, template_name: str, context: Dict[str, Any]) -> NotificationHistory:
        tpl = NotificationTemplate.objects.filter(name=template_name, channel='telegram').first()
        body = tpl.body.format(**context) if tpl else context.get('text', '')
        nh = NotificationHistory.objects.create(channel='telegram', template=tpl, payload={'text': body})

        # Rate limiting per chat_id
        if not self.rate_limiter.allow(f'tg:{user_chat_id}', limit=5, period_seconds=60):
            nh.mark_failed('rate_limited')
            return nh

        # Persist pending and queue task
        from notifications.tasks import send_notification_task
        send_notification_task.delay(str(nh.id), {'provider':'telegram','chat_id': user_chat_id, 'text': body})
        return nh

    def send_email(self, recipient_list, template_name: str, context: Dict[str, Any]) -> NotificationHistory:
        tpl = NotificationTemplate.objects.filter(name=template_name, channel='email').first()
        subject = tpl.subject.format(**context) if tpl else context.get('subject','')
        body = tpl.body.format(**context) if tpl else context.get('body','')
        nh = NotificationHistory.objects.create(channel='email', template=tpl, payload={'subject': subject, 'body': body, 'to': recipient_list})

        # Rate limiting per recipient (simple): key per recipient email
        for r in recipient_list:
            if not self.rate_limiter.allow(f'em:{r}', limit=10, period_seconds=60):
                nh.mark_failed('rate_limited')
                return nh

        from notifications.tasks import send_notification_task
        send_notification_task.delay(str(nh.id), {'provider':'email','recipients': recipient_list, 'subject': subject, 'body': body})
        return nh

    def record_manual(self, channel: str, payload: dict) -> NotificationHistory:
        return NotificationHistory.objects.create(channel=channel, payload=payload)
