from django.urls import path

from .views import DailyRecapView, MarketSummaryView, SignalExplanationView

app_name = 'insights'

urlpatterns = [
    path('signals/<uuid:signal_id>/explain/', SignalExplanationView.as_view(), name='signal-explain'),
    path('market-summary/', MarketSummaryView.as_view(), name='market-summary'),
    path('daily-recap/', DailyRecapView.as_view(), name='daily-recap'),
]
