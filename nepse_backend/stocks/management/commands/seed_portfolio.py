from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from stocks.models import Stock, PortfolioItem

class Command(BaseCommand):
    help = 'Seeds the user portfolio with their 10 stock holdings'

    def handle(self, *args, **options):
        # 1. Get the admin user
        try:
            user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Superuser 'admin' not found. Please create it first."))
            return

        # 2. User's actual portfolio holdings
        holdings = [
            {'symbol': 'API', 'balance': 100, 'cost_price': 353.42},
            {'symbol': 'GBBL', 'balance': 50, 'cost_price': 423.08},
            {'symbol': 'HLI', 'balance': 1, 'cost_price': 100.00},
            {'symbol': 'NABIL', 'balance': 187, 'cost_price': 533.01},
            {'symbol': 'NICA', 'balance': 100, 'cost_price': 372.26},
            {'symbol': 'PCBL', 'balance': 285, 'cost_price': 276.85},
            {'symbol': 'PCIL', 'balance': 10, 'cost_price': 100.00},
            {'symbol': 'PPCL', 'balance': 70, 'cost_price': 426.95},
            {'symbol': 'PRVU', 'balance': 90, 'cost_price': 226.62},
            {'symbol': 'SAHAS', 'balance': 49, 'cost_price': 625.85},
        ]

        self.stdout.write("Seeding portfolio for admin...")
        seeded_count = 0

        for h in holdings:
            symbol = h['symbol']
            try:
                stock = Stock.objects.get(symbol=symbol)
                
                # Get or create portfolio item
                portfolio_item, created = PortfolioItem.objects.update_or_create(
                    user=user,
                    stock=stock,
                    defaults={
                        'balance': h['balance'],
                        'cost_price': h['cost_price']
                    }
                )
                
                action = "Created" if created else "Updated"
                self.stdout.write(f"  - {action} {symbol}: {h['balance']} shares @ Rs. {h['cost_price']}")
                seeded_count += 1
            except Stock.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  - WARNING: Stock symbol {symbol} not found in database!"))

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {seeded_count} portfolio holdings!"))
