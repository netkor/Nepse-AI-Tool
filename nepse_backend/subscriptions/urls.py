from django.urls import path
from subscriptions.views import SubscriptionPlanListView, SubscribeView, CancelSubscriptionView

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', SubscriptionPlanListView.as_view(), name='plans-list'),
    path('subscribe/<slug:plan_slug>/', SubscribeView.as_view(), name='subscribe'),
    path('cancel/<uuid:subscription_id>/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
]
