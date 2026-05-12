"""
Base Signal Engine

Abstract base class for all signal generation engines.
Defines interface, common methods, and result structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Signal type enumeration."""
    RSI = "rsi"
    MACD = "macd"
    BREAKOUT = "breakout"
    VOLUME_SPIKE = "volume_spike"
    
    def __str__(self):
        return self.value


class SignalStrength(Enum):
    """Signal strength/confidence levels."""
    VERY_WEAK = 0.2
    WEAK = 0.4
    MODERATE = 0.6
    STRONG = 0.8
    VERY_STRONG = 1.0
    
    def __str__(self):
        return self.name.lower()


class SignalDirection(Enum):
    """Signal direction: buy or sell."""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    
    def __str__(self):
        return self.value


@dataclass
class SignalResult:
    """
    Result of signal generation.
    
    Attributes:
        signal_type: Type of signal (RSI, MACD, etc.)
        direction: Buy, sell, or neutral
        strength: Confidence level (0.0-1.0)
        price: Price at signal generation
        timestamp: When signal was generated
        message: Human-readable signal description
        metadata: Additional signal-specific data
        indicators: Technical indicator values used
    """
    signal_type: SignalType
    direction: SignalDirection
    strength: float  # 0.0 to 1.0
    price: float
    timestamp: datetime
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    indicators: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate strength is between 0.0 and 1.0."""
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"Strength must be between 0.0 and 1.0, got {self.strength}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'signal_type': str(self.signal_type),
            'direction': str(self.direction),
            'strength': self.strength,
            'price': float(self.price),
            'timestamp': self.timestamp.isoformat(),
            'message': self.message,
            'metadata': self.metadata,
            'indicators': self.indicators,
        }


class BaseSignal(ABC):
    """
    Abstract base class for signal engines.
    
    Each concrete signal engine (RSI, MACD, etc.) extends this class
    and implements the required methods.
    
    Example:
        class RSISignal(BaseSignal):
            signal_type = SignalType.RSI
            
            def calculate(self, data):
                # Calculate RSI
                rsi = compute_rsi(data)
                return rsi
            
            def generate(self, historical_data):
                rsi = self.calculate(historical_data)
                strength = self._calculate_strength(rsi)
                # Return SignalResult
    """
    
    signal_type: SignalType = None
    
    def __init__(
        self,
        lookback_period: int = 14,
        confidence_threshold: float = 0.5,
        cooldown_minutes: int = 0
    ):
        """
        Initialize signal engine.
        
        Args:
            lookback_period: Number of candles to analyze
            confidence_threshold: Minimum strength to generate signal (0.0-1.0)
            cooldown_minutes: Minutes to wait before next signal of same type
        """
        self.lookback_period = lookback_period
        self.confidence_threshold = confidence_threshold
        self.cooldown_minutes = cooldown_minutes
        self.last_signal_time: Optional[datetime] = None
        
        if not self.signal_type:
            raise ValueError(f"{self.__class__.__name__} must define signal_type")
    
    @abstractmethod
    def calculate(self, data: List[Dict[str, Any]]) -> Any:
        """
        Calculate technical indicator.
        
        Args:
            data: List of OHLCV candles (open, high, low, close, volume)
        
        Returns:
            Calculated indicator value(s)
        """
        pass
    
    @abstractmethod
    def generate(self, historical_data: List[Dict[str, Any]]) -> Optional[SignalResult]:
        """
        Generate signal from historical data.
        
        Args:
            historical_data: List of OHLCV candles
        
        Returns:
            SignalResult if signal generated, None otherwise
        """
        pass
    
    def _calculate_strength(self, value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
        """
        Calculate signal strength (0.0-1.0) from a value.
        
        Args:
            value: Raw indicator value
            min_val: Minimum possible value
            max_val: Maximum possible value
        
        Returns:
            Strength between 0.0 and 1.0
        """
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def _normalize_strength(self, strength: float) -> float:
        """
        Normalize strength to ensure it's between 0.0 and 1.0.
        
        Args:
            strength: Strength value
        
        Returns:
            Normalized strength
        """
        return max(0.0, min(1.0, strength))
    
    def _meets_confidence_threshold(self, strength: float) -> bool:
        """
        Check if signal meets confidence threshold.
        
        Args:
            strength: Signal strength
        
        Returns:
            True if strength >= threshold
        """
        return strength >= self.confidence_threshold
    
    def _can_generate_signal(self) -> bool:
        """
        Check if enough time has passed since last signal (cooldown).
        
        Returns:
            True if signal can be generated
        """
        if self.cooldown_minutes <= 0:
            return True
        
        if self.last_signal_time is None:
            return True
        
        from datetime import timedelta
        time_since_last = datetime.now() - self.last_signal_time
        cooldown_delta = timedelta(minutes=self.cooldown_minutes)
        
        return time_since_last >= cooldown_delta
    
    def _record_signal_time(self):
        """Record the time of current signal for cooldown tracking."""
        self.last_signal_time = datetime.now()
    
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validate input data is sufficient.
        
        Args:
            data: Historical data
        
        Returns:
            True if data is valid
        
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Historical data cannot be empty")
        
        if len(data) < self.lookback_period:
            raise ValueError(
                f"Insufficient data. Need {self.lookback_period} candles, got {len(data)}"
            )
        
        # Check all entries have required fields
        required_fields = {'open', 'high', 'low', 'close', 'volume', 'timestamp'}
        for i, candle in enumerate(data):
            missing_fields = required_fields - set(candle.keys())
            if missing_fields:
                raise ValueError(
                    f"Candle {i} missing fields: {missing_fields}"
                )
        
        return True
    
    def get_recent_data(self, data: List[Dict[str, Any]], periods: int) -> List[Dict[str, Any]]:
        """
        Get the most recent N periods of data.
        
        Args:
            data: Historical data
            periods: Number of periods
        
        Returns:
            Most recent periods
        """
        return data[-periods:] if len(data) > periods else data
    
    def log_signal(self, result: SignalResult):
        """
        Log signal generation.
        
        Args:
            result: Signal result
        """
        logger.info(
            f"Signal generated: {self.signal_type} - {result.direction} - "
            f"Strength: {result.strength:.2f} - Price: {result.price}"
        )
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"type={self.signal_type}, "
            f"lookback={self.lookback_period}, "
            f"threshold={self.confidence_threshold}"
            f")"
        )
