from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import pandas as pd
import numpy as np
from stocks.models import Stock, StockHistory
from .calculators import (
    get_stock_dataframe, calculate_indicators, get_active_signal,
    resample_weekly_dataframe, get_weekly_signals, calculate_seasonal_returns,
    calculate_confluence_score
)
from datetime import date, timedelta
from django.db.models import Q
from stocks.models import MarketEvent

def get_upcoming_events(stock):
    today = date.today()
    events = MarketEvent.objects.filter(
        event_date__gte=today,
        event_date__lte=today + timedelta(days=30)
    ).filter(Q(stock=stock) | Q(stock__isnull=True)).order_by('event_date')
    
    event_list = []
    for e in events:
        days_away = (e.event_date - today).days
        event_list.append({
            'title': e.title,
            'type': e.get_event_type_display(),
            'date': e.event_date.strftime('%Y-%m-%d'),
            'days_away': days_away
        })
    
    annotation = None
    if event_list:
        next_event = event_list[0]
        annotation = f"{next_event['title']} in {next_event['days_away']} days"
        
    return event_list, annotation


class SignalsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        min_turnover = request.query_params.get('min_turnover')
        if min_turnover:
            try:
                min_turnover = float(min_turnover)
            except ValueError:
                min_turnover = None

        stocks = Stock.objects.all().order_by('symbol')
        active_signals = []

        for stock in stocks:
            df = get_stock_dataframe(stock, limit=65)
            if df.empty or len(df) < 2:
                continue

            df = calculate_indicators(df)
            
            # Apply liquidity filter
            if min_turnover is not None:
                latest_avg_turnover = df.iloc[-1].get('avg_turnover20')
                if latest_avg_turnover is None or latest_avg_turnover < min_turnover:
                    continue

            signal = get_active_signal(df)
            events, annotation = get_upcoming_events(stock)
            
            active_signals.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'price': float(stock.current_price),
                'change_percentage': float(stock.change_percentage),
                'recommendation': signal['recommendation'],
                'rsi_value': signal['rsi_value'],
                'signal_type': signal['type'],
                'signal_label': signal['signal_label'],
                'signal_desc': signal['signal_desc'],
                'price_action': signal['price_action'],
                'mean_reversion': signal['mean_reversion'],
                'divergence': signal['divergence'],
                'dow': signal['dow'],
                'stop_loss': signal['stop_loss'],
                'take_profit': signal['take_profit'],
                'trailing_sl': signal['trailing_sl'],
                'signals_list': signal['signals'],
                'upcoming_events': events,
                'event_annotation': annotation
            })

        return Response(active_signals)

class StockSignalsDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            return Response(
                {"detail": f"Stock {symbol} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        df = get_stock_dataframe(stock)
        if df.empty:
            return Response([])

        df = calculate_indicators(df)
        
        chart_data = []
        for _, row in df.iterrows():
            chart_data.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'],
                'sma20': row['sma20'],
                'sma50': row['sma50'],
                'vol_ma20': row['vol_ma20'],
                'rsi': row['rsi'],
            })

        return Response(chart_data)

class MarketSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_history = StockHistory.objects.order_by('-date').first()
        if not latest_history:
            return Response({"detail": "No market history found."}, status=status.HTTP_404_NOT_FOUND)
        
        latest_date = latest_history.date
        distinct_dates = list(StockHistory.objects.order_by('-date').values_list('date', flat=True).distinct()[:2])
        prev_date = distinct_dates[1] if len(distinct_dates) > 1 else None

        latest_rows = StockHistory.objects.filter(date=latest_date).select_related('stock')
        prev_rows = StockHistory.objects.filter(date=prev_date) if prev_date else []
        prev_close_map = {row.stock_id: float(row.close_price) for row in prev_rows}

        advances = 0
        declines = 0
        unchanged = 0
        total_volume = 0
        total_amount = 0.0
        
        turnover_list = []
        for r in latest_rows:
            close = float(r.close_price)
            prev = prev_close_map.get(r.stock_id, float(r.open_price))
            diff = close - prev
            pct = (diff / prev) * 100 if prev > 0 else 0.0
            
            if diff > 0.01:
                advances += 1
            elif diff < -0.01:
                declines += 1
            else:
                unchanged += 1

            vol = int(r.volume)
            turnover = close * vol
            
            total_volume += vol
            total_amount += turnover

            turnover_list.append({
                'symbol': r.stock.symbol,
                'name': r.stock.name,
                'price': close,
                'change_percentage': pct,
                'volume': vol,
                'turnover': turnover
            })

        turnover_list.sort(key=lambda x: x['turnover'], reverse=True)
        top_turnover = turnover_list[:5]

        stocks = Stock.objects.all()
        buy_count = 0
        sell_count = 0
        hold_count = 0
        total_signals = 0

        for stock in stocks:
            df = get_stock_dataframe(stock, limit=65)
            if df.empty or len(df) < 50:
                hold_count += 1
                total_signals += 1
                continue

            df = calculate_indicators(df)
            signal = get_active_signal(df)
            sig_type = signal['type']
            if signal['recommendation'] == 'BUY' or sig_type == 'BULLISH_HOLD':
                buy_count += 1
            elif signal['recommendation'] == 'SELL' or sig_type == 'BEARISH_HOLD':
                sell_count += 1
            else:
                hold_count += 1
            total_signals += 1

        total_signals = total_signals if total_signals > 0 else 1
        buy_pct = (buy_count / total_signals) * 100
        sell_pct = (sell_count / total_signals) * 100
        hold_pct = (hold_count / total_signals) * 100

        base_index = 2653.40
        avg_change_pct = sum(x['change_percentage'] for x in turnover_list) / len(turnover_list) if turnover_list else 0.0
        index_change = base_index * (avg_change_pct / 100.0)
        simulated_index = base_index + index_change

        return Response({
            'date': latest_date.strftime('%Y-%m-%d'),
            'nepse_index': round(simulated_index, 2),
            'nepse_change': round(index_change, 2),
            'nepse_change_percentage': round(avg_change_pct, 2),
            'total_volume': total_volume,
            'total_amount': round(total_amount, 2),
            'advances': advances,
            'declines': declines,
            'unchanged': unchanged,
            'buy_pressure_pct': round(buy_pct, 1),
            'sell_pressure_pct': round(sell_pct, 1),
            'neutral_pressure_pct': round(hold_pct, 1),
            'top_turnover': top_turnover
        })

# ----------------------------------------------------------------------
# NEW Views: Weekly Signals, Bulk Transactions, and Seasonal Effect
# ----------------------------------------------------------------------
class WeeklySignalsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stocks = Stock.objects.all().order_by('symbol')
        weekly_signals = []

        for stock in stocks:
            df = get_stock_dataframe(stock, limit=300)
            if df.empty or len(df) < 50:
                continue

            df_weekly = resample_weekly_dataframe(df)
            if df_weekly.empty or len(df_weekly) < 50:
                continue

            signal = get_weekly_signals(df_weekly)
            
            weekly_signals.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'price': float(stock.current_price),
                'change_percentage': float(stock.change_percentage),
                'recommendation': signal['recommendation'],
                'signal_type': signal['type'],
                'signal_label': signal['signal_label'],
                'signal_desc': signal['signal_desc'],
            })

        return Response(weekly_signals)

class BulkTransactionsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_history = StockHistory.objects.order_by('-date').first()
        if not latest_history:
            return Response([])
        
        latest_date = latest_history.date
        distinct_dates = list(StockHistory.objects.order_by('-date').values_list('date', flat=True).distinct()[:2])
        prev_date = distinct_dates[1] if len(distinct_dates) > 1 else None

        # Load latest rows and previous close map for change pct
        latest_rows = StockHistory.objects.filter(date=latest_date).select_related('stock')
        prev_rows = StockHistory.objects.filter(date=prev_date) if prev_date else []
        prev_close_map = {row.stock_id: float(row.close_price) for row in prev_rows}

        bulk_trades = []
        for r in latest_rows:
            close = float(r.close_price)
            vol = int(r.volume)
            turnover = close * vol
            
            # Threshold: Volume > 120,000 shares OR Turnover > Rs. 80 Lakhs (8000000)
            if vol > 120000 or turnover > 8000000.0:
                prev = prev_close_map.get(r.stock_id, float(r.open_price))
                pct = ((close - prev) / prev) * 100 if prev > 0 else 0.0

                bulk_trades.append({
                    'symbol': r.stock.symbol,
                    'name': r.stock.name,
                    'price': close,
                    'change_percentage': round(pct, 2),
                    'volume': vol,
                    'turnover': round(turnover, 2),
                })
        
        # Sort by turnover descending
        bulk_trades.sort(key=lambda x: x['turnover'], reverse=True)
        return Response(bulk_trades)

class SeasonalPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, symbol):
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            return Response(
                {"detail": f"Stock {symbol} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        df = get_stock_dataframe(stock)
        seasonal_data = calculate_seasonal_returns(df)
        return Response(seasonal_data)

class CustomStrategyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        min_turnover = request.query_params.get('min_turnover')
        if min_turnover:
            try:
                min_turnover = float(min_turnover)
            except ValueError:
                min_turnover = None

        stocks = Stock.objects.all().order_by('symbol')
        matches = []

        def get_fundamental_trends(symbol):
            # Mock fundamental data for the screener
            strong_stocks = ['NABIL', 'API', 'CBBL', 'GBIME', 'NICA', 'NLIC', 'CIT', 'EBL', 'KBL', 'NBL']
            moderate_stocks = ['GBBL', 'PCBL', 'SHIVM', 'CHDC', 'NIL', 'SICL', 'SANIMA']
            
            if symbol in strong_stocks:
                return {'eps': 'Upward', 'roe': 'Strong', 'net_profit': 'Upward', 'pe_ratio': 'Undervalued', 'verdict': 'Prioritized (Strong Fundamentals)'}
            elif symbol in moderate_stocks:
                return {'eps': 'Stable', 'roe': 'Average', 'net_profit': 'Stable', 'pe_ratio': 'Fair', 'verdict': 'Moderate'}
            else:
                return {'eps': 'Flat / N/A', 'roe': 'Flat / N/A', 'net_profit': 'Flat / N/A', 'pe_ratio': 'High/NA', 'verdict': 'Neutral / Avoid'}

        for stock in stocks:
            df = get_stock_dataframe(stock, limit=65)
            if df.empty or len(df) < 50:
                continue

            df = calculate_indicators(df)
            
            # Apply liquidity filter
            if min_turnover is not None:
                latest_avg_turnover = df.iloc[-1].get('avg_turnover20')
                if latest_avg_turnover is None or latest_avg_turnover < min_turnover:
                    continue

            signal = get_active_signal(df)
            fundamentals = get_fundamental_trends(stock.symbol)

            # High Conviction Criteria: Buy signal + Strong/Moderate fundamentals
            if signal['recommendation'] == 'BUY' and fundamentals['verdict'] in ['Prioritized (Strong Fundamentals)', 'Moderate']:
                last_row = df.iloc[-1]
                events, annotation = get_upcoming_events(stock)
                matches.append({
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'price': float(last_row['close']),
                    'volume': int(last_row['volume']),
                    'eps_trend': fundamentals['eps'],
                    'roe_trend': fundamentals['roe'],
                    'pe_ratio': fundamentals['pe_ratio'],
                    'fundamental_verdict': fundamentals['verdict'],
                    'technical_label': signal['signal_label'],
                    'tp_level': signal['take_profit'],
                    'sl_level': signal['stop_loss'],
                    'upcoming_events': events,
                    'event_annotation': annotation
                })

        return Response(matches)


class ConfluenceSignalsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        min_turnover = request.query_params.get('min_turnover')
        if min_turnover:
            try:
                min_turnover = float(min_turnover)
            except ValueError:
                min_turnover = None

        stocks = Stock.objects.all().order_by('symbol')
        results = []

        for stock in stocks:
            df = get_stock_dataframe(stock, limit=65)
            if df.empty or len(df) < 50:
                continue

            df = calculate_indicators(df)
            
            # Apply liquidity filter
            if min_turnover is not None:
                latest_avg_turnover = df.iloc[-1].get('avg_turnover20')
                if latest_avg_turnover is None or latest_avg_turnover < min_turnover:
                    continue

            confluence = calculate_confluence_score(df, stock=stock)
            events, annotation = get_upcoming_events(stock)
            
            results.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'price': float(stock.current_price),
                'change_percentage': float(stock.change_percentage),
                'confluence_score': confluence['score'],
                'recommendation': confluence['recommendation'],
                'technical_score': confluence['technical_score'],
                'technical_details': confluence['technical_details'],
                'fundamental_penalty_pct': confluence['fundamental_penalty_pct'],
                'fundamental_details': confluence['fundamental_details'],
                'upcoming_events': events,
                'event_annotation': annotation
            })

        # Sort by confluence score descending
        results.sort(key=lambda x: x['confluence_score'], reverse=True)
        return Response(results)

