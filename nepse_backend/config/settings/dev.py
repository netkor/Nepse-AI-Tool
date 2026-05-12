"""
Django development settings for NEPSE AI Signal & Alert System.

Imports all shared settings from base.py and applies development-specific overrides.
"""

import os

from .base import *  # noqa: F401, F403

# ============================================================
# Development Overrides
# ============================================================
DEBUG = True
ALLOWED_HOSTS = ["*"]

# Email backend - print to console in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ============================================================
# Database - PostgreSQL
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'nepse_db'),
        'USER': os.getenv('POSTGRES_USER', 'nepse_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'nepse_pass'),
        'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}
