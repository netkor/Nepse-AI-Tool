"""
Views for Signals app.
Handles trading signal retrieval and filtering.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from stocks.models import Stock
from .models import Signal
from .serializers import SignalSerializer


class SignalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for signals.
    GET /api/signals/ - List signals
    GET /api/signals/{id}/ - Get signal detail
    """
    queryset = Signal.objects.select_related('stock').order_by('-created_at')
    serializer_class = SignalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['stock', 'signal_type', 'is_notified']
    search_fields = ['stock__symbol', 'stock__name', 'reason']
    ordering_fields = ['confidence_score', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by confidence score if provided
        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            try:
                confidence = int(min_confidence)
                queryset = queryset.filter(confidence_score__gte=confidence)
            except ValueError:
                pass
        
        # Filter by signal type
        signal_type = self.request.query_params.get('signal_type')
        if signal_type in ['BUY', 'SELL', 'ALERT']:
            queryset = queryset.filter(signal_type=signal_type)
        
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def signals_by_stock(request, stock_symbol):
    """
    Get signals for a specific stock.
    GET /api/signals/stock/{symbol}/
    """
    try:
        stock = Stock.objects.get(symbol=stock_symbol.upper())
    except Stock.DoesNotExist:
        return Response(
            {
                'success': False,
                'message': f'Stock {stock_symbol} not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get signals for the stock
    signals = Signal.objects.filter(stock=stock).order_by('-created_at')[:20]
    serializer = SignalSerializer(signals, many=True)
    
    return Response(
        {
            'success': True,
            'data': {
                'stock': {
                    'id': stock.id,
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'price': float(stock.price),
                },
                'signals': serializer.data,
                'total_signals': signals.count(),
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_signal_notified(request, signal_id):
    """
    Mark a signal as notified.
    POST /api/signals/{id}/mark-notified/
    """
    try:
        signal = Signal.objects.get(id=signal_id)
    except Signal.DoesNotExist:
        return Response(
            {
                'success': False,
                'message': 'Signal not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    signal.is_notified = True
    signal.save()
    
    return Response(
        {
            'success': True,
            'message': 'Signal marked as notified.'
        },
        status=status.HTTP_200_OK
    )
