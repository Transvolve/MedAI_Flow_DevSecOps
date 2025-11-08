"""Rate limiting middleware implementation using slowapi with Redis backend."""
from typing import Optional
from slowapi import Limiter
from redis import Redis
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class RedisLimiter(Limiter):
    """Extended Limiter with Redis backend support."""

    def __init__(
        self,
        key_func,
        redis_url: str,
        default_limits: Optional[list[str]] = None,
        strategy: Optional[str] = None,
        headers_enabled: bool = True,
        redis_prefix: str = "slowapi",
        redis_pool_size: int = 10,
        redis_timeout: int = 5
    ):
        """Initialize Redis-backed rate limiter.

        Args:
            key_func: Function to extract key from request
            redis_url: Redis connection URL (redis://host:port)
            default_limits: List of default rate limits
            strategy: Rate limiting strategy (fixed-window/moving-window)
            headers_enabled: Whether to send rate limit headers
            redis_prefix: Prefix for Redis keys
            redis_pool_size: Redis connection pool size
            redis_timeout: Redis operation timeout in seconds
        """
        super().__init__(
            key_func=key_func,
            default_limits=default_limits,
            strategy=strategy,
            headers_enabled=headers_enabled
        )

        try:
            self.redis = Redis.from_url(
                redis_url,
                decode_responses=True,
                max_connections=redis_pool_size,
                socket_timeout=redis_timeout
            )
            self.redis_prefix = redis_prefix
            logger.info(f"Redis rate limiter initialized with URL: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {str(e)}")
            raise

    def get_redis_key(self, key: str) -> str:
        """Generate Redis key with prefix."""
        return f"{self.redis_prefix}:{key}"

    def hit(self, key: str, limit: int, period: timedelta) -> tuple[bool, int]:
        """Record a hit and check the limit.

        Args:
            key: Rate limit key
            limit: Maximum number of requests
            period: Time period for the limit

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        redis_key = self.get_redis_key(key)
        pipe = self.redis.pipeline()

        try:
            # Increment counter and set expiry
            pipe.incr(redis_key)
            pipe.expire(redis_key, int(period.total_seconds()))
            current = pipe.execute()[0]

            # Check if limit exceeded
            is_allowed = current <= limit
            remaining = max(0, limit - current)

            return is_allowed, remaining
        except Exception as e:
            logger.error(f"Redis operation failed: {str(e)}")
            # Fail open if Redis is down
            return True, limit

