"""
Serializers for Alerts app.
"""
from rest_framework import serializers
from .models import Watchlist, WatchlistStock, PriceAlert


class WatchlistStockSerializer(serializers.ModelSerializer):
    """
    Serializer for stocks in a watchlist.
    """
    symbol = serializers.CharField(source='stock.symbol', read_only=True)
    name = serializers.CharField(source='stock.name', read_only=True)
    price = serializers.DecimalField(
        source='stock.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    change_percent = serializers.DecimalField(
        source='stock.change_percent',
        max_digits=6,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = WatchlistStock
        fields = ('id', 'symbol', 'name', 'price', 'change_percent', 'added_at')
        read_only_fields = ('id', 'added_at')


class WatchlistSerializer(serializers.ModelSerializer):
    """
    Serializer for user watchlist.
    """
    stocks = WatchlistStockSerializer(
        source='watchliststock_set',
        many=True,
        read_only=True
    )
    stock_count = serializers.SerializerMethodField()

    class Meta:
        model = Watchlist
        fields = ('id', 'stocks', 'stock_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_stock_count(self, obj):
        return obj.stocks.count()


class PriceAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for price alerts.
    """
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    current_price = serializers.DecimalField(
        source='stock.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = PriceAlert
        fields = (
            'id',
            'stock',
            'stock_symbol',
            'stock_name',
            'current_price',
            'min_price',
            'max_price',
            'status',
            'is_notified',
            'created_at',
            'updated_at',
            'triggered_at',
        )
        read_only_fields = ('id', 'is_notified', 'triggered_at', 'created_at', 'updated_at')


class PriceAlertCreateSerializer(serializers.Serializer):
    """
    Serializer for creating price alerts.
    """
    stock_id = serializers.IntegerField()
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    max_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    def validate(self, data):
        if data.get('min_price') is None and data.get('max_price') is None:
            raise serializers.ValidationError(
                'At least one of min_price or max_price must be set.'
            )
        
        if (data.get('min_price') is not None and 
            data.get('max_price') is not None and 
            data['min_price'] > data['max_price']):
            raise serializers.ValidationError(
                'min_price cannot be greater than max_price.'
            )
        
        return data
