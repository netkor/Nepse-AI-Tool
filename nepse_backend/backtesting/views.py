from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import BacktestRun, BacktestResult
from .serializers import BacktestRunSerializer, BacktestResultSerializer


class BacktestLatestView(APIView):
    """
    GET /api/backtest/results/
    Returns the most recent completed BacktestRun with all its
    BacktestResult rows nested.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        run = BacktestRun.objects.filter(status='COMPLETED').first()
        if not run:
            return Response(
                {'detail': 'No completed backtest runs found. Run: python manage.py run_backtest'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = BacktestRunSerializer(run)
        return Response(serializer.data)


class BacktestSignalTypeView(APIView):
    """
    GET /api/backtest/results/<signal_type>/
    Returns detailed results for a single signal type from the latest
    completed run.  Usable by the frontend to annotate live alerts with
    historical accuracy stats.
    """
    permission_classes = [IsAuthenticated]

    VALID_TYPES = {
        'EMA_CROSS', 'MACD_CROSS', 'RSI_MEAN_REVERSION',
        'RSI_DIVERGENCE', 'DOW_THEORY', 'WEEKLY_SMA_CROSS',
        'VOLUME_BREAKOUT',
    }

    def get(self, request, signal_type):
        signal_type = signal_type.upper()
        if signal_type not in self.VALID_TYPES:
            return Response(
                {'detail': f"Invalid signal type '{signal_type}'. Valid: {', '.join(sorted(self.VALID_TYPES))}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        run = BacktestRun.objects.filter(status='COMPLETED').first()
        if not run:
            return Response(
                {'detail': 'No completed backtest runs found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        results = BacktestResult.objects.filter(run=run, signal_type=signal_type)
        if not results.exists():
            return Response(
                {'detail': f"No backtest results for signal type '{signal_type}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BacktestResultSerializer(results, many=True)
        return Response({
            'run_id': run.pk,
            'holding_days': run.holding_days,
            'signal_type': signal_type,
            'results': serializer.data,
        })
