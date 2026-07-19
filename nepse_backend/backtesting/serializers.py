from rest_framework import serializers
from .models import BacktestRun, BacktestResult


class BacktestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = BacktestResult
        fields = [
            'signal_type', 'direction', 'total_trades',
            'winning_trades', 'losing_trades', 'win_rate',
            'avg_return_pct', 'avg_holding_days',
            'max_drawdown_pct', 'best_trade_pct',
        ]


class BacktestRunSerializer(serializers.ModelSerializer):
    results = BacktestResultSerializer(many=True, read_only=True)

    class Meta:
        model = BacktestRun
        fields = [
            'id', 'started_at', 'completed_at', 'holding_days',
            'total_stocks', 'total_trades', 'status', 'results',
        ]
