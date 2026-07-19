import os
import sys
import re
import time
import requests
from django.core.management.base import BaseCommand
from stocks.models import Stock

# Add nepse-data/src to sys.path to import companyIdMap
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../nepse-data/src')))

try:
    from constants.companyIdMap import companyIdMap
except ImportError:
    companyIdMap = {}

SECTOR_MAP = {
    'Commercial Bank': 'Commercial Bank',
    'Commercial Banks': 'Commercial Bank',
    'Development Bank': 'Development Bank',
    'Development Banks': 'Development Bank',
    'Finance': 'Finance',
    'Finance Companies': 'Finance',
    'Microfinance': 'Microfinance',
    'Microfinances': 'Microfinance',
    'Hydropower': 'Hydropower',
    'Life Insurance': 'Life Insurance',
    'Non-Life Insurance': 'Non-Life Insurance',
    'Hotel & Tourism': 'Hotel & Tourism',
    'Manufacturing and Processing': 'Manufacturing and Processing',
    'Manufacturing & Processing': 'Manufacturing and Processing',
    'Trading': 'Trading',
    'Investment': 'Investment',
    'Mutual Fund': 'Mutual Fund',
    'Others': 'Others',
    'Corporate Debentures': 'Others',
    'Government Bonds': 'Others',
    'Preference Share': 'Others',
    'Promoter Share': 'Others'
}

class Command(BaseCommand):
    help = 'Assign NEPSE sectors to Stock models by scraping sharesansar.'

    def handle(self, *args, **options):
        stocks = Stock.objects.all()
        total = stocks.count()
        self.stdout.write(self.style.WARNING(f"Starting sector assignment for {total} stocks..."))

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
        }

        # Regex to match sector in HTML page
        # e.g., <div id="sector" style="display: none;">Commercial Bank</div>
        # or <h4>Sector: <span class="text-org">Commercial Bank</span></h4>
        _SECTOR_RE = re.compile(r'id="sector"[^>]*>\s*([^<]+)')
        _SECTOR_SPAN_RE = re.compile(r'Sector:\s*<span[^>]*>\s*([^<]+)')

        updated_count = 0
        skipped_count = 0

        for i, stock in enumerate(stocks, 1):
            symbol = stock.symbol.upper()
            
            # Check if company exists in mapping
            if symbol not in companyIdMap:
                self.stdout.write(self.style.ERROR(f"[{i}/{total}] No company map ID for {symbol}, setting sector to Others"))
                stock.sector = 'Others'
                stock.save()
                skipped_count += 1
                continue

            time.sleep(0.3)  # Respectful delay
            url = f"https://www.sharesansar.com/company/{symbol.lower()}"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"[{i}/{total}] Failed to fetch {symbol}: HTTP {resp.status_code}"))
                    skipped_count += 1
                    continue

                html = resp.text
                sector_match = _SECTOR_RE.search(html) or _SECTOR_SPAN_RE.search(html)
                if sector_match:
                    raw_sector = sector_match.group(1).strip()
                    normalized_sector = SECTOR_MAP.get(raw_sector, 'Others')
                    stock.sector = normalized_sector
                    stock.save()
                    self.stdout.write(self.style.SUCCESS(f"[{i}/{total}] Assigned {symbol} -> {normalized_sector} (raw: {raw_sector})"))
                    updated_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"[{i}/{total}] Sector not found in HTML for {symbol}, setting to Others"))
                    stock.sector = 'Others'
                    stock.save()
                    skipped_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{i}/{total}] Error processing {symbol}: {e}"))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Sector assignment complete. Updated: {updated_count}, Skipped/Defaulted: {skipped_count} out of {total}"
        ))
