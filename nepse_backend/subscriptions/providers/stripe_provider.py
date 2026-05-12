import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class StripeProvider:
    def __init__(self, api_key: str = None):
        api_key = api_key or getattr(settings, 'STRIPE_API_KEY', None)
        if not api_key:
            logger.warning('STRIPE_API_KEY not configured')
        stripe.api_key = api_key

    def create_customer(self, email: str, metadata: dict = None):
        return stripe.Customer.create(email=email, metadata=metadata or {})

    def create_subscription(self, customer_id: str, price_id: str):
        return stripe.Subscription.create(customer=customer_id, items=[{'price': price_id}])

    def retrieve_subscription(self, subscription_id: str):
        return stripe.Subscription.retrieve(subscription_id)

    def cancel_subscription(self, subscription_id: str):
        return stripe.Subscription.delete(subscription_id)

    def create_price_for_plan(self, amount_cents: int, currency: str, interval: str, nickname: str):
        # This is a helper; in production you'd create products and prices via Dashboard or idempotent API
        return stripe.Price.create(unit_amount=amount_cents, currency=currency.lower(), recurring={'interval': interval}, nickname=nickname)
