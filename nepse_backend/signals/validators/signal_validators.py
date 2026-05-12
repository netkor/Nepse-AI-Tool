"""
Signal Validators

Validation logic for signal input data and parameters.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalValidator:
    """
    Validates signal input data and parameters.
    """
    
    @staticmethod
    def validate_ohlcv_data(data: List[Dict[str, Any]]) -> bool:
        """
        Validate OHLCV candle data format.
        
        Args:
            data: List of OHLCV candles
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("OHLCV data cannot be empty")
        
        if not isinstance(data, list):
            raise ValueError("OHLCV data must be a list")
        
        required_fields = {'open', 'high', 'low', 'close', 'volume', 'timestamp'}
        
        for i, candle in enumerate(data):
            if not isinstance(candle, dict):
                raise ValueError(f"Candle {i} must be a dictionary")
            
            missing_fields = required_fields - set(candle.keys())
            if missing_fields:
                raise ValueError(
                    f"Candle {i} missing required fields: {missing_fields}"
                )
            
            # Validate numeric fields
            for field in ['open', 'high', 'low', 'close', 'volume']:
                try:
                    value = float(candle[field])
                    if value < 0:
                        raise ValueError(f"Field '{field}' cannot be negative")
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Candle {i}: '{field}' must be a valid number"
                    )
            
            # Validate OHLC relationship
            o, h, l, c = (
                float(candle['open']),
                float(candle['high']),
                float(candle['low']),
                float(candle['close'])
            )
            
            if not (l <= o <= h and l <= c <= h):
                raise ValueError(
                    f"Candle {i}: Invalid OHLC relationship "
                    f"(O:{o}, H:{h}, L:{l}, C:{c})"
                )
            
            # Validate timestamp
            try:
                if isinstance(candle['timestamp'], str):
                    datetime.fromisoformat(candle['timestamp'])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Candle {i}: Invalid timestamp format"
                )
        
        return True
    
    @staticmethod
    def validate_signal_parameters(signal_type: str, params: Dict[str, Any]) -> bool:
        """
        Validate signal engine parameters.
        
        Args:
            signal_type: Type of signal
            params: Engine parameters
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If parameters are invalid
        """
        # Common parameters
        if 'lookback_period' in params:
            lp = params['lookback_period']
            if not isinstance(lp, int) or lp < 1:
                raise ValueError("lookback_period must be positive integer")
        
        if 'confidence_threshold' in params:
            ct = params['confidence_threshold']
            if not isinstance(ct, (int, float)) or not (0 <= ct <= 1):
                raise ValueError("confidence_threshold must be between 0 and 1")
        
        if 'cooldown_minutes' in params:
            cm = params['cooldown_minutes']
            if not isinstance(cm, int) or cm < 0:
                raise ValueError("cooldown_minutes must be non-negative integer")
        
        # RSI-specific
        if signal_type == 'rsi':
            if 'oversold' in params:
                os = params['oversold']
                if not isinstance(os, (int, float)) or not (0 < os < 100):
                    raise ValueError("oversold must be between 0 and 100")
            
            if 'overbought' in params:
                ob = params['overbought']
                if not isinstance(ob, (int, float)) or not (0 < ob < 100):
                    raise ValueError("overbought must be between 0 and 100")
            
            # Check oversold < overbought
            if 'oversold' in params and 'overbought' in params:
                if params['oversold'] >= params['overbought']:
                    raise ValueError("oversold must be less than overbought")
        
        # MACD-specific
        if signal_type == 'macd':
            if 'fast_period' in params:
                fp = params['fast_period']
                if not isinstance(fp, int) or fp < 1:
                    raise ValueError("fast_period must be positive integer")
            
            if 'slow_period' in params:
                sp = params['slow_period']
                if not isinstance(sp, int) or sp < 1:
                    raise ValueError("slow_period must be positive integer")
            
            if 'signal_period' in params:
                sig = params['signal_period']
                if not isinstance(sig, int) or sig < 1:
                    raise ValueError("signal_period must be positive integer")
            
            # Check fast < slow
            if 'fast_period' in params and 'slow_period' in params:
                if params['fast_period'] >= params['slow_period']:
                    raise ValueError("fast_period must be less than slow_period")
        
        # Breakout-specific
        if signal_type == 'breakout':
            if 'confirmation_candles' in params:
                cc = params['confirmation_candles']
                if not isinstance(cc, int) or cc < 1:
                    raise ValueError("confirmation_candles must be positive integer")
            
            if 'volume_confirmation' in params:
                vc = params['volume_confirmation']
                if not isinstance(vc, bool):
                    raise ValueError("volume_confirmation must be boolean")
        
        # Volume Spike-specific
        if signal_type == 'volume_spike':
            if 'spike_threshold' in params:
                st = params['spike_threshold']
                if not isinstance(st, (int, float)) or st <= 1:
                    raise ValueError("spike_threshold must be greater than 1")
            
            if 'price_change_threshold' in params:
                pct = params['price_change_threshold']
                if not isinstance(pct, (int, float)) or pct < 0:
                    raise ValueError("price_change_threshold must be non-negative")
        
        return True
    
    @staticmethod
    def validate_signal_type(signal_type: str) -> bool:
        """
        Validate signal type is recognized.
        
        Args:
            signal_type: Signal type to validate
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If signal type is unknown
        """
        valid_types = {'rsi', 'macd', 'breakout', 'volume_spike'}
        
        if signal_type not in valid_types:
            raise ValueError(
                f"Invalid signal type '{signal_type}'. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        return True
    
    @staticmethod
    def validate_historical_data_length(data: List[Dict[str, Any]], min_length: int = 20) -> bool:
        """
        Validate historical data has sufficient length.
        
        Args:
            data: Historical data
            min_length: Minimum required length
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If data is too short
        """
        if len(data) < min_length:
            raise ValueError(
                f"Insufficient historical data. "
                f"Need at least {min_length} candles, got {len(data)}"
            )
        
        return True


class SignalResultValidator:
    """
    Validates generated signal results.
    """
    
    @staticmethod
    def validate_signal_result(result: Any) -> bool:
        """
        Validate signal result object.
        
        Args:
            result: Signal result object
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If result is invalid
        """
        # Check required attributes
        required_attrs = [
            'signal_type',
            'direction',
            'strength',
            'price',
            'timestamp',
            'message',
        ]
        
        for attr in required_attrs:
            if not hasattr(result, attr):
                raise ValueError(f"Signal result missing required attribute: {attr}")
        
        # Validate strength
        if not (0.0 <= result.strength <= 1.0):
            raise ValueError(
                f"Signal strength must be between 0.0 and 1.0, got {result.strength}"
            )
        
        # Validate price
        if result.price <= 0:
            raise ValueError(f"Signal price must be positive, got {result.price}")
        
        # Validate timestamp
        if not isinstance(result.timestamp, datetime):
            raise ValueError(f"Signal timestamp must be datetime object")
        
        # Validate message is string
        if not isinstance(result.message, str):
            raise ValueError(f"Signal message must be string")
        
        return True
