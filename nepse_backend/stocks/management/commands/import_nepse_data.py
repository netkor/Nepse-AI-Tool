import os
import csv
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from stocks.models import Stock, StockHistory

class Command(BaseCommand):
    help = 'Imports historical NEPSE data from the cloned nepse-data CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing stock and history data before importing',
        )

    def handle(self, *args, **options):
        # 1. Clear database if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing all existing stock and history records...'))
            StockHistory.objects.all().delete()
            Stock.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared database.'))

        # 2. Locate data directory
        # The cloned repo is at: BASE_DIR.parent / 'nepse-data'
        data_dir = settings.BASE_DIR.parent / 'nepse-data' / 'data' / 'company-wise'
        if not data_dir.exists():
            self.stdout.write(self.style.ERROR(
                f"Data directory not found at {data_dir}. "
                "Make sure you cloned the repository to the correct location."
            ))
            return

        csv_files = list(data_dir.glob('*.csv'))
        total_files = len(csv_files)
        self.stdout.write(f"Found {total_files} CSV files to process.")

        # 3. Process each file
        stocks_to_update = []
        history_to_create = []
        processed_count = 0
        total_history_inserted = 0

        # We'll batch save history records to stay memory efficient
        BATCH_SIZE = 10000

        for idx, file_path in enumerate(csv_files, 1):
            symbol = file_path.stem  # e.g. "ACLBSL"
            
            # Find or create the stock
            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={'name': f"{symbol} (Nepal Stock Market)"}
            )

            # Read the CSV rows
            try:
                with open(file_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    # Store history rows for this stock
                    stock_rows = []
                    for row in reader:
                        # Clean/parse values safely
                        try:
                            # published_date,open,high,low,close,per_change,traded_quantity,traded_amount,status
                            date_str = row.get('published_date')
                            if not date_str:
                                continue
                            
                            # Standardise date format (usually YYYY-MM-DD)
                            date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
                            
                            open_p = float(row.get('open', 0))
                            high_p = float(row.get('high', 0))
                            low_p = float(row.get('low', 0))
                            close_p = float(row.get('close', 0))
                            vol = int(float(row.get('traded_quantity', 0)))
                            change_pct = float(row.get('per_change', 0))

                            stock_rows.append({
                                'date': date_val,
                                'open': open_p,
                                'high': high_p,
                                'low': low_p,
                                'close': close_p,
                                'volume': vol,
                                'change_pct': change_pct
                            })
                        except (ValueError, TypeError):
                            # Skip malformed rows
                            continue

                if not stock_rows:
                    continue

                # Sort by date ascending to find the latest metrics
                stock_rows.sort(key=lambda x: x['date'])

                # Save history rows to bulk insert list
                for r in stock_rows:
                    history_to_create.append(
                        StockHistory(
                            stock=stock,
                            date=r['date'],
                            open_price=r['open'],
                            high_price=r['high'],
                            low_price=r['low'],
                            close_price=r['close'],
                            volume=r['volume']
                        )
                    )

                # Update the stock's latest day metrics
                latest = stock_rows[-1]
                stock.current_price = latest['close']
                stock.volume = latest['volume']
                stock.change_percentage = latest['change_pct']
                stocks_to_update.append(stock)

                processed_count += 1

                # If batch size reached, bulk insert history and update stocks
                if len(history_to_create) >= BATCH_SIZE:
                    self._flush_batch(history_to_create, stocks_to_update)
                    total_history_inserted += len(history_to_create)
                    history_to_create = []
                    stocks_to_update = []

                if idx % 50 == 0 or idx == total_files:
                    self.stdout.write(f"Processed {idx}/{total_files} files...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {symbol}: {str(e)}"))

        # Flush any remaining items in final batch
        if history_to_create or stocks_to_update:
            total_history_inserted += len(history_to_create)
            self._flush_batch(history_to_create, stocks_to_update)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully processed {processed_count} stocks and inserted {total_history_inserted} history rows!"
        ))

    def _flush_batch(self, history_list, stock_list):
        """Helper to bulk insert history records and bulk update stocks in a transaction."""
        with transaction.atomic():
            # Bulk create history ignoring conflicts to prevent unique constraint crashes
            StockHistory.objects.bulk_create(history_list, ignore_conflicts=True)
            
            # Bulk update current prices and volume metrics on the stock model
            Stock.objects.bulk_update(
                stock_list, 
                ['current_price', 'volume', 'change_percentage']
            )
