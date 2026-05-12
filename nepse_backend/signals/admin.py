"""
Admin configuration for Signals app.
"""
from django.contrib import admin
from .models import Signal


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ('stock', 'signal_type', 'confidence_score', 'is_notified', 'created_at')
    list_filter = ('signal_type', 'is_notified', 'created_at')
    search_fields = ('stock__symbol', 'reason')
    readonly_fields = ('created_at', 'indicator_details')
    date_hierarchy = 'created_at'
