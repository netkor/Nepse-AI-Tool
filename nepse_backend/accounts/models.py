"""
Models for the Accounts app.
Handles user authentication and profile management.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator


class CustomUser(AbstractUser):
    """
    Extended User model with additional fields for NEPSE AI system.
    """
    email = models.EmailField(unique=True)
    telegram_chat_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Telegram chat ID for receiving alerts"
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Telegram username for reference"
    )
    telegram_verified = models.BooleanField(
        default=False,
        help_text="Whether Telegram chat ID has been verified"
    )
    preferred_alert_threshold = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum confidence score (%) for alerts"
    )
    is_email_alerts_enabled = models.BooleanField(
        default=True,
        help_text="Whether email alerts are enabled"
    )
    is_telegram_alerts_enabled = models.BooleanField(
        default=False,
        help_text="Whether Telegram alerts are enabled"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email
