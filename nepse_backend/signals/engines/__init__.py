"""
Signal Engines Module

Modular signal generation engines for different technical indicators.

Available Engines:
    - RSISignal: Relative Strength Index
    - MACDSignal: Moving Average Convergence Divergence
    - BreakoutSignal: Support/Resistance breakouts
    - VolumeSpikeSignal: Unusual volume movements
"""

from .base import BaseSignal, SignalType, SignalStrength, SignalResult
from .rsi import RSISignal
from .macd import MACDSignal
from .breakout import BreakoutSignal
from .volume_spike import VolumeSpikeSignal

__all__ = [
    'BaseSignal',
    'SignalType',
    'SignalStrength',
    'SignalResult',
    'RSISignal',
    'MACDSignal',
    'BreakoutSignal',
    'VolumeSpikeSignal',
]
