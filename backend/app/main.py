from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .routes import router
from .middleware import setup_middleware
from .security import Token, User, create_access_token, get_current_user, verify_password
import logging
import time
from .config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", mode="a")
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",  # Secure docs endpoint
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Register routes
app.include_router(
    router,
    prefix="/api/v1",
    tags=["api"],
    dependencies=[Depends(get_current_user)]
)

setup_middleware(app)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login, get an access token for future requests."""
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
        expires_delta=access_token_expires
    )

    logger.info(f"User {form_data.username} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/health")
async def health() -> dict:
    """Health check endpoint - no auth required."""
    return {"status": "ok", "uptime": time.time()}


@app.get("/version")
async def get_version() -> dict:
    """Version info endpoint - no auth required."""
    return {"version": settings.app_version}


@app.get("/api/v1/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user

