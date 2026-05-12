Notifications app

Contains providers (Telegram, Email), a service layer, Celery tasks, templates and a small Redis-backed rate limiter.

Usage examples:

from notifications.services import NotificationService
ns = NotificationService()
ns.send_telegram(user_chat_id, 'signal_basic', {'signal_type':'RSI','direction':'BUY','price':123.4,'strength':0.8})

