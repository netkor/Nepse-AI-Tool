"""
Backtesting engine — replays each existing signal type against historical
StockHistory data, simulates trades with ATR-based exits, and collects
per-signal performance metrics.

No lookahead bias: signals are computed only on data up to the current bar.
"""

import logging
from collections import defaultdict

import numpy as np
import pandas as pd

from stocks.models import Stock, StockHistory, FundamentalSnapshot
from signals.calculators import (
    get_stock_dataframe,
    calculate_indicators,
    resample_weekly_dataframe,
    calculate_confluence_score,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Signal detection helpers (mirror the live signal logic, but return
# granular per-category results instead of a single recommendation)
# ──────────────────────────────────────────────────────────────────────

def _detect_signals_at_bar(df, idx, stock=None, snapshots=None):
    """
    Given a DataFrame with indicators already computed and a bar index,
    return a list of fired signals.  Each entry is a dict:
        {'signal_type': str, 'direction': 'BUY'|'SELL'}

    Only examines data at df.iloc[idx] and df.iloc[idx-1] — never peeks
    ahead.  Requires idx >= 1 and the DataFrame to have indicators computed.
    """
    if idx < 1 or idx >= len(df):
        return []

    latest = df.iloc[idx]
    prev = df.iloc[idx - 1]
    fired = []

    # ── EMA Cross ────────────────────────────────────────────────────
    ema20_latest = latest.get('ema20')
    ema50_latest = latest.get('ema50')
    ema20_prev = prev.get('ema20')
    ema50_prev = prev.get('ema50')

    if None not in (ema20_latest, ema50_latest, ema20_prev, ema50_prev):
        if ema20_prev <= ema50_prev and ema20_latest > ema50_latest:
            fired.append({'signal_type': 'EMA_CROSS', 'direction': 'BUY'})
        elif ema20_prev >= ema50_prev and ema20_latest < ema50_latest:
            fired.append({'signal_type': 'EMA_CROSS', 'direction': 'SELL'})

    # ── MACD Cross ───────────────────────────────────────────────────
    macd_latest = latest.get('macd')
    macd_signal_latest = latest.get('macd_signal')
    macd_prev = prev.get('macd')
    macd_signal_prev = prev.get('macd_signal')

    if None not in (macd_latest, macd_signal_latest, macd_prev, macd_signal_prev):
        if macd_prev <= macd_signal_prev and macd_latest > macd_signal_latest:
            fired.append({'signal_type': 'MACD_CROSS', 'direction': 'BUY'})
        elif macd_prev >= macd_signal_prev and macd_latest < macd_signal_latest:
            fired.append({'signal_type': 'MACD_CROSS', 'direction': 'SELL'})

    # ── Volume Breakout ──────────────────────────────────────────────
    vol_ma = latest.get('vol_ma20')
    if (vol_ma and vol_ma > 0
            and latest['volume'] > (2.5 * vol_ma)
            and latest['close'] > prev['close']):
        fired.append({'signal_type': 'VOLUME_BREAKOUT', 'direction': 'BUY'})

    # ── RSI Mean Reversion ───────────────────────────────────────────
    rsi_latest = latest.get('rsi')
    if rsi_latest is not None:
        if rsi_latest <= 30:
            fired.append({'signal_type': 'RSI_MEAN_REVERSION', 'direction': 'BUY'})
        elif rsi_latest >= 70:
            fired.append({'signal_type': 'RSI_MEAN_REVERSION', 'direction': 'SELL'})

    # ── RSI Divergence ───────────────────────────────────────────────
    if idx >= 25 and rsi_latest is not None:
        valleys = []
        peaks = []
        scan_start = max(1, idx - 25)
        for i in range(scan_start, idx):
            if i <= 0 or i >= len(df) - 1:
                continue
            if df['close'].iloc[i] < df['close'].iloc[i - 1] and df['close'].iloc[i] < df['close'].iloc[i + 1]:
                valleys.append(i)
            if df['close'].iloc[i] > df['close'].iloc[i - 1] and df['close'].iloc[i] > df['close'].iloc[i + 1]:
                peaks.append(i)

        # Bullish divergence
        if len(valleys) >= 2:
            v1, v2 = valleys[-2], valleys[-1]
            price_v1 = float(df['close'].iloc[v1])
            price_v2 = float(df['close'].iloc[v2])
            rsi_v1 = df['rsi'].iloc[v1]
            rsi_v2 = df['rsi'].iloc[v2]
            if rsi_v1 is not None and rsi_v2 is not None:
                if price_v2 < price_v1 and rsi_v2 > rsi_v1 and rsi_v2 < 45:
                    fired.append({'signal_type': 'RSI_DIVERGENCE', 'direction': 'BUY'})

        # Bearish divergence
        if len(peaks) >= 2:
            p1, p2 = peaks[-2], peaks[-1]
            price_p1 = float(df['close'].iloc[p1])
            price_p2 = float(df['close'].iloc[p2])
            rsi_p1 = df['rsi'].iloc[p1]
            rsi_p2 = df['rsi'].iloc[p2]
            if rsi_p1 is not None and rsi_p2 is not None:
                if price_p2 > price_p1 and rsi_p2 < rsi_p1 and rsi_p2 > 55:
                    fired.append({'signal_type': 'RSI_DIVERGENCE', 'direction': 'SELL'})

    # ── Dow Theory ───────────────────────────────────────────────────
    if idx >= 40:
        dow_valleys = []
        dow_peaks = []
        scan_start = max(1, idx - 40)
        for i in range(scan_start, idx):
            if i <= 0 or i >= len(df) - 1:
                continue
            if df['close'].iloc[i] < df['close'].iloc[i - 1] and df['close'].iloc[i] < df['close'].iloc[i + 1]:
                dow_valleys.append(float(df['close'].iloc[i]))
            if df['close'].iloc[i] > df['close'].iloc[i - 1] and df['close'].iloc[i] > df['close'].iloc[i + 1]:
                dow_peaks.append(float(df['close'].iloc[i]))

        if len(dow_valleys) >= 3 and len(dow_peaks) >= 3:
            v1, v2, v3 = dow_valleys[-3], dow_valleys[-2], dow_valleys[-1]
            p1, p2, p3 = dow_peaks[-3], dow_peaks[-2], dow_peaks[-1]

            if p3 > p2 > p1 and v3 > v2 > v1:
                fired.append({'signal_type': 'DOW_THEORY', 'direction': 'BUY'})
            elif p3 < p2 < p1 and v3 < v2 < v1:
                fired.append({'signal_type': 'DOW_THEORY', 'direction': 'SELL'})

    # ── Confluence Score ─────────────────────────────────────────────
    current_date = latest.get('date')
    confluence = calculate_confluence_score(df, stock=stock, date=current_date, snapshots=snapshots, idx=idx)
    if confluence['recommendation'] in ['STRONG BUY', 'BUY']:
        fired.append({'signal_type': 'CONFLUENCE_SCORE', 'direction': 'BUY'})
    elif confluence['recommendation'] in ['STRONG SELL', 'SELL']:
        fired.append({'signal_type': 'CONFLUENCE_SCORE', 'direction': 'SELL'})

    return fired


def _detect_weekly_signals_at_bar(df_weekly, idx):
    """
    Check for weekly SMA 20/50 crossover at bar index.
    """
    if idx < 1 or idx >= len(df_weekly):
        return []

    latest = df_weekly.iloc[idx]
    prev = df_weekly.iloc[idx - 1]
    fired = []

    sma20_latest = latest.get('sma20')
    sma50_latest = latest.get('sma50')
    sma20_prev = prev.get('sma20')
    sma50_prev = prev.get('sma50')

    if None in (sma20_latest, sma50_latest, sma20_prev, sma50_prev):
        return fired

    if sma20_prev <= sma50_prev and sma20_latest > sma50_latest:
        fired.append({'signal_type': 'WEEKLY_SMA_CROSS', 'direction': 'BUY'})
    elif sma20_prev >= sma50_prev and sma20_latest < sma50_latest:
        fired.append({'signal_type': 'WEEKLY_SMA_CROSS', 'direction': 'SELL'})

    return fired


# ──────────────────────────────────────────────────────────────────────
# Trade simulation
# ──────────────────────────────────────────────────────────────────────

def _simulate_trade(df, entry_idx, holding_days, direction, atr_value=None):
    """
    Simulate a trade entered at df.iloc[entry_idx] and held for up to
    `holding_days` bars.  Uses ATR-based stop-loss (1.5×ATR) and
    take-profit (3.0×ATR) if atr_value is provided.

    Returns a dict with trade outcome metrics, or None if insufficient
    future data.
    """
    entry_price = float(df.iloc[entry_idx]['close'])
    entry_date = df.iloc[entry_idx]['date']

    if entry_price <= 0:
        return None

    # Determine SL / TP levels
    stop_loss = None
    take_profit = None
    if atr_value is not None and atr_value > 0:
        if direction == 'BUY':
            stop_loss = entry_price - (1.5 * atr_value)
            take_profit = entry_price + (3.0 * atr_value)
        else:  # SELL — inverted logic for short-side measurement
            stop_loss = entry_price + (1.5 * atr_value)
            take_profit = entry_price - (3.0 * atr_value)

    # Walk forward through the holding window
    max_bar = min(entry_idx + 1 + holding_days, len(df))
    future_slice = df.iloc[entry_idx + 1: max_bar]

    if future_slice.empty:
        return None

    exit_price = None
    exit_date = None
    exit_reason = 'HOLD_EXPIRED'
    actual_holding = 0

    for offset, (_, bar) in enumerate(future_slice.iterrows(), start=1):
        bar_high = float(bar['high'])
        bar_low = float(bar['low'])
        bar_close = float(bar['close'])

        if direction == 'BUY':
            # Check stop-loss first (conservative — assume worst case hit)
            if stop_loss is not None and bar_low <= stop_loss:
                exit_price = stop_loss
                exit_date = bar['date']
                exit_reason = 'STOP_LOSS'
                actual_holding = offset
                break
            # Check take-profit
            if take_profit is not None and bar_high >= take_profit:
                exit_price = take_profit
                exit_date = bar['date']
                exit_reason = 'TAKE_PROFIT'
                actual_holding = offset
                break
        else:  # SELL direction
            if stop_loss is not None and bar_high >= stop_loss:
                exit_price = stop_loss
                exit_date = bar['date']
                exit_reason = 'STOP_LOSS'
                actual_holding = offset
                break
            if take_profit is not None and bar_low <= take_profit:
                exit_price = take_profit
                exit_date = bar['date']
                exit_reason = 'TAKE_PROFIT'
                actual_holding = offset
                break

    # If neither SL nor TP was hit, exit at close of last bar in window
    if exit_price is None:
        exit_price = float(future_slice.iloc[-1]['close'])
        exit_date = future_slice.iloc[-1]['date']
        actual_holding = len(future_slice)

    # Calculate return
    if direction == 'BUY':
        return_pct = ((exit_price - entry_price) / entry_price) * 100
    else:
        return_pct = ((entry_price - exit_price) / entry_price) * 100

    return {
        'entry_price': entry_price,
        'exit_price': exit_price,
        'entry_date': entry_date,
        'exit_date': exit_date,
        'return_pct': return_pct,
        'holding_days': actual_holding,
        'exit_reason': exit_reason,
        'is_winner': return_pct > 0,
    }


# ──────────────────────────────────────────────────────────────────────
# Main engine entry point
# ──────────────────────────────────────────────────────────────────────

def run_backtest(holding_days=10, signal_type_filter=None, symbols_filter=None,
                 progress_callback=None):
    """
    Run the full backtest across all stocks and signal types.

    Args:
        holding_days: max bars to hold a position (default 10 for daily,
                      engine uses 20 for weekly signals automatically)
        signal_type_filter: optional single signal type string to test
        symbols_filter: optional list of stock symbols to limit scope
        progress_callback: optional callable(current, total, symbol) for
                           progress reporting

    Returns:
        dict keyed by (signal_type, direction) → list of trade result dicts
    """
    # Collect all trades keyed by (signal_type, direction)
    all_trades = defaultdict(list)

    # Build queryset
    stocks_qs = Stock.objects.all().order_by('symbol')
    if symbols_filter:
        stocks_qs = stocks_qs.filter(symbol__in=symbols_filter)

    stock_list = list(stocks_qs)
    total_stocks = len(stock_list)

    for stock_idx, stock in enumerate(stock_list):
        if progress_callback:
            progress_callback(stock_idx + 1, total_stocks, stock.symbol)

        # ── Daily signals ────────────────────────────────────────────
        df = get_stock_dataframe(stock)
        if df.empty or len(df) < 50:
            continue

        df = calculate_indicators(df)

        # Pre-load fundamental snapshots to avoid N+1 query problem in loop
        snapshots = list(FundamentalSnapshot.objects.filter(stock=stock).order_by('date'))

        # Track cooldowns per signal type to prevent overlapping trades
        # cooldown[signal_type] = bar index when cooldown expires
        cooldown = defaultdict(int)

        min_bar = 50  # need enough history for indicators to stabilise

        for i in range(min_bar, len(df)):
            signals = _detect_signals_at_bar(df, i, stock=stock, snapshots=snapshots)

            for sig in signals:
                st = sig['signal_type']
                direction = sig['direction']

                # Apply optional filter
                if signal_type_filter and st != signal_type_filter:
                    continue

                # Check cooldown
                cooldown_key = f"{st}_{direction}"
                if i < cooldown[cooldown_key]:
                    continue

                # Get ATR at entry bar for SL/TP
                atr_val = df.iloc[i].get('atr')
                if atr_val is None:
                    atr_val = 0

                trade = _simulate_trade(df, i, holding_days, direction,
                                        atr_value=float(atr_val))
                if trade:
                    trade['symbol'] = stock.symbol
                    all_trades[(st, direction)].append(trade)
                    # Set cooldown
                    cooldown[cooldown_key] = i + holding_days

        # ── Weekly signals ───────────────────────────────────────────
        if signal_type_filter and signal_type_filter != 'WEEKLY_SMA_CROSS':
            continue

        df_weekly = resample_weekly_dataframe(df)
        if df_weekly.empty or len(df_weekly) < 50:
            continue

        df_weekly['sma20'] = df_weekly['close'].rolling(window=20, min_periods=1).mean()
        df_weekly['sma50'] = df_weekly['close'].rolling(window=50, min_periods=1).mean()

        weekly_holding = max(holding_days, 20)  # min 4 weeks for weekly signals
        weekly_cooldown = defaultdict(int)

        for i in range(50, len(df_weekly)):
            w_signals = _detect_weekly_signals_at_bar(df_weekly, i)
            for sig in w_signals:
                st = sig['signal_type']
                direction = sig['direction']
                cooldown_key = f"{st}_{direction}"

                if i < weekly_cooldown[cooldown_key]:
                    continue

                # Weekly bars don't have ATR — simulate without SL/TP
                trade = _simulate_trade(df_weekly, i, weekly_holding, direction,
                                        atr_value=None)
                if trade:
                    trade['symbol'] = stock.symbol
                    all_trades[(st, direction)].append(trade)
                    weekly_cooldown[cooldown_key] = i + weekly_holding

    return all_trades


def aggregate_results(all_trades):
    """
    Aggregate raw trade lists into summary metrics per (signal_type, direction).

    Returns:
        list of dicts, each with keys matching BacktestResult fields.
    """
    summaries = []

    for (signal_type, direction), trades in sorted(all_trades.items()):
        if not trades:
            continue

        returns = [t['return_pct'] for t in trades]
        holdings = [t['holding_days'] for t in trades]
        winners = [t for t in trades if t['is_winner']]
        losers = [t for t in trades if not t['is_winner']]

        total = len(trades)
        win_count = len(winners)
        lose_count = len(losers)

        summaries.append({
            'signal_type': signal_type,
            'direction': direction,
            'total_trades': total,
            'winning_trades': win_count,
            'losing_trades': lose_count,
            'win_rate': round((win_count / total) * 100, 2) if total > 0 else 0.0,
            'avg_return_pct': round(float(np.mean(returns)), 2) if returns else 0.0,
            'avg_holding_days': round(float(np.mean(holdings)), 1) if holdings else 0.0,
            'max_drawdown_pct': round(float(min(returns)), 2) if returns else 0.0,
            'best_trade_pct': round(float(max(returns)), 2) if returns else 0.0,
        })

    return summaries
