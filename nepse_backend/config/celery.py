"""
Celery configuration for NEPSE AI Signal & Alert System.

Sets up the Celery application for background task processing,
periodic scheduling via Celery Beat, and monitoring via Flower.

Usage:
    # Start Celery worker
    celery -A config worker -l info
    
    # Start Celery Beat scheduler
    celery -A config beat -l info
    
    # Start Flower monitoring dashboard
    celery -A config flower
"""

import os
import logging
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Create Celery app
app = Celery('config')

# Load configuration from Django settings with CELERY prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Get logger
logger = logging.getLogger(__name__)


# ============================================================
# Celery Signals
# ============================================================

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log when a task starts."""
    logger.debug(f"Task {task.name} [{task_id}] started")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, result=None, **kwargs):
    """Log when a task completes successfully."""
    logger.debug(f"Task {task.name} [{task_id}] completed: {result}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log when a task fails."""
    logger.error(
        f"Task {sender.name} [{task_id}] failed with exception: {exception}",
        exc_info=True
    )

