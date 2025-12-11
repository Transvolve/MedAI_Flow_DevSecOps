"""
main.py
-------
Application entry point for MedAI_Flow_DevSecOps.

Includes:
- Secure authentication (JWT)
- Prometheus metrics
- Role-based access control
- Middleware setup for security, rate limiting, and CORS
"""

from datetime import timedelta
import logging
import time

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from backend.app.config import settings
from backend.app.middleware import setup_middleware
from backend.app.routes import router
from backend.app.analysis.api import router as analysis_router
from backend.app.auth import (
    Token,
    User,
    create_access_token,
    get_current_user,
    verify_password,
    requires_role,
)

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# FastAPI Initialization
# -----------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# -----------------------------------------------------------------------------
# Prometheus Metrics Endpoint (Unauthenticated)
# -----------------------------------------------------------------------------
@app.get("/metrics", include_in_schema=False)
async def get_metrics():
    """Expose Prometheus metrics for system monitoring."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

# -----------------------------------------------------------------------------
# Setup Middleware & Routes
# -----------------------------------------------------------------------------
setup_middleware(app)
app.include_router(router)
app.include_router(analysis_router)

# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------
@app.post("/token", response_model=Token, tags=["auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Obtain JWT access token using OAuth2 password flow.
    """
    if form_data.username not in settings.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = settings.users[form_data.username]
    if not verify_password(form_data.password, user_data["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": form_data.username, "role": user_data["role"]},
        expires_delta=access_token_expires,
    )

    logger.info(f"User {form_data.username} authenticated successfully.")
    return {"access_token": access_token, "token_type": "bearer"}

# -----------------------------------------------------------------------------
# Health & Version Endpoints
# -----------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "uptime": time.time()}


@app.get("/version", tags=["system"])
async def get_version() -> dict:
    """Return current version of the application."""
    return {"version": settings.app_version}

# -----------------------------------------------------------------------------
# User Profile & Admin Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/v1/me", response_model=User, tags=["auth"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Return info of the currently authenticated user."""
    return current_user


@app.get("/admin/data", dependencies=[Depends(requires_role(["admin"]))], tags=["admin"])
async def admin_data():
    """Example admin-only endpoint for testing RBAC."""
    return {"secure_info": "Only admins can view this."}

