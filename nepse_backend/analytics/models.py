from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from django.contrib.postgres.indexes import GinIndex


class Event(models.Model):
    """Raw analytic events emitted across the system."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    value = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['event_type', 'created_at'], name='event_type_created_at_idx'),
            GinIndex(fields=['metadata'], name='event_metadata_gin')
        ]


class AggregatedMetric(models.Model):
    """Stores pre-aggregated metric values for fast dashboards."""
    PERIOD_CHOICES = (('daily','daily'),('weekly','weekly'),('monthly','monthly'),('all_time','all_time'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=128, db_index=True)
    period = models.CharField(max_length=32, choices=PERIOD_CHOICES, db_index=True)
    period_start = models.DateField(db_index=True)
    period_end = models.DateField()
    value = models.FloatField()
    extra = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('metric_name','period','period_start'),)
        ordering = ('-period_start',)
        indexes = [
            models.Index(fields=['metric_name','period','period_start'], name='metric_period_start_idx'),
        ]
