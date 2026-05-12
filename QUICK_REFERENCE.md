"""
NEPSE AI TOOL - QUICK REFERENCE GUIDE

Fast lookup for all new features, files, and endpoints
"""

# ==============================================================================
# NEW API ENDPOINTS (Phase 2)
# ==============================================================================

## Authentication

POST   /api/auth/logout/
  - Blacklist tokens on logout
  - Request: { "refresh": "token_string" }
  - Response: { "success": true, "message": "Logout successful" }

POST   /api/auth/refresh/
  - Get new access token from refresh token
  - Request: { "refresh": "token_string" }
  - Response: { "success": true, "access": "new_token" }

## Health & Monitoring

GET    /api/health/health/
  - Check service health
  - Response: { "status": "ok", "service": "nepse-ai-backend", ... }

---

# ==============================================================================
# NEW MODULES & CLASSES
# ==============================================================================

## config/auth.py

TokenManager
  - create_access_token(user, extra_claims)
  - create_refresh_token(user)
  - decode_access_token(token)
  - refresh_access_token(refresh_token)
  - blacklist_token(token, timeout)
  - is_token_blacklisted(token)

EnhancedJWTAuthentication
  - Custom JWT auth class with blacklist support
  - Drop-in replacement for JWTAuthentication

Functions:
  - get_tokens_for_user(user)
  - get_user_from_token(token)
  - verify_token_signature(token)

## core/models.py

BaseModel
  - Abstract base with UUID, timestamps, is_active
  - id (UUID primary key)
  - created_at (auto timestamp)
  - updated_at (auto timestamp)
  - is_active (soft-delete flag)
  - Methods: soft_delete(), restore()

SoftDeleteQuerySet & SoftDeleteManager
  - Automatic filtering of inactive objects
  - Methods: active(), inactive(), all_including_deleted()

TimestampedModel
  - Just created_at/updated_at, no UUID

UUIDModel
  - Just UUID primary key

## core/services.py

BaseService
  - Abstract service class for business logic
  - Methods: get_by_id, get_all, create, update, delete, soft_delete
  - Automatic transaction management
  - Built-in error handling and logging

ServiceRegistry
  - Manage service instances
  - Singleton pattern support
  - Methods: register, get, has, clear

Decorators:
  - @service_transaction - Atomic operations
  - @service_cache(timeout) - Cache results
  - @service_logger - Automatic logging

## core/permissions.py

Permission Classes:
  - IsOwner - Only owner can access
  - IsOwnerOrReadOnly - Owner can write, others read-only
  - IsAdmin - Only staff users
  - IsSuperUser - Only superusers
  - IsOwnerAndVerified - Owner + verified user
  - RolePermission - Base for custom roles
  - HasPermission - Dynamic permission checking

Functions:
  - get_user_permissions(user)
  - user_has_permission(user, permission)
  - user_has_any_permission(user, permissions)
  - user_has_all_permissions(user, permissions)

Decorators:
  - @require_permission(perm)
  - @require_any_permission(*perms)
  - @require_authenticated()
  - @require_admin()

## core/utils.py

Pagination:
  - StandardResultsSetPagination (20 items)
  - LargeResultsSetPagination (100 items)
  - SmallResultsSetPagination (10 items)

Functions:
  - validate_email(email)
  - validate_phone(phone)
  - get_user_or_404(user_id)
  - filter_active_objects(queryset)

## config/exceptions.py

Exception Classes:
  - NepseAIException - Base exception
  - ValidationError
  - SignalGenerationError
  - AlertTriggeringError
  - TelegramServiceError
  - DataProviderError
  - NotificationError
  - SubscriptionError
  - PermissionDeniedError
  - ResourceNotFoundError

Functions:
  - custom_exception_handler(exc, context)
  - @retry_on_exception(max_retries, delay, backoff, exceptions)

## config/logging_config.py

Functions:
  - get_logging_config(debug)
  - setup_logging(debug)

Loggers Available:
  - django.*
  - celery.*
  - config
  - accounts
  - stocks
  - signals
  - alerts

---

# ==============================================================================
# ENVIRONMENT VARIABLES
# ==============================================================================

## Django

DEBUG=True                          # Debug mode (False for production)
SECRET_KEY=change-me                # Django secret key
DJANGO_SETTINGS_MODULE=config.settings.dev  # Settings module
ALLOWED_HOSTS=localhost,127.0.0.1  # Allowed hosts

## Database

POSTGRES_DB=nepse_db                # Database name
POSTGRES_USER=nepse_user            # Database user
POSTGRES_PASSWORD=change-me         # Database password
POSTGRES_HOST=postgres              # Database host (docker service name)
POSTGRES_PORT=5432                  # Database port

## Redis & Celery

CELERY_BROKER_URL=redis://redis:6379/0  # Celery broker
CELERY_RESULT_BACKEND=redis://redis:6379/0  # Task results backend
CELERY_WORKER_CONCURRENCY=2         # Worker processes
SIGNAL_ENGINE_INTERVAL_MINUTES=15   # Signal generation interval

## JWT

JWT_SECRET=change-me                # JWT secret key
JWT_ALGORITHM=HS256                 # JWT algorithm
JWT_EXPIRATION_HOURS=24             # Access token lifetime
JWT_REFRESH_EXPIRATION_DAYS=7       # Refresh token lifetime

## Telegram (Optional)

TELEGRAM_BOT_TOKEN=                 # Telegram bot token
TELEGRAM_API_URL=https://api.telegram.org/bot

## CORS

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

## Flower (Monitoring)

FLOWER_BASIC_AUTH=admin:changeme    # Flower authentication

---

# ==============================================================================
# DOCKER COMMANDS
# ==============================================================================

## Build & Run

docker-compose up --build           # Build and start all services
docker-compose down                 # Stop all services
docker-compose down -v              # Stop and remove volumes
docker-compose restart              # Restart all services
docker-compose logs -f              # Watch all logs
docker-compose logs -f backend      # Watch backend logs only

## Database Operations

docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py seed_stock_data
docker-compose exec backend python manage.py shell

## Celery Operations

docker-compose logs -f celery_worker      # Watch worker
docker-compose logs -f celery_beat        # Watch scheduler
docker-compose exec backend celery -A config inspect active

## Access Services

Frontend:       http://localhost:5173      (or :3000)
Backend API:    http://localhost:8000/api
Admin Panel:    http://localhost:8000/admin
Flower Monitor: http://localhost:5555
Database:       postgresql://localhost:5432
Redis:          redis://localhost:6379

---

# ==============================================================================
# TESTING QUICK COMMANDS
# ==============================================================================

## Authentication Flow

# 1. Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"pass123","password2":"pass123"}'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"pass123"}'

# 3. Get Profile (replace TOKEN)
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer TOKEN"

# 4. Logout (replace TOKEN and REFRESH)
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"REFRESH"}'

# 5. Refresh Token (replace REFRESH)
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"REFRESH"}'

---

# ==============================================================================
# COMMON PATTERNS & USAGE
# ==============================================================================

## Using Service Layer

from stocks.models import Stock
from core.services import BaseService

class StockService(BaseService):
    model = Stock

# Usage
stock = StockService.get_by_id('stock_id')
all_stocks = StockService.get_all()
new_stock = StockService.create(symbol='TEST', name='Test', price=100)
StockService.update('stock_id', price=105)
StockService.delete('stock_id')

## Using Permissions in Views

from rest_framework.decorators import api_view, permission_classes
from core.permissions import require_permission, IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated, HasPermission])
@require_permission('can_manage_stocks')
def create_stock(request):
    # Only authenticated users with permission
    pass

## Using Token Manager

from config.auth import TokenManager, get_tokens_for_user

# Create tokens
tokens = get_tokens_for_user(user)
# Result: {'access': 'token', 'refresh': 'token'}

# Decode token
claims = TokenManager.decode_access_token(access_token)

# Refresh
new_access = TokenManager.refresh_access_token(refresh_token)

# Logout (blacklist)
TokenManager.blacklist_token(refresh_token)

## Using Decorators

from core.services import service_transaction, service_cache

class UserService(BaseService):
    model = User
    
    @service_transaction
    def create_bulk(self, users_data):
        # All creates are atomic
        for data in users_data:
            self.create(**data)
    
    @service_cache(timeout=3600)
    def get_active(self):
        # Results cached for 1 hour
        return self.get_all({'is_active': True})

---

# ==============================================================================
# IMPORTANT FILES
# ==============================================================================

Configuration:
  - nepse_backend/config/settings/base.py
  - nepse_backend/config/settings/dev.py
  - nepse_backend/config/settings/prod.py
  - nepse_backend/config/celery.py

Authentication:
  - nepse_backend/config/auth.py (NEW)
  - nepse_backend/accounts/views.py (UPDATED)
  - nepse_backend/accounts/urls.py (UPDATED)

Core Infrastructure:
  - nepse_backend/core/models.py (NEW)
  - nepse_backend/core/services.py (NEW)
  - nepse_backend/core/permissions.py (NEW)
  - nepse_backend/core/utils.py (NEW)
  - nepse_backend/core/exceptions.py (REFERENCED)

Docker:
  - docker-compose.yml
  - nepse_backend/Dockerfile
  - nepse_frontend/Dockerfile

Environment:
  - .env.example
  - .env (local, add to .gitignore)

---

# ==============================================================================
# TROUBLESHOOTING QUICK FIXES
# ==============================================================================

| Problem | Solution |
|---------|----------|
| "Token has been invalidated" | Token was blacklisted (logged out), get new access token using refresh |
| "Authentication credentials were not provided" | Add `Authorization: Bearer TOKEN` header |
| "Permission denied" | User lacks required permission, check permission_classes |
| "Database connection failed" | Ensure PostgreSQL container is running: `docker-compose ps postgres` |
| "Redis connection failed" | Ensure Redis container is running: `docker-compose ps redis` |
| "Celery tasks not running" | Check worker: `docker-compose logs celery_worker` |
| "Token refresh fails" | Refresh token might be expired or blacklisted |
| "Import not found" | Run `docker-compose up --build` to rebuild with new code |
| "Migrations needed" | Run `docker-compose exec backend python manage.py migrate` |

---

# ==============================================================================
# PERFORMANCE TIPS
# ==============================================================================

### Caching Service Results
```python
@service_cache(timeout=3600)
def get_expensive_data(self):
    # Results cached for 1 hour
    pass
```

### Batch Operations
```python
@service_transaction
def bulk_update(self, updates):
    for update in updates:
        self.update(**update)
```

### Async Tasks
```python
# Use Celery for long operations
from celery import shared_task

@shared_task
def process_signals():
    # Async processing
    pass
```

### Connection Pooling
Already configured in Docker PostgreSQL settings.
Production: Configure pgBouncer or similar.

---

# ==============================================================================
# WHAT'S NEXT
# ==============================================================================

Phase 3 (Ready to implement):
  - Modular signal engine
  - Signal history tracking
  - Signal cooldown system
  - Confidence calculation

Phase 4:
  - Centralized notification system
  - Telegram delivery
  - Notification templates
  - Retry logic

Phase 5:
  - Analytics tracking
  - Event aggregation
  - Performance metrics
  - Dashboard API

Phase 6:
  - Subscription management
  - Feature gating
  - Payment integration
  - Usage tracking

---

Document Updated: 2024-05-12
Status: Complete
Next: Phase 3 Ready
