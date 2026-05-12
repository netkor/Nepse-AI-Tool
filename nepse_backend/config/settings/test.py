"""
Django test settings for NEPSE AI Signal & Alert System.

Uses SQLite in-memory database and local memory cache for running tests
without requiring PostgreSQL or Redis infrastructure.
"""

from .base import *  # noqa: F401, F403

# ============================================================
# Test Overrides
# ============================================================
DEBUG = True
ALLOWED_HOSTS = ["*"]

# ============================================================
# Database - SQLite in-memory for fast tests
# ============================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ============================================================
# Cache - Local memory (no Redis required)
# ============================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# ============================================================
# Celery - Eager mode for synchronous test execution
# ============================================================
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================
# Email - Console backend
# ============================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
