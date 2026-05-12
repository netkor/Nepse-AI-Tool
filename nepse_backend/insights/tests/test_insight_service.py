from django.contrib.auth import get_user_model
from django.test import TestCase

from signals.models.history import SignalHistory
from stocks.models import Stock
from insights.services.insight_service import InsightService


class InsightServiceTest(TestCase):
    def setUp(self):
        self.stock = Stock.objects.create(
            symbol='NABIL',
            name='Nabil Bank Ltd.',
            price='520.00',
            volume=1000,
            change_percent='2.50',
            is_active=True,
        )
        self.signal = SignalHistory.objects.create(
            stock=self.stock,
            signal_type='rsi',
            direction='buy',
            price='520.00',
            strength=0.87,
            message='RSI and MACD are aligned for an upside move.',
            indicators={
                'rsi': 29,
                'macd': 1.8,
                'signal': 1.2,
                'volume_multiple': 1.7,
                'support': 515,
            },
        )

    def test_explain_signal_returns_template_based_summary(self):
        data = InsightService.explain_signal(self.signal)

        self.assertEqual(data['signal_id'], self.signal.signal_id)
        self.assertIn('RSI', data['title'])
        self.assertIn('NABIL', data['summary'])
        self.assertGreaterEqual(len(data['highlights']), 1)

    def test_build_market_summary_counts_recent_signals(self):
        summary = InsightService.build_market_summary(days=1)

        self.assertEqual(summary['total_signals'], 1)
        self.assertEqual(summary['sentiment'], 'bullish')
        self.assertEqual(summary['strongest_signal']['stock_symbol'], 'NABIL')

    def test_generate_daily_recap_returns_actionable_bullets(self):
        recap = InsightService.generate_daily_recap(days=1)

        self.assertIn('headline', recap)
        self.assertGreaterEqual(len(recap['bullets']), 1)
        self.assertEqual(recap['recommended_focus'], 'watchlist_review')
