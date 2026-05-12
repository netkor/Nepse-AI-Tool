"""
Technical indicator calculations for signal generation.
"""
import pandas as pd
import numpy as np
from decimal import Decimal


def calculate_sma(prices: list, period: int) -> float:
    """
    Calculate Simple Moving Average.
    
    Args:
        prices: List of prices (most recent last)
        period: Period for MA calculation
    
    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def calculate_ema(prices: list, period: int) -> float:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: List of prices
        period: Period for EMA calculation
    
    Returns:
        EMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    
    prices_arr = np.array([float(p) for p in prices])
    ema = prices_arr[-period:].mean()
    multiplier = 2 / (period + 1)
    
    for price in prices_arr[-period+1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return float(ema)


def calculate_rsi(prices: list, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: List of prices
        period: Period for RSI calculation (default 14)
    
    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    
    prices_arr = np.array([float(p) for p in prices])
    deltas = np.diff(prices_arr)
    
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    
    rs = up / down if down != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    
    for delta in deltas[period+1:]:
        up = (up * (period - 1) + (delta if delta > 0 else 0)) / period
        down = (down * (period - 1) + (-delta if delta < 0 else 0)) / period
        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)


def detect_ma_crossover(prices: list, fast_period: int = 5, slow_period: int = 20) -> dict:
    """
    Detect moving average crossover signals.
    
    Returns:
        {
            'signal': 'BUY' | 'SELL' | None,
            'fast_ma': float,
            'slow_ma': float,
            'confidence': 0-100
        }
    """
    result = {
        'signal': None,
        'fast_ma': None,
        'slow_ma': None,
        'confidence': 0
    }
    
    if len(prices) < slow_period + 1:
        return result
    
    # Current MAs
    fast_ma_current = calculate_sma(prices, fast_period)
    slow_ma_current = calculate_sma(prices, slow_period)
    
    # Previous MAs
    fast_ma_prev = calculate_sma(prices[:-1], fast_period)
    slow_ma_prev = calculate_sma(prices[:-1], slow_period)
    
    if None in [fast_ma_current, slow_ma_current, fast_ma_prev, slow_ma_prev]:
        return result
    
    result['fast_ma'] = fast_ma_current
    result['slow_ma'] = slow_ma_current
    
    # Check for crossover
    if fast_ma_prev <= slow_ma_prev and fast_ma_current > slow_ma_current:
        result['signal'] = 'BUY'
        result['confidence'] = 75
    elif fast_ma_prev >= slow_ma_prev and fast_ma_current < slow_ma_current:
        result['signal'] = 'SELL'
        result['confidence'] = 75
    
    return result


def detect_volume_spike(volumes: list, threshold: float = 2.0) -> dict:
    """
    Detect volume spike signals.
    
    Args:
        volumes: List of volumes (most recent last)
        threshold: Multiplier for average volume (default 2.0)
    
    Returns:
        {
            'signal': True/False,
            'current_volume': int,
            'average_volume': float,
            'spike_ratio': float,
            'confidence': 0-100
        }
    """
    result = {
        'signal': False,
        'current_volume': 0,
        'average_volume': 0,
        'spike_ratio': 0,
        'confidence': 0
    }
    
    if len(volumes) < 10:
        return result
    
    current_volume = int(volumes[-1])
    avg_volume = float(np.mean(volumes[-10:-1]))  # Average of last 9 days
    
    result['current_volume'] = current_volume
    result['average_volume'] = avg_volume
    
    if avg_volume > 0:
        spike_ratio = current_volume / avg_volume
        result['spike_ratio'] = spike_ratio
        
        if spike_ratio >= threshold:
            result['signal'] = True
            result['confidence'] = min(int((spike_ratio / threshold) * 60), 85)
    
    return result


def detect_rsi_extremes(prices: list, overbought: int = 70, oversold: int = 30) -> dict:
    """
    Detect RSI extreme signals.
    
    Returns:
        {
            'signal': 'BUY' | 'SELL' | None,
            'rsi_value': float,
            'confidence': 0-100
        }
    """
    result = {
        'signal': None,
        'rsi_value': None,
        'confidence': 0
    }
    
    rsi = calculate_rsi(prices)
    if rsi is None:
        return result
    
    result['rsi_value'] = rsi
    
    if rsi >= overbought:
        result['signal'] = 'SELL'
        result['confidence'] = min(int((rsi - overbought) * 2), 70)
    elif rsi <= oversold:
        result['signal'] = 'BUY'
        result['confidence'] = min(int((oversold - rsi) * 2), 70)
    
    return result
