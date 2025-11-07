"""Redis security configuration and connection management."""
import ssl
from typing import Optional
from redis import Redis
from redis.connection import Connection, SSLConnection
from redis.retry import Retry
import logging
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
        retry_on_timeout: bool = True,
        retry_on_error: list[str] = None
    ):
        """Initialize secure Redis connection.

        Args:
            url: Redis connection URL
            password: Redis AUTH password
            ssl_enabled: Enable SSL/TLS
            pool_size: Connection pool size
            timeout: Connection timeout in seconds
            retry_on_timeout: Retry on timeout errors
            retry_on_error: List of Redis errors to retry on
        """
        self.url = url
        self.password = password
        self.ssl_enabled = ssl_enabled
        self.pool_size = pool_size
        self.timeout = timeout

        # Default retry strategy
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_error = retry_on_error or []

        # SSL context if enabled
        self.ssl_context = None
        if ssl_enabled:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = True
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED

    def get_connection_params(self) -> dict:
        """Get secure Redis connection parameters."""
        params = {
            "decode_responses": True,
            "max_connections": self.pool_size,
            "socket_timeout": self.timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "retry_on_errors": self.retry_on_error
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
            client = Redis.from_url(
                self.url,
                **self.get_connection_params()
            )

            # Test connection
            client.ping()

            logger.info(
                f"Established secure Redis connection to {self.url} "
                f"(SSL: {self.ssl_enabled}, Pool: {self.pool_size})"
            )
            return client

        except Exception as e:
            logger.error(f"Failed to establish Redis connection: {str(e)}")
            raise

def get_secure_redis_client() -> Redis:
    """Get a configured secure Redis client singleton."""
    return SecureRedisConnection(
        url=settings.redis_url,
        password=settings.redis_password,
        ssl_enabled=settings.redis_ssl,
        pool_size=settings.redis_pool_size,
        timeout=settings.redis_timeout
    ).create_client()

