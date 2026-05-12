from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.db.models import Avg, Count
from django.utils import timezone

from signals.models.history import SignalHistory


@dataclass(frozen=True)
class InsightTemplate:
    title: str
    summary: str
    action: str


class InsightService:
    """Template-based insight generation for trading signals and market activity."""

    SIGNAL_TEMPLATES = {
        'rsi:buy': InsightTemplate(
            title='RSI oversold bounce setup',
            summary='{symbol} is flashing an RSI-based buy signal with {strength} strength.',
            action='Watch for reversal confirmation near support.',
        ),
        'rsi:sell': InsightTemplate(
            title='RSI overbought pullback risk',
            summary='{symbol} is showing RSI exhaustion and a potential pullback.',
            action='Consider waiting for momentum to cool before entering.',
        ),
        'macd:buy': InsightTemplate(
            title='MACD bullish crossover',
            summary='{symbol} is strengthening after a bullish MACD crossover.',
            action='Confirm the trend with follow-through volume.',
        ),
        'macd:sell': InsightTemplate(
            title='MACD bearish crossover',
            summary='{symbol} is weakening after a bearish MACD crossover.',
            action='Look for downside continuation or support response.',
        ),
        'breakout:buy': InsightTemplate(
            title='Breakout continuation signal',
            summary='{symbol} has pushed through resistance with breakout momentum.',
            action='Monitor volume and retest behavior for confirmation.',
        ),
        'breakout:sell': InsightTemplate(
            title='Breakdown risk detected',
            summary='{symbol} has lost key support and may continue lower.',
            action='Treat failed support as a risk-off cue.',
        ),
        'volume_spike:buy': InsightTemplate(
            title='Volume spike accumulation signal',
            summary='{symbol} is seeing unusual volume alongside positive price action.',
            action='Large participation can support a short-term move higher.',
        ),
        'volume_spike:sell': InsightTemplate(
            title='Volume spike distribution signal',
            summary='{symbol} is seeing unusual volume alongside weak price action.',
            action='Heavy distribution can accelerate downside movement.',
        ),
        'alert:neutral': InsightTemplate(
            title='Price alert triggered',
            summary='{symbol} crossed an alert threshold and needs attention.',
            action='Review the market structure before acting.',
        ),
    }

    @classmethod
    def explain_signal(cls, signal: SignalHistory) -> Dict[str, Any]:
        template_key = f"{signal.signal_type}:{signal.direction}"
        template = cls.SIGNAL_TEMPLATES.get(template_key) or cls.SIGNAL_TEMPLATES.get('alert:neutral')
        details = signal.indicators or {}
        bullets = cls._build_bullets(signal, details)
        strength = round(float(signal.strength or 0) * 100)

        return {
            'signal_id': signal.signal_id,
            'signal_type': signal.signal_type,
            'stock_symbol': signal.stock.symbol,
            'stock_name': signal.stock.name,
            'title': template.title,
            'summary': template.summary.format(
                symbol=signal.stock.symbol,
                strength=f'{strength}%',
            ),
            'action': template.action,
            'strength': round(float(signal.strength or 0), 2),
            'direction': signal.direction,
            'message': signal.message,
            'highlights': bullets,
            'indicator_details': details,
        }

    @staticmethod
    def _build_bullets(signal: SignalHistory, details: Dict[str, Any]) -> List[str]:
        bullets: List[str] = []
        signal_type = (signal.signal_type or '').lower()
        direction = (signal.direction or '').lower()

        if signal_type == 'rsi':
            rsi = details.get('rsi')
            if rsi is not None:
                if direction == 'buy':
                    bullets.append(f'RSI at {rsi} supports an oversold bounce setup.')
                else:
                    bullets.append(f'RSI at {rsi} suggests the move may be stretched.')
            if details.get('support') is not None:
                bullets.append(f'Price is holding near support at {details["support"]}.')
        elif signal_type == 'macd':
            if details.get('macd') is not None and details.get('signal') is not None:
                bullets.append(
                    f"MACD {details['macd']} vs signal {details['signal']} suggests momentum is shifting."
                )
            if details.get('histogram') is not None:
                bullets.append(f"Histogram is at {details['histogram']}, showing trend acceleration or fade.")
        elif signal_type == 'breakout':
            if details.get('breakout_level') is not None:
                bullets.append(f'Breakout level: {details["breakout_level"]}.')
            if details.get('support') is not None:
                bullets.append(f'Nearby support is {details["support"]}.')
            if details.get('resistance') is not None:
                bullets.append(f'Key resistance is {details["resistance"]}.')
        elif signal_type == 'volume_spike':
            if details.get('volume_multiple') is not None:
                bullets.append(f'Volume is {details["volume_multiple"]}x the recent average.')
            if details.get('price_change_percent') is not None:
                bullets.append(f'Price moved {details["price_change_percent"]}% during the spike.')
        else:
            if details.get('price') is not None:
                bullets.append(f'Alert triggered around {details["price"]}.')

        if not bullets:
            bullets.append(signal.message or 'No additional indicator context was provided.')

        return bullets[:4]

    @classmethod
    def build_market_summary(cls, days: int = 1, cache_ttl: int = 300) -> Dict[str, Any]:
        cache_key = f'insights:market-summary:{days}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        cutoff = timezone.now() - timedelta(days=days)
        qs = SignalHistory.objects.select_related('stock').filter(signal_generation_time__gte=cutoff)

        total = qs.count()
        if total == 0:
            summary = {
                'window_days': days,
                'generated_at': timezone.now().isoformat(),
                'total_signals': 0,
                'sentiment': 'quiet',
                'headline': 'No new signals in the selected window.',
                'top_stock': None,
                'signal_mix': {},
                'average_strength': 0.0,
            }
            cache.set(cache_key, summary, cache_ttl)
            return summary

        mix = Counter(qs.values_list('signal_type', flat=True))
        direction_mix = Counter(qs.values_list('direction', flat=True))
        top_stock_row = (
            qs.values('stock__symbol', 'stock__name')
            .annotate(count=Count('id'), avg_strength=Avg('strength'))
            .order_by('-count', '-avg_strength')
            .first()
        )
        strongest = qs.order_by('-strength', '-signal_generation_time').first()
        average_strength = qs.aggregate(avg=Avg('strength'))['avg'] or 0.0
        bullish = direction_mix.get('buy', 0)
        bearish = direction_mix.get('sell', 0)

        if bullish > bearish:
            sentiment = 'bullish'
            headline = 'Buy signals are leading the market narrative.'
        elif bearish > bullish:
            sentiment = 'bearish'
            headline = 'Sell pressure is currently dominating the signal feed.'
        else:
            sentiment = 'balanced'
            headline = 'Signal activity is balanced between buyers and sellers.'

        summary = {
            'window_days': days,
            'generated_at': timezone.now().isoformat(),
            'total_signals': total,
            'sentiment': sentiment,
            'headline': headline,
            'average_strength': round(float(average_strength), 2),
            'signal_mix': dict(mix),
            'direction_mix': dict(direction_mix),
            'top_stock': top_stock_row,
            'strongest_signal': {
                'signal_id': strongest.signal_id,
                'signal_type': strongest.signal_type,
                'stock_symbol': strongest.stock.symbol,
                'strength': round(float(strongest.strength or 0), 2),
                'message': strongest.message,
            } if strongest else None,
        }
        cache.set(cache_key, summary, cache_ttl)
        return summary

    @classmethod
    def generate_daily_recap(cls, days: int = 1, cache_ttl: int = 600) -> Dict[str, Any]:
        cache_key = f'insights:daily-recap:{days}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        summary = cls.build_market_summary(days=days)
        mix = summary.get('signal_mix', {})
        total = summary.get('total_signals', 0)
        top_stock = summary.get('top_stock')
        strongest = summary.get('strongest_signal')

        bullets = []
        if total == 0:
            bullets.append('No new signals were generated during the recap window.')
        else:
            if mix.get('buy', 0) > mix.get('sell', 0):
                bullets.append('Momentum is tilted bullish with more buy signals than sell signals.')
            elif mix.get('sell', 0) > mix.get('buy', 0):
                bullets.append('Momentum is tilted bearish with elevated sell pressure.')
            else:
                bullets.append('Buy and sell signals are roughly balanced.')

            if top_stock:
                bullets.append(
                    f"Most active stock: {top_stock['stock__symbol']} with {top_stock['count']} signals."
                )
            if strongest:
                bullets.append(
                    f"Strongest signal: {strongest['signal_type']} on {strongest['stock_symbol']} at {round(float(strongest['strength']) * 100)}% strength."
                )

        recap = {
            'window_days': days,
            'generated_at': timezone.now().isoformat(),
            'headline': summary['headline'],
            'summary': summary,
            'bullets': bullets,
            'recommended_focus': 'watchlist_review' if summary.get('sentiment') != 'quiet' else 'market_watch',
        }
        cache.set(cache_key, recap, cache_ttl)
        return recap

    @classmethod
    def precompute_insights(cls, days: int = 1) -> Dict[str, Any]:
        return {
            'market_summary': cls.build_market_summary(days=days),
            'daily_recap': cls.generate_daily_recap(days=days),
        }
