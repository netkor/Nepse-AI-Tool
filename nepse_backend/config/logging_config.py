"""
Logging configuration for NEPSE AI Signal & Alert System.

Provides structured logging setup compatible with:
- Development (console output)
- Production (JSON structured logs)
- Celery task logging
- Django request logging

Usage:
    from config.logging_config import setup_logging
    setup_logging()
"""

import logging
import logging.config
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def get_logging_config(debug=True):
    """
    Get logging configuration dict.
    
    Args:
        debug (bool): If True, use verbose console logging. Otherwise, use production format.
    
    Returns:
        dict: Django-compatible logging configuration
    """
    
    # Create logs directory if it doesn't exist
    logs_dir = BASE_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Format strings
    verbose_format = (
        '[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] %(message)s'
    )
    simple_format = (
        '[%(asctime)s] %(levelname)s %(message)s'
    )
    json_format = (
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"logger": "%(name)s", "message": "%(message)s", "lineno": %(lineno)d}'
    )
    
    log_format = verbose_format if debug else json_format
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': verbose_format,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': simple_format,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'json': {
                'format': json_format,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG' if debug else 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose' if debug else 'json',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'app.log',
                'maxBytes': 1024 * 1024 * 10,  # 10 MB
                'backupCount': 5,
                'formatter': 'json',
            },
            'celery_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'celery.log',
                'maxBytes': 1024 * 1024 * 10,  # 10 MB
                'backupCount': 5,
                'formatter': 'json',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'errors.log',
                'maxBytes': 1024 * 1024 * 10,  # 10 MB
                'backupCount': 5,
                'formatter': 'json',
            },
        },
        'loggers': {
            # Django loggers
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            'django.db': {
                'handlers': ['console'],
                'level': 'DEBUG' if debug else 'WARNING',
                'propagate': False,
            },
            
            # Celery loggers
            'celery': {
                'handlers': ['console', 'celery_file'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            'celery.task': {
                'handlers': ['console', 'celery_file'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            
            # App-specific loggers
            'config': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'accounts': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'stocks': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'signals': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'alerts': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }
    
    return config


def setup_logging(debug=True):
    """
    Configure logging for the application.
    
    Args:
        debug (bool): If True, use verbose console logging.
    
    Usage:
        from django.conf import settings
        from config.logging_config import setup_logging
        setup_logging(debug=settings.DEBUG)
    """
    config = get_logging_config(debug=debug)
    logging.config.dictConfig(config)
    
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging configured (debug={debug})")
    return logger
