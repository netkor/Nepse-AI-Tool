Subscriptions app

Includes models for `SubscriptionPlan`, `Subscription`, `BillingCustomer`, and `PaymentHistory`.
Provides `StripeProvider` and `SubscriptionService` helper for creating plans and subscribing users.

Quick start:

- Add `subscriptions` to `INSTALLED_APPS`
- Set `STRIPE_API_KEY` in environment or Django settings
- Optionally set `CREATE_STRIPE_PRICES=True` to auto-create Stripe prices

Endpoints:
- `GET /api/subscriptions/plans/`
- `POST /api/subscriptions/subscribe/<plan_slug>/` (auth required)
- `POST /api/subscriptions/cancel/<subscription_id>/` (auth required)
