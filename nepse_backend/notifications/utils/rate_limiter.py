from django.core.cache import cache
import time


class RedisRateLimiter:
    """Simple token-bucket style limiter using Django cache (Redis).

    allow(key, limit=5, period_seconds=60) -> bool
    """

    def allow(self, key: str, limit: int = 5, period_seconds: int = 60) -> bool:
        now = int(time.time())
        window = now // period_seconds
        cache_key = f"rl:{key}:{window}"
        current = cache.get(cache_key) or 0
        if current >= limit:
            return False
        cache.incr(cache_key, 1)
        # ensure key expires after period
        cache.add(cache_key, current + 1, timeout=period_seconds)
        return True
