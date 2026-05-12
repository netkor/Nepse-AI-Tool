"""
Signal Service Layer

Business logic for signal generation, validation, and persistence.
Implements the service layer pattern from core/services.py
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from django.utils import timezone
from django.db import transaction

from core.services import BaseService, service_transaction, service_cache, service_logger
from stocks.models import Stock
from .models import SignalHistory, SignalPerformance
from .engines import BaseSignal, RSISignal, MACDSignal, BreakoutSignal, VolumeSpikeSignal, SignalResult

logger = logging.getLogger(__name__)


class SignalService(BaseService):
    """
    Signal service layer.
    
    Handles signal generation, validation, persistence, and analytics.
    """
    
    model = SignalHistory
    
    # Available signal engines
    ENGINES = {
        'rsi': RSISignal,
        'macd': MACDSignal,
        'breakout': BreakoutSignal,
        'volume_spike': VolumeSpikeSignal,
    }
    
    @classmethod
    @service_transaction
    def generate_signal(
        cls,
        stock: Stock,
        signal_type: str,
        historical_data: List[Dict[str, Any]],
        engine_params: Optional[Dict[str, Any]] = None
    ) -> Optional[SignalHistory]:
        """
        Generate a signal and persist it.
        
        Args:
            stock: Stock to generate signal for
            signal_type: Type of signal (rsi, macd, breakout, volume_spike)
            historical_data: List of OHLCV candles
            engine_params: Optional engine configuration
        
        Returns:
            SignalHistory object if signal generated, None otherwise
        """
        if signal_type not in cls.ENGINES:
            logger.error(f"Unknown signal type: {signal_type}")
            return None
        
        try:
            # Create engine instance
            engine_class = cls.ENGINES[signal_type]
            engine = engine_class(**(engine_params or {}))
            
            # Generate signal
            result: Optional[SignalResult] = engine.generate(historical_data)
            
            if result is None:
                logger.debug(f"No signal generated for {stock.symbol} - {signal_type}")
                return None
            
            # Persist signal
            signal_record = SignalHistory.objects.create(
                signal_type=signal_type,
                direction=result.direction.value,
                stock=stock,
                price=result.price,
                strength=result.strength,
                message=result.message,
                metadata=result.metadata,
                indicators=result.indicators,
                was_actionable=result.strength >= 0.5,
            )
            
            logger.info(
                f"Signal persisted: {signal_type} {result.direction.value} "
                f"for {stock.symbol} (strength: {result.strength:.2f})"
            )
            
            return signal_record
            
        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}", exc_info=True)
            return None
    
    @classmethod
    @service_transaction
    def generate_all_signals(
        cls,
        stock: Stock,
        historical_data: List[Dict[str, Any]]
    ) -> List[SignalHistory]:
        """
        Generate signals from all available engines.
        
        Args:
            stock: Stock to generate signals for
            historical_data: List of OHLCV candles
        
        Returns:
            List of generated signals
        """
        signals = []
        
        for signal_type in cls.ENGINES:
            signal = cls.generate_signal(
                stock=stock,
                signal_type=signal_type,
                historical_data=historical_data
            )
            if signal:
                signals.append(signal)
        
        return signals
    
    @classmethod
    @service_cache(timeout=3600)
    def get_recent_signals(
        cls,
        stock: Optional[Stock] = None,
        hours: int = 24,
        signal_type: Optional[str] = None,
        min_strength: float = 0.5
    ) -> List[SignalHistory]:
        """
        Get recent signals.
        
        Args:
            stock: Filter by stock (optional)
            hours: Hours to look back
            signal_type: Filter by signal type (optional)
            min_strength: Minimum signal strength
        
        Returns:
            List of recent signals
        """
        cutoff = timezone.now() - timedelta(hours=hours)
        
        query = SignalHistory.objects.filter(
            signal_generation_time__gte=cutoff,
            strength__gte=min_strength,
            is_active=True
        )
        
        if stock:
            query = query.filter(stock=stock)
        
        if signal_type:
            query = query.filter(signal_type=signal_type)
        
        return list(query)
    
    @classmethod
    def get_signal_performance(
        cls,
        signal_type: Optional[str] = None,
        days: int = 7,
        min_strength: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate signal performance metrics.
        
        Args:
            signal_type: Filter by signal type (optional)
            days: Days to analyze
            min_strength: Minimum signal strength to include
        
        Returns:
            Performance statistics dictionary
        """
        cutoff = timezone.now() - timedelta(days=days)
        
        query = SignalHistory.objects.filter(
            signal_generation_time__gte=cutoff,
            strength__gte=min_strength,
            was_profitable__isnull=False,
            is_active=True
        )
        
        if signal_type:
            query = query.filter(signal_type=signal_type)
        
        total = query.count()
        
        if total == 0:
            return {
                'total_signals': 0,
                'profitable_signals': 0,
                'win_rate': 0.0,
                'avg_strength': 0.0,
                'avg_roi': 0.0,
            }
        
        profitable = query.filter(was_profitable=True).count()
        
        # Aggregate stats
        stats = query.aggregate(
            avg_strength=__import__('django.db.models', fromlist=['Avg']).Avg('strength'),
            avg_roi=__import__('django.db.models', fromlist=['Avg']).Avg('roi_percent'),
        )
        
        return {
            'total_signals': total,
            'profitable_signals': profitable,
            'win_rate': (profitable / total * 100) if total > 0 else 0,
            'avg_strength': stats['avg_strength'] or 0.0,
            'avg_roi': stats['avg_roi'] or 0.0,
            'period_days': days,
        }
    
    @classmethod
    @service_transaction
    def update_signal_performance(
        cls,
        signal_id: str,
        current_price: float,
        high_price: float,
        low_price: float
    ):
        """
        Update signal performance metrics based on price movement.
        
        Args:
            signal_id: Signal UUID
            current_price: Current price
            high_price: High price since signal
            low_price: Low price since signal
        """
        try:
            signal = SignalHistory.objects.get(signal_id=signal_id)
            
            # Store price points
            signal.high_price_post_signal = high_price
            signal.low_price_post_signal = low_price
            
            # Calculate performance based on direction
            entry_price = float(signal.price)
            
            if signal.direction == 'buy':
                # For buy signals, check if we're profitable at high
                pnl = (high_price - entry_price) / entry_price * 100
            else:  # sell
                # For sell signals, check if we're profitable at low
                pnl = (entry_price - low_price) / entry_price * 100
            
            signal.profit_loss_percent = pnl
            signal.roi_percent = pnl * (1 / max(0.001, signal.strength))
            signal.was_profitable = pnl > 0
            
            signal.save()
            
            logger.debug(f"Updated performance for signal {signal_id}: PnL={pnl:.2f}%")
            
        except SignalHistory.DoesNotExist:
            logger.warning(f"Signal not found: {signal_id}")
    
    @classmethod
    @service_transaction
    def mark_signal_notified(cls, signal_id: str, user_ids: List[str]):
        """
        Mark signal as notified to users.
        
        Args:
            signal_id: Signal UUID
            user_ids: List of user IDs
        """
        try:
            signal = SignalHistory.objects.get(signal_id=signal_id)
            signal.mark_notified(user_ids)
            logger.info(f"Signal {signal_id} notified to {len(user_ids)} users")
        except SignalHistory.DoesNotExist:
            logger.warning(f"Signal not found: {signal_id}")
    
    @classmethod
    def soft_delete_signals_before(cls, days: int = 90):
        """
        Soft-delete signals older than specified days.
        
        Args:
            days: Signals older than this many days will be deleted
        """
        cutoff = timezone.now() - timedelta(days=days)
        count = cls.soft_delete_bulk(
            filters={'signal_generation_time__lt': cutoff}
        )
        logger.info(f"Soft-deleted {count} signals older than {days} days")
        return count


class SignalPerformanceService(BaseService):
    """
    Signal performance aggregation service.
    
    Updates performance statistics periodically.
    """
    
    model = SignalPerformance
    
    @classmethod
    @service_transaction
    def aggregate_daily_performance(cls):
        """
        Aggregate daily signal performance statistics.
        Used by Celery periodic task.
        """
        from datetime import date
        
        today = timezone.now().date()
        period_start = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )
        period_end = timezone.make_aware(
            datetime.combine(today + timedelta(days=1), datetime.min.time())
        )
        
        signal_types = ['rsi', 'macd', 'breakout', 'volume_spike']
        directions = ['buy', 'sell', 'all']
        
        for signal_type in signal_types:
            for direction in directions:
                stats = SignalHistory.calculate_performance_stats(
                    signal_type=signal_type if direction != 'all' else None,
                    direction=None if direction == 'all' else direction,
                    period_start=period_start,
                    period_end=period_end
                )
                
                if stats:
                    SignalPerformance.objects.update_or_create(
                        signal_type=signal_type,
                        direction=direction,
                        period='daily',
                        period_start=period_start,
                        defaults=stats
                    )
        
        logger.info(f"Aggregated daily signal performance for {today}")
    
    @classmethod
    def get_leaderboard(cls, period: str = 'all_time', top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing signal types.
        
        Args:
            period: Performance period
            top_n: Number of top performers
        
        Returns:
            List of performance records
        """
        query = SignalPerformance.objects.filter(
            period=period,
            direction='all'
        ).order_by('-win_rate', '-avg_roi')[:top_n]
        
        return [
            {
                'signal_type': p.signal_type,
                'win_rate': p.win_rate,
                'avg_roi': p.avg_roi,
                'total_signals': p.total_signals,
                'profitable_signals': p.profitable_signals,
            }
            for p in query
        ]
