from typing import Optional
from fastapi import Header, HTTPException
from .config import settings


async def verify_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    if token != settings.api_token:
        raise HTTPException(status_code=403, detail="Invalid token")
