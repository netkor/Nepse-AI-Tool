"""
MACD (Moving Average Convergence Divergence) Signal Engine

Implements the MACD technical indicator.
Identifies trend changes through moving average crossovers.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from .base import BaseSignal, SignalType, SignalDirection, SignalResult

logger = logging.getLogger(__name__)


class MACDSignal(BaseSignal):
    """
    MACD (Moving Average Convergence Divergence) signal engine.
    
    MACD = 12-period EMA - 26-period EMA
    Signal Line = 9-period EMA of MACD
    Histogram = MACD - Signal Line
    
    Signals:
        - BUY: MACD crosses above signal line (bullish crossover)
        - SELL: MACD crosses below signal line (bearish crossover)
        - NEUTRAL: MACD and signal line in alignment
    
    Example:
        engine = MACDSignal(fast=12, slow=26, signal=9)
        result = engine.generate(historical_data)
    """
    
    signal_type = SignalType.MACD
    
    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        confidence_threshold: float = 0.5,
        cooldown_minutes: int = 60
    ):
        """
        Initialize MACD signal engine.
        
        Args:
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line EMA period (default 9)
            confidence_threshold: Minimum strength (0.0-1.0)
            cooldown_minutes: Minutes between signals
        """
        super().__init__(
            lookback_period=slow_period + signal_period - 1,
            confidence_threshold=confidence_threshold,
            cooldown_minutes=cooldown_minutes
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        if not (fast_period < slow_period):
            raise ValueError(
                f"Fast period ({fast_period}) must be less than "
                f"slow period ({slow_period})"
            )
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average.
        
        Args:
            data: Price data
            period: EMA period
        
        Returns:
            List of EMA values
        """
        if len(data) < period:
            return []
        
        ema_values = []
        multiplier = 2.0 / (period + 1)
        
        # Calculate first SMA
        sma = sum(data[:period]) / period
        ema_values.append(sma)
        
        # Calculate subsequent EMAs
        for i in range(period, len(data)):
            ema = (data[i] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)
        
        return ema_values
    
    def calculate(self, data: List[Dict[str, Any]]) -> Tuple[float, float, float]:
        """
        Calculate MACD indicator.
        
        Args:
            data: List of OHLCV candles
        
        Returns:
            Tuple of (MACD, Signal Line, Histogram)
        """
        self.validate_data(data)
        
        # Get closing prices
        prices = [candle['close'] for candle in data]
        
        # Calculate fast and slow EMAs
        fast_ema = self._calculate_ema(prices, self.fast_period)
        slow_ema = self._calculate_ema(prices, self.slow_period)
        
        # Align to the shorter length
        min_len = min(len(fast_ema), len(slow_ema))
        fast_ema = fast_ema[-min_len:]
        slow_ema = slow_ema[-min_len:]
        
        if len(fast_ema) == 0 or len(slow_ema) == 0:
            return 0.0, 0.0, 0.0
        
        # Calculate MACD line
        macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
        
        # Calculate signal line (9-period EMA of MACD)
        signal_line = self._calculate_ema(macd_line, self.signal_period)
        
        # Get latest values
        current_macd = macd_line[-1] if macd_line else 0.0
        current_signal = signal_line[-1] if signal_line else 0.0
        histogram = current_macd - current_signal
        
        return current_macd, current_signal, histogram
    
    def generate(self, historical_data: List[Dict[str, Any]]) -> Optional[SignalResult]:
        """
        Generate MACD signal.
        
        Args:
            historical_data: List of OHLCV candles
        
        Returns:
            SignalResult if signal generated, None otherwise
        """
        try:
            self.validate_data(historical_data)
            
            if not self._can_generate_signal():
                return None
            
            # Need at least 2 data points to compare for crossover
            if len(historical_data) < self.lookback_period + 2:
                return None
            
            # Calculate current MACD
            current_macd, current_signal, histogram = self.calculate(historical_data)
            
            # Calculate previous MACD for crossover detection
            prev_macd, prev_signal, prev_histogram = self.calculate(historical_data[:-1])
            
            # Get current price
            current_candle = historical_data[-1]
            current_price = current_candle['close']
            current_time = datetime.fromisoformat(current_candle['timestamp'])
            
            # Detect crossover
            direction = SignalDirection.NEUTRAL
            message = "MACD - No crossover"
            strength = 0.5
            
            # Bullish crossover: MACD crosses above signal line
            if prev_macd <= prev_signal and current_macd > current_signal:
                direction = SignalDirection.BUY
                strength = min(1.0, abs(histogram) / abs(current_price) * 100)  # Normalize
                message = f"MACD bullish crossover - MACD: {current_macd:.6f}, Signal: {current_signal:.6f}"
                
            # Bearish crossover: MACD crosses below signal line
            elif prev_macd >= prev_signal and current_macd < current_signal:
                direction = SignalDirection.SELL
                strength = min(1.0, abs(histogram) / abs(current_price) * 100)  # Normalize
                message = f"MACD bearish crossover - MACD: {current_macd:.6f}, Signal: {current_signal:.6f}"
            
            # Divergence detection: MACD and signal have same sign but growing apart
            elif (current_macd > 0 and current_signal > 0 and
                  current_macd > current_signal and current_macd > prev_macd):
                direction = SignalDirection.BUY
                strength = 0.6
                message = f"MACD bullish divergence - Histogram: {histogram:.6f}"
            elif (current_macd < 0 and current_signal < 0 and
                  current_macd < current_signal and current_macd < prev_macd):
                direction = SignalDirection.SELL
                strength = 0.6
                message = f"MACD bearish divergence - Histogram: {histogram:.6f}"
            
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
                    'histogram_positive': histogram > 0,
                    'histogram_growing': histogram > prev_histogram,
                },
                indicators={
                    'macd': current_macd,
                    'signal_line': current_signal,
                    'histogram': histogram,
                    'previous_histogram': prev_histogram,
                }
            )
            
            self.log_signal(result)
            return result
            
        except Exception as e:
            logger.error(f"Error generating MACD signal: {str(e)}")
            return None
