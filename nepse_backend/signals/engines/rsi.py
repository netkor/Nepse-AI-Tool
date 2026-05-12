"""
RSI (Relative Strength Index) Signal Engine

Implements the Relative Strength Index technical indicator.
Identifies overbought (>70) and oversold (<30) conditions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .base import BaseSignal, SignalType, SignalDirection, SignalResult

logger = logging.getLogger(__name__)


class RSISignal(BaseSignal):
    """
    RSI (Relative Strength Index) signal engine.
    
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss
    
    Signals:
        - BUY: RSI crosses above 30 (oversold) or touches oversold level
        - SELL: RSI crosses below 70 (overbought) or touches overbought level
        - NEUTRAL: RSI in neutral zone (30-70)
    
    Example:
        engine = RSISignal(lookback_period=14, oversold=30, overbought=70)
        result = engine.generate(historical_data)
        if result:
            print(f"Signal: {result.direction} at {result.price}")
    """
    
    signal_type = SignalType.RSI
    
    def __init__(
        self,
        lookback_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        confidence_threshold: float = 0.5,
        cooldown_minutes: int = 60
    ):
        """
        Initialize RSI signal engine.
        
        Args:
            lookback_period: Period for RSI calculation (default 14)
            oversold: RSI level considered oversold (default 30)
            overbought: RSI level considered overbought (default 70)
            confidence_threshold: Minimum strength (0.0-1.0)
            cooldown_minutes: Minutes between signals
        """
        super().__init__(
            lookback_period=lookback_period,
            confidence_threshold=confidence_threshold,
            cooldown_minutes=cooldown_minutes
        )
        self.oversold = oversold
        self.overbought = overbought
        
        if not (0 < oversold < overbought < 100):
            raise ValueError(
                f"Invalid RSI levels: oversold={oversold}, overbought={overbought}"
            )
    
    def calculate(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate RSI indicator.
        
        Args:
            data: List of OHLCV candles
        
        Returns:
            RSI value (0-100)
        """
        self.validate_data(data)
        
        # Get recent data
        prices = [candle['close'] for candle in self.get_recent_data(data, self.lookback_period)]
        
        if len(prices) < 2:
            return 50.0  # Neutral
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        # Calculate average gain and loss
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        # Calculate RS and RSI
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        
        rs = avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    def generate(self, historical_data: List[Dict[str, Any]]) -> Optional[SignalResult]:
        """
        Generate RSI signal.
        
        Args:
            historical_data: List of OHLCV candles
        
        Returns:
            SignalResult if signal generated, None otherwise
        """
        try:
            self.validate_data(historical_data)
            
            if not self._can_generate_signal():
                return None
            
            # Calculate RSI
            rsi = self.calculate(historical_data)
            
            # Get current price
            current_candle = historical_data[-1]
            current_price = current_candle['close']
            current_time = datetime.fromisoformat(current_candle['timestamp'])
            
            # Get previous RSI for divergence detection
            if len(historical_data) >= self.lookback_period + 1:
                prev_rsi = self.calculate(historical_data[:-1])
            else:
                prev_rsi = rsi
            
            # Determine signal
            direction = SignalDirection.NEUTRAL
            message = f"RSI at {rsi:.2f} - Neutral zone"
            
            if rsi <= self.oversold:
                # Oversold - BUY signal
                direction = SignalDirection.BUY
                strength = self._calculate_strength(
                    rsi, min_val=0, max_val=self.oversold
                )
                strength = 1.0 - strength  # Invert: lower RSI = stronger signal
                message = f"RSI at {rsi:.2f} - Oversold, potential bounce"
                
            elif rsi >= self.overbought:
                # Overbought - SELL signal
                direction = SignalDirection.SELL
                strength = self._calculate_strength(
                    rsi, min_val=self.overbought, max_val=100
                )
                message = f"RSI at {rsi:.2f} - Overbought, potential pullback"
                
            elif self.oversold < rsi < self.overbought:
                # Neutral zone
                strength = 0.5
            
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
                    'oversold_threshold': self.oversold,
                    'overbought_threshold': self.overbought,
                    'divergence': abs(rsi - prev_rsi) > 10,  # RSI divergence
                },
                indicators={
                    'rsi': rsi,
                    'previous_rsi': prev_rsi,
                }
            )
            
            self.log_signal(result)
            return result
            
        except Exception as e:
            logger.error(f"Error generating RSI signal: {str(e)}")
            return None
