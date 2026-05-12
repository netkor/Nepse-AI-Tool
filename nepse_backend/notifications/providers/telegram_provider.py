import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramProvider:
    """Simple Telegram notification provider using Bot API."""

    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.base_url = f'https://api.telegram.org/bot{self.bot_token}' if self.bot_token else None

    def is_enabled(self) -> bool:
        return bool(self.bot_token)

    def send(self, chat_id: str, text: str, parse_mode: str = 'HTML') -> dict:
        if not self.is_enabled():
            raise RuntimeError('Telegram bot token not configured')
        url = f'{self.base_url}/sendMessage'
        payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        resp = requests.post(url, json=payload, timeout=10)
        try:
            resp.raise_for_status()
            data = resp.json()
            if not data.get('ok'):
                raise RuntimeError(f'Telegram API error: {data}')
            return data
        except Exception as e:
            logger.exception('Telegram send failed')
            raise
