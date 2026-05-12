"""Core application."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration class for the core app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core'
