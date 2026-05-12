"""
URL configuration for Signals app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'signals'

router = DefaultRouter()
router.register(r'', views.SignalViewSet, basename='signal')

urlpatterns = [
    path('', include(router.urls)),
    path('stock/<str:stock_symbol>/', views.signals_by_stock, name='signals_by_stock'),
    path('<int:signal_id>/mark-notified/', views.mark_signal_notified, name='mark_signal_notified'),
]
