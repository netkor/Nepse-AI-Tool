from django.db import models


class BacktestRun(models.Model):
    """
    Represents a single execution of the backtest engine.
    Each run stores its configuration and aggregate stats.
    """
    STATUS_CHOICES = [
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    holding_days = models.IntegerField(
        default=10,
        help_text='Number of trading days to hold each simulated position'
    )
    total_stocks = models.IntegerField(default=0)
    total_trades = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RUNNING')
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"BacktestRun #{self.pk} ({self.status}) — {self.started_at:%Y-%m-%d %H:%M}"


class BacktestResult(models.Model):
    """
    Aggregate performance metrics for one (signal_type × direction) combination
    within a single BacktestRun.
    """
    SIGNAL_TYPE_CHOICES = [
        ('EMA_CROSS', 'EMA Cross (Golden/Death)'),
        ('MACD_CROSS', 'MACD Crossover'),
        ('RSI_MEAN_REVERSION', 'RSI Mean Reversion'),
        ('RSI_DIVERGENCE', 'RSI Divergence'),
        ('DOW_THEORY', 'Dow Theory'),
        ('WEEKLY_SMA_CROSS', 'Weekly SMA Cross'),
        ('VOLUME_BREAKOUT', 'Volume Spike Breakout'),
        ('CONFLUENCE_SCORE', 'Confluence Score'),
    ]
    DIRECTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]

    run = models.ForeignKey(
        BacktestRun,
        on_delete=models.CASCADE,
        related_name='results'
    )
    signal_type = models.CharField(max_length=30, choices=SIGNAL_TYPE_CHOICES)
    direction = models.CharField(max_length=4, choices=DIRECTION_CHOICES)

    # Aggregate metrics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.FloatField(
        default=0.0,
        help_text='Percentage of winning trades (0-100)'
    )
    avg_return_pct = models.FloatField(
        default=0.0,
        help_text='Mean percentage return across all trades'
    )
    avg_holding_days = models.FloatField(
        default=0.0,
        help_text='Mean actual holding period in trading days'
    )
    max_drawdown_pct = models.FloatField(
        default=0.0,
        help_text='Worst single-trade percentage loss'
    )
    best_trade_pct = models.FloatField(
        default=0.0,
        help_text='Best single-trade percentage gain'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['signal_type', 'direction']
        unique_together = ('run', 'signal_type', 'direction')

    def __str__(self):
        return (
            f"{self.signal_type} {self.direction}: "
            f"{self.win_rate:.1f}% win rate ({self.total_trades} trades)"
        )
