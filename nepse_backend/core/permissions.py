"""
Permission and role-based access control system for NEPSE AI.

Provides:
- Permission classes for DRF
- Role-based access control utilities
- User permission checking
- Permission decorators

Usage:
    from core.permissions import IsOwner, HasPermission, require_permission
    
    class MyViewSet(viewsets.ModelViewSet):
        permission_classes = [IsAuthenticated, IsOwner]
    
    @require_permission('can_manage_stocks')
    def manage_stocks(request):
        pass
"""

import logging
from typing import List, Optional
from functools import wraps
from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

User = get_user_model()


# ============================================================
# Base Permission Classes
# ============================================================

class IsOwnerOrReadOnly(BasePermission):
    """
    Allows write access only to the owner of an object.
    Read access is allowed to any user.
    """
    
    def has_object_permission(self, request, view, obj):
        """Allow any read method, write only if owner."""
        # Read permissions for any request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # Write permission only for owner
        return hasattr(obj, 'user') and obj.user == request.user


class IsOwner(BasePermission):
    """
    Allows access only to the owner of an object.
    """
    
    def has_object_permission(self, request, view, obj):
        """Allow access only if user is the owner."""
        return hasattr(obj, 'user') and obj.user == request.user


class IsAdmin(BasePermission):
    """Allows access only to admin users."""
    
    def has_permission(self, request, view):
        """Check if user is staff/admin."""
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )


class IsSuperUser(BasePermission):
    """Allows access only to superusers."""
    
    def has_permission(self, request, view):
        """Check if user is superuser."""
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )


class IsOwnerAndVerified(BasePermission):
    """
    Allows access only if:
    1. User is the owner of the object
    2. User is verified (has verified email/phone)
    """
    
    def has_object_permission(self, request, view, obj):
        """Check ownership and verification status."""
        if not (hasattr(obj, 'user') and obj.user == request.user):
            return False
        
        # Check if user is verified (customize based on your model)
        if hasattr(request.user, 'email_verified'):
            return request.user.email_verified
        
        return True


# ============================================================
# Role-Based Access Control (RBAC)
# ============================================================

class RolePermission(BasePermission):
    """
    Base class for role-based permissions.
    
    Subclasses should define required_roles attribute.
    
    Usage:
        class IsAnalyst(RolePermission):
            required_roles = ['analyst', 'admin']
    """
    
    required_roles: List[str] = []
    
    def has_permission(self, request, view):
        """Check if user has required role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
        
        # Check if user has required role
        user_roles = self._get_user_roles(request.user)
        return any(role in self.required_roles for role in user_roles)
    
    def _get_user_roles(self, user) -> List[str]:
        """Get user roles. Override for custom role logic."""
        roles = []
        
        if user.is_staff:
            roles.append('staff')
        if user.is_superuser:
            roles.append('admin')
        
        # Check for custom role field
        if hasattr(user, 'role'):
            roles.append(user.role)
        
        return roles


class HasPermission(BasePermission):
    """
    Check if user has specific permission.
    
    Usage:
        class StockViewSet(viewsets.ModelViewSet):
            permission_classes = [HasPermission]
            permission_name = 'can_manage_stocks'
    """
    
    def has_permission(self, request, view):
        """Check permission."""
        # Get permission name from view
        permission_name = getattr(view, 'permission_name', None)
        
        if not permission_name:
            logger.warning("HasPermission used without permission_name on view")
            return False
        
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check Django permission
        return request.user.has_perm(permission_name)


# ============================================================
# Permission Utilities
# ============================================================

def get_user_permissions(user) -> List[str]:
    """
    Get all permissions for a user.
    
    Args:
        user: User instance
    
    Returns:
        List of permission codenames
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.is_superuser:
        # Return all permissions
        from django.contrib.auth.models import Permission
        return list(Permission.objects.values_list('codename', flat=True))
    
    # Get user permissions
    return list(
        user.user_permissions.values_list('codename', flat=True)
    ) + list(
        Permission.objects.filter(
            group__user=user
        ).values_list('codename', flat=True).distinct()
    )


def user_has_permission(user, permission: str) -> bool:
    """
    Check if user has specific permission.
    
    Args:
        user: User instance
        permission: Permission codename (e.g., 'can_manage_stocks')
    
    Returns:
        bool: True if user has permission
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return user.has_perm(permission)


def user_has_any_permission(user, permissions: List[str]) -> bool:
    """
    Check if user has any of the specified permissions.
    
    Args:
        user: User instance
        permissions: List of permission codenames
    
    Returns:
        bool: True if user has any permission
    """
    return any(user_has_permission(user, perm) for perm in permissions)


def user_has_all_permissions(user, permissions: List[str]) -> bool:
    """
    Check if user has all specified permissions.
    
    Args:
        user: User instance
        permissions: List of permission codenames
    
    Returns:
        bool: True if user has all permissions
    """
    return all(user_has_permission(user, perm) for perm in permissions)


# ============================================================
# Permission Decorators
# ============================================================

def require_permission(permission: str):
    """
    Decorator to check user permission.
    
    Usage:
        @require_permission('can_manage_stocks')
        def manage_stocks(request):
            pass
    
    Raises:
        PermissionDenied: If user lacks permission
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not user_has_permission(request.user, permission):
                logger.warning(
                    f"Permission denied for {request.user}: {permission}"
                )
                raise PermissionDenied(
                    f"User lacks required permission: {permission}"
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions):
    """
    Decorator to check if user has any of the specified permissions.
    
    Usage:
        @require_any_permission('can_read_stocks', 'can_manage_stocks')
        def view_stocks(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not user_has_any_permission(request.user, permissions):
                logger.warning(
                    f"Permission denied for {request.user}: {permissions}"
                )
                raise PermissionDenied("User lacks required permissions")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_authenticated():
    """
    Decorator to require authenticated user.
    
    Usage:
        @require_authenticated()
        def protected_view(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_admin():
    """Decorator to require admin/staff user."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not (request.user and request.user.is_staff):
                logger.warning(f"Admin access denied for {request.user}")
                raise PermissionDenied("Admin access required")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
