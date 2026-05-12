"""
Signal History Models

Track all generated signals for analytics, debugging, and backtesting.
"""

from django.db import models
import uuid

from core.models import BaseModel


class SignalHistory(BaseModel):
    """
    Historical record of all generated signals.
    
    Used for:
    - Signal performance analytics
    - Backtesting signal engines
    - Debugging signal generation logic
    - User signal notifications
    """
    
    SIGNAL_TYPE_CHOICES = [
        ('rsi', 'RSI'),
        ('macd', 'MACD'),
        ('breakout', 'Breakout'),
        ('volume_spike', 'Volume Spike'),
    ]
    
    DIRECTION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('neutral', 'Neutral'),
    ]
    
    # Basic signal info
    signal_id = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    signal_type = models.CharField(max_length=20, choices=SIGNAL_TYPE_CHOICES, db_index=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, db_index=True)
    
    # Stock reference
    stock = models.ForeignKey(
        'stocks.Stock',
        on_delete=models.CASCADE,
        related_name='signal_histories',
        db_index=True
    )
    
    # Signal details
    price = models.DecimalField(max_digits=15, decimal_places=2, db_index=True)
    strength = models.FloatField(  # 0.0 to 1.0
        help_text="Signal confidence/strength (0.0-1.0)"
    )
    message = models.TextField(help_text="Human-readable signal description")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    indicators = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw indicator values used for signal generation"
    )
    
    # Performance tracking
    signal_generation_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this signal was generated"
    )
    high_price_post_signal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Highest price after signal"
    )
    low_price_post_signal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Lowest price after signal"
    )
    profit_loss_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Profit/loss if sold at low_price_post_signal"
    )
    roi_percent = models.FloatField(
        null=True,
        blank=True,
        help_text="Return on investment percentage"
    )
    
    # User notifications
    users_notified = models.JSONField(
        default=list,
        blank=True,
        help_text="User IDs who were notified of this signal"
    )
    notifications_sent = models.IntegerField(default=0)
    
    # Alert association
    alert = models.ForeignKey(
        'alerts.PriceAlert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='signal_histories',
        help_text="Associated alert if this signal triggered an alert"
    )
    
    # Performance flags
    was_profitable = models.BooleanField(
        null=True,
        blank=True,
        help_text="True if signal resulted in profit"
    )
    was_actionable = models.BooleanField(
        default=True,
        help_text="Whether the signal was strong enough to act on"
    )
    
    class Meta:
        db_table = 'signals_history'
        indexes = [
            models.Index(fields=['stock', 'signal_type', 'signal_generation_time']),
            models.Index(fields=['direction', 'signal_generation_time']),
            models.Index(fields=['strength', 'signal_generation_time']),
        ]
        ordering = ['-signal_generation_time']
    
    def __str__(self):
        return (
            f"{self.signal_type.upper()} {self.direction} "
            f"- {self.stock.symbol} @ {self.price} "
            f"(strength: {self.strength:.2f})"
        )
    
    def calculate_performance(self, exit_price: float):
        """
        Calculate signal performance metrics.
        
        Args:
            exit_price: Price signal was exited at
        """
        entry_price = float(self.price)
        
        # Profit/loss
        if self.direction == 'buy':
            pnl = exit_price - entry_price
        else:  # sell
            pnl = entry_price - exit_price
        
        self.profit_loss_percent = (pnl / entry_price) * 100
        self.roi_percent = self.profit_loss_percent * (1 / max(0.001, self.strength))
        self.was_profitable = pnl > 0
        
        self.save(update_fields=['profit_loss_percent', 'roi_percent', 'was_profitable'])
    
    def mark_notified(self, user_ids):
        """
        Record which users were notified about this signal.
        
        Args:
            user_ids: List of user UUIDs
        """
        self.users_notified = list(set(self.users_notified) | set(user_ids))
        self.notifications_sent = len(self.users_notified)
        self.save(update_fields=['users_notified', 'notifications_sent'])


class SignalPerformance(BaseModel):
    """
    Aggregated signal performance statistics by engine and time period.
    Updated periodically via Celery tasks.
    """
    
    SIGNAL_TYPE_CHOICES = [
        ('rsi', 'RSI'),
        ('macd', 'MACD'),
        ('breakout', 'Breakout'),
        ('volume_spike', 'Volume Spike'),
    ]
    
    DIRECTION_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('all', 'All'),
    ]
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
    ]
    
    # Identification
    signal_type = models.CharField(max_length=20, choices=SIGNAL_TYPE_CHOICES, db_index=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, db_index=True)
    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_signals = models.IntegerField(default=0)
    profitable_signals = models.IntegerField(default=0)
    avg_strength = models.FloatField(default=0.0)
    avg_roi = models.FloatField(default=0.0)
    win_rate = models.FloatField(
        default=0.0,
        help_text="Percentage of profitable signals"
    )
    
    # Advanced metrics
    total_pnl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    best_trade = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    worst_trade = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    drawdown = models.FloatField(default=0.0, help_text="Maximum drawdown %")
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'signals_performance'
        unique_together = ('signal_type', 'direction', 'period', 'period_start')
        indexes = [
            models.Index(fields=['signal_type', 'period']),
            models.Index(fields=['period_start', 'period_end']),
        ]
        ordering = ['-period_start']
    
    def __str__(self):
        return (
            f"{self.signal_type} {self.period} - "
            f"Signals: {self.total_signals}, "
            f"Win Rate: {self.win_rate:.1f}%, "
            f"Avg ROI: {self.avg_roi:.2f}%"
        )
    
    @classmethod
    def calculate_performance_stats(cls, signal_type, direction, period_start, period_end):
        """
        Calculate performance statistics for a period.
        
        Args:
            signal_type: Type of signal
            direction: Signal direction (buy/sell)
            period_start: Period start datetime
            period_end: Period end datetime
        
        Returns:
            Dictionary with stats
        """
        from django.db.models import Avg, Count, Q
        from decimal import Decimal
        
        query = SignalHistory.objects.filter(
            signal_type=signal_type,
            direction=direction,
            signal_generation_time__gte=period_start,
            signal_generation_time__lt=period_end
        )
        
        total = query.count()
        if total == 0:
            return None
        
        profitable = query.filter(was_profitable=True).count()
        
        stats = query.aggregate(
            avg_strength=Avg('strength'),
            avg_roi=Avg('roi_percent'),
            total_pnl=models.Sum('profit_loss_percent'),
            best_trade=models.Max('profit_loss_percent'),
            worst_trade=models.Min('profit_loss_percent'),
        )
        
        return {
            'total_signals': total,
            'profitable_signals': profitable,
            'win_rate': (profitable / total * 100) if total > 0 else 0,
            'avg_strength': stats['avg_strength'] or 0.0,
            'avg_roi': stats['avg_roi'] or 0.0,
            'total_pnl': stats['total_pnl'] or Decimal(0),
            'best_trade': stats['best_trade'] or None,
            'worst_trade': stats['worst_trade'] or None,
        }
