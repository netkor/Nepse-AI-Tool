import os
import sys
import re
import time
from datetime import datetime
import requests
from django.core.management.base import BaseCommand
from stocks.models import Stock, FundamentalSnapshot

# Add nepse-data/src to sys.path to import companyIdMap
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../nepse-data/src')))

try:
    from constants.companyIdMap import companyIdMap
except ImportError:
    companyIdMap = {}

class Command(BaseCommand):
    help = 'Import and scrape quarterly fundamental metrics for stocks.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            default=None,
            help='Comma-separated list of symbols to import (default: all)',
        )

    def handle(self, *args, **options):
        symbols_str = options['symbols']
        if symbols_str:
            symbols = [s.strip().upper() for s in symbols_str.split(',')]
            stocks = Stock.objects.filter(symbol__in=symbols)
        else:
            stocks = Stock.objects.all()

        total = stocks.count()
        self.stdout.write(self.style.WARNING(f"Starting fundamentals scraping for {total} stocks..."))

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

        # Session regexes
        _TOKEN_RE = re.compile(r'name="_token"\s+value="([^"]+)"')
        _COMPANYID_RE = re.compile(r'id="companyid"[^>]*>\s*([0-9]+)')
        _SYMBOL_RE = re.compile(r'id="symbol"[^>]*>\s*([A-Za-z0-9]+)')
        
        # Sector regexes
        _SECTOR_RE = re.compile(r'id="sector"[^>]*>\s*([^<]+)')
        _SECTOR_SPAN_RE = re.compile(r'Sector:\s*<span[^>]*>\s*([^<]+)')

        sector_map = {
            'Commercial Bank': 'Commercial Bank', 'Commercial Banks': 'Commercial Bank',
            'Development Bank': 'Development Bank', 'Development Banks': 'Development Bank',
            'Finance': 'Finance', 'Finance Companies': 'Finance',
            'Microfinance': 'Microfinance', 'Microfinances': 'Microfinance',
            'Hydropower': 'Hydropower', 'Life Insurance': 'Life Insurance',
            'Non-Life Insurance': 'Non-Life Insurance', 'Hotel & Tourism': 'Hotel & Tourism',
            'Manufacturing and Processing': 'Manufacturing and Processing',
            'Manufacturing & Processing': 'Manufacturing and Processing',
            'Trading': 'Trading', 'Investment': 'Investment', 'Mutual Fund': 'Mutual Fund',
            'Others': 'Others', 'Corporate Debentures': 'Others',
            'Government Bonds': 'Others', 'Preference Share': 'Others', 'Promoter Share': 'Others'
        }

        session = requests.Session()
        session.headers.update(headers)

        success_count = 0

        for i, stock in enumerate(stocks, 1):
            symbol = stock.symbol.upper()

            if symbol not in companyIdMap:
                self.stdout.write(self.style.ERROR(f"[{i}/{total}] No company ID mapped for {symbol}. Skipping."))
                continue

            time.sleep(0.3)
            # 1. Visit company profile page to prime session & get token/ID
            url = f"https://www.sharesansar.com/company/{symbol.lower()}"
            try:
                resp = session.get(url, timeout=15)
                if resp.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"[{i}/{total}] Profile visit failed for {symbol}: HTTP {resp.status_code}"))
                    continue

                html = resp.text
                token_match = _TOKEN_RE.search(html)
                companyid_match = _COMPANYID_RE.search(html)

                if not token_match or not companyid_match:
                    self.stdout.write(self.style.ERROR(f"[{i}/{total}] Token or CompanyID not found for {symbol}"))
                    continue

                token = token_match.group(1)
                company_id = companyid_match.group(1)

                # Auto-assign/heal sector if it is empty in DB
                sector_to_send = stock.sector
                if not sector_to_send:
                    sec_match = _SECTOR_RE.search(html) or _SECTOR_SPAN_RE.search(html)
                    if sec_match:
                        raw_sector = sec_match.group(1).strip()
                        sector_to_send = sector_map.get(raw_sector, 'Others')
                        stock.sector = sector_to_send
                        stock.save()
                        self.stdout.write(self.style.SUCCESS(f"[{i}/{total}] Auto-healed sector for {symbol} -> {sector_to_send}"))
                    else:
                        sector_to_send = 'Others'

                # 2. POST to company-quarterly-report
                post_headers = {'X-CSRF-Token': token}
                post_data = {
                    "company": company_id,
                    "symbol": symbol,
                    "sector": sector_to_send,
                }

                
                time.sleep(0.2)
                post_resp = session.post(
                    "https://www.sharesansar.com/company-quarterly-report",
                    headers=post_headers,
                    data=post_data,
                    timeout=15
                )

                if post_resp.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"[{i}/{total}] POST failed for {symbol}: HTTP {post_resp.status_code}"))
                    continue

                qtr_html = post_resp.text

                # Parse date/quarter from the quarterly report table header
                date_str = self.parse_date_from_header(qtr_html)
                if not date_str:
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    self.stdout.write(self.style.WARNING(f"[{i}/{total}] Header date not parsed for {symbol}, using current date {date_str}"))

                # Helper to extract metrics
                eps = self.extract_metric(qtr_html, "Basic Earnings Per Share(Annualized EPS)") or self.extract_metric(qtr_html, "Basic Earnings Per Share (Annualized)")
                pe_ratio = self.extract_metric(qtr_html, "P/E Ratio") or self.extract_metric(qtr_html, "P/E Ratio")
                book_value = self.extract_metric(qtr_html, "Net Worth Per Share")
                roe = self.extract_metric(qtr_html, "Return on Equity")
                
                # Bank specific
                cd_ratio = self.extract_metric(qtr_html, "Credit to Deposit Ratio")
                npl_ratio = self.extract_metric(qtr_html, "Non-Performing loan(NPL) to Total Loan")
                capital_adequacy_ratio = self.extract_metric(qtr_html, "Capital fund to RWA")

                if eps is None and book_value is None and roe is None:
                    self.stdout.write(self.style.ERROR(f"[{i}/{total}] Extracted all null metrics for {symbol}. Scraping might have failed."))
                    continue

                # Save snapshot
                snapshot, created = FundamentalSnapshot.objects.update_or_create(
                    stock=stock,
                    date=date_str,
                    defaults={
                        'eps': eps,
                        'pe_ratio': pe_ratio,
                        'book_value': book_value,
                        'roe': roe,
                        'cd_ratio': cd_ratio,
                        'npl_ratio': npl_ratio,
                        'capital_adequacy_ratio': capital_adequacy_ratio,
                    }
                )

                action = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(
                    f"[{i}/{total}] {action} snapshot for {symbol} on {date_str}: EPS={eps}, PE={pe_ratio}, BV={book_value}, ROE={roe}"
                ))
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[{i}/{total}] Exception during parsing for {symbol}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {success_count} fundamentals snapshots."))

    def extract_metric(self, html, label):
        # Match label in td, followed by another td containing the value
        # Escaping regex characters in label
        escaped_label = re.escape(label).replace(r'\ ', r'\s*')
        # E.g., <td>Basic Earnings Per Share(Annualized EPS)</td> <td>31.36</td>
        # We handle tags, newlines and spaces flexibly
        pattern = rf'<td>\s*{escaped_label}\s*</td>\s*<td>\s*([\d\.,\-]+)'
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            val = match.group(1).replace(',', '').strip()
            if val == '-':
                return None
            try:
                return float(val)
            except ValueError:
                return None
        return None

    def parse_date_from_header(self, html):
        match = re.search(r'<th>\s*(1st|2nd|3rd|4th|First|Second|Third|Fourth)\s+Quarter\s+(\d{4})/(\d{4})', html, re.IGNORECASE)
        if match:
            q = match.group(1).lower()
            year_start = int(match.group(2))
            
            ad_year = year_start - 57
            if '1st' in q or 'first' in q:
                return f"{ad_year}-07-15"
            elif '2nd' in q or 'second' in q:
                return f"{ad_year}-10-15"
            elif '3rd' in q or 'third' in q:
                return f"{ad_year + 1}-01-15"
            elif '4th' in q or 'fourth' in q:
                return f"{ad_year + 1}-04-15"
        return None
