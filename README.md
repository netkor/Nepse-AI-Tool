# NEPSE AI Signal & Alert System

A complete **production-ready web application** for Nepal stock market (NEPSE) tracking with AI-powered signals, alerts, and insights.

## 🎯 Overview

NEPSE AI provides:
- **Real-time trading signals** using technical indicators (MA, Volume, RSI)
- **Smart alerts** via Telegram Bot API
- **Watchlist management** with price alerts
- **Dashboard** with market overview and recent signals
- **JWT authentication** with secure token management
- **Background job scheduler** (no Celery needed)
- **Mock NEPSE data** for development

## 🛠️ Tech Stack (FREE TIER ONLY)

### Backend
- **Django 5.0** + Django REST Framework
- **SQLite** - Database
- **SimpleJWT** - Authentication
- **APScheduler** - Background jobs
- **Pandas** - Data analysis
- **Telegram Bot API** - Notifications

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Recharts** - Charts (future)
- **React Router** - Navigation

### DevOps
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - Production WSGI server
- **SQLite** - No external DB needed

## 📦 Project Structure

```
nepse-ai-tool/
├── nepse_backend/          # Django backend
│   ├── nepse_backend/      # Project settings
│   ├── accounts/           # User authentication
│   ├── stocks/             # Stock management
│   ├── signals/            # Signal engine
│   ├── alerts/             # Watchlist & alerts
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── nepse_frontend/         # React frontend
│   ├── src/
│   │   ├── api/            # API client & interceptors
│   │   ├── context/        # Auth context
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── hooks/          # Custom hooks
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml      # Full stack orchestration
└── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Docker Compose (Easiest)

```bash
# 1. Clone the repo
cd nepse-ai-tool

# 2. Configure environment
cp nepse_backend/.env.example nepse_backend/.env

# 3. Run with Docker
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000/api
# Admin: http://localhost:8000/admin
```

### Option 2: Local Development

#### Backend Setup
```bash
cd nepse_backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Setup database
python manage.py migrate
python manage.py seed_stock_data
python manage.py createsuperuser

# Run server
python manage.py runserver
```

#### Frontend Setup (in new terminal)
```bash
cd nepse_frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start dev server
npm run dev
```

Access:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Admin: `http://localhost:8000/admin`

## 📝 Initial Setup Guide

### 1. User Registration
- Navigate to `/register`
- Create account with email, username, password
- Login at `/login`

### 2. Setup Telegram Alerts (Optional)
- Create a Telegram bot via [@BotFather](https://t.me/botfather)
- Get bot token and add to backend `.env`:
  ```
  TELEGRAM_BOT_TOKEN=your_token_here
  ```
- User sends `/start` to bot to get chat ID
- User adds chat ID in profile settings
- Enable "Telegram Alerts" in preferences

### 3. Build Your Watchlist
- Go to **Watchlist** page
- Search for NEPSE stocks
- Add stocks to track

### 4. Set Price Alerts
- Click on a stock in watchlist
- Set minimum and maximum price thresholds
- Get notified when prices hit targets

### 5. Monitor Signals
- Go to **Signals** page
- View BUY/SELL/ALERT signals
- Filter by type and confidence level

## 🔧 API Documentation

### Authentication Endpoints
```bash
POST /api/auth/register/
{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}

POST /api/auth/login/
{
  "username": "user@example.com",
  "password": "securepassword"
}
# Returns: { "access": "token...", "refresh": "token..." }

POST /api/auth/refresh/
{
  "refresh": "refresh_token..."
}
```

### Stock Endpoints
```bash
GET /api/stocks/                    # List all stocks
GET /api/stocks/{id}/               # Get stock details
GET /api/stocks/{symbol}/history/   # Price history
GET /api/stocks/statistics/overview/ # Market stats
```

### Signal Endpoints
```bash
GET /api/signals/                   # List all signals
GET /api/signals/?signal_type=BUY   # Filter by type
GET /api/signals/?min_confidence=75 # Filter by confidence
GET /api/signals/stock/{symbol}/    # Get signals for stock
```

### Alert Endpoints
```bash
GET /api/alerts/watchlist/                  # Get watchlist
POST /api/alerts/watchlist/
  { "stock_id": 1 }                         # Add to watchlist

GET /api/alerts/price/                      # List price alerts
POST /api/alerts/price/
  { "stock_id": 1, "min_price": 100, "max_price": 200 }
```

## 📊 Signal Engine

Runs automatically every **15 minutes** (configurable).

### Indicators

1. **Moving Average Crossover** (5-day vs 20-day)
   - **BUY**: Fast MA crosses above Slow MA
   - **SELL**: Fast MA crosses below Slow MA
   - Confidence: 75%

2. **Volume Spike** (>2x average)
   - **ALERT**: Unusual trading volume detected
   - Confidence: 60-85%

3. **RSI Extreme** (Overbought/Oversold)
   - **BUY**: RSI < 30
   - **SELL**: RSI > 70
   - Confidence: 50-70%

### Duplicate Prevention
- No same signal for same stock within **1 hour**
- Prevents alert fatigue

## 🔔 Telegram Notifications

When signals trigger or price alerts hit:

```
🟢 BUY SIGNAL
Stock: NABIL
Price: Rs 720
Confidence: 82%

Reason: MA(5) buy crossover MA(20).
Fast MA: $715.23, Slow MA: $712.45
```

## 🐳 Docker Deployment

### Build & Run
```bash
docker-compose up --build
```

### Services
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`
- **Redis**: `localhost:6379`

### Volumes
- `backend_db`: SQLite database
- `redis_data`: Redis persistence

## 🌐 Environment Variables

### Backend (.env)
```env
DEBUG=False
SECRET_KEY=<change-this>
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:3000
TELEGRAM_BOT_TOKEN=<your-token>
SIGNAL_ENGINE_INTERVAL_MINUTES=15
JWT_EXPIRATION_HOURS=24
```

### Frontend (.env.local)
```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## 📈 Market Data

Mock NEPSE stocks included:
- **NABIL** - Nabil Bank
- **EBL** - Everest Bank
- **NTC** - Nepal Telecom
- **HIDCL** - Himalayan Development
- ... 16 more stocks

Generate 90 days of historical data automatically on startup.

## 🔒 Security Features

✅ JWT-based authentication  
✅ Password hashing (PBKDF2)  
✅ CORS configured  
✅ HTTPS ready (configure reverse proxy)  
✅ SQLite for simplicity  
✅ No sensitive data in logs  
✅ Token refresh mechanism  
✅ Environment variable protection  

## 🚀 Production Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=False`
- [ ] Update `ALLOWED_HOSTS`
- [ ] Configure HTTPS/SSL
- [ ] Setup database backup
- [ ] Enable rate limiting
- [ ] Monitor APScheduler jobs
- [ ] Setup logging service
- [ ] Add health checks

## 📁 Key Files

| File | Purpose |
|------|---------|
| `nepse_backend/settings.py` | Django configuration |
| `nepse_backend/scheduler.py` | Background jobs setup |
| `nepse_backend/telegram_service.py` | Telegram notifications |
| `signals/services.py` | Signal generation engine |
| `signals/utils.py` | Technical indicators |
| `stocks/data_provider.py` | Data abstraction layer |
| `accounts/views.py` | Auth endpoints |
| `nepse_frontend/src/api/index.js` | API client |
| `nepse_frontend/src/context/AuthContext.jsx` | Auth state |

## 🎓 Learning Resources

- **Django REST Framework**: [Tutorial](https://www.django-rest-framework.org/)
- **React Hooks**: [Docs](https://react.dev/reference/react)
- **Technical Analysis**: [TA-Lib Concepts](https://en.wikipedia.org/wiki/Technical_analysis)
- **JWT Auth**: [jwt.io](https://jwt.io)

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check migrations
python manage.py migrate

# Seed data
python manage.py seed_stock_data

# Create superuser
python manage.py createsuperuser
```

### Frontend can't reach backend
- Ensure backend is running on `8000`
- Check `VITE_API_BASE_URL` in `.env.local`
- Check CORS in backend `.env`

### Signals not generating
- Check scheduler is running: `ps aux | grep scheduler`
- Verify stocks exist: `python manage.py shell`
- Check logs for errors

### Telegram alerts not working
- Verify `TELEGRAM_BOT_TOKEN` is set
- Ensure user `telegram_verified=True`
- Check if "Telegram Alerts" enabled in profile

## 📞 Support & Issues

For help:
1. Check README in respective folders (`nepse_backend/`, `nepse_frontend/`)
2. Review error logs
3. Create issue with error details

## 📄 License

This project is open source for educational purposes.

## 🎉 Features Included

✅ Complete Django backend with 4 apps  
✅ React frontend with Vite  
✅ JWT authentication with refresh tokens  
✅ Technical signal engine (3 indicators)  
✅ APScheduler background jobs  
✅ Telegram Bot integration  
✅ SQLite database  
✅ Docker & Docker Compose  
✅ Mock NEPSE data (20 stocks)  
✅ Admin panel  
✅ Comprehensive documentation  

## 🚀 Next Steps (Future Enhancements)

- Real NEPSE API integration
- Advanced charting (Recharts)
- Email notifications
- Mobile app (React Native)
- Database migration (PostgreSQL)
- Advanced analytics dashboard
- Machine learning predictions
- API rate limiting
- WebSocket real-time updates

---

**Built with ❤️ for NEPSE traders**

Start tracking NEPSE stocks with AI-powered signals today! 📈
