from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone
from datetime import date, timedelta
from analytics.models import Event, AggregatedMetric
from django.core.cache import cache


class AnalyticsService:
    """Service for recording events and computing aggregations."""

    @staticmethod
    def record_event(event_type: str, user=None, value: Optional[float]=None, metadata: Optional[Dict[str,Any]]=None) -> Event:
        metadata = metadata or {}
        return Event.objects.create(event_type=event_type, user=user, value=value, metadata=metadata)

    @staticmethod
    def get_events(event_type: Optional[str]=None, since_days: int=7):
        qs = Event.objects.all()
        if event_type:
            qs = qs.filter(event_type=event_type)
        since = timezone.now() - timedelta(days=since_days)
        qs = qs.filter(created_at__gte=since)
        return qs

    @staticmethod
    def aggregate_daily_for_date(target_date: date):
        # Aggregate counts and sums per event_type for a single date
        start = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time()))
        end = start + timedelta(days=1)
        qs = Event.objects.filter(created_at__gte=start, created_at__lt=end)
        results = {}
        for et_row in qs.values('event_type'):
            pass
        # efficient aggregation via values + annotate
        from django.db.models import Count, Sum, Avg
        agg = qs.values('event_type').annotate(count=Count('id'), total=Sum('value'), avg=Avg('value'))
        created = []
        for row in agg:
            metric_name = f"events.{row['event_type']}.count"
            value = row['count']
            extra = {'total': row['total'] or 0.0, 'avg': row['avg'] or 0.0}
            am, _ = AggregatedMetric.objects.update_or_create(
                metric_name=metric_name,
                period='daily',
                period_start=target_date,
                defaults={'period_end': target_date, 'value': value, 'extra': extra}
            )
            created.append(am)
        return created

    @staticmethod
    def aggregate_last_n_days(n: int = 7):
        today = timezone.now().date()
        created = []
        for i in range(1, n+1):
            d = today - timedelta(days=i)
            created.extend(AnalyticsService.aggregate_daily_for_date(d))
        return created

    @staticmethod
    def get_aggregated(metric_name: str, period: str='daily', limit: int=30):
        qs = AggregatedMetric.objects.filter(metric_name=metric_name, period=period).order_by('-period_start')[:limit]
        return qs

    @staticmethod
    def get_leaderboard(metric_name: str, period: str = 'daily', top_n: int = 10, cache_ttl: int = 60):
        """Return top N aggregated metric entries for the given metric and period.

        Results are cached for `cache_ttl` seconds to reduce DB load on dashboards.
        Returns a list of dicts: {'period_start': date, 'value': float, 'extra': dict}
        """
        cache_key = f"analytics:leaderboard:{metric_name}:{period}:{top_n}"
        data = cache.get(cache_key)
        if data is not None:
            return data

        qs = AggregatedMetric.objects.filter(metric_name=metric_name, period=period).order_by('-value')[:top_n]
        data = [
            {'period_start': a.period_start, 'value': a.value, 'extra': a.extra}
            for a in qs
        ]
        cache.set(cache_key, data, cache_ttl)
        return data
