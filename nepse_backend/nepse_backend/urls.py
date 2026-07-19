from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/stocks/', include('stocks.urls')),
    path('api/signals/', include('signals.urls')),
    path('api/alerts/', include('alerts.urls')),
    path('api/watchlist/', include('alerts.urls_watchlist')), # Separated watchlist urls
    path('api/backtest/', include('backtesting.urls')),
]
