from rest_framework import generics
from analytics.models import AggregatedMetric
from analytics.serializers import AggregatedMetricSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from analytics.services.analytics_service import AnalyticsService


class LeaderboardView(APIView):
    """Return top N metric entries for a metric and period."""

    def get(self, request):
        metric = request.query_params.get('metric')
        period = request.query_params.get('period', 'daily')
        top = int(request.query_params.get('top', 10))
        if not metric:
            return Response({'error': 'metric query param required'}, status=400)
        data = AnalyticsService.get_leaderboard(metric, period=period, top_n=top)
        return Response({'metric': metric, 'period': period, 'top': top, 'rows': data})


class AggregatedMetricListView(generics.ListAPIView):
    serializer_class = AggregatedMetricSerializer

    def get_queryset(self):
        metric = self.request.query_params.get('metric')
        period = self.request.query_params.get('period','daily')
        qs = AggregatedMetric.objects.all()
        if metric:
            qs = qs.filter(metric_name=metric)
        if period:
            qs = qs.filter(period=period)
        return qs.order_by('-period_start')
