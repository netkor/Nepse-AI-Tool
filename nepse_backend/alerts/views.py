"""
Views for Alerts app.
Handles watchlist and price alert management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from stocks.models import Stock
from .models import Watchlist, PriceAlert
from .serializers import (
    WatchlistSerializer,
    PriceAlertSerializer,
    PriceAlertCreateSerializer,
)
from .services import AlertService


# ============================================================
# WATCHLIST ENDPOINTS
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def watchlist(request):
    """
    Get or manage user's watchlist.
    GET /api/alerts/watchlist/ - Get watchlist
    POST /api/alerts/watchlist/ - Add stock to watchlist (stock_id in body)
    """
    if request.method == 'GET':
        watchlist_obj = AlertService.get_watchlist(request.user)
        serializer = WatchlistSerializer(watchlist_obj)
        
        return Response(
            {
                'success': True,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        stock_id = request.data.get('stock_id')
        
        if not stock_id:
            return Response(
                {
                    'success': False,
                    'message': 'stock_id is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock = Stock.objects.get(id=stock_id)
        except Stock.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': 'Stock not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        added = AlertService.add_to_watchlist(request.user, stock)
        
        if not added:
            return Response(
                {
                    'success': False,
                    'message': 'Stock is already in your watchlist.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        watchlist_obj = AlertService.get_watchlist(request.user)
        serializer = WatchlistSerializer(watchlist_obj)
        
        return Response(
            {
                'success': True,
                'message': f'Stock {stock.symbol} added to watchlist.',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def watchlist_remove(request, stock_id):
    """
    Remove stock from watchlist.
    DELETE /api/alerts/watchlist/{stock_id}/
    """
    try:
        stock = Stock.objects.get(id=stock_id)
    except Stock.DoesNotExist:
        return Response(
            {
                'success': False,
                'message': 'Stock not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    removed = AlertService.remove_from_watchlist(request.user, stock)
    
    if not removed:
        return Response(
            {
                'success': False,
                'message': 'Stock is not in your watchlist.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(
        {
            'success': True,
            'message': f'Stock {stock.symbol} removed from watchlist.'
        },
        status=status.HTTP_200_OK
    )


# ============================================================
# PRICE ALERT ENDPOINTS
# ============================================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def price_alerts(request):
    """
    Get or create price alerts.
    GET /api/alerts/price/ - Get user's price alerts
    POST /api/alerts/price/ - Create new price alert
    """
    if request.method == 'GET':
        status_filter = request.query_params.get('status')
        alerts = AlertService.get_user_alerts(request.user, status=status_filter)
        serializer = PriceAlertSerializer(alerts, many=True)
        
        return Response(
            {
                'success': True,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )

    elif request.method == 'POST':
        serializer = PriceAlertCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Invalid data.',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stock = Stock.objects.get(id=serializer.validated_data['stock_id'])
        except Stock.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'message': 'Stock not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            alert = AlertService.create_price_alert(
                user=request.user,
                stock=stock,
                min_price=serializer.validated_data.get('min_price'),
                max_price=serializer.validated_data.get('max_price'),
            )
        except ValueError as e:
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alert_serializer = PriceAlertSerializer(alert)
        return Response(
            {
                'success': True,
                'message': 'Price alert created successfully.',
                'data': alert_serializer.data
            },
            status=status.HTTP_201_CREATED
        )


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def price_alert_detail(request, alert_id):
    """
    Update or delete a price alert.
    PATCH /api/alerts/price/{id}/ - Update alert
    DELETE /api/alerts/price/{id}/ - Delete alert
    """
    try:
        alert = PriceAlert.objects.get(id=alert_id, user=request.user)
    except PriceAlert.DoesNotExist:
        return Response(
            {
                'success': False,
                'message': 'Alert not found.'
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'PATCH':
        serializer = PriceAlertSerializer(alert, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Invalid data.',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        return Response(
            {
                'success': True,
                'message': 'Alert updated successfully.',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    elif request.method == 'DELETE':
        alert.delete()
        return Response(
            {
                'success': True,
                'message': 'Alert deleted successfully.'
            },
            status=status.HTTP_200_OK
        )
