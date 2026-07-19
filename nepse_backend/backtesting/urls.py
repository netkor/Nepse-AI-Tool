from django.urls import path
from .views import BacktestLatestView, BacktestSignalTypeView

urlpatterns = [
    path('results/', BacktestLatestView.as_view(), name='backtest_latest'),
    path('results/<str:signal_type>/', BacktestSignalTypeView.as_view(), name='backtest_signal_type'),
]
