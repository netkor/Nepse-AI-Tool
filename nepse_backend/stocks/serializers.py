"""
Serializers for Stocks app.
"""
from rest_framework import serializers
from .models import Stock, StockHistory


class StockHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for stock historical data (OHLCV).
    """
    class Meta:
        model = StockHistory
        fields = (
            'id',
            'date',
            'open_price',
            'high_price',
            'low_price',
            'close_price',
            'volume',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class StockDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single stock with history.
    """
    history = StockHistorySerializer(many=True, read_only=True)
    current_change = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = (
            'id',
            'symbol',
            'name',
            'sector',
            'price',
            'volume',
            'change_percent',
            'market_cap',
            'is_active',
            'current_change',
            'history',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_current_change(self, obj):
        """
        Calculate the change from previous day (if available).
        """
        previous = obj.history.order_by('-date').values('close_price').first()
        if previous:
            previous_close = float(previous['close_price'])
            current = float(obj.price)
            if previous_close > 0:
                return round(((current - previous_close) / previous_close) * 100, 2)
        return None


class StockListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for stock list.
    """
    class Meta:
        model = Stock
        fields = (
            'id',
            'symbol',
            'name',
            'price',
            'volume',
            'change_percent',
            'sector',
            'is_active',
            'updated_at',
        )
        read_only_fields = ('id', 'updated_at')
