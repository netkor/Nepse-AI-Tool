import logging

from celery import shared_task

from .services.insight_service import InsightService

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_market_summary(self, days: int = 1):
    """Precompute the cached market summary used by dashboards."""
    try:
        return InsightService.build_market_summary(days=days)
    except Exception as exc:
        logger.exception('Failed to generate market summary')
        return {'success': False, 'error': str(exc)}


@shared_task(bind=True)
def generate_daily_recap(self, days: int = 1):
    """Precompute the cached daily recap used by notifications and dashboard widgets."""
    try:
        return InsightService.generate_daily_recap(days=days)
    except Exception as exc:
        logger.exception('Failed to generate daily recap')
        return {'success': False, 'error': str(exc)}
