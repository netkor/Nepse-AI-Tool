"""
Apps configuration for main NEPSE Backend.
"""
from django.apps import AppConfig


class NepseBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'
    verbose_name = 'NEPSE Backend'
