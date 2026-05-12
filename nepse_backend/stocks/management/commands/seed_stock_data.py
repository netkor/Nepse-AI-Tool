"""
Management command to seed mock stock data.
Usage: python manage.py seed_stock_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from stocks.models import Stock, StockHistory
from stocks.data_provider import MockDataProvider


class Command(BaseCommand):
    help = 'Seed mock NEPSE stock data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing stock data before seeding',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of historical days to generate (default: 90)',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)
        days = options.get('days', 90)

        if clear:
            self.stdout.write(self.style.WARNING('Clearing existing stock data...'))
            Stock.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared!'))

        self.stdout.write(self.style.SUCCESS('Starting stock data seeding...'))

        provider = MockDataProvider()

        # Get and create stocks
        stocks_data = provider.get_stocks()
        created_count = 0

        for stock_data in stocks_data:
            stock, created = Stock.objects.get_or_create(
                symbol=stock_data['symbol'],
                defaults={
                    'name': stock_data['name'],
                    'sector': stock_data['sector'],
                    'price': stock_data['price'],
                    'volume': stock_data['volume'],
                    'change_percent': stock_data['change_percent'],
                    'market_cap': stock_data['market_cap'],
                    'is_active': stock_data['is_active'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {stock.symbol} - {stock.name}')
                )
            else:
                # Update existing stock
                stock.price = stock_data['price']
                stock.volume = stock_data['volume']
                stock.change_percent = stock_data['change_percent']
                stock.save()
                self.stdout.write(
                    self.style.WARNING(f'~ Updated: {stock.symbol}')
                )

            # Create historical data
            history_data = provider.get_stock_history(stock.symbol, days=days)
            history_created = 0

            for day_data in history_data:
                history, created = StockHistory.objects.get_or_create(
                    stock=stock,
                    date=day_data['date'],
                    defaults={
                        'open_price': day_data['open_price'],
                        'high_price': day_data['high_price'],
                        'low_price': day_data['low_price'],
                        'close_price': day_data['close_price'],
                        'volume': day_data['volume'],
                    }
                )
                if created:
                    history_created += 1

            self.stdout.write(
                f'  → Created {history_created} historical records'
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Seeding complete! {created_count} stocks created.')
        )
