from django.contrib import admin
from .models import BacktestRun, BacktestResult


class BacktestResultInline(admin.TabularInline):
    model = BacktestResult
    extra = 0
    readonly_fields = [
        'signal_type', 'direction', 'total_trades', 'winning_trades',
        'losing_trades', 'win_rate', 'avg_return_pct', 'avg_holding_days',
        'max_drawdown_pct', 'best_trade_pct',
    ]


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'holding_days', 'total_stocks', 'total_trades', 'started_at', 'completed_at']
    list_filter = ['status']
    readonly_fields = ['started_at', 'completed_at']
    inlines = [BacktestResultInline]


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = [
        'run', 'signal_type', 'direction', 'total_trades',
        'win_rate', 'avg_return_pct', 'max_drawdown_pct', 'best_trade_pct',
    ]
    list_filter = ['signal_type', 'direction']
