from fastapi import Request
import time, uuid
from starlette.middleware.base import BaseHTTPMiddleware

def setup_middleware(app):
    @app.middleware("http")
    async def add_request_timing(request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(duration, 4))
        return response
