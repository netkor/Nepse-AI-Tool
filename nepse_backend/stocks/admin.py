from django.contrib import admin
from .models import Stock, StockHistory, FundamentalSnapshot

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'sector', 'current_price', 'volume', 'change_percentage', 'last_updated')
    search_fields = ('symbol', 'name')
    list_filter = ('sector', 'last_updated')

@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume')
    search_fields = ('stock__symbol', 'date')
    list_filter = ('date',)

@admin.register(FundamentalSnapshot)
class FundamentalSnapshotAdmin(admin.ModelAdmin):
    list_display = ('stock', 'date', 'eps', 'pe_ratio', 'book_value', 'roe')
    search_fields = ('stock__symbol', 'date')
    list_filter = ('date',)

