"""
Telegram integration service for sending alerts to users.
"""
import requests
import logging
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """
    Service for sending Telegram notifications.
    """
    
    BASE_URL = settings.TELEGRAM_API_URL
    BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN

    @classmethod
    def is_enabled(cls) -> bool:
        """
        Check if Telegram is properly configured.
        """
        return bool(cls.BOT_TOKEN and cls.BOT_TOKEN.strip())

    @classmethod
    def send_message(
        cls,
        chat_id: str,
        message: str,
        parse_mode: str = 'HTML'
    ) -> bool:
        """
        Send a message to a Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            message: Message text
            parse_mode: 'HTML' or 'Markdown'
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not cls.is_enabled():
            logger.warning('Telegram not configured')
            return False
        
        try:
            url = f"{cls.BASE_URL}{cls.BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode,
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram request failed: {str(e)}")
            return False

    @classmethod
    def send_signal_alert(
        cls,
        chat_id: str,
        signal_type: str,
        stock_symbol: str,
        stock_price: float,
        reason: str,
        confidence: int
    ) -> bool:
        """
        Send a formatted signal alert.
        
        Args:
            chat_id: Telegram chat ID
            signal_type: 'BUY', 'SELL', or 'ALERT'
            stock_symbol: Stock symbol
            stock_price: Current stock price
            reason: Signal reason
            confidence: Confidence percentage (0-100)
        
        Returns:
            True if sent successfully
        """
        emoji = '🟢' if signal_type == 'BUY' else '🔴' if signal_type == 'SELL' else '🔵'
        
        message = (
            f"{emoji} <b>{signal_type} SIGNAL</b>\n"
            f"<b>Stock:</b> {stock_symbol}\n"
            f"<b>Price:</b> Rs {stock_price:,.2f}\n"
            f"<b>Confidence:</b> {confidence}%\n\n"
            f"<b>Reason:</b>\n{reason}"
        )
        
        return cls.send_message(chat_id, message, parse_mode='HTML')

    @classmethod
    def send_price_alert(
        cls,
        chat_id: str,
        stock_symbol: str,
        stock_price: float,
        alert_type: str,  # 'min' or 'max'
        threshold_price: float
    ) -> bool:
        """
        Send a price alert notification.
        
        Args:
            chat_id: Telegram chat ID
            stock_symbol: Stock symbol
            stock_price: Current stock price
            alert_type: 'min' or 'max'
            threshold_price: The threshold that was triggered
        
        Returns:
            True if sent successfully
        """
        emoji = '📉' if alert_type == 'min' else '📈'
        alert_text = 'dropped to' if alert_type == 'min' else 'rose to'
        
        message = (
            f"{emoji} <b>PRICE ALERT</b>\n"
            f"<b>Stock:</b> {stock_symbol}\n"
            f"<b>Current Price:</b> Rs {stock_price:,.2f}\n"
            f"<b>Alert Type:</b> {alert_text.capitalize()}\n"
            f"<b>Threshold:</b> Rs {threshold_price:,.2f}"
        )
        
        return cls.send_message(chat_id, message, parse_mode='HTML')

    @classmethod
    def send_verification_code(cls, chat_id: str, code: str) -> bool:
        """
        Send a verification code to set up Telegram alerts.
        
        Args:
            chat_id: Telegram chat ID
            code: Verification code (usually the chat_id itself)
        
        Returns:
            True if sent successfully
        """
        message = (
            f"🔐 <b>NEPSE AI Alert System</b>\n\n"
            f"Your Chat ID is:\n<code>{code}</code>\n\n"
            f"Please use this code to enable Telegram alerts in your profile."
        )
        
        return cls.send_message(chat_id, message, parse_mode='HTML')

    @classmethod
    def test_connection(cls, chat_id: str) -> bool:
        """
        Test Telegram connection by sending a test message.
        """
        message = "✅ Telegram integration is working correctly!"
        return cls.send_message(chat_id, message)
