"""
Service layer pattern utilities for NEPSE AI Signal & Alert System.

Provides:
- BaseService: Abstract service class
- Database transaction management
- Error handling and retries
- Service registry pattern

Usage:
    from core.services import BaseService, ServiceRegistry
    
    class UserService(BaseService):
        model = User
        
        @classmethod
        def get_active_users(cls):
            return cls.model.objects.filter(is_active=True)
    
    # Register service
    registry = ServiceRegistry()
    registry.register('users', UserService)
"""

import logging
from typing import Any, Dict, List, Optional, Type, Callable
from functools import wraps
from django.db import transaction, models
from config.exceptions import NepseAIException

logger = logging.getLogger(__name__)


# ============================================================
# Service Base Class
# ============================================================

class BaseService:
    """
    Abstract base service class for business logic.
    
    Provides:
    - Transaction management
    - Error handling
    - Logging
    - Database operations
    
    Usage:
        class StockService(BaseService):
            model = Stock
            
            @classmethod
            def get_active_stocks(cls):
                return cls.model.objects.filter(is_active=True)
    """
    
    model: Optional[Type[models.Model]] = None
    
    @classmethod
    def get_by_id(cls, id: Any) -> Optional[models.Model]:
        """Get object by ID."""
        if not cls.model:
            raise NotImplementedError("model attribute must be set")
        
        try:
            return cls.model.objects.get(id=id)
        except cls.model.DoesNotExist:
            logger.warning(f"{cls.model.__name__} not found: id={id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {cls.model.__name__}: {e}")
            raise NepseAIException(f"Failed to fetch {cls.model.__name__}")
    
    @classmethod
    def get_all(cls, filters: Optional[Dict] = None) -> List[models.Model]:
        """Get all objects with optional filters."""
        if not cls.model:
            raise NotImplementedError("model attribute must be set")
        
        queryset = cls.model.objects.all()
        
        if filters:
            try:
                queryset = queryset.filter(**filters)
            except Exception as e:
                logger.error(f"Error applying filters: {e}")
                raise NepseAIException("Failed to apply filters")
        
        return list(queryset)
    
    @classmethod
    def create(cls, **kwargs) -> models.Model:
        """Create a new object."""
        if not cls.model:
            raise NotImplementedError("model attribute must be set")
        
        try:
            with transaction.atomic():
                obj = cls.model.objects.create(**kwargs)
                logger.info(f"Created {cls.model.__name__}: {obj}")
                return obj
        except Exception as e:
            logger.error(f"Error creating {cls.model.__name__}: {e}")
            raise NepseAIException(f"Failed to create {cls.model.__name__}")
    
    @classmethod
    def update(cls, id: Any, **kwargs) -> Optional[models.Model]:
        """Update an object."""
        if not cls.model:
            raise NotImplementedError("model attribute must be set")
        
        try:
            with transaction.atomic():
                obj = cls.model.objects.get(id=id)
                for key, value in kwargs.items():
                    setattr(obj, key, value)
                obj.save()
                logger.info(f"Updated {cls.model.__name__}: {obj}")
                return obj
        except cls.model.DoesNotExist:
            logger.warning(f"{cls.model.__name__} not found: id={id}")
            return None
        except Exception as e:
            logger.error(f"Error updating {cls.model.__name__}: {e}")
            raise NepseAIException(f"Failed to update {cls.model.__name__}")
    
    @classmethod
    def delete(cls, id: Any) -> bool:
        """Delete an object."""
        if not cls.model:
            raise NotImplementedError("model attribute must be set")
        
        try:
            with transaction.atomic():
                obj = cls.model.objects.get(id=id)
                obj.delete()
                logger.info(f"Deleted {cls.model.__name__}: {obj}")
                return True
        except cls.model.DoesNotExist:
            logger.warning(f"{cls.model.__name__} not found: id={id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting {cls.model.__name__}: {e}")
            raise NepseAIException(f"Failed to delete {cls.model.__name__}")
    
    @classmethod
    def soft_delete(cls, id: Any) -> bool:
        """Soft delete an object (mark as inactive)."""
        if not cls.model:
            raise NotImplementedError("model attribute must be set")
        
        try:
            with transaction.atomic():
                obj = cls.model.objects.get(id=id)
                if hasattr(obj, 'soft_delete'):
                    obj.soft_delete()
                    logger.info(f"Soft deleted {cls.model.__name__}: {obj}")
                    return True
                else:
                    logger.warning(f"{cls.model.__name__} does not support soft delete")
                    return False
        except Exception as e:
            logger.error(f"Error soft deleting {cls.model.__name__}: {e}")
            raise NepseAIException(f"Failed to soft delete {cls.model.__name__}")


# ============================================================
# Decorators
# ============================================================

def service_transaction(func):
    """
    Decorator to wrap service methods with database transaction.
    
    Usage:
        class MyService(BaseService):
            @service_transaction
            def bulk_create(self, items):
                # All operations here are atomic
                pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Transaction failed in {func.__name__}: {e}")
            raise NepseAIException(f"Transaction failed: {str(e)}")
    return wrapper


def service_cache(timeout: int = 300):
    """
    Decorator to cache service method results.
    
    Usage:
        class MyService(BaseService):
            @service_cache(timeout=600)
            def get_popular_items(self):
                # Results cached for 10 minutes
                pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from django.core.cache import cache
            
            # Create cache key from function name and args
            cache_key = f"{func.__module__}.{func.__qualname__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Not in cache, call function
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cached {func.__name__} for {timeout}s")
            return result
        
        return wrapper
    return decorator


def service_logger(func):
    """
    Decorator to log service method calls.
    
    Usage:
        class MyService(BaseService):
            @service_logger
            def process_data(self, data):
                pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    
    return wrapper


# ============================================================
# Service Registry
# ============================================================

class ServiceRegistry:
    """
    Registry for managing service instances.
    
    Provides:
    - Service registration and retrieval
    - Singleton pattern support
    - Lazy loading of services
    
    Usage:
        registry = ServiceRegistry()
        registry.register('stocks', StockService)
        service = registry.get('stocks')
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._instances: Dict[str, Any] = {}
    
    def register(self, name: str, service: Type, singleton: bool = True):
        """
        Register a service.
        
        Args:
            name: Service name/key
            service: Service class
            singleton: If True, same instance is returned each time
        """
        self._services[name] = {
            'service': service,
            'singleton': singleton,
        }
        logger.debug(f"Registered service: {name}")
    
    def get(self, name: str) -> Any:
        """
        Get a service instance.
        
        Args:
            name: Service name/key
        
        Returns:
            Service instance or class
        """
        if name not in self._services:
            raise ValueError(f"Service not registered: {name}")
        
        config = self._services[name]
        
        if config['singleton']:
            # Return same instance
            if name not in self._instances:
                self._instances[name] = config['service']()
            return self._instances[name]
        else:
            # Return new instance each time
            return config['service']()
    
    def has(self, name: str) -> bool:
        """Check if service is registered."""
        return name in self._services
    
    def clear(self):
        """Clear all registrations and instances."""
        self._services.clear()
        self._instances.clear()
        logger.debug("Cleared service registry")


# ============================================================
# Global Service Registry
# ============================================================

_global_registry = ServiceRegistry()


def register_service(name: str, service: Type, singleton: bool = True):
    """Register a service globally."""
    _global_registry.register(name, service, singleton)


def get_service(name: str) -> Any:
    """Get a service from global registry."""
    return _global_registry.get(name)
