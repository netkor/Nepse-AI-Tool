# NEPSE Analysis Project Memory

This file serves as a memory store for the agent. It contains key architectural details, models, and calculation logic for the `nepse analysis` project.

## Architecture & Tech Stack

1. **`nepse-data`**: A web scraping component (Python).
   - Scrapes data from `sharesansar.com` (both historical and daily).
   - Stores data as CSV files per company (`data/company-wise/<SYMBOL>.csv`).
   - Uses GitHub Actions for automation (CRON job runs 5 times daily).

2. **`nepse_backend`**: A Django/DRF backend application.
   - Responsible for API delivery, user authentication, and financial technical analysis.
   - Connects to SQLite (currently `db.sqlite3`).
   - Apps:
     - `stocks`: Manages `Stock`, `StockHistory`, and `PortfolioItem`.
     - `alerts`: Manages `Watchlist` and `Alert`.
     - `signals`: Handles calculation logic and scanners.
     - `accounts`: Handles authentication (JWT).

3. **`nepse_frontend`**: A React application (built with Vite).
   - Dashboards, stock screeners, portfolio management, and watchlist alerts.
   - Key UI pages: `Dashboard.jsx`, `Portfolio.jsx`, `Scanners.jsx`, `StockDetail.jsx`, `WatchlistAlerts.jsx`.

## Key Backend Models & Behaviors

*   **`stocks.models.PortfolioItem`**: When a new portfolio item is created, its `save()` method is overridden to automatically:
    1. Create a `Watchlist` entry for the user and stock.
    2. Create a Target Profit `Alert` set to +10% of the cost price.
    3. Create a Stop Loss `Alert` set to -10% of the cost price.

## Technical Analysis (Calculators)
Located in `nepse_backend/signals/calculators.py`. It uses `pandas` and `numpy` to calculate technical indicators.

*   **Signals Evaluated**:
    - **Price Action**: Crosses between EMA20 and EMA50 (Golden/Death Cross). Volume Breakouts (volume > 2.5x the 20-day average volume).
    - **MACD**: Crossovers between MACD and Signal lines.
    - **Mean Reversion**: Uses 14-day RSI (Oversold <= 30, Overbought >= 70).
    - **Divergence**: Spots bullish and bearish divergences between Price (closing highs/lows) and RSI (peaks/valleys).
    - **Dow Theory**: Analyzes historical price peaks and valleys for Higher Highs/Lows and Lower Highs/Lows.
    - **Weekly Signals**: Resamples data weekly (ending Fridays) and looks for 20-week and 50-week SMA crosses (Macro trend alerts).
    - **Seasonality**: Groups closing prices per month to calculate average historical monthly returns.

*   **Risk Management (Stop Loss / Take Profit)**:
    - Generated whenever a `BUY` signal occurs.
    - Employs 14-day ATR (Average True Range).
    - Target Profit = 3.0 * ATR above close.
    - Stop Loss = 1.5 * ATR below close.
    - Trailing SL = 1.5 * ATR below the 10-day high.

## Development Commands
*   **Frontend**: `cd nepse_frontend && npm run dev`
*   **Backend**: `cd nepse_backend && python manage.py runserver`
*   **Scrapers**: `cd nepse-data/src && python3 dailyDataScrapper.py`
*   **Backtest**: `source venv/bin/activate && cd nepse_backend && python manage.py run_backtest --holding-days=10`
*   **Update Data**: `bash update_data.sh` (pulls CSVs from GitHub + syncs to SQLite)

## Backtesting Module (Phase 1 — Complete)
Located in `nepse_backend/backtesting/`. Replays all existing signal types against historical data.

### Models
*   **`BacktestRun`**: One row per execution. Fields: `started_at`, `completed_at`, `holding_days`, `total_stocks`, `total_trades`, `status`.
*   **`BacktestResult`**: One row per (run × signal_type × direction). Fields: `total_trades`, `winning_trades`, `losing_trades`, `win_rate`, `avg_return_pct`, `avg_holding_days`, `max_drawdown_pct`, `best_trade_pct`.

### Signal Types Backtested
`EMA_CROSS`, `MACD_CROSS`, `RSI_MEAN_REVERSION`, `RSI_DIVERGENCE`, `DOW_THEORY`, `WEEKLY_SMA_CROSS`, `VOLUME_BREAKOUT`

### Key Files
*   `backtesting/engine.py` — Core backtest logic (no lookahead bias, ATR-based SL/TP, cooldown periods)
*   `backtesting/management/commands/run_backtest.py` — CLI: `--holding-days`, `--signal-type`, `--symbols`
*   `backtesting/views.py` — API: `GET /api/backtest/results/`, `GET /api/backtest/results/<signal_type>/`

### Initial Backtest Results (Run #1, 10-day hold, 372 stocks, 96,023 trades)
| Signal | Dir | Trades | Win% | Avg Ret |
|---|---|---|---|---|
| WEEKLY_SMA_CROSS | BUY | 955 | 48.4% | +6.33% |
| WEEKLY_SMA_CROSS | SELL | 1,021 | 49.9% | -3.50% |
| DOW_THEORY | SELL | 12,774 | 46.4% | +0.02% |
| EMA_CROSS | SELL | 4,313 | 44.9% | -0.31% |
| RSI_MEAN_REVERSION | BUY | 5,184 | 43.4% | +0.41% |
| VOLUME_BREAKOUT | BUY | 12,009 | 41.7% | +0.69% |
| DOW_THEORY | BUY | 9,391 | 42.5% | +0.66% |
| MACD_CROSS | BUY | 15,474 | 40.7% | +0.43% |

## Fundamental Data Layer (Phase 2 — Complete)
Adds sector classification and periodic financial metrics (like EPS, P/E, Book Value, and ROE) to stocks.

### Models
*   **`stocks.models.Stock`**: Added `sector` field with NEPSE's 13 categories (Commercial Bank, Development Bank, Finance, Microfinance, Hydropower, Life Insurance, Non-Life Insurance, Hotel & Tourism, Manufacturing and Processing, Trading, Investment, Mutual Fund, Others).
*   **`stocks.models.FundamentalSnapshot`**: Periodic fundamental metrics. Fields: `stock` (FK), `date`, `eps` (EPS), `pe_ratio` (P/E), `book_value` (Net Worth per share), `roe` (ROE), and bank-specific fields (`cd_ratio`, `npl_ratio`, `capital_adequacy_ratio`).

### Scraping Commands
*   `python manage.py assign_sectors` — Scrapes `sharesansar.com/company/<symbol>` to update sectors.
*   `python manage.py import_fundamentals` — Performs a session-primed POST request to `sharesansar.com/company-quarterly-report` to scrape and store fundamental snapshots with converted A.D. quarter dates. Automatically heals empty sectors during parsing.

### API Endpoints
*   `GET /api/stocks/<symbol>/fundamentals/` — List of fundamental snapshots for a symbol.
*   `GET /api/stocks/sectors/summary/` — Sector-wise counts, average stock prices, and active BUY/SELL/HOLD signal distributions.

## Confluence & Performance Optimization (Phase 3 — Complete)
Introduced a multi-factor technical confluence scoring engine with fundamental filters, along with major backtesting engine optimization.

### Multi-Factor Confluence Score
*   **Formula**: Combines EMA Cross (±20), MACD Crossover (±20), RSI Oversold/Overbought (±15), RSI Divergence (±15), and Dow Theory (±15) to produce a Technical Score from -100 to +100.
*   **Fundamental Gating**: Reduces the Technical Score using penalties (e.g. -20% for P/E > 35, -20% for ROE < 8%) based on the stock's historical quarterly fundamental snapshot active at the time.
*   **Recommendation Thresholds**:
    *   Technical Score >= 50: **STRONG BUY** (or **BUY** if penalized)
    *   Technical Score <= -50: **STRONG SELL** (or **SELL** if penalized)
    *   Otherwise: **HOLD**

### Performance Optimizations (1000x Speedup)
*   **Pre-loaded Snapshots**: Fundamental snapshots are queried once per stock in `run_backtest` and passed down, solving the Django N+1 query problem in the daily bar loop.
*   **Pre-calculated Valleys/Peaks**: Avoids executing python loops with Pandas `.iloc` inside `calculate_confluence_score`. Local peak/valley detection is done once per stock using vectorized shift operations, and the subset of peaks/valleys inside scanner lookback windows is retrieved using fast numpy array slicing.
*   **Backtest Engine Execution Time**: Reduced the full market backtest runtime from ~40 minutes to under 10 minutes.

### Confluence Backtest Results (Run #10, 10-day hold, 372 stocks)
| Signal | Dir | Trades | Win% | Avg Ret | Max DD | Best | Avg Days |
|---|---|---|---|---|---|---|---|
| CONFLUENCE_SCORE | BUY | 5,253 | 41.1% | +0.48% | -25.61% | 25.62% | 6.1 |
| CONFLUENCE_SCORE | SELL | 2,801 | 44.0% | -0.44% | -17.89% | 28.71% | 7.1 |

## Liquidity Filter (Phase 4 — Complete)
Ensures that we do not generate actionable BUY/SELL signals for illiquid stocks that cannot be easily entered/exited in the real market.

### Calculations & Logic
*   **Daily Turnover**: Calculated dynamically as `Close Price × Volume`.
*   **Average Turnover**: A 20-day rolling mean of daily turnover (`avg_turnover20`) is computed for every stock during indicator calculation.
*   **API Filter**: The backend endpoints (`/api/signals/`, `/api/signals/custom-strategy/`, etc.) accept a `min_turnover` parameter and apply a hard filter. Stocks falling below this threshold are entirely excluded from the scanner results.
*   **UI Settings**: The `Scanners.jsx` interface includes a filter dropdown that defaults to **Rs. 50 Lakhs (5,000,000)** for the 20-day average turnover, giving users the option to adjust the threshold dynamically.

## Portfolio-Level Risk Checks (Phase 5 — Complete)
Provides an automated portfolio diversification analysis tool that computes sector concentration and warns users if they are dangerously over-exposed to a single sector.

### Architecture & Logic
*   **API Endpoint**: `GET /api/stocks/portfolio/risk/` accepts a `threshold` parameter (default 50%). It aggregates the total current value of all holdings per sector based on the authentic `Stock.sector` field.
*   **Response**: Returns the portfolio's total value, individual sector percentage allocations, and a boolean `is_over_exposed` flag if a sector exceeds the threshold and the user holds more than one stock.
*   **Frontend UI**: `Portfolio.jsx` fetches the risk analysis and displays a `Diversification Warning` conditionally. The UI includes a `Sector Risk Threshold` dropdown allowing users to adjust their personal concentration risk tolerance (30%, 40%, 50%, 60%, or 100%).

## Event/Regulatory Calendar (Phase 6 — Complete)
Introduces a `MarketEvent` system to track known upcoming catalysts and surfaces them alongside technical alerts.

### Architecture & Logic
*   **Data Model**: The `MarketEvent` model tracks `event_type`, `event_date`, and `title`. It accepts an optional foreign key to a `Stock` (null indicates a market-wide event). A management command (`seed_mock_events`) populates test data.
*   **API Annotations**: Technical scanner endpoints (`SignalsListView`, `CustomStrategyView`, `ConfluenceSignalsListView`) query for upcoming events (within 30 days) and append an `upcoming_events` list and an `event_annotation` string to their payload.
*   **Frontend UI**: `Scanners.jsx` dynamically renders a calendar icon (📅) and the `event_annotation` below the stock symbol in the scanner tables. `StockDetail.jsx` displays a prominent "Upcoming Events" card.
