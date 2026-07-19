from django.db import models
from django.contrib.auth.models import User

SECTOR_CHOICES = [
    ('Commercial Bank', 'Commercial Bank'),
    ('Development Bank', 'Development Bank'),
    ('Finance', 'Finance'),
    ('Microfinance', 'Microfinance'),
    ('Hydropower', 'Hydropower'),
    ('Life Insurance', 'Life Insurance'),
    ('Non-Life Insurance', 'Non-Life Insurance'),
    ('Hotel & Tourism', 'Hotel & Tourism'),
    ('Manufacturing and Processing', 'Manufacturing and Processing'),
    ('Trading', 'Trading'),
    ('Investment', 'Investment'),
    ('Mutual Fund', 'Mutual Fund'),
    ('Others', 'Others'),
]

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(
        max_length=40,
        choices=SECTOR_CHOICES,
        blank=True,
        default='',
        help_text='NEPSE sector classification'
    )
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    volume = models.BigIntegerField(default=0)
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.name}"

class StockHistory(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='history')
    date = models.DateField()
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()

    class Meta:
        unique_together = ('stock', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.stock.symbol} on {self.date}"

class PortfolioItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio_items')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='portfolio_entries')
    balance = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol} ({self.balance} shares)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from alerts.models import Watchlist, Alert
        
        # 1. Automatically add to Watchlist
        Watchlist.objects.get_or_create(user=self.user, stock=self.stock)

        # 2. Automatically set Target Profit Alert (+10% of Cost Price)
        profit_target = self.cost_price * 1.10
        Alert.objects.get_or_create(
            user=self.user,
            stock=self.stock,
            alert_type='PRICE_ABOVE',
            defaults={'target_value': profit_target}
        )

        # 3. Automatically set Stop Loss Alert (-10% of Cost Price)
        stop_loss = self.cost_price * 0.90
        Alert.objects.get_or_create(
            user=self.user,
            stock=self.stock,
            alert_type='PRICE_BELOW',
            defaults={'target_value': stop_loss}
        )


class FundamentalSnapshot(models.Model):
    """
    Quarterly/periodic fundamental financial metrics for a stock.
    Bank-specific fields are nullable — only populated for banking sector stocks.
    Per CLAUDE.md: never fabricate data; store null if unavailable.
    """
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='fundamentals')
    date = models.DateField(help_text='Date the snapshot was recorded or published')

    # Universal fundamentals
    eps = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Earnings Per Share (Rs.)'
    )
    pe_ratio = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Price to Earnings ratio'
    )
    book_value = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text='Book Value per share (Rs.)'
    )
    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Dividend yield percentage'
    )
    roe = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='Return on Equity percentage'
    )

    # Bank-specific fundamentals (nullable for non-bank stocks)
    cd_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Credit to Deposit ratio (banks only)'
    )
    npl_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Non-Performing Loan ratio (banks only)'
    )
    capital_adequacy_ratio = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Capital Adequacy ratio (banks only)'
    )

    class Meta:
        unique_together = ('stock', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.stock.symbol} fundamentals on {self.date}"


EVENT_TYPE_CHOICES = [
    ('MONETARY_POLICY', 'Monetary Policy'),
    ('DIVIDEND', 'Dividend Announcement'),
    ('AGM', 'Annual General Meeting (AGM)'),
    ('BOOK_CLOSURE', 'Book Closure'),
    ('EARNINGS', 'Earnings Report'),
    ('OTHER', 'Other Event'),
]

class MarketEvent(models.Model):
    stock = models.ForeignKey(
        Stock, on_delete=models.CASCADE, related_name='events', 
        null=True, blank=True, 
        help_text="Null means it's a market-wide event (e.g. Monetary Policy)"
    )
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    event_date = models.DateField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        prefix = f"[{self.stock.symbol}] " if self.stock else "[MARKET] "
        return f"{prefix}{self.title} on {self.event_date}"
