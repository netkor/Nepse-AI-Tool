from django.urls import path
from django.views.decorators.cache import cache_page
from .views import (
    SignalsListView, StockSignalsDetailView, MarketSummaryView,
    WeeklySignalsListView, BulkTransactionsListView, SeasonalPerformanceView,
    CustomStrategyView, ConfluenceSignalsListView
)

urlpatterns = [
    # Cache lists for 10 minutes to speed up dashboard loads and prevent database locks
    path('', cache_page(60 * 10)(SignalsListView.as_view()), name='signals_list'),
    path('confluence/', cache_page(60 * 10)(ConfluenceSignalsListView.as_view()), name='confluence_signals_list'),
    path('market-summary/', cache_page(60 * 10)(MarketSummaryView.as_view()), name='market_summary'),
    path('weekly/', cache_page(60 * 10)(WeeklySignalsListView.as_view()), name='weekly_signals_list'),
    path('bulk-transactions/', cache_page(60 * 5)(BulkTransactionsListView.as_view()), name='bulk_transactions_list'),
    path('seasonal/<str:symbol>/', cache_page(60 * 10)(SeasonalPerformanceView.as_view()), name='seasonal_performance'),
    path('custom-strategy/', cache_page(60 * 10)(CustomStrategyView.as_view()), name='custom_strategy'),
    
    # Detail chart endpoint is fetched individually and remains un-cached or quick
    path('<str:symbol>/', StockSignalsDetailView.as_view(), name='stock_signals_detail'),
]
