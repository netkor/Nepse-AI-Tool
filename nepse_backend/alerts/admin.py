"""
Admin configuration for Alerts app.
"""
from django.contrib import admin
from .models import Watchlist, WatchlistStock, PriceAlert


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_stock_count', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_stock_count(self, obj):
        return obj.stocks.count()
    get_stock_count.short_description = 'Stocks'


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'min_price', 'max_price', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'stock')
    search_fields = ('user__email', 'stock__symbol')
    readonly_fields = ('created_at', 'updated_at', 'triggered_at')
