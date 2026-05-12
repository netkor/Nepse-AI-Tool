"""
Signal Models

Includes signal history and performance tracking models.
"""

import importlib.util
from pathlib import Path

from .history import SignalHistory, SignalPerformance

_legacy_models_path = Path(__file__).resolve().parents[1] / 'models.py'
_legacy_spec = importlib.util.spec_from_file_location('signals.legacy_models', _legacy_models_path)
_legacy_module = importlib.util.module_from_spec(_legacy_spec) if _legacy_spec and _legacy_spec.loader else None

if _legacy_spec and _legacy_spec.loader and _legacy_module is not None:
	_legacy_spec.loader.exec_module(_legacy_module)
	Signal = _legacy_module.Signal
else:
	Signal = None

__all__ = ['Signal', 'SignalHistory', 'SignalPerformance']
