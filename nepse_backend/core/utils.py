"""
Core utilities for NEPSE AI Signal & Alert System.

Provides:
- Pagination classes
- Filter backends
- Serializer mixins
- View mixins
- Permission classes
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.serializers import ModelSerializer
from django_filters.rest_framework import DjangoFilterBackend


# ============================================================
# Pagination
# ============================================================

class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list views (20 items per page)."""
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_size_query_description = 'Number of results to return per page.'


class LargeResultsSetPagination(PageNumberPagination):
    """Large pagination for analytics views (100 items per page)."""
    
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500
    page_size_query_description = 'Number of results to return per page.'


class SmallResultsSetPagination(PageNumberPagination):
    """Small pagination for mobile/compact views (10 items per page)."""
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_size_query_description = 'Number of results to return per page.'


# ============================================================
# Permissions
# ============================================================

class IsOwner(BasePermission):
    """
    Allow access only if the requesting user is the owner of the object.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the owner."""
        return obj.user == request.user


class IsOwnerOrReadOnly(BasePermission):
    """
    Allow access if the requesting user is the owner.
    Read-only access is allowed to any request.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is owner or only reading."""
        # Read permissions are allowed to any request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


# ============================================================
# Serializer Mixins
# ============================================================

class TimestampedSerializerMixin:
    """
    Mixin that adds created_at and updated_at read-only fields
    to serializers.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add created_at and updated_at fields if model has them
        if hasattr(self.Meta, 'model'):
            model = self.Meta.model
            if hasattr(model, '_meta'):
                field_names = [f.name for f in model._meta.get_fields()]
                if 'created_at' in field_names and 'created_at' not in self.fields:
                    from rest_framework.fields import DateTimeField
                    self.fields['created_at'] = DateTimeField(read_only=True)
                if 'updated_at' in field_names and 'updated_at' not in self.fields:
                    from rest_framework.fields import DateTimeField
                    self.fields['updated_at'] = DateTimeField(read_only=True)


# ============================================================
# View Mixins
# ============================================================

class ListCreateMixin:
    """
    Mixin for views that support both listing and creating.
    
    Usage:
        class MyViewSet(ListCreateMixin, viewsets.GenericViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
    """
    
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


# ============================================================
# Queryset Utilities
# ============================================================

def get_user_or_404(user_id):
    """
    Get user by ID or raise Http404.
    
    Args:
        user_id: User ID
    
    Returns:
        User: The user object
    
    Raises:
        Http404: If user doesn't exist
    """
    from django.shortcuts import get_object_or_404
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    return get_object_or_404(User, id=user_id)


def filter_active_objects(queryset):
    """
    Filter queryset to include only active objects.
    
    Args:
        queryset: Django QuerySet
    
    Returns:
        QuerySet: Filtered queryset with only active objects
    """
    if hasattr(queryset.model, 'is_active'):
        return queryset.filter(is_active=True)
    return queryset


# ============================================================
# Validation Utilities
# ============================================================

def validate_email(email):
    """
    Validate email format.
    
    Args:
        email (str): Email to validate
    
    Returns:
        bool: True if valid
    
    Raises:
        ValidationError: If invalid
    """
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email as django_validate_email
    
    try:
        django_validate_email(email)
        return True
    except ValidationError:
        raise ValidationError(f"Invalid email format: {email}")


def validate_phone(phone):
    """
    Validate phone number format.
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        bool: True if valid
    
    Raises:
        ValidationError: If invalid
    """
    import re
    from django.core.exceptions import ValidationError
    
    # Simple validation: allows +, digits, spaces, and hyphens
    if not re.match(r'^\+?[\d\s\-]{8,}$', phone):
        raise ValidationError(f"Invalid phone format: {phone}")
    return True
