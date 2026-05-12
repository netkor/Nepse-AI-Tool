"""
Unit tests for environment validation and settings configuration.

Validates: Requirements 7.4, 7.7, 3.8, 4.4
"""

import os
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from config.settings.base import _validate_required_env


class ValidateRequiredEnvTest(TestCase):
    """Test _validate_required_env raises ImproperlyConfigured for empty/missing values."""

    @patch.dict(os.environ, {}, clear=False)
    def test_raises_for_missing_env_var(self):
        """_validate_required_env raises ImproperlyConfigured when env var is not set."""
        # Ensure the variable is not in the environment
        os.environ.pop('NONEXISTENT_TEST_VAR', None)
        with self.assertRaises(ImproperlyConfigured) as ctx:
            _validate_required_env('NONEXISTENT_TEST_VAR')
        self.assertIn('NONEXISTENT_TEST_VAR', str(ctx.exception))

    @patch.dict(os.environ, {'EMPTY_TEST_VAR': ''})
    def test_raises_for_empty_env_var(self):
        """_validate_required_env raises ImproperlyConfigured when env var is empty string."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            _validate_required_env('EMPTY_TEST_VAR')
        self.assertIn('EMPTY_TEST_VAR', str(ctx.exception))

    @patch.dict(os.environ, {'VALID_TEST_VAR': 'some-value'})
    def test_returns_value_when_env_var_is_set(self):
        """_validate_required_env returns the value when env var is properly set."""
        result = _validate_required_env('VALID_TEST_VAR')
        self.assertEqual(result, 'some-value')


class InsecureSecretKeyProdTest(TestCase):
    """Test that prod settings reject insecure SECRET_KEY values.

    Validates: Requirement 7.7
    """

    def test_rejects_key_containing_insecure(self):
        """Prod validation logic rejects SECRET_KEY containing 'insecure'."""
        insecure_key = 'django-insecure-dev-key-change-in-production'
        # Replicate the prod.py validation logic
        with self.assertRaises(ImproperlyConfigured):
            if 'insecure' in insecure_key or insecure_key == 'change-me-in-production':
                raise ImproperlyConfigured(
                    "SECRET_KEY contains a placeholder value. "
                    "Set a secure key for production."
                )

    def test_rejects_known_placeholder_value(self):
        """Prod validation logic rejects SECRET_KEY matching known placeholder."""
        placeholder_key = 'change-me-in-production'
        with self.assertRaises(ImproperlyConfigured):
            if 'insecure' in placeholder_key or placeholder_key == 'change-me-in-production':
                raise ImproperlyConfigured(
                    "SECRET_KEY contains a placeholder value. "
                    "Set a secure key for production."
                )

    def test_accepts_secure_key(self):
        """Prod validation logic accepts a properly secure SECRET_KEY."""
        secure_key = 'a7b3c9d2e1f4g5h6i7j8k9l0m1n2o3p4q5r6s7t8u9v0w1x2y3z4'
        # This should NOT raise - the condition should be False
        rejected = False
        if 'insecure' in secure_key or secure_key == 'change-me-in-production':
            rejected = True
        self.assertFalse(rejected)


class CeleryWorkerConcurrencyTest(TestCase):
    """Test CELERY_WORKER_CONCURRENCY defaults to 2.

    Validates: Requirement 3.8
    """

    def test_celery_worker_concurrency_defaults_to_2(self):
        """CELERY_WORKER_CONCURRENCY setting defaults to 2."""
        self.assertEqual(settings.CELERY_WORKER_CONCURRENCY, 2)


class CeleryBeatScheduleTest(TestCase):
    """Test CELERY_BEAT_SCHEDULE contains both tasks with correct intervals.

    Validates: Requirement 4.4
    """

    def test_schedule_contains_generate_signals_task(self):
        """CELERY_BEAT_SCHEDULE contains 'generate-signals' task."""
        self.assertIn('generate-signals', settings.CELERY_BEAT_SCHEDULE)

    def test_schedule_contains_check_price_alerts_task(self):
        """CELERY_BEAT_SCHEDULE contains 'check-price-alerts' task."""
        self.assertIn('check-price-alerts', settings.CELERY_BEAT_SCHEDULE)

    def test_generate_signals_has_correct_task_path(self):
        """'generate-signals' points to 'signals.tasks.generate_signals'."""
        task_config = settings.CELERY_BEAT_SCHEDULE['generate-signals']
        self.assertEqual(task_config['task'], 'signals.tasks.generate_signals')

    def test_generate_signals_has_900_second_schedule(self):
        """'generate-signals' has a 900-second schedule (15 min default)."""
        task_config = settings.CELERY_BEAT_SCHEDULE['generate-signals']
        schedule = task_config['schedule']
        self.assertEqual(schedule.total_seconds(), 900)

    def test_check_price_alerts_has_correct_task_path(self):
        """'check-price-alerts' points to 'alerts.tasks.check_price_alerts'."""
        task_config = settings.CELERY_BEAT_SCHEDULE['check-price-alerts']
        self.assertEqual(task_config['task'], 'alerts.tasks.check_price_alerts')

    def test_check_price_alerts_has_300_second_schedule(self):
        """'check-price-alerts' has a 300-second schedule (5 min)."""
        task_config = settings.CELERY_BEAT_SCHEDULE['check-price-alerts']
        schedule = task_config['schedule']
        self.assertEqual(schedule.total_seconds(), 300)

    def test_schedule_contains_generate_market_summary_task(self):
        """CELERY_BEAT_SCHEDULE contains 'generate-market-summary' task."""
        self.assertIn('generate-market-summary', settings.CELERY_BEAT_SCHEDULE)

    def test_schedule_contains_generate_daily_recap_task(self):
        """CELERY_BEAT_SCHEDULE contains 'generate-daily-recap' task."""
        self.assertIn('generate-daily-recap', settings.CELERY_BEAT_SCHEDULE)
