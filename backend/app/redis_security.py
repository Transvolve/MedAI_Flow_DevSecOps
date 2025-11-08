"""Secure Redis connection management with SSL and authentication."""

import ssl
import logging
from typing import Optional, Dict, Any

import redis
from redis import Redis
from redis.connection import Connection, SSLConnection

from .config import settings

logger = logging.getLogger(__name__)

# Global singleton client instance (thread-safe for read access)
_redis_client: Optional[Redis] = None


class SecureRedisConnection:
    """Secure Redis connection manager with SSL and authentication."""

    def __init__(
        self,
        url: str,
        password: Optional[str] = None,
        ssl_enabled: bool = False,
        pool_size: int = 10,
        timeout: int = 5,
    ) -> None:
        self.url: str = url
        self.password: Optional[str] = password
        self.ssl_enabled: bool = ssl_enabled
        self.pool_size: int = pool_size
        self.timeout: int = timeout
        self.ssl_context: Optional[ssl.SSLContext] = None

        if self.ssl_enabled:
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            self.ssl_context = context

    def get_connection_params(self) -> Dict[str, Any]:
        """Prepare connection parameters for Redis.from_url()."""
        params: Dict[str, Any] = {
            "decode_responses": True,
            "max_connections": self.pool_size,
            "socket_timeout": self.timeout,
        }

        if self.password:
            params["password"] = self.password

        if self.ssl_enabled and self.ssl_context:
            params["connection_class"] = SSLConnection
            params["ssl_context"] = self.ssl_context
        else:
            params["connection_class"] = Connection

        return params

    def create_client(self) -> Redis:
        """Create and verify a secure Redis client instance."""
        try:
            client = Redis.from_url(self.url, **self.get_connection_params())
            if client is None or not client.ping():
                raise ConnectionError("Redis connection failed; connection not established.")
            logger.info(
                f"Established secure Redis connection to {self.url} "
                f"(SSL: {self.ssl_enabled}, Pool: {self.pool_size})"
            )
            return client
        except Exception as e:
            logger.error(f"Failed to establish Redis connection: {e}")
            raise


def get_secure_redis_client() -> Redis:
    """
    Return a secure Redis client instance (singleton pattern).
    Ensures initialization happens only once and can be mocked in tests.
    Falls back to fakeredis if real Redis is unavailable.
    """
    global _redis_client
    if _redis_client is None:
        try:
            connection = SecureRedisConnection(
                url=settings.redis_url,
                password=getattr(settings, "redis_password", None),
                ssl_enabled=getattr(settings, "redis_ssl", False),
                pool_size=getattr(settings, "redis_pool_size", 10),
                timeout=getattr(settings, "redis_timeout", 5),
            )
            _redis_client = connection.create_client()
        except (redis.exceptions.ConnectionError, ConnectionError) as e:
            logger.warning(
                f"Failed to establish Redis connection: {e}. "
                f"Falling back to fakeredis for testing/development."
            )
            try:
                import fakeredis
                _redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
                logger.info("Using fakeredis as fallback for Redis operations")
            except ImportError:
                logger.error("fakeredis not installed and Redis unavailable")
                raise

    assert _redis_client is not None, "Redis client is not initialized or failed to connect."
    return _redis_client

    return _redis_client


def set_redis_client(client: Optional[Redis]) -> None:
    """Replace the global Redis client (used in tests or mock scenarios)."""
    global _redis_client
    _redis_client = client
    logger.debug("Global Redis client has been overridden.")
