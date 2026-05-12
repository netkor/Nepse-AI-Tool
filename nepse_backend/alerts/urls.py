"""
URL configuration for Alerts app.
"""
from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    # Watchlist endpoints
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/<int:stock_id>/', views.watchlist_remove, name='watchlist_remove'),
    
    # Price alert endpoints
    path('price/', views.price_alerts, name='price_alerts'),
    path('price/<int:alert_id>/', views.price_alert_detail, name='price_alert_detail'),
]
