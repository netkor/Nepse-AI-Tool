"""
Admin configuration for Stocks app.
"""
from django.contrib import admin
from .models import Stock, StockHistory


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'price', 'change_percent', 'volume', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'sector')
    search_fields = ('symbol', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'close_price', 'volume', 'created_at')
    list_filter = ('stock', 'date', 'created_at')
    search_fields = ('stock__symbol', 'stock__name')
    readonly_fields = ('created_at',)
