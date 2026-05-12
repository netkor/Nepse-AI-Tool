"""
Exception handling and custom exception classes for NEPSE AI Signal & Alert System.

Provides:
- Custom exception classes for domain-specific errors
- Centralized REST API exception handler
- Error response formatting
- Logging integration

Usage:
    from config.exceptions import ValidationError, SignalGenerationError
    
    try:
        # business logic
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
    except SignalGenerationError as e:
        logger.error(f"Signal generation failed: {e}")
"""

import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError

logger = logging.getLogger(__name__)


# ============================================================
# Custom Exception Classes
# ============================================================

class NepseAIException(Exception):
    """Base exception for all NEPSE AI custom exceptions."""
    pass


class ValidationError(NepseAIException):
    """Raised when data validation fails."""
    pass


class SignalGenerationError(NepseAIException):
    """Raised when signal generation fails."""
    pass


class AlertTriggeringError(NepseAIException):
    """Raised when alert triggering fails."""
    pass


class TelegramServiceError(NepseAIException):
    """Raised when Telegram service operations fail."""
    pass


class DataProviderError(NepseAIException):
    """Raised when external data provider fails."""
    pass


class NotificationError(NepseAIException):
    """Raised when notification delivery fails."""
    pass


class SubscriptionError(NepseAIException):
    """Raised when subscription operations fail."""
    pass


class PermissionDeniedError(NepseAIException):
    """Raised when user lacks required permissions."""
    pass


class ResourceNotFoundError(NepseAIException):
    """Raised when requested resource is not found."""
    pass


# ============================================================
# REST API Exception Handler
# ============================================================

def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST API.
    
    Converts custom exceptions to appropriate HTTP responses with proper
    status codes and error formatting.
    
    Args:
        exc: The exception instance
        context: Context dict with view, request, etc.
    
    Returns:
        Response: DRF Response object with appropriate status code
    """
    
    # Get the original request for logging
    request = context.get('request')
    view = context.get('view')
    
    # Handle custom exceptions
    if isinstance(exc, ValidationError):
        logger.warning(
            f"Validation error in {view.__class__.__name__}: {str(exc)}"
        )
        return Response(
            {
                'error': 'validation_error',
                'detail': str(exc),
                'status': 'error',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    elif isinstance(exc, ResourceNotFoundError):
        logger.warning(
            f"Resource not found in {view.__class__.__name__}: {str(exc)}"
        )
        return Response(
            {
                'error': 'not_found',
                'detail': str(exc),
                'status': 'error',
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    
    elif isinstance(exc, PermissionDeniedError):
        logger.warning(
            f"Permission denied in {view.__class__.__name__}: {str(exc)}"
        )
        return Response(
            {
                'error': 'permission_denied',
                'detail': str(exc),
                'status': 'error',
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    
    elif isinstance(exc, (SignalGenerationError, AlertTriggeringError)):
        logger.error(
            f"Business logic error in {view.__class__.__name__}: {str(exc)}"
        )
        return Response(
            {
                'error': 'business_logic_error',
                'detail': str(exc),
                'status': 'error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    elif isinstance(exc, NepseAIException):
        logger.error(
            f"Unexpected error in {view.__class__.__name__}: {str(exc)}"
        )
        return Response(
            {
                'error': 'internal_error',
                'detail': 'An unexpected error occurred. Please try again.',
                'status': 'error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    # Handle DRF validation errors
    elif isinstance(exc, DRFValidationError):
        logger.warning(
            f"DRF validation error in {view.__class__.__name__}: {exc.detail}"
        )
        return Response(
            {
                'error': 'validation_error',
                'detail': exc.detail,
                'status': 'error',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    # Handle DRF API exceptions
    elif isinstance(exc, APIException):
        logger.warning(
            f"API error in {view.__class__.__name__}: {exc.detail}"
        )
        return Response(
            {
                'error': exc.__class__.__name__.lower(),
                'detail': str(exc.detail),
                'status': 'error',
            },
            status=exc.status_code,
        )
    
    # Handle unexpected exceptions
    else:
        logger.error(
            f"Unexpected exception in {view.__class__.__name__}: {str(exc)}",
            exc_info=True
        )
        return Response(
            {
                'error': 'internal_server_error',
                'detail': 'An internal server error occurred.',
                'status': 'error',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ============================================================
# Retry Decorators & Utilities
# ============================================================

def retry_on_exception(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Decorator for retrying failed function calls with exponential backoff.
    
    Args:
        max_retries (int): Maximum number of retries (default: 3)
        delay (int): Initial delay in seconds (default: 1)
        backoff (int): Backoff multiplier (default: 2)
        exceptions (tuple): Exceptions to catch and retry on (default: all)
    
    Example:
        @retry_on_exception(max_retries=3, delay=1, exceptions=(ConnectionError,))
        def fetch_data():
            # code that might fail
            pass
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                            f"retrying in {current_delay}s: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {str(e)}"
                        )
                        raise
        return wrapper
    return decorator
