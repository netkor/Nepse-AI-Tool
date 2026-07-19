from django.urls import path
from .views import (
    StockListView, StockHistoryView, PortfolioListCreateView, PortfolioDetailView,
    StockFundamentalsView, SectorSummaryView, PortfolioRiskView
)

urlpatterns = [
    path('', StockListView.as_view(), name='stock_list'),
    path('sectors/summary/', SectorSummaryView.as_view(), name='sector_summary'),
    path('<str:symbol>/history/', StockHistoryView.as_view(), name='stock_history'),
    path('<str:symbol>/fundamentals/', StockFundamentalsView.as_view(), name='stock_fundamentals'),
    path('portfolio/', PortfolioListCreateView.as_view(), name='portfolio_list'),
    path('portfolio/risk/', PortfolioRiskView.as_view(), name='portfolio_risk'),
    path('portfolio/<int:pk>/', PortfolioDetailView.as_view(), name='portfolio_detail'),
]

