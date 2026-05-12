from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from signals.models.history import SignalHistory
from .services.insight_service import InsightService


class SignalExplanationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, signal_id):
        signal = get_object_or_404(SignalHistory.objects.select_related('stock'), signal_id=signal_id)
        return Response({'success': True, 'data': InsightService.explain_signal(signal)})


class MarketSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 1))
        return Response({'success': True, 'data': InsightService.build_market_summary(days=days)})


class DailyRecapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 1))
        return Response({'success': True, 'data': InsightService.generate_daily_recap(days=days)})
