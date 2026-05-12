"""
Volume Spike Signal Engine

Implements unusual volume detection.
Identifies price movements with abnormal volume.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import statistics

from .base import BaseSignal, SignalType, SignalDirection, SignalResult

logger = logging.getLogger(__name__)


class VolumeSpikeSignal(BaseSignal):
    """
    Volume Spike signal engine.
    
    Detects unusual volume movements that often precede price moves.
    
    Signals:
        - BUY: Price up + volume spike (unusual buying pressure)
        - SELL: Price down + volume spike (unusual selling pressure)
        - NEUTRAL: Normal volume or no clear price direction
    
    Example:
        engine = VolumeSpikeSignal(lookback_period=20, spike_threshold=1.5)
        result = engine.generate(historical_data)
    """
    
    signal_type = SignalType.VOLUME_SPIKE
    
    def __init__(
        self,
        lookback_period: int = 20,
        spike_threshold: float = 1.5,
        price_change_threshold: float = 0.5,
        confidence_threshold: float = 0.6,
        cooldown_minutes: int = 90
    ):
        """
        Initialize Volume Spike signal engine.
        
        Args:
            lookback_period: Candles to analyze for volume baseline
            spike_threshold: Volume multiplier to trigger signal (e.g., 1.5 = 50% above average)
            price_change_threshold: Minimum % price change to confirm
            confidence_threshold: Minimum strength (0.0-1.0)
            cooldown_minutes: Minutes between signals
        """
        super().__init__(
            lookback_period=lookback_period,
            confidence_threshold=confidence_threshold,
            cooldown_minutes=cooldown_minutes
        )
        self.spike_threshold = spike_threshold
        self.price_change_threshold = price_change_threshold
    
    def _get_volume_stats(self, data: List[Dict[str, Any]]) -> tuple:
        """
        Calculate volume statistics.
        
        Args:
            data: OHLCV candles
        
        Returns:
            Tuple of (mean, std_dev, median)
        """
        recent = self.get_recent_data(data, self.lookback_period)
        volumes = [candle['volume'] for candle in recent]
        
        if not volumes:
            return 0.0, 0.0, 0.0
        
        mean = statistics.mean(volumes)
        
        if len(volumes) > 1:
            try:
                std_dev = statistics.stdev(volumes)
            except statistics.StatisticsError:
                std_dev = 0.0
        else:
            std_dev = 0.0
        
        median = statistics.median(volumes)
        
        return mean, std_dev, median
    
    def _calculate_price_change_percent(self, open_price: float, close_price: float) -> float:
        """
        Calculate percentage price change.
        
        Args:
            open_price: Opening price
            close_price: Closing price
        
        Returns:
            Percentage change
        """
        if open_price == 0:
            return 0.0
        return ((close_price - open_price) / open_price) * 100
    
    def calculate(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate average volume over lookback period.
        
        Args:
            data: OHLCV candles
        
        Returns:
            Average volume
        """
        self.validate_data(data)
        mean, _, _ = self._get_volume_stats(data)
        return mean
    
    def generate(self, historical_data: List[Dict[str, Any]]) -> Optional[SignalResult]:
        """
        Generate volume spike signal.
        
        Args:
            historical_data: List of OHLCV candles
        
        Returns:
            SignalResult if signal generated, None otherwise
        """
        try:
            self.validate_data(historical_data)
            
            if not self._can_generate_signal():
                return None
            
            # Current candle
            current_candle = historical_data[-1]
            current_volume = current_candle['volume']
            current_open = current_candle['open']
            current_close = current_candle['close']
            current_time = datetime.fromisoformat(current_candle['timestamp'])
            
            # Volume statistics
            avg_volume, std_dev, median_volume = self._get_volume_stats(historical_data)
            
            # Price change
            price_change = self._calculate_price_change_percent(current_open, current_close)
            
            # Check for volume spike
            volume_multiple = current_volume / avg_volume if avg_volume > 0 else 1.0
            is_spike = volume_multiple >= self.spike_threshold
            
            if not is_spike:
                return None
            
            direction = SignalDirection.NEUTRAL
            message = f"Volume: {current_volume} ({volume_multiple:.2f}x avg) - No price confirmation"
            strength = 0.5
            
            # BUY: Price up + volume spike
            if price_change >= self.price_change_threshold:
                direction = SignalDirection.BUY
                # Strength based on volume magnitude and price change
                volume_strength = min(1.0, (volume_multiple - 1.0) / (self.spike_threshold - 1.0) * 0.7)
                price_strength = min(1.0, price_change / 2.0 * 0.3)  # 2% price change = max 0.3
                strength = volume_strength + price_strength
                message = f"Bullish volume spike: {volume_multiple:.2f}x avg, +{price_change:.2f}%"
                
            # SELL: Price down + volume spike
            elif price_change <= -self.price_change_threshold:
                direction = SignalDirection.SELL
                # Strength based on volume magnitude and price change
                volume_strength = min(1.0, (volume_multiple - 1.0) / (self.spike_threshold - 1.0) * 0.7)
                price_strength = min(1.0, abs(price_change) / 2.0 * 0.3)  # 2% price change = max 0.3
                strength = volume_strength + price_strength
                message = f"Bearish volume spike: {volume_multiple:.2f}x avg, {price_change:.2f}%"
            
            # Check confidence threshold
            if not self._meets_confidence_threshold(strength):
                return None
            
            # Record signal time for cooldown
            self._record_signal_time()
            
            # Create result
            result = SignalResult(
                signal_type=self.signal_type,
                direction=direction,
                strength=self._normalize_strength(strength),
                price=float(current_close),
                timestamp=current_time,
                message=message,
                metadata={
                    'volume_multiple': volume_multiple,
                    'price_change_percent': price_change,
                    'above_average': volume_multiple > 1.0,
                    'std_devs_above_mean': (current_volume - avg_volume) / std_dev if std_dev > 0 else 0,
                },
                indicators={
                    'current_volume': current_volume,
                    'average_volume': avg_volume,
                    'median_volume': median_volume,
                    'volume_std_dev': std_dev,
                    'open_price': current_open,
                    'close_price': current_close,
                    'price_range': current_candle.get('high', current_close) - current_candle.get('low', current_open),
                }
            )
            
            self.log_signal(result)
            return result
            
        except Exception as e:
            logger.error(f"Error generating volume spike signal: {str(e)}")
            return None
