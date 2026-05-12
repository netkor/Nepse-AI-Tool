from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class NotificationTemplate(models.Model):
    """Reusable notification templates for different channels and events."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    channel = models.CharField(max_length=32, choices=(('telegram','telegram'),('email','email')))
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class NotificationHistory(models.Model):
    """Records of notifications sent (or attempted)."""
    STATUS_CHOICES = (('pending','pending'),('sent','sent'),('failed','failed'))

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=32)
    provider_reference = models.CharField(max_length=512, null=True, blank=True)
    template = models.ForeignKey(NotificationTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', db_index=True)
    attempts = models.IntegerField(default=0)
    last_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def mark_sent(self, provider_ref=None):
        self.status = 'sent'
        self.provider_reference = provider_ref
        self.attempts = (self.attempts or 0) + 1
        self.save(update_fields=['status','provider_reference','attempts','updated_at'])

    def mark_failed(self, error_message: str):
        self.status = 'failed'
        self.last_error = str(error_message)
        self.attempts = (self.attempts or 0) + 1
        self.save(update_fields=['status','last_error','attempts','updated_at'])
