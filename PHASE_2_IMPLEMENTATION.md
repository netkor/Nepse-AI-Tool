"""
PHASE 2: Backend Modernization - Implementation Guide

This document outlines the backend authentication, service layer, and
permission system upgrades for production-grade SaaS platform.
"""

# ==============================================================================
# PHASE 2: BACKEND MODERNIZATION & JWT ENHANCEMENTS
# ==============================================================================

## What's Been Implemented

### 1. Enhanced JWT Authentication System ✅
- **File**: `nepse_backend/config/auth.py`
- **Components**:
  - **TokenManager**: Centralized token management
  - **EnhancedJWTAuthentication**: Custom JWT auth with token blacklisting
  - **Utility functions**: get_tokens_for_user, get_user_from_token, verify_token_signature
- **Features**:
  - Custom JWT claims (user_id, email, username, timestamp)
  - Token refresh with automatic access token generation
  - Token blacklisting/invalidation support
  - Automatic token cache management (7-day timeout matching refresh lifetime)
  - Comprehensive error handling and logging
  - Token signature verification

### 2. Service Layer Pattern ✅
- **File**: `nepse_backend/core/services.py`
- **Components**:
  - **BaseService**: Abstract base class for all business services
  - **Service Registry**: Manage service instances and dependencies
  - **Decorators**: Transaction, caching, and logging decorators
- **Features**:
  - CRUD operations (create, read, update, delete)
  - Soft delete support for models with is_active field
  - Atomic transaction management
  - Error handling and logging integration
  - Singleton and lazy-loading patterns
  - Service caching with configurable timeout
  - Automatic logging of service calls

### 3. Role-Based Access Control (RBAC) ✅
- **File**: `nepse_backend/core/permissions.py`
- **Components**:
  - **Permission Classes**:
    - IsOwnerOrReadOnly
    - IsOwner
    - IsAdmin
    - IsSuperUser
    - IsOwnerAndVerified
    - RolePermission (base for custom roles)
    - HasPermission (dynamic permission checking)
  - **Permission Utilities**:
    - get_user_permissions()
    - user_has_permission()
    - user_has_any_permission()
    - user_has_all_permissions()
  - **Permission Decorators**:
    - @require_permission()
    - @require_any_permission()
    - @require_authenticated()
    - @require_admin()
- **Features**:
  - Django permission system integration
  - Custom role-based access control
  - Superuser bypass support
  - Group-based permissions
  - Decorator-based protection for views
  - Comprehensive logging of permission denials

### 4. Enhanced Accounts App ✅
- **Files**:
  - `nepse_backend/accounts/views.py`
  - `nepse_backend/accounts/urls.py`
- **New Endpoints**:
  - `POST /api/auth/logout/` - Logout user (blacklists token)
  - `POST /api/auth/refresh/` - Enhanced refresh token endpoint
- **Features**:
  - Token blacklisting on logout
  - Improved error responses
  - Logging for all auth operations
  - Consistent response format

### 5. Updated Django Settings ✅
- **File**: `nepse_backend/config/settings/base.py`
- **Changes**:
  - Updated DEFAULT_AUTHENTICATION_CLASSES to use EnhancedJWTAuthentication
  - All configuration now production-ready

### 6. Requirements Updated ✅
- **File**: `nepse_backend/requirements.txt`
- **Added**:
  - `PyJWT==2.8.1` (explicit version for clarity)

---

## Architecture Improvements

### Authentication Flow (Enhanced)

```
1. User Login
   POST /api/auth/login/
   {
     "username": "user@example.com",
     "password": "password123"
   }
   ↓
   CustomTokenObtainPairView generates both tokens with custom claims
   ↓
   Response:
   {
     "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
     "user_id": "uuid",
     "email": "user@example.com",
     "username": "user"
   }

2. Access Protected Endpoints
   Authorization: Bearer <access_token>
   ↓
   EnhancedJWTAuthentication:
   - Verifies token signature
   - Checks if token is blacklisted
   - Returns user object
   ↓
   Endpoint executes

3. Token Refresh
   POST /api/auth/refresh/
   {
     "refresh": "refresh_token_string"
   }
   ↓
   TokenManager.refresh_access_token()
   ↓
   Response:
   {
     "access": "new_access_token",
     "success": true
   }

4. User Logout
   POST /api/auth/logout/
   {
     "refresh": "refresh_token_string"
   }
   ↓
   TokenManager.blacklist_token() - adds to Redis cache
   ↓
   Response:
   {
     "success": true,
     "message": "Logout successful"
   }
   
5. Using Invalidated Token
   Authorization: Bearer <blacklisted_token>
   ↓
   EnhancedJWTAuthentication checks blacklist
   ↓
   AuthenticationFailed: "Token has been invalidated"
```

### Service Layer Pattern

```
User Request
   ↓
API View/ViewSet
   ↓
Service Layer (Business Logic)
   ├─ BaseService.create()
   ├─ BaseService.get_by_id()
   ├─ BaseService.update()
   ├─ BaseService.delete()
   └─ Custom business methods
   ↓
Database Model
   ↓
Response

Example:
    class StockService(BaseService):
        model = Stock
        
        @classmethod
        @service_transaction
        def bulk_update_prices(cls, stocks_data):
            for stock_data in stocks_data:
                cls.update(stock_data['id'], price=stock_data['price'])
        
        @classmethod
        @service_cache(timeout=3600)
        def get_trending_stocks(cls):
            return cls.get_all({'is_active': True}).order_by('-change_percent')[:10]
```

### Permission System

```
Permission Hierarchy:
├─ AllowAny (no authentication)
├─ IsAuthenticated (must be logged in)
├─ IsAdmin/IsSuperUser (staff or superuser)
├─ IsOwner (must be resource owner)
├─ IsOwnerOrReadOnly (owner can write, others can read)
├─ RolePermission (custom roles)
└─ HasPermission (dynamic permission checking)

Usage:
    @api_view(['POST'])
    @permission_classes([IsAuthenticated, HasPermission])
    def create_stock(request):
        # User must be authenticated and have 'can_manage_stocks' permission
        pass

    @require_permission('can_view_analytics')
    def view_analytics(request):
        # Function-level permission check
        pass
```

---

## API Endpoint Reference

### Authentication Endpoints

```
POST /api/auth/register/
  Register new user
  
  Request:
  {
    "email": "user@example.com",
    "username": "username",
    "password": "password123",
    "password2": "password123"
  }
  
  Response: 201
  {
    "success": true,
    "message": "User registered successfully.",
    "data": {
      "email": "user@example.com",
      "username": "username"
    }
  }

---

POST /api/auth/login/
  Obtain JWT tokens
  
  Request:
  {
    "username": "user@example.com",
    "password": "password123"
  }
  
  Response: 200
  {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }

---

POST /api/auth/refresh/
  Get new access token using refresh token
  
  Request:
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
  
  Response: 200
  {
    "success": true,
    "access": "new_access_token"
  }

---

POST /api/auth/logout/
  Invalidate current session (blacklist tokens)
  
  Headers:
  Authorization: Bearer <access_token>
  
  Request:
  {
    "refresh": "refresh_token_string"
  }
  
  Response: 200
  {
    "success": true,
    "message": "Logout successful."
  }

---

GET /api/auth/profile/
  Get user profile
  
  Headers:
  Authorization: Bearer <access_token>
  
  Response: 200
  {
    "success": true,
    "data": {
      "id": "uuid",
      "username": "username",
      "email": "user@example.com",
      "telegram_verified": false,
      "preferred_alert_threshold": 70,
      ...
    }
  }

---

PATCH /api/auth/profile/
  Update user profile
  
  Headers:
  Authorization: Bearer <access_token>
  
  Request:
  {
    "preferred_alert_threshold": 80,
    "is_telegram_alerts_enabled": true
  }
  
  Response: 200
  {
    "success": true,
    "message": "Profile updated successfully.",
    "data": { ... }
  }

---

POST /api/auth/change-password/
  Change user password
  
  Headers:
  Authorization: Bearer <access_token>
  
  Request:
  {
    "old_password": "old_password",
    "new_password": "new_password",
    "new_password2": "new_password"
  }
  
  Response: 200
  {
    "success": true,
    "message": "Password changed successfully."
  }
```

---

## Usage Examples

### Example 1: Create a Stock Service

```python
from core.services import BaseService, service_transaction, service_cache
from stocks.models import Stock

class StockService(BaseService):
    model = Stock
    
    @classmethod
    @service_cache(timeout=3600)
    def get_active_stocks(cls):
        """Get all active stocks (cached for 1 hour)."""
        return cls.get_all({'is_active': True})
    
    @classmethod
    @service_transaction
    def update_stock_prices(cls, price_updates):
        """Atomically update multiple stock prices."""
        for stock_id, price in price_updates.items():
            cls.update(stock_id, price=price)
    
    @classmethod
    def get_trending_stocks(cls, limit=10):
        """Get top trending stocks by change percentage."""
        stocks = cls.get_all({'is_active': True})
        return sorted(stocks, key=lambda s: s.change_percent, reverse=True)[:limit]


# Usage
StockService.update_stock_prices({
    'stock1_id': 100.50,
    'stock2_id': 205.75,
})

trending = StockService.get_trending_stocks(limit=5)
```

### Example 2: Permission-Protected Endpoint

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from core.permissions import IsAdmin, require_permission
from stocks.models import Stock
from stocks.serializers import StockSerializer

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    
    @action(detail=False, methods=['post'], 
            permission_classes=[IsAuthenticated, require_permission('can_manage_stocks')])
    def bulk_update(self, request):
        """Endpoint requiring specific permission."""
        # Only users with 'can_manage_stocks' permission can access
        pass
```

### Example 3: Using Token Manager

```python
from config.auth import TokenManager, get_user_from_token

# Decode and validate token
try:
    claims = TokenManager.decode_access_token(token)
    user_id = claims['user_id']
except TokenError:
    # Token is invalid or expired

# Get user from token
user = get_user_from_token(token)

# Refresh access token
new_access = TokenManager.refresh_access_token(refresh_token)

# Blacklist a token (logout)
TokenManager.blacklist_token(refresh_token)
```

---

## Database State Management

### Service Layer Transaction Example

```python
from core.services import BaseService, service_transaction
from django.db import transaction

class UserService(BaseService):
    model = User
    
    @service_transaction
    def create_user_with_profile(self, user_data, profile_data):
        """
        Create user and profile atomically.
        If profile creation fails, user creation is rolled back.
        """
        user = self.create(**user_data)
        profile = UserProfile.objects.create(user=user, **profile_data)
        return user, profile
```

---

## Testing Phase 2 Features

### 1. Test JWT Token Management

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Response contains access and refresh tokens
TOKEN_ACCESS="eyJ0eXAi..."
TOKEN_REFRESH="eyJ0eXAi..."

# Test protected endpoint
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer $TOKEN_ACCESS"

# Refresh token
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$TOKEN_REFRESH\"}"

# Logout (blacklist token)
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer $TOKEN_ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\": \"$TOKEN_REFRESH\"}"

# Try using blacklisted token (should fail)
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer $TOKEN_ACCESS"
  # Response: 401 Unauthorized - "Token has been invalidated"
```

### 2. Test Service Layer

```python
# In Django shell
python manage.py shell

>>> from stocks.services import StockService
>>> from stocks.models import Stock
>>> 
>>> # Get all active stocks
>>> stocks = StockService.get_active_stocks()
>>> print(f"Found {len(stocks)} active stocks")
>>>
>>> # Update a stock
>>> stock = StockService.get_by_id('stock_id')
>>> updated = StockService.update('stock_id', price=100.50)
>>>
>>> # Create new stock
>>> new_stock = StockService.create(symbol='TEST', name='Test Stock', price=100)
```

### 3. Test Permissions

```python
>>> from core.permissions import user_has_permission
>>> from django.contrib.auth import get_user_model
>>>
>>> User = get_user_model()
>>> user = User.objects.first()
>>>
>>> # Check if user has permission
>>> has_perm = user_has_permission(user, 'stocks.can_manage_stocks')
>>> print(has_perm)
False
>>>
>>> # Grant permission
>>> from django.contrib.auth.models import Permission
>>> perm = Permission.objects.get(codename='can_manage_stocks')
>>> user.user_permissions.add(perm)
>>> user_has_permission(user, 'stocks.can_manage_stocks')
True
```

---

## Production Readiness

✅ JWT authentication with token blacklisting  
✅ Service layer pattern for business logic  
✅ Role-based access control system  
✅ Comprehensive permission system  
✅ Error handling and logging  
✅ Transaction management  
✅ Caching support  
✅ Backwards compatible with existing API  

⚠️ Next: Signal Engine Refactor, Notifications (Phase 3)

---

## Files Modified/Created

### New Files
- `nepse_backend/config/auth.py` - Enhanced JWT authentication
- `nepse_backend/core/services.py` - Service layer pattern
- `nepse_backend/core/permissions.py` - Permission and RBAC system

### Modified Files
- `nepse_backend/accounts/views.py` - Added logout and refresh endpoints
- `nepse_backend/accounts/urls.py` - Updated URL patterns
- `nepse_backend/config/settings/base.py` - Updated authentication class
- `nepse_backend/requirements.txt` - Added PyJWT

---

## Backwards Compatibility

✅ All existing API endpoints remain unchanged  
✅ Existing authentication still works (with enhancements)  
✅ Existing models and views fully compatible  
✅ New features are additive, not breaking  
⚠️ Token blacklisting requires Redis (already in docker-compose)
