"""
Management command: run_backtest

Usage:
    python manage.py run_backtest
    python manage.py run_backtest --holding-days=20
    python manage.py run_backtest --signal-type=EMA_CROSS
    python manage.py run_backtest --symbols=NABIL,GBIME,API
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from backtesting.models import BacktestRun, BacktestResult
from backtesting.engine import run_backtest, aggregate_results


class Command(BaseCommand):
    help = (
        'Run the backtesting engine against historical StockHistory data. '
        'Replays signal types and records win rate, avg return, max drawdown, '
        'and sample size per signal type.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--holding-days',
            type=int,
            default=10,
            help='Number of trading days to hold each simulated position (default: 10)',
        )
        parser.add_argument(
            '--signal-type',
            type=str,
            default=None,
            help=(
                'Run backtest for a single signal type only. '
                'Options: EMA_CROSS, MACD_CROSS, RSI_MEAN_REVERSION, '
                'RSI_DIVERGENCE, DOW_THEORY, WEEKLY_SMA_CROSS, VOLUME_BREAKOUT'
            ),
        )
        parser.add_argument(
            '--symbols',
            type=str,
            default=None,
            help='Comma-separated list of stock symbols to limit scope (default: all)',
        )

    def handle(self, *args, **options):
        holding_days = options['holding_days']
        signal_type = options['signal_type']
        symbols_str = options['symbols']
        symbols_filter = [s.strip().upper() for s in symbols_str.split(',')] if symbols_str else None

        # Validate signal type
        valid_types = {
            'EMA_CROSS', 'MACD_CROSS', 'RSI_MEAN_REVERSION',
            'RSI_DIVERGENCE', 'DOW_THEORY', 'WEEKLY_SMA_CROSS',
            'VOLUME_BREAKOUT', 'CONFLUENCE_SCORE',
        }
        if signal_type and signal_type not in valid_types:
            self.stderr.write(self.style.ERROR(
                f"Invalid signal type '{signal_type}'. "
                f"Valid options: {', '.join(sorted(valid_types))}"
            ))
            return

        # Create BacktestRun record
        run = BacktestRun.objects.create(
            holding_days=holding_days,
            status='RUNNING',
        )

        self.stdout.write(self.style.WARNING(
            f"\n{'='*70}\n"
            f"  NEPSE Backtesting Engine — Run #{run.pk}\n"
            f"  Holding Period: {holding_days} trading days\n"
            f"  Signal Filter: {signal_type or 'ALL'}\n"
            f"  Symbols: {symbols_str or 'ALL'}\n"
            f"{'='*70}\n"
        ))

        def progress(current, total, symbol):
            if current % 25 == 0 or current == total:
                self.stdout.write(f"  [{current}/{total}] Processing {symbol}...")

        try:
            all_trades = run_backtest(
                holding_days=holding_days,
                signal_type_filter=signal_type,
                symbols_filter=symbols_filter,
                progress_callback=progress,
            )

            summaries = aggregate_results(all_trades)

            # Count totals
            total_trades = sum(s['total_trades'] for s in summaries)
            from stocks.models import Stock
            total_stocks = Stock.objects.count()

            # Save BacktestResult rows
            for s in summaries:
                BacktestResult.objects.create(
                    run=run,
                    signal_type=s['signal_type'],
                    direction=s['direction'],
                    total_trades=s['total_trades'],
                    winning_trades=s['winning_trades'],
                    losing_trades=s['losing_trades'],
                    win_rate=s['win_rate'],
                    avg_return_pct=s['avg_return_pct'],
                    avg_holding_days=s['avg_holding_days'],
                    max_drawdown_pct=s['max_drawdown_pct'],
                    best_trade_pct=s['best_trade_pct'],
                )

            # Update run record
            run.total_stocks = total_stocks
            run.total_trades = total_trades
            run.completed_at = timezone.now()
            run.status = 'COMPLETED'
            run.save()

            # Print summary table
            self.stdout.write(self.style.SUCCESS(
                f"\n{'='*70}\n"
                f"  BACKTEST COMPLETE — {total_trades} trades across {total_stocks} stocks\n"
                f"{'='*70}"
            ))

            if summaries:
                self.stdout.write(
                    f"\n  {'Signal Type':<25} {'Dir':<5} {'Trades':>7} "
                    f"{'Win%':>7} {'Avg Ret%':>9} {'Max DD%':>9} {'Best%':>8} {'Avg Days':>9}"
                )
                self.stdout.write(f"  {'-'*80}")

                for s in summaries:
                    self.stdout.write(
                        f"  {s['signal_type']:<25} {s['direction']:<5} "
                        f"{s['total_trades']:>7} {s['win_rate']:>6.1f}% "
                        f"{s['avg_return_pct']:>8.2f}% {s['max_drawdown_pct']:>8.2f}% "
                        f"{s['best_trade_pct']:>7.2f}% {s['avg_holding_days']:>8.1f}"
                    )

                self.stdout.write(f"  {'-'*80}\n")
            else:
                self.stdout.write(self.style.WARNING(
                    "  No trades were generated. Check that StockHistory has sufficient data."
                ))

        except Exception as e:
            run.status = 'FAILED'
            run.error_message = str(e)
            run.completed_at = timezone.now()
            run.save()
            self.stderr.write(self.style.ERROR(f"\n  BACKTEST FAILED: {e}\n"))
            raise
