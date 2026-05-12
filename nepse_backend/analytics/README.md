Analytics & Insights app

Quick usage:

from analytics.services import AnalyticsService

# record an event
AnalyticsService.record_event('signal.created', user=request.user, value=1.0, metadata={'signal_type':'rsi'})

# run aggregation (or use Celery task)
from analytics.tasks import aggregate_daily_events
aggregate_daily_events.delay()

