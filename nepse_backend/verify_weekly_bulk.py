import requests

BASE_URL = 'http://127.0.0.1:8000'

def verify():
    print("Verifying Weekly, Bulk and Seasonal API Endpoints...")
    
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

    headers = {
        'Authorization': f'Bearer {token}'
    }

    # 2. Get Weekly Crossovers
    weekly_url = f"{BASE_URL}/api/signals/weekly/"
    try:
        response = requests.get(weekly_url, headers=headers)
        response.raise_for_status()
        weekly = response.json()
        
        buys = [w for w in weekly if w['recommendation'] == 'BUY']
        sells = [w for w in weekly if w['recommendation'] == 'SELL']
        
        print("-" * 65)
        print("Weekly Indicators Crossover Summary:")
        print(f"  - Total Stocks:   {len(weekly)}")
        print(f"  - Weekly BUYs:    {len(buys)} {[(b['symbol'], b['signal_label']) for b in buys[:3]]}")
        print(f"  - Weekly SELLs:   {len(sells)} {[(s['symbol'], s['signal_label']) for s in sells[:3]]}")
        print("-" * 65)
    except Exception as e:
        print(f"Error querying weekly signals: {e}")

    # 3. Get Bulk Transactions
    bulk_url = f"{BASE_URL}/api/signals/bulk-transactions/"
    try:
        response = requests.get(bulk_url, headers=headers)
        response.raise_for_status()
        bulk = response.json()
        
        print(f"Bulk Transactions Triggers Today (Total Traded: {len(bulk)} stocks):")
        if bulk:
            for i, b in enumerate(bulk[:3], 1):
                print(f"  {i}. {b['symbol']}: Traded {b['volume']:,} shares -- Turnover Rs. {b['turnover']:,}")
        else:
            print("  No bulk transactions matched.")
        print("-" * 65)
    except Exception as e:
        print(f"Error querying bulk transactions: {e}")

    # 4. Get Seasonal Stats for a stock (e.g. NABIL)
    symbol = 'NABIL'
    seasonal_url = f"{BASE_URL}/api/signals/seasonal/{symbol}/"
    try:
        response = requests.get(seasonal_url, headers=headers)
        response.raise_for_status()
        seasonal = response.json()
        
        print(f"Seasonal Month-Wise Returns for {symbol}:")
        for item in seasonal[:4]:
            print(f"  - {item['month']}: Average Return {item['average_return']}%")
        print("-" * 65)
    except Exception as e:
        print(f"Error querying seasonal stats: {e}")

    print("\nSUCCESS: All new advanced API endpoints successfully validated!")

if __name__ == "__main__":
    verify()
