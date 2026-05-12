from typing import Optional, Dict
from subscriptions.models import SubscriptionPlan, BillingCustomer, Subscription, PaymentHistory
from subscriptions.providers.stripe_provider import StripeProvider
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self):
        self.stripe = StripeProvider()

    def create_plan(self, slug: str, name: str, price_cents: int, interval: str = 'monthly', currency: str='USD', features=None, metadata=None):
        features = features or []
        metadata = metadata or {}
        plan = SubscriptionPlan.objects.create(slug=slug, name=name, price_cents=price_cents, interval=interval, currency=currency, features=features, metadata=metadata)
        # Optionally create Stripe price here and store id in metadata
        try:
            if getattr(settings, 'CREATE_STRIPE_PRICES', False):
                price = self.stripe.create_price_for_plan(price_cents, currency, interval, nickname=name)
                plan.metadata['stripe_price_id'] = price.id
                plan.save(update_fields=['metadata'])
        except Exception:
            logger.exception('Failed creating stripe price for plan %s', slug)
        return plan

    def subscribe_user(self, user, plan: SubscriptionPlan, payment_method: Optional[str]=None):
        # Ensure BillingCustomer
        bc, _ = BillingCustomer.objects.get_or_create(user=user)
        with transaction.atomic():
            # create stripe customer if missing
            if not bc.provider_customer_id:
                try:
                    cust = self.stripe.create_customer(email=getattr(user, 'email', None), metadata={'user_id': str(user.id)})
                    bc.provider_customer_id = cust.id
                    bc.save(update_fields=['provider_customer_id'])
                except Exception:
                    logger.exception('failed creating stripe customer')
            # create subscription
            try:
                stripe_price = plan.metadata.get('stripe_price_id')
                if not stripe_price and getattr(settings, 'CREATE_STRIPE_PRICES', False):
                    p = self.stripe.create_price_for_plan(plan.price_cents, plan.currency, plan.interval, nickname=plan.name)
                    stripe_price = p.id
                    plan.metadata['stripe_price_id'] = stripe_price
                    plan.save(update_fields=['metadata'])

                sub = None
                if stripe_price and bc.provider_customer_id:
                    sub = self.stripe.create_subscription(bc.provider_customer_id, stripe_price)

                s, created = Subscription.objects.update_or_create(
                    user=user,
                    plan=plan,
                    defaults={
                        'provider_subscription_id': getattr(sub, 'id', None) if sub else None,
                        'status': 'active',
                        'current_period_start': timezone.now(),
                        'current_period_end': None
                    }
                )
                return s
            except Exception:
                logger.exception('Failed subscribing user %s to %s', user.id, plan.slug)
                raise

    def cancel_subscription(self, subscription: Subscription):
        try:
            if subscription.provider_subscription_id:
                self.stripe.cancel_subscription(subscription.provider_subscription_id)
            subscription.status = 'cancelled'
            subscription.save(update_fields=['status','updated_at'])
            return subscription
        except Exception:
            logger.exception('Failed cancelling subscription %s', subscription.id)
            raise

    def check_access(self, user, feature: str) -> bool:
        # Simple check: user has active subscription whose plan features include feature
        subs = Subscription.objects.filter(user=user, status='active')
        for s in subs:
            if feature in (s.plan.features or []):
                return True
        return False
