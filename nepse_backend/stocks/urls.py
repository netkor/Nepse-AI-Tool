"""
URL configuration for Stocks app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'stocks'

router = DefaultRouter()
router.register(r'', views.StockViewSet, basename='stock')

urlpatterns = [
    path('', include(router.urls)),
    path('<str:symbol>/history/', views.stock_history, name='stock_history'),
    path('statistics/overview/', views.stock_statistics, name='stock_statistics'),
]
