"""
Celery tasks for the Signals app.
Replaces APScheduler-based signal generation with distributed task processing.
"""
import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)

LOCK_EXPIRE = 60 * 14  # 14 minutes
LOCK_ID = 'generate_signals_lock'
SIGNAL_GENERATION_LOCK = 'generate_signals_lock'
SIGNAL_AGGREGATION_LOCK = 'aggregate_signals_lock'


@shared_task(bind=True, acks_late=True, max_retries=1)
def generate_signals(self):
    """
    Generate trading signals for all active stocks using modular signal engines.
    
    This task:
    1. Loads historical data for all active stocks
    2. Generates signals from all available engines (RSI, MACD, Breakout, Volume Spike)
    3. Persists signals to database
    4. Queues notifications for users
    
    Returns dict with statistics about generated signals.
    Uses Redis lock to prevent concurrent execution.
    """
    # Solo execution guard: prevent concurrent task runs
    acquired = cache.add(SIGNAL_GENERATION_LOCK, 'locked', LOCK_EXPIRE)
    if not acquired:
        logger.warning("generate_signals: skipped (already running)")
        return {'signals_created': 0, 'stocks_processed': 0, 'skipped': True}

    try:
        from signals.services import SignalService
        from stocks.models import Stock
        from stocks.data_provider import StockDataProvider

        signals_created = 0
        stocks_processed = 0
        stocks_failed = 0
        
        # Get all active stocks
        stocks = Stock.objects.filter(is_active=True)
        data_provider = StockDataProvider()
        
        for stock in stocks:
            try:
                stocks_processed += 1
                
                # Get historical data (last 100 candles for all engines)
                historical_data = data_provider.get_historical_data(
                    symbol=stock.symbol,
                    limit=100
                )
                
                if not historical_data:
                    logger.warning(f"No data available for {stock.symbol}")
                    continue
                
                # Generate signals from all engines
                signals = SignalService.generate_all_signals(
                    stock=stock,
                    historical_data=historical_data
                )
                
                signals_created += len(signals)
                
                # Queue notifications for generated signals
                for signal in signals:
                    queue_signal_notifications.delay(
                        signal_id=str(signal.signal_id)
                    )
                
            except Exception as e:
                logger.error(
                    f"Error generating signals for {stock.symbol}: {str(e)}",
                    exc_info=True
                )
                stocks_failed += 1
        
        logger.info(
            f"generate_signals completed: created={signals_created}, "
            f"processed={stocks_processed}, failed={stocks_failed}"
        )
        
        return {
            'signals_created': signals_created,
            'stocks_processed': stocks_processed,
            'stocks_failed': stocks_failed,
        }

    except Exception as e:
        logger.error(f"Critical error in generate_signals: {str(e)}", exc_info=True)
        return {'signals_created': 0, 'stocks_processed': 0, 'error': str(e)}
        
    finally:
        cache.delete(SIGNAL_GENERATION_LOCK)


@shared_task(bind=True, acks_late=True, max_retries=2)
def queue_signal_notifications(self, signal_id: str):
    """
    Queue notifications for a generated signal.
    
    Args:
        signal_id: UUID of the signal
    
    Sends notifications to users based on alert subscriptions.
    """
    try:
        from signals.models import SignalHistory
        from alerts.models import Alert
        from django.contrib.auth import get_user_model
        from config.telegram_service import TelegramService
        
        User = get_user_model()
        
        try:
            signal = SignalHistory.objects.get(signal_id=signal_id)
        except SignalHistory.DoesNotExist:
            logger.warning(f"Signal not found: {signal_id}")
            return {'notified': 0, 'failed': 0}
        
        # Find matching alerts for this signal
        matching_alerts = Alert.objects.filter(
            stock=signal.stock,
            is_active=True,
            min_strength__lte=signal.strength
        )
        
        if not matching_alerts:
            logger.debug(f"No matching alerts for signal {signal_id}")
            return {'notified': 0, 'failed': 0}
        
        # Get users to notify
        user_ids = set()
        for alert in matching_alerts:
            user_ids.add(str(alert.user.id))
        
        notified = 0
        failed = 0
        
        # Send Telegram notifications if enabled
        if TelegramService.is_enabled():
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    if user.telegram_verified and user.telegram_chat_id:
                        success = TelegramService.send_signal_alert(
                            chat_id=user.telegram_chat_id,
                            signal_type=signal.signal_type,
                            stock_symbol=signal.stock.symbol,
                            stock_price=float(signal.price),
                            direction=signal.direction,
                            strength=signal.strength,
                            message=signal.message
                        )
                        if success:
                            notified += 1
                        else:
                            failed += 1
                except Exception as e:
                    logger.error(f"Error notifying user {user_id}: {str(e)}")
                    failed += 1
        
        # Record which users were notified
        if notified > 0:
            signal.mark_notified(list(user_ids))
        
        logger.info(
            f"Signal {signal_id} notifications: "
            f"notified={notified}, failed={failed}"
        )
        
        return {'notified': notified, 'failed': failed}
        
    except Exception as e:
        logger.error(f"Error in queue_signal_notifications: {str(e)}", exc_info=True)
        raise


@shared_task(bind=True, max_retries=2)
def aggregate_signal_performance(self):
    """
    Aggregate signal performance statistics.
    
    Calculates daily performance metrics for all signal types.
    Runs daily via Celery Beat.
    """
    # Solo execution guard
    acquired = cache.add(SIGNAL_AGGREGATION_LOCK, 'locked', 3600)
    if not acquired:
        logger.warning("aggregate_signal_performance: skipped (already running)")
        return {'status': 'skipped'}
    
    try:
        from signals.services import SignalPerformanceService
        
        SignalPerformanceService.aggregate_daily_performance()
        
        logger.info("Signal performance aggregation completed")
        return {'status': 'completed'}
        
    except Exception as e:
        logger.error(f"Error aggregating signal performance: {str(e)}", exc_info=True)
        raise
        
    finally:
        cache.delete(SIGNAL_AGGREGATION_LOCK)


@shared_task(bind=True, max_retries=1)
def cleanup_old_signals(self, days: int = 90):
    """
    Clean up (soft-delete) old signals for storage optimization.
    
    Args:
        days: Delete signals older than this many days
    
    Runs weekly via Celery Beat.
    """
    try:
        from signals.services import SignalService
        
        count = SignalService.soft_delete_signals_before(days=days)
        
        logger.info(f"Cleaned up {count} signals older than {days} days")
        return {'deleted': count}
        
    except Exception as e:
        logger.error(f"Error cleaning up old signals: {str(e)}", exc_info=True)
        raise
