"""
Abstract data provider for stock data.
Can be extended to integrate with real NEPSE API or web scrapers.
"""
from decimal import Decimal
from typing import List, Dict
from datetime import datetime, timedelta
import random


class DataProvider:
    """
    Abstract base for stock data providers.
    """
    
    def get_stocks(self) -> List[Dict]:
        """
        Get list of stocks.
        Should return: [{'symbol': 'NABIL', 'name': '...', ...}, ...]
        """
        raise NotImplementedError
    
    def get_stock_history(self, symbol: str, days: int = 90) -> List[Dict]:
        """
        Get OHLCV data for a stock.
        Should return: [{'date': '...', 'open': ..., 'high': ..., ...}, ...]
        """
        raise NotImplementedError


class MockDataProvider(DataProvider):
    """
    Mock data provider for development and testing.
    Generates realistic but fictional stock data.
    """
    
    NEPSE_STOCKS = [
        {'symbol': 'NABIL', 'name': 'Nabil Bank Limited', 'sector': 'Finance'},
        {'symbol': 'NICA', 'name': 'Nepal Insurance Company Limited', 'sector': 'Insurance'},
        {'symbol': 'SCB', 'name': 'Standard Chartered Bank Nepal', 'sector': 'Finance'},
        {'symbol': 'NIFRA', 'name': 'Nabil Infra Finance Limited', 'sector': 'Finance'},
        {'symbol': 'HIDCL', 'name': 'Himalayan Development Corporation Limited', 'sector': 'Development'},
        {'symbol': 'EBL', 'name': 'Everest Bank Limited', 'sector': 'Finance'},
        {'symbol': 'NMB', 'name': 'NMB Bank Limited', 'sector': 'Finance'},
        {'symbol': 'NIL', 'name': 'Nepal Investment Bank Limited', 'sector': 'Finance'},
        {'symbol': 'KBL', 'name': 'Kathmandu Bank Limited', 'sector': 'Finance'},
        {'symbol': 'MBL', 'name': 'Machhapuchhare Bank Limited', 'sector': 'Finance'},
        {'symbol': 'SBL', 'name': 'Siddhartha Bank Limited', 'sector': 'Finance'},
        {'symbol': 'NTC', 'name': 'Nepal Telecom Limited', 'sector': 'Telecom'},
        {'symbol': 'NTPC', 'name': 'Nepal Telecom Pvt. Limited', 'sector': 'Telecom'},
        {'symbol': 'NEA', 'name': 'Nepal Electricity Authority', 'sector': 'Energy'},
        {'symbol': 'NBBL', 'name': 'Nepal Bangladesh Bank Limited', 'sector': 'Finance'},
        {'symbol': 'BOKL', 'name': 'Bank of Kathmandu Limited', 'sector': 'Finance'},
        {'symbol': 'ADBL', 'name': 'Agricultural Development Bank Limited', 'sector': 'Finance'},
        {'symbol': 'GFCL', 'name': 'Goodwill Finance Limited', 'sector': 'Finance'},
        {'symbol': 'JBIL', 'name': 'Jbimfs Limited', 'sector': 'Finance'},
        {'symbol': 'KBBL', 'name': 'Kumari Bank Limited', 'sector': 'Finance'},
    ]
    
    def get_stocks(self) -> List[Dict]:
        """
        Return list of NEPSE stocks.
        """
        stocks = []
        for stock_data in self.NEPSE_STOCKS:
            base_price = Decimal(str(random.uniform(500, 3000)))
            change_percent = Decimal(str(random.uniform(-5, 5)))
            
            stocks.append({
                'symbol': stock_data['symbol'],
                'name': stock_data['name'],
                'sector': stock_data['sector'],
                'price': base_price,
                'volume': random.randint(10000, 500000),
                'change_percent': change_percent,
                'market_cap': random.randint(1000000000, 50000000000),
                'is_active': True,
            })
        
        return stocks
    
    def get_stock_history(self, symbol: str, days: int = 90) -> List[Dict]:
        """
        Generate mock OHLCV data for a stock.
        """
        history = []
        base_price = random.uniform(500, 3000)
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days - i - 1)
            
            # Generate realistic price movements
            daily_change = random.uniform(-2, 2)  # ±2% daily movement
            open_price = base_price + random.uniform(-10, 10)
            close_price = open_price * (1 + daily_change / 100)
            high_price = max(open_price, close_price) + random.uniform(0, abs(close_price - open_price))
            low_price = min(open_price, close_price) - random.uniform(0, abs(close_price - open_price))
            
            volume = random.randint(10000, 500000)
            
            history.append({
                'date': date.date(),
                'open_price': Decimal(str(round(open_price, 2))),
                'high_price': Decimal(str(round(high_price, 2))),
                'low_price': Decimal(str(round(low_price, 2))),
                'close_price': Decimal(str(round(close_price, 2))),
                'volume': volume,
            })
            
            base_price = close_price
        
        return history
