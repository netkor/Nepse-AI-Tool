from rest_framework import serializers
from .models import Stock, StockHistory, PortfolioItem, FundamentalSnapshot
from signals.calculators import get_stock_dataframe, calculate_indicators, get_active_signal

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class StockHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHistory
        fields = '__all__'

class PortfolioItemSerializer(serializers.ModelSerializer):
    stock_details = StockSerializer(source='stock', read_only=True)
    total_investment = serializers.SerializerMethodField()
    current_value = serializers.SerializerMethodField()
    overall_pl = serializers.SerializerMethodField()
    pl_percentage = serializers.SerializerMethodField()
    active_signal = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioItem
        fields = [
            'id', 'user', 'stock', 'stock_details', 'balance', 'cost_price',
            'total_investment', 'current_value', 'overall_pl', 'pl_percentage',
            'active_signal', 'added_at'
        ]
        read_only_fields = ['user']

    def get_total_investment(self, obj):
        return float(obj.balance * obj.cost_price)

    def get_current_value(self, obj):
        return float(obj.balance * obj.stock.current_price)

    def get_overall_pl(self, obj):
        return self.get_current_value(obj) - self.get_total_investment(obj)

    def get_pl_percentage(self, obj):
        cost = self.get_total_investment(obj)
        if cost == 0:
            return 0
        return (self.get_overall_pl(obj) / cost) * 100

    def get_active_signal(self, obj):
        df = get_stock_dataframe(obj.stock, limit=65)
        if df.empty or len(df) < 50:
            return None
        df = calculate_indicators(df)
        sig = get_active_signal(df)
        if sig:
            return {
                'recommendation': sig.get('recommendation', 'HOLD'),
                'type': sig.get('type', 'NEUTRAL'),
                'label': sig.get('signal_label', sig.get('label', 'HOLD (Neutral)')),
                'desc': sig.get('signal_desc', sig.get('desc', ''))
            }
        return None

class FundamentalSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundamentalSnapshot
        fields = '__all__'

