import requests

BASE_URL = 'http://127.0.0.1:8000'

def verify():
    print("Verifying Advanced Signal Types API...")
    
    # 1. Login
    login_url = f"{BASE_URL}/api/auth/login/"
    try:
        response = requests.post(login_url, json={
            'username': 'admin',
            'password': 'admin'
        })
        response.raise_for_status()
        token = response.json().get('access')
    except Exception as e:
        print(f"Error logging in: {e}")
        return

    # 2. Get Signals List
    headers = {
        'Authorization': f'Bearer {token}'
    }
    signals_url = f"{BASE_URL}/api/signals/"
    try:
        response = requests.get(signals_url, headers=headers)
        response.raise_for_status()
        signals = response.json()
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return

    # Aggregate counts by category
    total = len(signals)
    price_action_buys = []
    price_action_sells = []
    mean_rev_buys = []
    mean_rev_sells = []
    div_buys = []
    div_sells = []
    dow_buys = []
    dow_sells = []

    for s in signals:
        if s['price_action'] == 'BUY':
            price_action_buys.append(s['symbol'])
        elif s['price_action'] == 'SELL':
            price_action_sells.append(s['symbol'])

        if s['mean_reversion'] == 'BUY':
            mean_rev_buys.append(s['symbol'])
        elif s['mean_reversion'] == 'SELL':
            mean_rev_sells.append(s['symbol'])

        if s['divergence'] == 'BUY':
            div_buys.append(s['symbol'])
        elif s['divergence'] == 'SELL':
            div_sells.append(s['symbol'])

        if s['dow'] == 'BUY':
            dow_buys.append(s['symbol'])
        elif s['dow'] == 'SELL':
            dow_sells.append(s['symbol'])

    print("-" * 75)
    print(f"Advanced Scans Statistics Summary (Total Stocks Analyzed: {total}):")
    print("-" * 75)
    print(f"1. Price Action Signals (MA Crossovers & Volume Breaks):")
    print(f"   - 🟢 BUY Triggers:  {len(price_action_buys)} stocks {price_action_buys[:5]}")
    print(f"   - 🔴 SELL Triggers: {len(price_action_sells)} stocks {price_action_sells[:5]}")
    print("-" * 75)
    print(f"2. Mean Reversion Signals (RSI Extremes):")
    print(f"   - 🟢 BUY Triggers (RSI <= 30):  {len(mean_rev_buys)} stocks {mean_rev_buys[:5]}")
    print(f"   - 🔴 SELL Triggers (RSI >= 70): {len(mean_rev_sells)} stocks {mean_rev_sells[:5]}")
    print("-" * 75)
    print(f"3. Divergence Signals (Price Pivot vs RSI Peak Divergence):")
    print(f"   - 🟢 BUY Triggers (Bullish):   {len(div_buys)} stocks {div_buys[:5]}")
    print(f"   - 🔴 SELL Triggers (Bearish):  {len(div_sells)} stocks {div_sells[:5]}")
    print("-" * 75)
    print(f"4. Dow Theory Structural Signals (Higher Highs / Lower Lows):")
    print(f"   - 🟢 BUY Triggers (Up Pivot):   {len(dow_buys)} stocks {dow_buys[:5]}")
    print(f"   - 🔴 SELL Triggers (Down Pivot): {len(dow_sells)} stocks {dow_sells[:5]}")
    print("-" * 75)

    print("\nSUCCESS: Calculated advanced category indicators successfully!")

if __name__ == "__main__":
    verify()
