"""
URL configuration for NEPSE Backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', include('core.urls', namespace='core')),
    path('api/auth/', include('accounts.urls', namespace='accounts')),
    path('api/stocks/', include('stocks.urls', namespace='stocks')),
    path('api/signals/', include('signals.urls', namespace='signals')),
    path('api/alerts/', include('alerts.urls', namespace='alerts')),
    path('api/insights/', include('insights.urls', namespace='insights')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
