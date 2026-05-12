"""
Breakout Signal Engine

Implements support/resistance breakout detection.
Identifies price breaks through key levels.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base import BaseSignal, SignalType, SignalDirection, SignalResult

logger = logging.getLogger(__name__)


class BreakoutSignal(BaseSignal):
    """
    Breakout signal engine.
    
    Detects when price breaks above resistance (support breakout = BUY)
    or below support (resistance breakout = SELL).
    
    Signals:
        - BUY: Price breaks above resistance level
        - SELL: Price breaks below support level
        - NEUTRAL: Price within support/resistance range
    
    Example:
        engine = BreakoutSignal(lookback_period=20, confirmation_candles=1)
        result = engine.generate(historical_data)
    """
    
    signal_type = SignalType.BREAKOUT
    
    def __init__(
        self,
        lookback_period: int = 20,
        confirmation_candles: int = 1,
        volume_confirmation: bool = True,
        confidence_threshold: float = 0.6,
        cooldown_minutes: int = 120
    ):
        """
        Initialize Breakout signal engine.
        
        Args:
            lookback_period: Candles to analyze for support/resistance
            confirmation_candles: Candles needed to confirm breakout
            volume_confirmation: Require high volume for confirmation
            confidence_threshold: Minimum strength (0.0-1.0)
            cooldown_minutes: Minutes between signals
        """
        super().__init__(
            lookback_period=lookback_period,
            confidence_threshold=confidence_threshold,
            cooldown_minutes=cooldown_minutes
        )
        self.confirmation_candles = confirmation_candles
        self.volume_confirmation = volume_confirmation
    
    def _find_support_resistance(self, data: List[Dict[str, Any]]) -> tuple:
        """
        Find support and resistance levels.
        
        Args:
            data: OHLCV candles
        
        Returns:
            Tuple of (support, resistance)
        """
        recent = self.get_recent_data(data, self.lookback_period)
        
        # Find extreme points
        lows = [candle['low'] for candle in recent]
        highs = [candle['high'] for candle in recent]
        
        support = min(lows)
        resistance = max(highs)
        
        return support, resistance
    
    def _get_average_volume(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate average volume over lookback period.
        
        Args:
            data: OHLCV candles
        
        Returns:
            Average volume
        """
        recent = self.get_recent_data(data, self.lookback_period)
        volumes = [candle['volume'] for candle in recent]
        
        if not volumes:
            return 0.0
        
        return sum(volumes) / len(volumes)
    
    def calculate(self, data: List[Dict[str, Any]]) -> tuple:
        """
        Calculate support and resistance levels.
        
        Args:
            data: OHLCV candles
        
        Returns:
            Tuple of (support, resistance)
        """
        self.validate_data(data)
        return self._find_support_resistance(data)
    
    def generate(self, historical_data: List[Dict[str, Any]]) -> Optional[SignalResult]:
        """
        Generate breakout signal.
        
        Args:
            historical_data: List of OHLCV candles
        
        Returns:
            SignalResult if signal generated, None otherwise
        """
        try:
            self.validate_data(historical_data)
            
            if not self._can_generate_signal():
                return None
            
            # Need enough data to confirm
            if len(historical_data) < self.lookback_period + self.confirmation_candles:
                return None
            
            # Get support and resistance
            support, resistance = self.calculate(historical_data)
            
            # Current candle
            current_candle = historical_data[-1]
            current_price = current_candle['close']
            current_high = current_candle['high']
            current_low = current_candle['low']
            current_volume = current_candle['volume']
            current_time = datetime.fromisoformat(current_candle['timestamp'])
            
            # Average volume
            avg_volume = self._get_average_volume(historical_data)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Previous candle
            prev_candle = historical_data[-2] if len(historical_data) > 1 else current_candle
            prev_close = prev_candle['close']
            
            direction = SignalDirection.NEUTRAL
            message = f"Support: {support:.2f}, Resistance: {resistance:.2f} - No breakout"
            strength = 0.5
            
            # Resistance breakout (BUY signal)
            if current_price > resistance and prev_close <= resistance:
                direction = SignalDirection.BUY
                breakout_distance = current_price - resistance
                strength = min(1.0, (breakout_distance / resistance) * 10)  # Normalize
                
                # Volume confirmation
                if self.volume_confirmation and volume_ratio < 1.2:
                    strength *= 0.7  # Lower strength if volume not confirmed
                
                message = f"Resistance breakout at {current_price:.2f} (above {resistance:.2f})"
                
            # Support breakout (SELL signal)
            elif current_price < support and prev_close >= support:
                direction = SignalDirection.SELL
                breakout_distance = support - current_price
                strength = min(1.0, (breakout_distance / support) * 10)  # Normalize
                
                # Volume confirmation
                if self.volume_confirmation and volume_ratio < 1.2:
                    strength *= 0.7  # Lower strength if volume not confirmed
                
                message = f"Support breakout at {current_price:.2f} (below {support:.2f})"
            
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
                price=float(current_price),
                timestamp=current_time,
                message=message,
                metadata={
                    'volume_ratio': volume_ratio,
                    'volume_confirmed': volume_ratio >= 1.2,
                    'breakout_percentage': abs(current_price - resistance if current_price > resistance else current_price - support) / min(resistance, support) * 100,
                },
                indicators={
                    'support': support,
                    'resistance': resistance,
                    'current_price': current_price,
                    'distance_to_support': current_price - support,
                    'distance_to_resistance': resistance - current_price,
                }
            )
            
            self.log_signal(result)
            return result
            
        except Exception as e:
            logger.error(f"Error generating breakout signal: {str(e)}")
            return None
