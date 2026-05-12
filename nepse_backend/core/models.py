"""
Core models for NEPSE AI Signal & Alert System.

Provides:
- BaseModel: Abstract base model with common fields
- SoftDelete: Mixin for soft-delete support
- TimestampedModel: Model with created_at/updated_at fields
- UUIDModel: Model using UUID as primary key
"""

import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all models.
    
    Provides:
    - id: UUID primary key
    - created_at: Timestamp when object was created
    - updated_at: Timestamp when object was last updated
    - is_active: Boolean flag for soft deletes
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when object was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when object was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this object is active (soft-delete support)"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def soft_delete(self):
        """Soft delete this object by marking is_active as False."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def restore(self):
        """Restore a soft-deleted object."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that respects soft-delete flag by default."""
    
    def active(self):
        """Return only active objects."""
        return self.filter(is_active=True)
    
    def inactive(self):
        """Return only inactive (deleted) objects."""
        return self.filter(is_active=False)
    
    def all_including_deleted(self):
        """Return all objects, including soft-deleted ones."""
        return self


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted objects by default."""
    
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(
            is_active=True
        )
    
    def all_including_deleted(self):
        """Get all objects including soft-deleted ones."""
        return SoftDeleteQuerySet(self.model, using=self._db).all()


class TimestampedModel(models.Model):
    """
    Abstract model with created_at and updated_at timestamps.
    
    Useful for models that don't need UUID or soft-delete functionality.
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when object was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when object was last updated"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class UUIDModel(models.Model):
    """
    Abstract model using UUID as primary key.
    
    Useful for microservices and distributed systems.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier"
    )
    
    class Meta:
        abstract = True
