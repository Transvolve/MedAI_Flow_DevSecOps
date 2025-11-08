"""Redis security configuration and connection management."""
import ssl
import logging
from typing import Optional

import redis
from redis import Redis
from redis.connection import Connection, SSLConnection

from .config import settings

logger = logging.getLogger(__name__)

class SecureRedisConnection:
    """Secure Redis connection manager with SSL and authentication."""

    def __init__(
        self,
        url: str,
        password: Optional[str] = None,
        ssl_enabled: bool = False,
        pool_size: int = 10,
        timeout: int = 5,
    ):
        self.url = url
        self.password = password
        self.ssl_enabled = ssl_enabled
        self.pool_size = pool_size
        self.timeout = timeout
        self.ssl_context = None
        if ssl_enabled:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = True
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED

    def get_connection_params(self) -> dict:
        params = {
            "decode_responses": True,
            "max_connections": self.pool_size,
            "socket_timeout": self.timeout,
        }
        if self.password:
            params["password"] = self.password
        if self.ssl_enabled:
            params["connection_class"] = SSLConnection
            params["ssl_context"] = self.ssl_context
        else:
            params["connection_class"] = Connection
        return params

    def create_client(self) -> Redis:
        """Create a secure Redis client instance."""
        try:
            client = Redis.from_url(self.url, **self.get_connection_params())
            client.ping()
            logger.info(
                f"Established secure Redis connection to {self.url} "
                f"(SSL: {self.ssl_enabled}, Pool: {self.pool_size})"
            )
            return client
        except Exception as e:
            logger.error(f"Failed to establish Redis connection: {str(e)}")
            raise

# Global variable to hold the Redis client instance, typed for clarity
_redis_client: Optional[Redis] = None

def get_secure_redis_client() -> Redis:
    """
    Returns a secure Redis client using a global singleton pattern.
    This allows the client to be instantiated once and mocked during tests.
    """
    global _redis_client
    if _redis_client is None:
        try:
            client = SecureRedisConnection(
                url=settings.redis_url,
                password=settings.redis_password,
                ssl_enabled=settings.redis_ssl,
                pool_size=settings.redis_pool_size,
                timeout=settings.redis_timeout,
            ).create_client()
            _redis_client = client
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Failed to establish initial Redis connection: {e}")
            raise e
    
    if _redis_client is None:
        raise ConnectionError("Redis client is not available.")
        
    return _redis_client

def set_redis_client(client: Redis):
    """
    Allows replacing the global Redis client. This is the key for our testing strategy.
    """
    global _redis_client
    _redis_client = client

