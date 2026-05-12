"""
Integration tests for Celery tasks.

Tests that generate_signals and check_price_alerts tasks execute correctly
in eager mode, handle failures gracefully, and respect solo execution guards.

Validates: Requirements 10.1, 10.2, 10.5, 10.6
"""

import logging
from unittest.mock import patch, MagicMock

from django.core.cache import cache
from django.test import TestCase, override_settings

from signals.services import SignalService
from alerts.services import AlertService
from config.telegram_service import TelegramService


CELERY_TEST_SETTINGS = {
    'CELERY_TASK_ALWAYS_EAGER': True,
    'CELERY_TASK_EAGER_PROPAGATES': True,
    'CACHES': {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'celery-tasks-test',
        }
    },
    'DATABASES': {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
}


@override_settings(**CELERY_TEST_SETTINGS)
class TestGenerateSignalsTask(TestCase):
    """Integration tests for the generate_signals Celery task.

    Validates: Requirements 10.1, 10.5, 10.6
    """

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch.object(TelegramService, 'is_enabled', return_value=False)
    @patch.object(SignalService, 'generate_signals')
    def test_returns_result_dict_with_expected_keys(self, mock_generate, mock_enabled):
        """generate_signals task returns dict with 'signals_created' and 'notifications_sent'."""
        mock_generate.return_value = (3, ['signal1', 'signal2', 'signal3'])

        from signals.tasks import generate_signals
        result = generate_signals()

        self.assertIsInstance(result, dict)
        self.assertIn('signals_created', result)
        self.assertIn('notifications_sent', result)
        self.assertEqual(result['signals_created'], 3)
        self.assertEqual(result['notifications_sent'], 0)

    @patch.object(TelegramService, 'is_enabled', return_value=False)
    @patch.object(SignalService, 'generate_signals')
    def test_returns_zero_counts_when_no_signals(self, mock_generate, mock_enabled):
        """generate_signals returns zero counts when no signals are generated."""
        mock_generate.return_value = (0, [])

        from signals.tasks import generate_signals
        result = generate_signals()

        self.assertEqual(result['signals_created'], 0)
        self.assertEqual(result['notifications_sent'], 0)

    @patch.object(SignalService, 'generate_signals')
    def test_task_failure_is_logged_without_retry(self, mock_generate):
        """When generate_signals raises an exception, it is logged and not retried."""
        mock_generate.side_effect = RuntimeError("Service unavailable")

        from signals.tasks import generate_signals

        with self.assertRaises(RuntimeError):
            generate_signals()

        # Verify max_retries=0 means no retry
        self.assertEqual(generate_signals.max_retries, 0)

    def test_solo_execution_guard_skips_when_locked(self):
        """generate_signals returns skipped=True when lock is already held."""
        from signals.tasks import generate_signals, LOCK_ID

        # Manually acquire the lock to simulate a concurrent run
        cache.add(LOCK_ID, 'locked', 60 * 14)

        result = generate_signals()

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('skipped'))
        self.assertEqual(result['signals_created'], 0)
        self.assertEqual(result['notifications_sent'], 0)

    @patch.object(TelegramService, 'is_enabled', return_value=False)
    @patch.object(SignalService, 'generate_signals')
    def test_lock_is_released_after_execution(self, mock_generate, mock_enabled):
        """generate_signals releases the cache lock after successful execution."""
        mock_generate.return_value = (1, ['signal1'])

        from signals.tasks import generate_signals, LOCK_ID

        generate_signals()

        # Lock should be released - a new add should succeed
        acquired = cache.add(LOCK_ID, 'test', 60)
        self.assertTrue(acquired)


@override_settings(**CELERY_TEST_SETTINGS)
class TestCheckPriceAlertsTask(TestCase):
    """Integration tests for the check_price_alerts Celery task.

    Validates: Requirements 10.2, 10.5, 10.6
    """

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    @patch.object(TelegramService, 'is_enabled', return_value=False)
    @patch.object(AlertService, 'check_and_trigger_price_alerts')
    def test_returns_result_dict_with_triggered_count(self, mock_check, mock_enabled):
        """check_price_alerts task returns dict with 'triggered_count' key."""
        mock_check.return_value = 5

        from alerts.tasks import check_price_alerts
        result = check_price_alerts()

        self.assertIsInstance(result, dict)
        self.assertIn('triggered_count', result)
        self.assertEqual(result['triggered_count'], 5)

    @patch.object(TelegramService, 'is_enabled', return_value=False)
    @patch.object(AlertService, 'check_and_trigger_price_alerts')
    def test_returns_zero_when_no_alerts_triggered(self, mock_check, mock_enabled):
        """check_price_alerts returns triggered_count=0 when no alerts fire."""
        mock_check.return_value = 0

        from alerts.tasks import check_price_alerts
        result = check_price_alerts()

        self.assertEqual(result['triggered_count'], 0)

    @patch.object(AlertService, 'check_and_trigger_price_alerts')
    def test_task_failure_is_logged_without_retry(self, mock_check):
        """When check_price_alerts raises an exception, it is logged and not retried."""
        mock_check.side_effect = RuntimeError("Database connection lost")

        from alerts.tasks import check_price_alerts

        with self.assertRaises(RuntimeError):
            check_price_alerts()

        # Verify max_retries=0 means no retry
        self.assertEqual(check_price_alerts.max_retries, 0)

    def test_solo_execution_guard_skips_when_locked(self):
        """check_price_alerts returns skipped=True when lock is already held."""
        from alerts.tasks import check_price_alerts, LOCK_ID

        # Manually acquire the lock to simulate a concurrent run
        cache.add(LOCK_ID, 'locked', 60 * 4)

        result = check_price_alerts()

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get('skipped'))
        self.assertEqual(result['triggered_count'], 0)

    @patch.object(TelegramService, 'is_enabled', return_value=False)
    @patch.object(AlertService, 'check_and_trigger_price_alerts')
    def test_lock_is_released_after_execution(self, mock_check, mock_enabled):
        """check_price_alerts releases the cache lock after successful execution."""
        mock_check.return_value = 2

        from alerts.tasks import check_price_alerts, LOCK_ID

        check_price_alerts()

        # Lock should be released - a new add should succeed
        acquired = cache.add(LOCK_ID, 'test', 60)
        self.assertTrue(acquired)
