# NEPSE AI Signal & Alert System - Backend

Django REST Framework backend for NEPSE AI Signal & Alert System.

## 📋 Features

✅ **JWT Authentication** - Secure access/refresh token-based authentication  
✅ **Stock Management** - Tracking 20+ NEPSE stocks with historical OHLCV data  
✅ **Signal Engine** - Technical indicators (MA crossover, Volume spike, RSI)  
✅ **Telegram Alerts** - Real-time notifications via Telegram Bot API  
✅ **APScheduler** - Background jobs (no Celery required)  
✅ **Watchlist & Price Alerts** - User-managed watchlists and custom alerts  
✅ **Mock Data** - Built-in realistic data generator  

## 🛠️ Tech Stack

- **Django 5.0** - Web framework
- **Django REST Framework** - API development
- **SQLite** - Database
- **SimpleJWT** - JWT authentication
- **APScheduler** - Background job scheduler
- **Pandas & NumPy** - Data analysis & calculations
- **Gunicorn** - WSGI server (production)

## 🚀 Setup

### Local Development

1. **Clone & Navigate**
```bash
cd nepse_backend
```

2. **Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Create Database & Seed Data**
```bash
python manage.py migrate
python manage.py seed_stock_data
```

6. **Create Superuser**
```bash
python manage.py createsuperuser
```

7. **Run Development Server**
```bash
python manage.py runserver
```

Backend runs on `http://localhost:8000`

## 📊 API Endpoints

### Authentication
```
POST   /api/auth/register/          - Register new user
POST   /api/auth/login/             - Login & get tokens
POST   /api/auth/refresh/           - Refresh access token
GET    /api/auth/profile/           - Get user profile
PATCH  /api/auth/profile/           - Update profile
POST   /api/auth/change-password/   - Change password
```

### Stocks
```
GET    /api/stocks/                 - List all stocks
GET    /api/stocks/{id}/            - Get stock detail
GET    /api/stocks/{symbol}/history/ - Get stock price history
GET    /api/stocks/statistics/overview/ - Market statistics
```

### Signals
```
GET    /api/signals/                - List all signals
GET    /api/signals/{id}/           - Get signal detail
GET    /api/signals/stock/{symbol}/ - Get signals for stock
POST   /api/signals/{id}/mark-notified/ - Mark signal as notified
```

### Alerts (Watchlist & Price Alerts)
```
GET    /api/alerts/watchlist/       - Get user's watchlist
POST   /api/alerts/watchlist/       - Add stock to watchlist
DELETE /api/alerts/watchlist/{id}/  - Remove from watchlist

GET    /api/alerts/price/           - List price alerts
POST   /api/alerts/price/           - Create price alert
PATCH  /api/alerts/price/{id}/      - Update alert
DELETE /api/alerts/price/{id}/      - Delete alert
```

## 🔑 Authentication

All endpoints (except register/login) require JWT token:

```bash
Authorization: Bearer <access_token>
```

Tokens are managed in `accounts/views.py` with:
- **Access Token**: 24 hours validity
- **Refresh Token**: 7 days validity

## 📈 Signal Engine

Located in `signals/services.py` - runs every 15 minutes (configurable):

### Indicators
1. **MA Crossover** (5-day vs 20-day)
   - Buy: When fast MA crosses above slow MA
   - Sell: When fast MA crosses below slow MA

2. **Volume Spike** (2x average volume)
   - Detects unusual trading activity

3. **RSI** (Relative Strength Index)
   - Buy: RSI < 30 (oversold)
   - Sell: RSI > 70 (overbought)

**Duplicate Prevention**: No same signal for same stock within 1 hour

## 🔔 Telegram Integration

### Setup

1. Create a Telegram bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID by messaging `/start` to the bot
3. Add to `.env`:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

### How It Works

- Users add their `telegram_chat_id` to profile
- System sends alerts when signals trigger
- Users get notified with:
  - Signal type, confidence, stock info
  - Price alerts with thresholds

## 🌱 Mock Data

Generate realistic NEPSE stock data:

```bash
python manage.py seed_stock_data
python manage.py seed_stock_data --clear --days 180
```

Includes 20 realistic NEPSE stocks with 90 days of historical data.

## 📁 Project Structure

```
nepse_backend/
├── nepse_backend/          # Main settings
│   ├── settings.py         # Django settings
│   ├── urls.py             # URL routing
│   ├── scheduler.py        # APScheduler setup
│   ├── telegram_service.py # Telegram API
│   └── utils.py            # Helpers
├── accounts/               # User auth
├── stocks/                 # Stock management
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── data_provider.py    # Data abstraction
│   └── management/commands/seed_stock_data.py
├── signals/                # Signal engine
│   ├── models.py
│   ├── services.py         # Signal generation
│   ├── utils.py            # Indicators
│   ├── serializers.py
│   └── views.py
├── alerts/                 # Watchlist & alerts
├── manage.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 🐳 Docker

### Build & Run

```bash
docker build -t nepse-backend .
docker run -p 8000:8000 nepse-backend
```

See root `docker-compose.yml` for complete stack.

## 🔒 Security Notes

- ⚠️ **Change SECRET_KEY in production**
- ⚠️ **Use environment variables for sensitive data**
- ⚠️ **Enable CSRF in production**
- ✅ Passwords hashed with Django defaults
- ✅ JWT tokens signed with SECRET_KEY
- ✅ CORS configured for frontend origin
- ✅ Telegram token never exposed in logs

## 📊 Admin Panel

Access Django admin at `/admin/` with superuser credentials:

```bash
python manage.py createsuperuser
```

Manage stocks, signals, users, and alerts from the admin interface.

## 🚀 Production Deployment

1. Update `.env` with production settings:
```
DEBUG=False
SECRET_KEY=<new-random-key>
ALLOWED_HOSTS=yourdomain.com
```

2. Collect static files:
```bash
python manage.py collectstatic --noinput
```

3. Run with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:8000 nepse_backend.wsgi:application
```

4. Use Docker Compose (see root README)

## 📝 Environment Variables

```env
# Core
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///db.sqlite3

# JWT
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
JWT_REFRESH_EXPIRATION_DAYS=7

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_API_URL=https://api.telegram.org/bot

# Signal Engine
SIGNAL_ENGINE_INTERVAL_MINUTES=15
```

## 🔗 Connected Services

- **Frontend**: React app on `localhost:5173`
- **Database**: SQLite (`db.sqlite3`)
- **Telegram**: External API
- **APScheduler**: In-process background jobs

## 📞 Support

For issues or features, check the main README or create an issue in the repository.

---

**Happy Stock Trading! 📈**
