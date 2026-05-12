"""
Service for managing user alerts and notifications.
"""
from typing import Optional
from django.utils import timezone
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from stocks.models import Stock
from .models import Watchlist, PriceAlert, WatchlistStock

User = get_user_model()


class AlertService:
    """
    Service for managing watchlists and price alerts.
    """

    @classmethod
    def get_or_create_watchlist(cls, user: User) -> Watchlist:
        """
        Get or create a watchlist for a user.
        """
        watchlist, created = Watchlist.objects.get_or_create(user=user)
        return watchlist

    @classmethod
    def add_to_watchlist(cls, user: User, stock: Stock) -> bool:
        """
        Add a stock to user's watchlist.
        Returns True if added, False if already exists.
        """
        watchlist = cls.get_or_create_watchlist(user)
        
        if watchlist.stocks.filter(id=stock.id).exists():
            return False
        
        watchlist.stocks.add(stock)
        return True

    @classmethod
    def remove_from_watchlist(cls, user: User, stock: Stock) -> bool:
        """
        Remove a stock from user's watchlist.
        Returns True if removed, False if not in watchlist.
        """
        watchlist = cls.get_or_create_watchlist(user)
        
        if not watchlist.stocks.filter(id=stock.id).exists():
            return False
        
        watchlist.stocks.remove(stock)
        return True

    @classmethod
    def get_watchlist(cls, user: User):
        """
        Get user's watchlist with stocks.
        """
        watchlist = cls.get_or_create_watchlist(user)
        return watchlist

    @classmethod
    def create_price_alert(
        cls,
        user: User,
        stock: Stock,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> PriceAlert:
        """
        Create a price alert for a stock.
        """
        if min_price is None and max_price is None:
            raise ValueError("At least one of min_price or max_price must be set.")
        
        alert, created = PriceAlert.objects.get_or_create(
            user=user,
            stock=stock,
            min_price=min_price,
            max_price=max_price,
            defaults={'status': 'ACTIVE'}
        )
        
        return alert

    @classmethod
    def check_and_trigger_price_alerts(cls) -> int:
        """
        Check all active price alerts and trigger if condition met.
        Returns number of alerts triggered.
        """
        triggered_count = 0
        active_alerts = PriceAlert.objects.filter(
            status='ACTIVE',
            is_notified=False
        ).select_related('stock', 'user')

        for alert in active_alerts:
            current_price = float(alert.stock.price)
            triggered = False

            if alert.min_price and current_price <= float(alert.min_price):
                triggered = True
            elif alert.max_price and current_price >= float(alert.max_price):
                triggered = True

            if triggered:
                alert.is_notified = True
                alert.status = 'TRIGGERED'
                alert.triggered_at = timezone.now()
                alert.save()
                triggered_count += 1

        return triggered_count

    @classmethod
    def deactivate_alert(cls, alert: PriceAlert) -> bool:
        """
        Deactivate an alert.
        """
        alert.status = 'INACTIVE'
        alert.save()
        return True

    @classmethod
    def get_user_alerts(cls, user: User, status: Optional[str] = None):
        """
        Get user's price alerts.
        """
        alerts = PriceAlert.objects.filter(user=user).select_related('stock')
        
        if status:
            alerts = alerts.filter(status=status)
        
        return alerts.order_by('-created_at')
