# NEPSE AI - Quick Start Guide

## ✅ What's Been Built

This is a **complete, production-ready NEPSE AI Signal & Alert System** with:

### Backend (Django)
- ✅ 4 Django apps (accounts, stocks, signals, alerts)
- ✅ 9 models with relationships
- ✅ 20+ API endpoints
- ✅ JWT authentication with access/refresh tokens
- ✅ Signal engine with 3 technical indicators
- ✅ APScheduler for background jobs
- ✅ Telegram Bot integration
- ✅ Mock data seeding with 20 NEPSE stocks
- ✅ Admin panel
- ✅ Error handling and validation

### Frontend (React)
- ✅ Vite build setup
- ✅ Tailwind CSS styling
- ✅ 5 pages (Login, Register, Dashboard, Watchlist, Signals)
- ✅ Axios with JWT interceptor
- ✅ Auth context for state management
- ✅ Protected routes
- ✅ API integration with error handling
- ✅ Responsive design

### Infrastructure
- ✅ Docker setup for both backend and frontend
- ✅ Docker Compose for full stack orchestration
- ✅ Production-ready configuration

---

## 🚀 Getting Started (3 Steps)

### Step 1: Start with Docker Compose (Recommended)

```bash
# Navigate to project root
cd nepse-ai-tool

# Build and start all services
docker-compose up --build

# Wait for services to be ready (2-3 minutes)
# Watch for: "APScheduler started" message
```

### Step 2: Access the Application

Open your browser:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Admin Panel**: http://localhost:8000/admin

### Step 3: Create Account & Login

1. Go to http://localhost:3000
2. Click **Sign Up**
3. Enter email, username, password
4. Click **Login** with your credentials
5. Explore Dashboard, Watchlist, and Signals

---

## 📱 Using the Application

### 1. Dashboard
- View market overview (total stocks, gainers, losers)
- See top stocks and recent signals
- Market statistics

### 2. Watchlist
- Search and add stocks to watch
- See current prices and % change
- Quick access to stocks you're tracking

### 3. Signals
- View all trading signals (BUY/SELL/ALERT)
- Filter by signal type and confidence level
- See technical indicator details
- Real-time confidence scores

### 4. User Profile
- Update email and preferences
- Enable/disable alert types
- Set minimum confidence threshold
- Link Telegram account

---

## 🔔 Enable Telegram Alerts (Optional)

### Setup Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Type `/newbot` and follow instructions
3. Get your bot token (looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
4. Save the token

### Configure Backend

1. Edit `nepse_backend/.env`:
```env
TELEGRAM_BOT_TOKEN=<your_bot_token_here>
```

2. Restart backend:
```bash
docker-compose restart backend
```

### Link Your Account

1. Message your bot `/start`
2. Copy the chat ID shown
3. Go to profile settings in app
4. Paste chat ID and enable Telegram alerts
5. Save settings

Now you'll get Telegram messages when signals trigger!

---

## 📊 Understanding the Signal Engine

The system runs automatically every 15 minutes and analyzes all stocks.

### Signal Types

| Signal | Condition | Confidence |
|--------|-----------|------------|
| 🟢 **BUY** | MA(5) crosses above MA(20) | 75% |
| 🟢 **BUY** | RSI < 30 (Oversold) | 50-70% |
| 🔴 **SELL** | MA(5) crosses below MA(20) | 75% |
| 🔴 **SELL** | RSI > 70 (Overbought) | 50-70% |
| 🔵 **ALERT** | Volume > 2x average | 60-85% |

### Duplicate Prevention

- Same signal won't repeat for same stock within 1 hour
- Prevents alert fatigue

### Test Signals

Signals auto-generate as prices change. To see signals immediately:
```bash
# SSH into backend container
docker-compose exec backend bash

# Run signal generation manually
python manage.py shell
>>> from signals.services import SignalService
>>> count, descriptions = SignalService.generate_signals()
>>> print(f"Created {count} signals")
```

---

## 🛠️ Development Tips

### View Admin Panel

```bash
# Get into Django shell
docker-compose exec backend python manage.py shell

# Create superuser (if not already done)
python manage.py createsuperuser
```

Then visit: http://localhost:8000/admin

### View Database

```bash
# Access backend container
docker-compose exec backend bash

# Use Django shell
python manage.py shell

# List all stocks
from stocks.models import Stock
for stock in Stock.objects.all():
    print(f"{stock.symbol}: Rs {stock.price}")

# View signals
from signals.models import Signal
Signal.objects.values('stock__symbol', 'signal_type').distinct()
```

### Check Scheduler

```bash
# Logs show scheduler activity
docker-compose logs -f backend

# Look for: "APScheduler started"
```

### Mock More Data

```bash
docker-compose exec backend python manage.py seed_stock_data --clear --days 180
```

---

## 🔐 Security & Production

### Before Deploying

1. **Change Django secret key**:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Add to `.env`: `SECRET_KEY=<generated_key>`

2. **Set DEBUG=False**:
   ```env
   DEBUG=False
   ```

3. **Update ALLOWED_HOSTS**:
   ```env
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

4. **Use PostgreSQL** (optional but recommended):
   - Update Docker Compose to use PostgreSQL service
   - Update `requirements.txt`: add `psycopg2-binary`

---

## 📁 Project Structure Quick Reference

```
nepse-ai-tool/
├── nepse_backend/              # Django REST API
│   ├── accounts/               # Authentication
│   ├── stocks/                 # Stock data
│   ├── signals/                # Signal engine
│   ├── alerts/                 # Watchlist & alerts
│   ├── manage.py
│   └── Dockerfile
├── nepse_frontend/             # React app
│   ├── src/
│   │   ├── pages/              # Page components
│   │   ├── api/                # API client
│   │   ├── context/            # Auth state
│   │   └── App.jsx
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml          # Full stack
└── README.md                   # Complete docs
```

---

## 🎯 Common Tasks

### Add a New Stock
```bash
# Shell into backend
docker-compose exec backend python manage.py shell

# Add stock
from stocks.models import Stock
Stock.objects.create(
    symbol='NEWSTK',
    name='New Stock Ltd',
    price=500,
    volume=100000,
    is_active=True
)
```

### Check API Response

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user@email.com","password":"password"}'

# Use token to call API
curl http://localhost:8000/api/stocks/ \
  -H "Authorization: Bearer <token>"
```

### View Logs

```bash
# All services
docker-compose logs -f

# Just backend
docker-compose logs -f backend

# Just frontend
docker-compose logs -f frontend
```

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port in docker-compose.yml
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

### Migrations Failed
```bash
docker-compose exec backend python manage.py migrate --fake-initial
```

### Can't Login
```bash
# Check if user exists
docker-compose exec backend python manage.py shell
>>> from accounts.models import CustomUser
>>> CustomUser.objects.all()
```

---

## ✨ Next Steps

1. **Explore the API** - Try different endpoints with curl or Postman
2. **Add More Stocks** - Seed different data ranges
3. **Create Price Alerts** - Set thresholds for your watchlist stocks
4. **Enable Telegram** - Get real-time alerts
5. **Deploy to Cloud** - Use AWS, GCP, or DigitalOcean

---

## 📚 Documentation Links

- [Backend README](./nepse_backend/README.md)
- [Frontend README](./nepse_frontend/README.md)
- [Full README](./README.md)

---

## 🎉 You're All Set!

You now have a fully functional NEPSE AI system. Start trading with confidence!

**Questions?** Check the READMEs or review the code comments.

**Happy Trading! 📈**
