"""
Models for the Stocks app.
Handles stock data and historical price information.
"""
from django.db import models


class Stock(models.Model):
    """
    NEPSE Stock information.
    """
    symbol = models.CharField(
        max_length=20,
        unique=True,
        help_text="Stock symbol/ticker (e.g., NABIL)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full company name"
    )
    sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Industry sector"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Current stock price"
    )
    volume = models.BigIntegerField(
        default=0,
        help_text="Current trading volume"
    )
    change_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Percentage change from previous close"
    )
    market_cap = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="Market capitalization"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether stock is actively traded"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class StockHistory(models.Model):
    """
    Historical OHLCV (Open, High, Low, Close, Volume) data for stocks.
    """
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='history'
    )
    date = models.DateField(
        help_text="Trading date"
    )
    open_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Opening price"
    )
    high_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Highest price of the day"
    )
    low_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Lowest price of the day"
    )
    close_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Closing price"
    )
    volume = models.BigIntegerField(
        default=0,
        help_text="Trading volume"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['stock', 'date']
        indexes = [
            models.Index(fields=['stock', '-date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.stock.symbol} - {self.date}"
