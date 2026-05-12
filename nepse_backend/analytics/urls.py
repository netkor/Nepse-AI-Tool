from django.urls import path
from analytics.views import AggregatedMetricListView
from analytics.views import LeaderboardView

app_name = 'analytics'

urlpatterns = [
    path('metrics/', AggregatedMetricListView.as_view(), name='metrics-list'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
