"""
middleware.py — Secure middleware configuration for MedAI_Flow_DevSecOps
Implements:
- Redis-backed rate limiting (SlowAPI)
- Comprehensive security headers
- HTTPS enforcement (optional, configurable)
- Request tracking and timing
- CORS configuration
"""

import time
import uuid
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi import _rate_limit_exceeded_handler

from .config import settings
from .rate_limit import RedisLimiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security headers aligned with OWASP, NIST SP 800-53, and FDA cybersecurity guidance
# ---------------------------------------------------------------------------
SECURITY_HEADERS = {
    "Server": "MedAI-API-Gateway",  # Mask framework details
    "X-Frame-Options": "DENY",  # Prevent clickjacking
    "X-XSS-Protection": "1; mode=block",  # Basic XSS filter
    "X-Content-Type-Options": "nosniff",  # Prevent MIME-type sniffing
    "Referrer-Policy": "no-referrer",  # No referrer leakage
    "Cache-Control": "no-store",  # Disable sensitive caching
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",  # HSTS
    "Content-Security-Policy": (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    ),
    "Permissions-Policy": (
        "accelerometer=(), camera=(), geolocation=(), "
        "gyroscope=(), magnetometer=(), microphone=(), "
        "payment=(), usb=()"
    ),
    # New: defense against cross-origin data leaks (Spectre, COOP/COEP)
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
}

# ---------------------------------------------------------------------------
# Middleware setup
# ---------------------------------------------------------------------------

def setup_middleware(app: FastAPI) -> None:
    """Configure security, rate-limiting, CORS, and audit middleware."""
    try:
        # Initialize Redis-backed rate limiter
        limiter = RedisLimiter(
            key_func=get_remote_address,
            redis_url=settings.redis_url,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"],
            redis_prefix="medai_flow",
            redis_pool_size=settings.redis_pool_size,
            redis_timeout=settings.redis_timeout,
        )

        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
        app.add_middleware(SlowAPIMiddleware)

        logger.info("Rate limiting middleware initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize rate limiting: {str(e)}")
        raise

    # -----------------------------------------------------------------------
    # Add CORS middleware
    # -----------------------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # -----------------------------------------------------------------------
    # HTTPS enforcement (optional, disable if using reverse proxy TLS)
    # -----------------------------------------------------------------------
    @app.middleware("http")
    async def enforce_https(request: Request, call_next: Callable):
        """Redirect plain HTTP to HTTPS (disable if already enforced at gateway)."""
        if getattr(settings, "enforce_https", False) and request.url.scheme != "https":
            secure_url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(secure_url))
        return await call_next(request)

    # -----------------------------------------------------------------------
    # Add security headers and request tracking
    # -----------------------------------------------------------------------
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Callable):
        """Attach standard security headers and audit trail metadata."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        response: Response = await call_next(request)

        # Add all defined security headers
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add tracking headers
        duration = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(duration, 4))

        return response

    logger.info("Middleware configuration completed successfully")

