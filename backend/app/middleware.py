import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp
from secure import SecureHeaders
from .config import settings
from .rate_limit import RedisLimiter
import logging

logger = logging.getLogger(__name__)

# Initialize secure headers
secure_headers = SecureHeaders(
    csp={
        'default-src': "'self'",
        'img-src': "'self' data: https:",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
        'style-src': "'self' 'unsafe-inline'",
        'frame-ancestors': "'none'",
    },
    hsts={
        'max-age': 31536000,
        'include_subdomains': True,
        'preload': True
    },
    permissions_policy={
        'accelerometer': '()',
        'camera': '()',
        'geolocation': '()',
        'gyroscope': '()',
        'magnetometer': '()',
        'microphone': '()',
        'payment': '()',
        'usb': '()'
    }
)

def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the application."""
    try:
        # Initialize Redis-backed rate limiter
        limiter = RedisLimiter(
            key_func=get_remote_address,
            redis_url=settings.redis_url,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"],
            redis_prefix="medai_flow",
            redis_pool_size=settings.redis_pool_size,
            redis_timeout=settings.redis_timeout
        )
        
        # Register rate limit error handler
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # Add slowapi middleware for rate limiting
        app.add_middleware(SlowAPIMiddleware)
        
        logger.info("Rate limiting middleware initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiting: {str(e)}")
        raise
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )
    
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable):
        """Add security headers and request tracking."""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        response = await call_next(request)
        
        # Add security headers
        secure_headers.fastapi(response)
        
        # Add timing and tracking headers
        duration = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(duration, 4))
        
        # Rate limit headers are automatically added by SlowAPIMiddleware
        return response
