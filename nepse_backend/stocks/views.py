from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Stock, StockHistory, PortfolioItem, FundamentalSnapshot
from .serializers import StockSerializer, StockHistorySerializer, PortfolioItemSerializer, FundamentalSnapshotSerializer
from signals.calculators import get_stock_dataframe, calculate_indicators, get_active_signal

class StockListView(generics.ListAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Stock.objects.all().order_by('symbol')

class StockHistoryView(generics.ListAPIView):
    serializer_class = StockHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        symbol = self.kwargs['symbol']
        return StockHistory.objects.filter(stock__symbol=symbol).order_by('date')

class PortfolioListCreateView(generics.ListCreateAPIView):
    serializer_class = PortfolioItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PortfolioItem.objects.filter(user=self.request.user).order_by('stock__symbol')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class PortfolioDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PortfolioItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PortfolioItem.objects.filter(user=self.request.user)


class StockFundamentalsView(generics.ListAPIView):
    """
    GET /api/stocks/<symbol>/fundamentals/
    Returns the history of quarterly fundamental snapshots for a given stock symbol.
    """
    serializer_class = FundamentalSnapshotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        symbol = self.kwargs['symbol'].upper()
        return FundamentalSnapshot.objects.filter(stock__symbol=symbol).order_by('-date')


class SectorSummaryView(APIView):
    """
    GET /api/stocks/sectors/summary/
    Returns stock counts, average prices, and signal distributions per sector.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Avg, Count
        
        # Get count and average price grouped by sector
        sector_data = Stock.objects.exclude(sector='').values('sector').annotate(
            stock_count=Count('id'),
            avg_price=Avg('current_price')
        )

        results = []
        for item in sector_data:
            sector_name = item['sector']
            sector_stocks = Stock.objects.filter(sector=sector_name)
            
            buy_count = 0
            sell_count = 0
            hold_count = 0
            
            # Simple technical signal aggregation per sector
            for stock in sector_stocks:
                df = get_stock_dataframe(stock, limit=65)
                if df.empty or len(df) < 50:
                    hold_count += 1
                    continue
                df = calculate_indicators(df)
                signal = get_active_signal(df)
                if signal['recommendation'] == 'BUY':
                    buy_count += 1
                elif signal['recommendation'] == 'SELL':
                    sell_count += 1
                else:
                    hold_count += 1
            
            results.append({
                'sector': sector_name,
                'stock_count': item['stock_count'],
                'avg_price': round(float(item['avg_price']), 2) if item['avg_price'] else 0.0,
                'signals': {
                    'buy': buy_count,
                    'sell': sell_count,
                    'hold': hold_count,
                }
            })
            
        return Response(results)

class PortfolioRiskView(APIView):
    """
    GET /api/stocks/portfolio/risk/
    Returns portfolio sector concentration and exposure warnings.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threshold_str = request.query_params.get('threshold', '50')
        try:
            threshold = float(threshold_str)
        except ValueError:
            threshold = 50.0

        portfolio = PortfolioItem.objects.filter(user=request.user).select_related('stock')
        
        sector_allocation = {}
        total_value = 0.0

        for item in portfolio:
            current_val = float(item.balance * item.stock.current_price)
            sector = item.stock.sector or 'Others'
            
            sector_allocation[sector] = sector_allocation.get(sector, 0.0) + current_val
            total_value += current_val

        results = []
        for sector, val in sector_allocation.items():
            pct = (val / total_value) * 100 if total_value > 0 else 0.0
            is_over_exposed = (pct > threshold) and (len(portfolio) > 1)
            results.append({
                'sector': sector,
                'value': val,
                'percentage': round(pct, 2),
                'is_over_exposed': is_over_exposed
            })
            
        results.sort(key=lambda x: x['percentage'], reverse=True)

        return Response({
            'total_portfolio_value': round(total_value, 2),
            'threshold': threshold,
            'sectors': results
        })
