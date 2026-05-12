from celery import shared_task
from analytics.services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def aggregate_daily_events(self):
    """Aggregate yesterday's events into AggregatedMetric records."""
    from django.utils import timezone
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    try:
        created = AnalyticsService.aggregate_daily_for_date(yesterday)
        return {'ok': True, 'created': len(created)}
    except Exception as exc:
        logger.exception('Daily aggregation failed')
        return {'ok': False, 'error': str(exc)}
