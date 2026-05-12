"""
Models for the Alerts app.
Handles user watchlists and price alerts.
"""
from django.db import models
from django.conf import settings
from stocks.models import Stock


class Watchlist(models.Model):
    """
    User watchlist to track specific stocks.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist'
    )
    stocks = models.ManyToManyField(
        Stock,
        related_name='watched_by_users',
        blank=True,
        through='WatchlistStock'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Watchlists'

    def __str__(self):
        return f"{self.user.email}'s Watchlist"


class WatchlistStock(models.Model):
    """
    Intermediate model for watchlist with additional fields.
    """
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['watchlist', 'stock']

    def __str__(self):
        return f"{self.watchlist.user.email} watches {self.stock.symbol}"


class PriceAlert(models.Model):
    """
    User-defined price alerts for specific stocks.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('TRIGGERED', 'Triggered'),
        ('INACTIVE', 'Inactive'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='price_alerts'
    )
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='price_alerts'
    )
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Alert when price drops below this value"
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Alert when price rises above this value"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )
    is_notified = models.BooleanField(
        default=False,
        help_text="Whether user has been notified for this alert"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    triggered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the alert was triggered"
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'stock', 'min_price', 'max_price']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['stock', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.stock.symbol} Alert"
