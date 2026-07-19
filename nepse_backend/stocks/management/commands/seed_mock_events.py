from django.core.management.base import BaseCommand
from stocks.models import Stock, MarketEvent
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Seeds mock market events for testing Phase 6'

    def handle(self, *args, **kwargs):
        # Clear existing events to prevent duplicates if run multiple times
        MarketEvent.objects.all().delete()
        
        today = date.today()

        # 1. Market-wide event (Monetary Policy)
        MarketEvent.objects.create(
            stock=None,
            event_type='MONETARY_POLICY',
            event_date=today + timedelta(days=14),
            title='NRB Quarterly Monetary Policy Review',
            description='Expected announcement on interest rate caps and margin lending limits.'
        )
        self.stdout.write(self.style.SUCCESS("Seeded market-wide Monetary Policy event."))

        # 2. Stock-specific event (NABIL AGM)
        try:
            nabil = Stock.objects.get(symbol='NABIL')
            MarketEvent.objects.create(
                stock=nabil,
                event_type='AGM',
                event_date=today + timedelta(days=10),
                title='40th Annual General Meeting',
                description='Approval of 11% cash dividend.'
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded AGM event for {nabil.symbol}."))
        except Stock.DoesNotExist:
            self.stdout.write(self.style.WARNING("NABIL stock not found, skipping AGM event."))

        # 3. Stock-specific event (NICA Book Closure)
        try:
            nica = Stock.objects.get(symbol='NICA')
            MarketEvent.objects.create(
                stock=nica,
                event_type='BOOK_CLOSURE',
                event_date=today + timedelta(days=5),
                title='Book Closure for Dividend',
                description='Books closing for 20% bonus share distribution.'
            )
            self.stdout.write(self.style.SUCCESS(f"Seeded Book Closure event for {nica.symbol}."))
        except Stock.DoesNotExist:
            self.stdout.write(self.style.WARNING("NICA stock not found, skipping Book Closure event."))

        self.stdout.write(self.style.SUCCESS('Successfully seeded mock market events.'))
