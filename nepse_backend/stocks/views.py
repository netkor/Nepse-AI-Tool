"""
Views for Stocks app.
Handles stock data and historical information.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Stock, StockHistory
from .serializers import StockListSerializer, StockDetailSerializer, StockHistorySerializer


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for stocks.
    GET /api/stocks/ - List all stocks
    GET /api/stocks/{id}/ - Get stock details
    """
    queryset = Stock.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['sector', 'is_active']
    search_fields = ['symbol', 'name']
    ordering_fields = ['symbol', 'price', 'change_percent', 'volume']
    ordering = ['symbol']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StockDetailSerializer
        return StockListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by sector if provided
        sector = self.request.query_params.get('sector')
        if sector:
            queryset = queryset.filter(sector=sector)
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_history(request, symbol):
    """
    Get historical data for a specific stock.
    GET /api/stocks/{symbol}/history/?days=90
    """
    try:
        stock = Stock.objects.get(symbol=symbol.upper())
    except Stock.DoesNotExist:
        return Response(
            {
                'success': False,
                'message': f'Stock with symbol {symbol} not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # Get number of days (default 90)
    days = int(request.query_params.get('days', 90))
    
    history = stock.history.all()[:days]
    serializer = StockHistorySerializer(history, many=True)
    
    return Response(
        {
            'success': True,
            'data': {
                'stock': {
                    'id': stock.id,
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'current_price': float(stock.price),
                },
                'history': serializer.data
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_statistics(request):
    """
    Get market statistics.
    GET /api/stocks/statistics/overview/
    """
    stocks = Stock.objects.filter(is_active=True)
    
    total_stocks = stocks.count()
    avg_change = sum(float(s.change_percent) for s in stocks) / total_stocks if total_stocks > 0 else 0
    gainers = stocks.filter(change_percent__gt=0).count()
    losers = stocks.filter(change_percent__lt=0).count()
    total_volume = sum(s.volume for s in stocks)
    
    return Response(
        {
            'success': True,
            'data': {
                'total_stocks': total_stocks,
                'gainers': gainers,
                'losers': losers,
                'average_change_percent': round(avg_change, 2),
                'total_volume': total_volume,
            }
        },
        status=status.HTTP_200_OK
    )
