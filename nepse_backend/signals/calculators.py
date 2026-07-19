import pandas as pd
import numpy as np
from stocks.models import Stock, StockHistory

def get_stock_dataframe(stock, limit=None):
    """
    Fetches history for a stock and returns a pandas DataFrame.
    """
    history = StockHistory.objects.filter(stock=stock).order_by('date')
    if limit:
        history_list = list(history.order_by('-date')[:limit])
        history_list.reverse()
    else:
        history_list = list(history)

    if not history_list:
        return pd.DataFrame()

    data = {
        'date': [h.date for h in history_list],
        'open': [float(h.open_price) for h in history_list],
        'high': [float(h.high_price) for h in history_list],
        'low': [float(h.low_price) for h in history_list],
        'close': [float(h.close_price) for h in history_list],
        'volume': [int(h.volume) for h in history_list],
    }
    return pd.DataFrame(data)

def calculate_indicators(df):
    """
    Calculates SMA, EMA, MACD, Volume MA, ATR, and 14-day RSI on a DataFrame.
    """
    if df.empty or len(df) < 2:
        return df
        
    df['turnover'] = df['close'] * df['volume']
    df['avg_turnover20'] = df['turnover'].rolling(window=20, min_periods=1).mean()
        
    df['sma20'] = df['close'].rolling(window=20, min_periods=1).mean()
    df['sma50'] = df['close'].rolling(window=50, min_periods=1).mean()
    
    # EMA
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    df['vol_ma20'] = df['volume'].rolling(window=20, min_periods=1).mean()
    
    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(window=14, min_periods=1).mean()
    
    # Vectorized RSI 14-day calculation using Wilder's smoothing
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    df['avg_gain'] = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    df['avg_loss'] = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    
    rs = df['avg_gain'] / df['avg_loss']
    df['rsi'] = 100 - (100 / (1 + rs))

    # Pre-calculate peak/valley flags for high-performance scanners
    close_vals = df['close'].astype(float)
    df['valley'] = (close_vals < close_vals.shift(1)) & (close_vals < close_vals.shift(-1))
    df['peak'] = (close_vals > close_vals.shift(1)) & (close_vals > close_vals.shift(-1))

    df = df.replace({np.nan: None})
    return df

def get_active_signal(df):
    """
    Scans the DataFrame for multiple signal category indicators.
    """
    latest_close = float(df.iloc[-1]['close']) if not df.empty else 0.0
    latest_rsi = df.iloc[-1].get('rsi') if not df.empty else None
    
    output = {
        'recommendation': 'HOLD',
        'type': 'NEUTRAL',
        'rsi_value': round(latest_rsi, 1) if latest_rsi is not None else None,
        'stop_loss': None,
        'take_profit': None,
        'trailing_sl': None,
        'signals': [],
        'price_action': 'HOLD',
        'mean_reversion': 'HOLD',
        'divergence': 'HOLD',
        'dow': 'HOLD',
        'signal_label': 'HOLD (Neutral)',
        'signal_desc': 'The stock is in a neutral range. Monitor for upcoming trend breakouts.'
    }

    if df.empty or len(df) < 50:
        output['signal_desc'] = 'Not enough historical data to run technical indicators.'
        return output

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    sma20_latest = latest.get('sma20')
    sma50_latest = latest.get('sma50')
    ema20_latest = latest.get('ema20')
    ema50_latest = latest.get('ema50')
    ema20_prev = prev.get('ema20')
    ema50_prev = prev.get('ema50')
    macd_latest = latest.get('macd')
    macd_signal_latest = latest.get('macd_signal')
    macd_prev = prev.get('macd')
    macd_signal_prev = prev.get('macd_signal')
    rsi_latest = latest.get('rsi')
    atr_latest = latest.get('atr')

    signals_triggered = []

    # Category 1: Price Action
    if None not in (ema20_latest, ema50_latest, ema20_prev, ema50_prev):
        if ema20_prev <= ema50_prev and ema20_latest > ema50_latest:
            output['price_action'] = 'BUY'
            signals_triggered.append({
                'category': 'PRICE_ACTION',
                'recommendation': 'BUY',
                'label': 'Golden Cross (EMA)',
                'desc': 'Bullish Trigger: The 20-day EMA crossed above the 50-day EMA. Strong upward momentum.'
            })
        elif ema20_prev >= ema50_prev and ema20_latest < ema50_latest:
            output['price_action'] = 'SELL'
            signals_triggered.append({
                'category': 'PRICE_ACTION',
                'recommendation': 'SELL',
                'label': 'Death Cross (EMA)',
                'desc': 'Bearish Trigger: The 20-day EMA crossed below the 50-day EMA. Downtrend warning.'
            })
            
    # Category: MACD
    if None not in (macd_latest, macd_signal_latest, macd_prev, macd_signal_prev):
        if macd_prev <= macd_signal_prev and macd_latest > macd_signal_latest:
            output['price_action'] = 'BUY'
            signals_triggered.append({
                'category': 'PRICE_ACTION',
                'recommendation': 'BUY',
                'label': 'MACD Bullish Crossover',
                'desc': 'Bullish Trigger: MACD crossed above its signal line. Positive momentum starting.'
            })
        elif macd_prev >= macd_signal_prev and macd_latest < macd_signal_latest:
            output['price_action'] = 'SELL'
            signals_triggered.append({
                'category': 'PRICE_ACTION',
                'recommendation': 'SELL',
                'label': 'MACD Bearish Crossover',
                'desc': 'Bearish Trigger: MACD crossed below its signal line. Negative momentum starting.'
            })
            
    vol_ma = latest.get('vol_ma20')
    if vol_ma and vol_ma > 0 and latest['volume'] > (2.5 * vol_ma) and latest['close'] > prev['close']:
        output['price_action'] = 'BUY'
        times_avg = latest['volume'] / vol_ma
        signals_triggered.append({
            'category': 'PRICE_ACTION',
            'recommendation': 'BUY',
            'label': 'Volume Spike Breakout',
            'desc': f"Bullish Spike: Traded volume is {times_avg:.1f}x higher than average with rising price."
        })

    # Category 2: Mean Reversion
    if rsi_latest is not None:
        if rsi_latest <= 30:
            output['mean_reversion'] = 'BUY'
            signals_triggered.append({
                'category': 'MEAN_REVERSION',
                'recommendation': 'BUY',
                'label': 'RSI Oversold Trigger',
                'desc': f"Mean Reversion Buy: RSI is extremely oversold at {rsi_latest:.1f}. A positive price rebound is probable."
            })
        elif rsi_latest >= 70:
            output['mean_reversion'] = 'SELL'
            signals_triggered.append({
                'category': 'MEAN_REVERSION',
                'recommendation': 'SELL',
                'label': 'RSI Overbought Trigger',
                'desc': f"Mean Reversion Sell: RSI is extremely overbought at {rsi_latest:.1f}. Price is stretched; correction is likely."
            })

    # Category 3: Divergence
    if len(df) >= 30 and rsi_latest is not None:
        valleys = []
        peaks = []
        for i in range(len(df) - 25, len(df) - 1):
            if i <= 0 or i >= len(df) - 1:
                continue
            if df['close'].iloc[i] < df['close'].iloc[i-1] and df['close'].iloc[i] < df['close'].iloc[i+1]:
                valleys.append(i)
            if df['close'].iloc[i] > df['close'].iloc[i-1] and df['close'].iloc[i] > df['close'].iloc[i+1]:
                peaks.append(i)

        if len(valleys) >= 2:
            v1, v2 = valleys[-2], valleys[-1]
            price_v1, price_v2 = float(df['close'].iloc[v1]), float(df['close'].iloc[v2])
            rsi_v1 = df['rsi'].iloc[v1]
            rsi_v2 = df['rsi'].iloc[v2]
            if rsi_v1 is not None and rsi_v2 is not None:
                if price_v2 < price_v1 and rsi_v2 > rsi_v1 and rsi_v2 < 45:
                    output['divergence'] = 'BUY'
                    signals_triggered.append({
                        'category': 'DIVERGENCE',
                        'recommendation': 'BUY',
                        'label': 'RSI Bullish Divergence',
                        'desc': 'Bullish Alert: Price made a lower low but RSI formed a higher low, indicating bearish exhaustion.'
                    })

        if len(peaks) >= 2:
            p1, p2 = peaks[-2], peaks[-1]
            price_p1, price_p2 = float(df['close'].iloc[p1]), float(df['close'].iloc[p2])
            rsi_p1 = df['rsi'].iloc[p1]
            rsi_p2 = df['rsi'].iloc[p2]
            if rsi_p1 is not None and rsi_p2 is not None:
                if price_p2 > price_p1 and rsi_p2 < rsi_p1 and rsi_p2 > 55:
                    output['divergence'] = 'SELL'
                    signals_triggered.append({
                        'category': 'DIVERGENCE',
                        'recommendation': 'SELL',
                        'label': 'RSI Bearish Divergence',
                        'desc': 'Bearish Alert: Price made a higher high but RSI formed a lower high, indicating bullish exhaustion.'
                    })

    # Category 4: Dow Theory
    if len(df) >= 40:
        valleys = []
        peaks = []
        for i in range(len(df) - 40, len(df) - 1):
            if i <= 0 or i >= len(df) - 1:
                continue
            if df['close'].iloc[i] < df['close'].iloc[i-1] and df['close'].iloc[i] < df['close'].iloc[i+1]:
                valleys.append(float(df['close'].iloc[i]))
            if df['close'].iloc[i] > df['close'].iloc[i-1] and df['close'].iloc[i] > df['close'].iloc[i+1]:
                peaks.append(float(df['close'].iloc[i]))
                
        if len(valleys) >= 3 and len(peaks) >= 3:
            v1, v2, v3 = valleys[-3], valleys[-2], valleys[-1]
            p1, p2, p3 = peaks[-3], peaks[-2], peaks[-1]
            
            if p3 > p2 > p1 and v3 > v2 > v1:
                output['dow'] = 'BUY'
                signals_triggered.append({
                    'category': 'DOW',
                    'recommendation': 'BUY',
                    'label': 'Dow Higher Highs (Bullish)',
                    'desc': 'Bullish Structure: Price is forming a sequence of higher highs and higher lows. Dow Theory BUY.'
                })
            elif p3 < p2 < p1 and v3 < v2 < v1:
                output['dow'] = 'SELL'
                signals_triggered.append({
                    'category': 'DOW',
                    'recommendation': 'SELL',
                    'label': 'Dow Lower Lows (Bearish)',
                    'desc': 'Bearish Structure: Price is forming a sequence of lower highs and lower lows. Dow Theory SELL.'
                })

    output['signals'] = signals_triggered

    buy_signals = [s for s in signals_triggered if s['recommendation'] == 'BUY']
    sell_signals = [s for s in signals_triggered if s['recommendation'] == 'SELL']

    if buy_signals:
        output['recommendation'] = 'BUY'
        output['signal_label'] = buy_signals[0]['label']
        output['signal_desc'] = buy_signals[0]['desc']
        # Risk Management: Calculate Stop Loss and Take Profit via ATR
        if atr_latest is not None:
            output['stop_loss'] = round(latest_close - (1.5 * atr_latest), 2)
            output['take_profit'] = round(latest_close + (3.0 * atr_latest), 2)
            high_10d = df['high'].tail(10).max()
            output['trailing_sl'] = round(high_10d - (1.5 * atr_latest), 2)
    elif sell_signals:
        output['recommendation'] = 'SELL'
        output['signal_label'] = sell_signals[0]['label']
        output['signal_desc'] = sell_signals[0]['desc']
    else:
        output['recommendation'] = 'HOLD'
        if ema20_latest and ema50_latest and ema20_latest > ema50_latest:
            output['type'] = 'BULLISH_HOLD'
            output['signal_label'] = 'HOLD (Bullish Trend)'
            output['signal_desc'] = 'The stock is in a stable bullish uptrend (20 EMA > 50 EMA). Hold your position.'
        else:
            output['type'] = 'BEARISH_HOLD'
            output['signal_label'] = 'HOLD (Bearish Trend)'
            output['signal_desc'] = 'The stock is in a weak bearish downtrend (20 EMA < 50 EMA). Do not buy more.'

    return output

# ----------------------------------------------------------------------
# NEW: Weekly Resampling and Crossovers Calculations
# ----------------------------------------------------------------------
def resample_weekly_dataframe(df):
    """
    Groups daily stock dataframe into weekly Friday bars.
    """
    if df.empty or len(df) < 5:
        return pd.DataFrame()
        
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    df_copy.set_index('date', inplace=True)
    
    # Resample daily bars to weekly (ending on Fridays)
    weekly = df_copy.resample('W-FRI').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Clean up empty weeks (e.g. holidays or suspensions)
    weekly.dropna(subset=['close'], inplace=True)
    weekly.reset_index(inplace=True)
    return weekly

def get_weekly_signals(df_weekly):
    """
    Calculates 20/50 weekly crossovers and returns the signal details dictionary.
    """
    output = {
        'recommendation': 'HOLD',
        'type': 'NEUTRAL',
        'signal_label': 'HOLD (Neutral)',
        'signal_desc': 'Weekly moving averages are in a neutral range.'
    }
    
    if df_weekly.empty or len(df_weekly) < 50:
        output['signal_desc'] = 'Insufficient weekly records to compute indicators.'
        return output

    # Weekly indicators
    df_weekly['sma20'] = df_weekly['close'].rolling(window=20, min_periods=1).mean()
    df_weekly['sma50'] = df_weekly['close'].rolling(window=50, min_periods=1).mean()

    latest = df_weekly.iloc[-1]
    prev = df_weekly.iloc[-2]

    sma20_latest = latest.get('sma20')
    sma50_latest = latest.get('sma50')
    sma20_prev = prev.get('sma20')
    sma50_prev = prev.get('sma50')

    if None in (sma20_latest, sma50_latest, sma20_prev, sma50_prev):
        return output

    # 1. Weekly Golden Cross Crossover
    if sma20_prev <= sma50_prev and sma20_latest > sma50_latest:
        output['recommendation'] = 'BUY'
        output['type'] = 'WEEKLY_GOLDEN_CROSS'
        output['signal_label'] = 'WEEKLY BUY (Golden Cross)'
        output['signal_desc'] = 'Macro Trend Alert! The weekly short-term average (20 SMA) crossed above the long-term average (50 SMA). This is a strong long-term BUY signal.'
    
    # 2. Weekly Death Cross Crossover
    elif sma20_prev >= sma50_prev and sma20_latest < sma50_latest:
        output['recommendation'] = 'SELL'
        output['type'] = 'WEEKLY_DEATH_CROSS'
        output['signal_label'] = 'WEEKLY SELL (Death Cross)'
        output['signal_desc'] = 'Macro Trend Alert! The weekly short-term average (20 SMA) crossed below the long-term average (50 SMA). This is a strong long-term SELL signal.'
    
    else:
        # Default trends
        if sma20_latest > sma50_latest:
            output['type'] = 'BULLISH_HOLD'
            output['signal_label'] = 'HOLD (Weekly Bullish)'
            output['signal_desc'] = 'Weekly trend is established bullish (20 SMA > 50 SMA). Hold for long term gains.'
        else:
            output['type'] = 'BEARISH_HOLD'
            output['signal_label'] = 'HOLD (Weekly Bearish)'
            output['signal_desc'] = 'Weekly trend is established bearish (20 SMA < 50 SMA). Keep cash in reserve.'

    return output

# ----------------------------------------------------------------------
# NEW: Seasonal Performance Calculations
# ----------------------------------------------------------------------
def calculate_seasonal_returns(df):
    """
    Groups historical prices by month and calculates average monthly return statistics.
    Returns list of dicts: [{'month': 'Jan', 'average_return': 2.1}, ...]
    """
    if df.empty or len(df) < 30:
        return []
        
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    
    # Resample to monthly closing prices
    monthly = df_copy.resample('ME', on='date').agg({
        'close': 'last'
    }).dropna().reset_index()
    
    if len(monthly) < 3:
        return []

    # Calculate returns percentage month-over-month
    monthly['return'] = monthly['close'].pct_change() * 100
    monthly['month_num'] = monthly['date'].dt.month
    
    # Group by calendar month and calculate average returns
    avg_returns = monthly.groupby('month_num')['return'].mean().to_dict()
    
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    
    seasonal_data = []
    for m in range(1, 13):
        avg_ret = avg_returns.get(m, 0.0)
        # Avoid NaN values
        if np.isnan(avg_ret):
            avg_ret = 0.0
        seasonal_data.append({
            'month': month_names[m],
            'average_return': round(avg_ret, 2)
        })
        
    return seasonal_data


def calculate_confluence_score(df, stock=None, date=None, snapshots=None, idx=None):
    """
    Combines technical signals into a single score bounded between -100 and +100.
    Applies fundamental gating (using snapshots active on/before `date` or latest if `date` is None).
    """
    if idx is None:
        idx = len(df) - 1

    if df.empty or len(df) < 50 or idx < 0 or idx >= len(df):
        return {
            'score': 0,
            'recommendation': 'HOLD',
            'technical_score': 0,
            'technical_details': {},
            'fundamental_penalty_pct': 0,
            'fundamental_details': {}
        }

    latest = df.iloc[idx]
    prev = df.iloc[idx - 1]

    # Initialize components
    tech_details = {}
    tech_score = 0

    # 1. EMA Cross
    ema20_latest = latest.get('ema20')
    ema50_latest = latest.get('ema50')
    ema20_prev = prev.get('ema20')
    ema50_prev = prev.get('ema50')
    if None not in (ema20_latest, ema50_latest, ema20_prev, ema50_prev):
        if ema20_prev <= ema50_prev and ema20_latest > ema50_latest:
            tech_score += 20
            tech_details['ema_cross'] = 20
        elif ema20_prev >= ema50_prev and ema20_latest < ema50_latest:
            tech_score -= 20
            tech_details['ema_cross'] = -20
        else:
            tech_details['ema_cross'] = 0

    # 2. MACD
    macd_latest = latest.get('macd')
    macd_signal_latest = latest.get('macd_signal')
    macd_prev = prev.get('macd')
    macd_signal_prev = prev.get('macd_signal')
    if None not in (macd_latest, macd_signal_latest, macd_prev, macd_signal_prev):
        if macd_prev <= macd_signal_prev and macd_latest > macd_signal_latest:
            tech_score += 20
            tech_details['macd_cross'] = 20
        elif macd_prev >= macd_signal_prev and macd_latest < macd_signal_latest:
            tech_score -= 20
            tech_details['macd_cross'] = -20
        else:
            tech_details['macd_cross'] = 0

    # 3. RSI Oversold/Overbought
    rsi_latest = latest.get('rsi')
    if rsi_latest is not None:
        if rsi_latest <= 30:
            tech_score += 15
            tech_details['rsi_oversold'] = 15
        elif rsi_latest >= 70:
            tech_score -= 15
            tech_details['rsi_overbought'] = -15
        else:
            tech_details['rsi_oversold'] = 0
            tech_details['rsi_overbought'] = 0

    # 4. RSI Divergence
    div_buy = False
    div_sell = False
    if idx >= 30 and rsi_latest is not None:
        scan_start = max(1, idx - 25)
        valley_vals = df['valley'].values[scan_start:idx]
        peak_vals = df['peak'].values[scan_start:idx]
        close_vals = df['close'].values[scan_start:idx]
        rsi_vals = df['rsi'].values[scan_start:idx]
        
        valleys = [i for i, val in enumerate(valley_vals) if val]
        peaks = [i for i, val in enumerate(peak_vals) if val]
        
        if len(valleys) >= 2:
            v1, v2 = valleys[-2], valleys[-1]
            if float(close_vals[v2]) < float(close_vals[v1]) and rsi_vals[v2] > rsi_vals[v1] and rsi_vals[v2] < 45:
                div_buy = True
        if len(peaks) >= 2:
            p1, p2 = peaks[-2], peaks[-1]
            if float(close_vals[p2]) > float(close_vals[p1]) and rsi_vals[p2] < rsi_vals[p1] and rsi_vals[p2] > 55:
                div_sell = True

    if div_buy:
        tech_score += 15
        tech_details['rsi_divergence'] = 15
    elif div_sell:
        tech_score -= 15
        tech_details['rsi_divergence'] = -15
    else:
        tech_details['rsi_divergence'] = 0

    # 5. Dow Theory
    dow_buy = False
    dow_sell = False
    if idx >= 40:
        scan_start = max(1, idx - 40)
        valley_vals = df['valley'].values[scan_start:idx]
        peak_vals = df['peak'].values[scan_start:idx]
        close_vals = df['close'].values[scan_start:idx]
        
        valleys = [float(close_vals[i]) for i, val in enumerate(valley_vals) if val]
        peaks = [float(close_vals[i]) for i, val in enumerate(peak_vals) if val]
        
        if len(valleys) >= 3 and len(peaks) >= 3:
            v1, v2, v3 = valleys[-3], valleys[-2], valleys[-1]
            p1, p2, p3 = peaks[-3], peaks[-2], peaks[-1]
            if p3 > p2 > p1 and v3 > v2 > v1:
                dow_buy = True
            elif p3 < p2 < p1 and v3 < v2 < v1:
                dow_sell = True

    if dow_buy:
        tech_score += 15
        tech_details['dow_theory'] = 15
    elif dow_sell:
        tech_score -= 15
        tech_details['dow_theory'] = -15
    else:
        tech_details['dow_theory'] = 0

    # 6. Volume Breakout
    vol_ma = latest.get('vol_ma20')
    if vol_ma and vol_ma > 0 and latest['volume'] > (2.5 * vol_ma) and latest['close'] > prev['close']:
        tech_score += 15
        tech_details['volume_breakout'] = 15
    else:
        tech_details['volume_breakout'] = 0

    # Clamp technical score between -100 and 100
    tech_score = max(-100, min(100, tech_score))

    # Fundamental Adjustments
    fund_details = {}
    penalty = 0

    if stock:
        # Retrieve fundamental snapshot
        snapshot = None
        if snapshots is not None:
            if date:
                from datetime import date as dt_date, datetime
                if isinstance(date, str):
                    date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                else:
                    date_obj = date
                for s in reversed(snapshots):
                    s_date = s.date.date() if isinstance(s.date, datetime) else s.date
                    if s_date <= date_obj:
                        snapshot = s
                        break
            else:
                snapshot = snapshots[-1] if snapshots else None
        else:
            from stocks.models import FundamentalSnapshot
            query = FundamentalSnapshot.objects.filter(stock=stock)
            if date:
                query = query.filter(date__lte=date)
            snapshot = query.order_by('-date').first()

        if snapshot:
            # Universal fundamental adjustments
            # P/E Ratio Penalty
            pe = float(snapshot.pe_ratio) if snapshot.pe_ratio is not None else None
            if pe is not None and pe > 25:
                p_pe = 20
                penalty += p_pe
                fund_details['pe_ratio_penalty'] = f"-{p_pe}% (High P/E: {pe:.1f})"

            # ROE Penalty
            roe = float(snapshot.roe) if snapshot.roe is not None else None
            if roe is not None and roe < 8.0:
                p_roe = 15
                penalty += p_roe
                fund_details['roe_penalty'] = f"-{p_roe}% (Low ROE: {roe:.1f}%)"

            # Sector-specific adjustments
            sector = stock.sector
            if sector in ['Commercial Bank', 'Development Bank']:
                # NPL Ratio Penalty
                npl = float(snapshot.npl_ratio) if snapshot.npl_ratio is not None else None
                if npl is not None and npl > 4.0:
                    p_npl = 30
                    penalty += p_npl
                    fund_details['npl_penalty'] = f"-{p_npl}% (High NPL: {npl:.2f}%)"

                # Capital Adequacy Ratio (CAR) Penalty
                car = float(snapshot.capital_adequacy_ratio) if snapshot.capital_adequacy_ratio is not None else None
                if car is not None and car < 11.0:
                    p_car = 25
                    penalty += p_car
                    fund_details['car_penalty'] = f"-{p_car}% (Low CAR: {car:.2f}%)"

    # Compute final score
    final_score = tech_score
    if tech_score > 0 and penalty > 0:
        # Reduce positive score by penalty percentage
        reduction = tech_score * (penalty / 100.0)
        final_score = max(0, int(tech_score - reduction))
    
    # Recommendations
    if final_score >= 60:
        rec = 'STRONG BUY'
    elif final_score >= 30:
        rec = 'BUY'
    elif final_score <= -60:
        rec = 'STRONG SELL'
    elif final_score <= -30:
        rec = 'SELL'
    else:
        rec = 'HOLD'

    return {
        'score': final_score,
        'recommendation': rec,
        'technical_score': tech_score,
        'technical_details': tech_details,
        'fundamental_penalty_pct': penalty,
        'fundamental_details': fund_details
    }

