from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=128)
    price_cents = models.IntegerField(help_text='Price in cents', default=0)
    currency = models.CharField(max_length=8, default='USD')
    interval = models.CharField(max_length=16, choices=(('monthly','monthly'),('yearly','yearly')))
    features = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BillingCustomer(models.Model):
    """Link to payment provider customer (e.g., Stripe customer id)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=64, default='stripe')
    provider_customer_id = models.CharField(max_length=256, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"BillingCustomer:{self.user_id}"


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    provider_subscription_id = models.CharField(max_length=256, null=True, blank=True)
    status = models.CharField(max_length=32, choices=(('active','active'),('cancelled','cancelled'),('past_due','past_due')),
                              default='active')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('user','plan'),)

    def is_active(self):
        return self.status == 'active'


class PaymentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(max_length=64, default='stripe')
    provider_charge_id = models.CharField(max_length=256, null=True, blank=True)
    amount_cents = models.IntegerField()
    currency = models.CharField(max_length=8, default='USD')
    success = models.BooleanField(default=False)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment:{self.user_id}:{self.amount_cents}" 
