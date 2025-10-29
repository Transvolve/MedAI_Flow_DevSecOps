from fastapi import FastAPI, Request
from .routes import router
from .middleware import setup_middleware
import logging, time

app = FastAPI(title="MedAI Flow Backend", version="1.0")

# Register routes
app.include_router(router)

# Middleware setup
setup_middleware(app)

@app.get("/health")
async def health():
    return {"status": "ok", "uptime": time.time()}
