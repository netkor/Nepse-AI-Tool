from rest_framework import serializers
from .models import Watchlist, Alert
from stocks.serializers import StockSerializer

class WatchlistSerializer(serializers.ModelSerializer):
    stock_details = StockSerializer(source='stock', read_only=True)

    class Meta:
        model = Watchlist
        fields = ['id', 'user', 'stock', 'stock_details', 'added_at']
        read_only_fields = ['user']

class AlertSerializer(serializers.ModelSerializer):
    stock_details = StockSerializer(source='stock', read_only=True)

    class Meta:
        model = Alert
        fields = ['id', 'user', 'stock', 'stock_details', 'alert_type', 'target_value', 'is_active', 'is_triggered', 'created_at', 'triggered_at']
        read_only_fields = ['user', 'is_triggered', 'triggered_at']
