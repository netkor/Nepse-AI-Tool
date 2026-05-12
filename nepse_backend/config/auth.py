"""
Enhanced JWT authentication system for NEPSE AI Signal & Alert System.

Provides:
- JWT token generation with custom claims
- Token refresh mechanism
- Token blacklisting/invalidation
- User authentication utilities
- Token validation helpers

Usage:
    from config.auth import get_tokens_for_user, create_access_token, TokenManager
    
    # Get both access and refresh tokens
    tokens = get_tokens_for_user(user)
    
    # Validate and get claims
    claims = TokenManager.decode_access_token(token)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

import jwt
from django.conf import settings
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


# ============================================================
# Token Manager Class
# ============================================================

class TokenManager:
    """
    Centralized token management.
    
    Handles:
    - Token creation with custom claims
    - Token validation
    - Token refresh
    - Token invalidation (blacklisting)
    """
    
    TOKEN_CACHE_PREFIX = 'blacklisted_token:'
    TOKEN_CACHE_TIMEOUT = 7 * 24 * 3600  # 7 days (same as refresh token lifetime)
    
    @staticmethod
    def create_access_token(user, extra_claims: Optional[Dict] = None) -> str:
        """
        Create a JWT access token with custom claims.
        
        Args:
            user: User instance
            extra_claims: Dict of additional JWT claims
        
        Returns:
            str: JWT token string
        """
        try:
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            # Add custom claims
            access['user_id'] = str(user.id)
            access['email'] = user.email
            access['username'] = user.username
            access['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Add extra claims if provided
            if extra_claims:
                access.update(extra_claims)
            
            logger.debug(f"Created access token for user {user.username}")
            return str(access)
        
        except Exception as e:
            logger.error(f"Failed to create access token for {user.username}: {e}")
            raise
    
    @staticmethod
    def create_refresh_token(user) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user: User instance
        
        Returns:
            str: JWT refresh token string
        """
        try:
            refresh = RefreshToken.for_user(user)
            logger.debug(f"Created refresh token for user {user.username}")
            return str(refresh)
        except Exception as e:
            logger.error(f"Failed to create refresh token for {user.username}: {e}")
            raise
    
    @staticmethod
    def decode_access_token(token: str) -> Dict:
        """
        Decode and validate an access token.
        
        Args:
            token: JWT token string
        
        Returns:
            dict: Token claims/payload
        
        Raises:
            TokenError: If token is invalid or expired
        """
        try:
            # Check if token is blacklisted
            if TokenManager.is_token_blacklisted(token):
                raise TokenError("Token has been invalidated")
            
            # Decode token
            decoded = jwt.decode(
                token,
                settings.SIMPLE_JWT['SIGNING_KEY'],
                algorithms=[settings.SIMPLE_JWT['ALGORITHM']],
            )
            
            logger.debug(f"Successfully decoded token for user {decoded.get('username')}")
            return decoded
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise TokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise TokenError(f"Invalid token: {e}")
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Create a new access token from a refresh token.
        
        Args:
            refresh_token: JWT refresh token string
        
        Returns:
            str: New access token
        
        Raises:
            TokenError: If refresh token is invalid
        """
        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token
            logger.debug(f"Refreshed access token")
            return str(access)
        except TokenError as e:
            logger.warning(f"Failed to refresh token: {e}")
            raise
    
    @staticmethod
    def blacklist_token(token: str, timeout: Optional[int] = None) -> bool:
        """
        Blacklist/invalidate a token.
        
        Args:
            token: JWT token string to blacklist
            timeout: Cache timeout in seconds (default: TOKEN_CACHE_TIMEOUT)
        
        Returns:
            bool: True if successfully blacklisted
        """
        try:
            if timeout is None:
                timeout = TokenManager.TOKEN_CACHE_TIMEOUT
            
            cache_key = f"{TokenManager.TOKEN_CACHE_PREFIX}{token}"
            cache.set(cache_key, True, timeout)
            
            logger.info(f"Token blacklisted for {timeout}s")
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: JWT token string
        
        Returns:
            bool: True if blacklisted, False otherwise
        """
        cache_key = f"{TokenManager.TOKEN_CACHE_PREFIX}{token}"
        return cache.get(cache_key, False)


# ============================================================
# Utility Functions
# ============================================================

def get_tokens_for_user(user) -> Dict[str, str]:
    """
    Get both access and refresh tokens for a user.
    
    Args:
        user: User instance
    
    Returns:
        dict: {'access': token, 'refresh': token}
    """
    return {
        'access': TokenManager.create_access_token(user),
        'refresh': TokenManager.create_refresh_token(user),
    }


def get_user_from_token(token: str) -> Optional[User]:
    """
    Extract user from token.
    
    Args:
        token: JWT token string
    
    Returns:
        User: User instance or None
    
    Raises:
        TokenError: If token is invalid
    """
    try:
        claims = TokenManager.decode_access_token(token)
        user_id = claims.get('user_id')
        
        if not user_id:
            return None
        
        user = User.objects.get(id=user_id)
        return user
    except (TokenError, User.DoesNotExist) as e:
        logger.warning(f"Failed to get user from token: {e}")
        return None


def verify_token_signature(token: str) -> bool:
    """
    Verify that a token has a valid signature.
    
    Args:
        token: JWT token string
    
    Returns:
        bool: True if signature is valid
    """
    try:
        jwt.decode(
            token,
            settings.SIMPLE_JWT['SIGNING_KEY'],
            algorithms=[settings.SIMPLE_JWT['ALGORITHM']],
        )
        return True
    except jwt.InvalidSignatureError:
        logger.warning("Invalid token signature")
        return False
    except Exception:
        return False


# ============================================================
# Custom JWT Authentication Class
# ============================================================

class EnhancedJWTAuthentication(JWTAuthentication):
    """
    Enhanced JWT authentication that supports token blacklisting.
    
    Extends the default SimpleJWT authentication to check if tokens
    have been blacklisted (invalidated).
    """
    
    def authenticate(self, request):
        """
        Authenticate request using JWT token.
        
        Checks:
        1. Token is present in Authorization header
        2. Token signature is valid
        3. Token is not expired
        4. Token is not blacklisted
        """
        result = super().authenticate(request)
        
        if result is None:
            return None
        
        validated_token, authenticated_user = result
        
        # Check if token is blacklisted
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            if TokenManager.is_token_blacklisted(token):
                logger.warning(f"Attempted use of blacklisted token by {authenticated_user}")
                raise AuthenticationFailed("Token has been invalidated")
        
        return validated_token, authenticated_user
