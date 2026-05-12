"""
Django base settings for NEPSE AI Signal & Alert System.

Shared configuration used by both development and production environments.
"""

import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _validate_required_env(var_name):
    """Validate that a required environment variable is set."""
    value = os.getenv(var_name)
    if not value:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            f"Required environment variable '{var_name}' is not set."
        )
    return value

# Build paths inside the project
# BASE_DIR points to nepse_backend/ (two levels up from settings/base.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'django_filters',

    # Local apps
    'core',
    'config',
    'accounts',
    'stocks',
    'signals',
    'alerts',
    'insights',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# ============================================================
# DRF Configuration
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'config.auth.EnhancedJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.utils.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}

# ============================================================
# JWT Configuration
# ============================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=int(os.getenv('JWT_EXPIRATION_HOURS', '24'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_EXPIRATION_DAYS', '7'))),
    'ALGORITHM': os.getenv('JWT_ALGORITHM', 'HS256'),
    'SIGNING_KEY': os.getenv('JWT_SECRET', SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
}

# ============================================================
# CORS Configuration
# ============================================================
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ============================================================
# Telegram Configuration
# ============================================================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_API_URL = os.getenv('TELEGRAM_API_URL', 'https://api.telegram.org/bot')

# ============================================================
# Signal Engine Configuration
# ============================================================
SIGNAL_ENGINE_INTERVAL_MINUTES = int(os.getenv('SIGNAL_ENGINE_INTERVAL_MINUTES', '15'))

# ============================================================
# Celery Configuration
# ============================================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Celery task configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

CELERY_BEAT_SCHEDULE = {
    'generate-signals': {
        'task': 'signals.tasks.generate_signals',
        'schedule': timedelta(
            seconds=int(os.getenv('SIGNAL_ENGINE_INTERVAL_MINUTES', '15')) * 60
        ),
        'options': {'expires': 60 * 14},
    },
    'check-price-alerts': {
        'task': 'alerts.tasks.check_price_alerts',
        'schedule': timedelta(seconds=300),
        'options': {'expires': 60 * 4},
    },
    'generate-market-summary': {
        'task': 'insights.tasks.generate_market_summary',
        'schedule': timedelta(hours=24),
        'options': {'expires': 60 * 60},
    },
    'generate-daily-recap': {
        'task': 'insights.tasks.generate_daily_recap',
        'schedule': timedelta(hours=24),
        'options': {'expires': 60 * 60},
    },
}

# Celery worker configuration
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_WORKER_CONCURRENCY = int(os.getenv('CELERY_WORKER_CONCURRENCY', '2'))
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_BROKER_POOL_LIMIT = None
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10

# ============================================================
# Cache Configuration (Redis backend for task locking)
# ============================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    }
}

# ============================================================
# Logging Configuration
# ============================================================
from config.logging_config import get_logging_config

LOGGING = get_logging_config(debug=os.getenv('DEBUG', 'True').lower() == 'true')
