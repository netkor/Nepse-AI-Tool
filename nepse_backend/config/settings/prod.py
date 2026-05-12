"""
Django production settings for NEPSE AI Signal & Alert System.

Imports all shared settings from base.py and applies production hardening.
"""

import os

from .base import *  # noqa: F401, F403
from .base import _validate_required_env, SECRET_KEY

# ============================================================
# Validate required environment variables for production
# ============================================================
_validate_required_env('SECRET_KEY')
_validate_required_env('POSTGRES_DB')
_validate_required_env('POSTGRES_USER')
_validate_required_env('POSTGRES_PASSWORD')
_validate_required_env('JWT_SECRET')

# Reject insecure SECRET_KEY in production
if 'insecure' in SECRET_KEY or SECRET_KEY == 'change-me-in-production':
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        "SECRET_KEY contains a placeholder value. Set a secure key for production."
    )

# ============================================================
# Production Overrides
# ============================================================
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# ============================================================
# Security Hardening
# ============================================================
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True

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
