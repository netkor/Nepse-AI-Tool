"""
Signal generation service with technical analysis.
Core business logic for generating trading signals.
"""
from decimal import Decimal
from typing import List, Tuple, Optional
from django.utils import timezone
from datetime import timedelta

from stocks.models import Stock, StockHistory
from .models import Signal
from . import utils


class SignalService:
    """
    Service for generating trading signals based on technical indicators.
    Prevents duplicate signals within a time window.
    """

    DUPLICATE_SIGNAL_WINDOW_HOURS = 1  # Prevent same signal within 1 hour
    MIN_CONFIDENCE_THRESHOLD = 50  # Minimum confidence to create signal

    @classmethod
    def generate_signals(cls) -> Tuple[int, List[str]]:
        """
        Generate signals for all active stocks.
        
        Returns:
            (signals_created: int, signal_descriptions: List[str])
        """
        signals_created = 0
        signal_descriptions = []

        active_stocks = Stock.objects.filter(is_active=True)

        for stock in active_stocks:
            stock_signals = cls._analyze_stock(stock)
            
            for signal_data in stock_signals:
                signal = cls._create_signal_if_not_duplicate(stock, signal_data)
                if signal:
                    signals_created += 1
                    signal_descriptions.append(
                        f"{signal.signal_type} signal for {stock.symbol} "
                        f"(Confidence: {signal.confidence_score}%)"
                    )

        return signals_created, signal_descriptions

    @classmethod
    def _analyze_stock(cls, stock: Stock) -> List[dict]:
        """
        Analyze a single stock for trading signals.
        
        Returns:
            List of signal data dictionaries to create
        """
        signals = []
        
        # Get historical data
        history = stock.history.order_by('-date').values_list(
            'close_price', 'volume', flat=False
        )[:90]
        
        if len(history) < 20:
            return signals
        
        # Extract prices and volumes
        prices = [float(h[0]) for h in reversed(history)]
        volumes = [int(h[1]) for h in reversed(history)]
        
        # 1. Moving Average Crossover
        ma_signal = utils.detect_ma_crossover(prices, fast_period=5, slow_period=20)
        if ma_signal['signal']:
            signals.append({
                'signal_type': ma_signal['signal'],
                'reason': f"MA(5) {ma_signal['signal'].lower()} crossover MA(20). "
                          f"Fast MA: ${ma_signal['fast_ma']:.2f}, "
                          f"Slow MA: ${ma_signal['slow_ma']:.2f}",
                'confidence_score': ma_signal['confidence'],
                'indicator_details': {
                    'indicator': 'MA_CROSSOVER',
                    'fast_ma': ma_signal['fast_ma'],
                    'slow_ma': ma_signal['slow_ma'],
                }
            })
        
        # 2. Volume Spike
        volume_signal = utils.detect_volume_spike(volumes, threshold=2.0)
        if volume_signal['signal']:
            signals.append({
                'signal_type': 'ALERT',
                'reason': f"Volume spike detected. Current: {volume_signal['current_volume']:,}, "
                         f"10-day avg: {volume_signal['average_volume']:,.0f}, "
                         f"Ratio: {volume_signal['spike_ratio']:.2f}x",
                'confidence_score': volume_signal['confidence'],
                'indicator_details': {
                    'indicator': 'VOLUME_SPIKE',
                    'current_volume': volume_signal['current_volume'],
                    'average_volume': volume_signal['average_volume'],
                    'spike_ratio': volume_signal['spike_ratio'],
                }
            })
        
        # 3. RSI Extreme
        rsi_signal = utils.detect_rsi_extremes(prices, overbought=70, oversold=30)
        if rsi_signal['signal']:
            signals.append({
                'signal_type': rsi_signal['signal'],
                'reason': f"RSI indicates {rsi_signal['signal'].lower()} opportunity. "
                         f"RSI: {rsi_signal['rsi_value']:.2f}",
                'confidence_score': rsi_signal['confidence'],
                'indicator_details': {
                    'indicator': 'RSI',
                    'rsi_value': rsi_signal['rsi_value'],
                }
            })
        
        return signals

    @classmethod
    def _create_signal_if_not_duplicate(cls, stock: Stock, signal_data: dict) -> Optional[Signal]:
        """
        Create a signal only if a similar one hasn't been created recently.
        
        Returns:
            Signal instance if created, None if duplicate
        """
        # Check for recent signal
        if Signal.get_recent_signal(
            stock,
            signal_data['signal_type'],
            hours=cls.DUPLICATE_SIGNAL_WINDOW_HOURS
        ):
            return None
        
        # Create signal
        signal = Signal.objects.create(
            stock=stock,
            signal_type=signal_data['signal_type'],
            reason=signal_data['reason'],
            confidence_score=signal_data['confidence_score'],
            indicator_details=signal_data.get('indicator_details', {}),
            is_notified=False,
        )
        
        return signal

    @classmethod
    def get_signals_for_stock(cls, stock: Stock, days: int = 7) -> List[Signal]:
        """
        Get signals for a specific stock from the last N days.
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        return Signal.objects.filter(
            stock=stock,
            created_at__gte=cutoff_date
        ).order_by('-created_at')

    @classmethod
    def get_latest_signals(cls, limit: int = 20) -> List[Signal]:
        """
        Get the latest signals across all stocks.
        """
        return Signal.objects.select_related('stock').order_by('-created_at')[:limit]
