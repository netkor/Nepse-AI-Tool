"""
Admin configuration for Accounts app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('NEPSE Settings', {
            'fields': (
                'telegram_chat_id',
                'telegram_username',
                'telegram_verified',
                'preferred_alert_threshold',
                'is_email_alerts_enabled',
                'is_telegram_alerts_enabled',
            )
        }),
    )
    list_display = ('email', 'username', 'is_staff', 'is_telegram_alerts_enabled', 'created_at')
    list_filter = ('is_staff', 'is_telegram_alerts_enabled', 'is_email_alerts_enabled', 'created_at')
