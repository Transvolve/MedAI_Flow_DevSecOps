from fastapi import FastAPI  # Request
from .routes import router
from .middleware import setup_middleware
import logging
import time
from .config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title=settings.app_name, version=settings.app_version)

# Register routes
app.include_router(router)

setup_middleware(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "uptime": time.time()}


@app.get("/version")
async def get_version() -> dict:
    """Temporary test endpoint to trigger CI/CD."""
    return {"version": settings.app_version}
