"""
Celery tasks for the alerts app.
Handles periodic price alert checking and Telegram notifications.
"""
import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 4  # 4 minutes
LOCK_ID = 'check_price_alerts_lock'


@shared_task(bind=True, acks_late=True, max_retries=0)
def check_price_alerts(self):
    """
    Check and trigger price alerts for all active alerts.

    Uses a Redis-based solo execution guard to prevent concurrent runs.
    Sends Telegram notifications to eligible users when alerts are triggered.

    Returns:
        dict with 'triggered_count' key indicating number of alerts triggered.
    """
    # Solo execution guard - prevent concurrent runs
    acquired = cache.add(LOCK_ID, 'locked', LOCK_EXPIRE)
    if not acquired:
        logger.warning("check_price_alerts: skipped (already running)")
        return {'triggered_count': 0, 'skipped': True}

    try:
        from alerts.models import PriceAlert
        from alerts.services import AlertService
        from config.telegram_service import TelegramService

        # Check all active alerts and trigger those meeting conditions
        triggered_count = AlertService.check_and_trigger_price_alerts()

        if triggered_count > 0 and TelegramService.is_enabled():
            # Send Telegram notifications for recently triggered alerts
            triggered_alerts = PriceAlert.objects.filter(
                status='TRIGGERED',
                triggered_at__isnull=False
            ).select_related('stock', 'user')

            for alert in triggered_alerts[:10]:  # Limit to 10 per run
                if (alert.user.is_telegram_alerts_enabled and
                        alert.user.telegram_verified):

                    alert_type = 'min' if (
                        alert.min_price and
                        float(alert.stock.price) <= float(alert.min_price)
                    ) else 'max'
                    threshold = alert.min_price if alert_type == 'min' else alert.max_price

                    TelegramService.send_price_alert(
                        chat_id=alert.user.telegram_chat_id,
                        stock_symbol=alert.stock.symbol,
                        stock_price=float(alert.stock.price),
                        alert_type=alert_type,
                        threshold_price=float(threshold) if threshold else 0,
                    )

        logger.info(f"check_price_alerts: triggered={triggered_count}")
        return {'triggered_count': triggered_count}

    finally:
        cache.delete(LOCK_ID)
