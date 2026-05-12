"""
Serializers for Signals app.
"""
from rest_framework import serializers
from .models import Signal


class SignalSerializer(serializers.ModelSerializer):
    """
    Serializer for trading signals.
    """
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    stock_price = serializers.DecimalField(
        source='stock.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Signal
        fields = (
            'id',
            'stock',
            'stock_symbol',
            'stock_name',
            'stock_price',
            'signal_type',
            'reason',
            'confidence_score',
            'indicator_details',
            'is_notified',
            'created_at',
        )
        read_only_fields = (
            'id',
            'stock',
            'stock_symbol',
            'stock_name',
            'stock_price',
            'signal_type',
            'reason',
            'confidence_score',
            'indicator_details',
            'is_notified',
            'created_at',
        )
