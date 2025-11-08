"""
security (renamed to auth.py)
------------
Production-grade JWT authentication, password hashing, and role enforcement
with Redis-based token revocation. Designed for healthcare systems (FDA / ISO
compliance) — ensures all tokens can be revoked and validated centrally.
"""

from __future__ import annotations

import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.redis_security import get_secure_redis_client
from backend.app.metrics import track_redis_operation

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    username: str
    role: str
    disabled: Optional[bool] = None


# ---------------------------------------------------------------------
# Password hashing (Argon2)
# ---------------------------------------------------------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def truncate_password(password: str) -> str:
    """Truncate to 72 bytes (bcrypt legacy limit) and return safe UTF-8 string."""
    try:
        pass_bytes = str(password).encode("utf-8")[:72]
        return pass_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return password[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)


# ---------------------------------------------------------------------
# JWT Token Management
# ---------------------------------------------------------------------
@track_redis_operation("jwt_revoke")
def _revoke_token(jti: str, exp_ts: Optional[int]) -> None:
    """Mark a token as revoked in Redis with TTL = token expiry."""
    r = get_secure_redis_client()
    key = f"jwt:blacklist:{jti}"
    now = int(datetime.now(tz=timezone.utc).timestamp())
    ttl = max(1, (exp_ts - now) if exp_ts else settings.jwt_exp_minutes * 60)
    r.set(key, "1", ex=ttl)


@track_redis_operation("jwt_is_revoked")
def _is_token_revoked(jti: str) -> bool:
    """Return True if the given JTI exists in Redis blacklist."""
    r = get_secure_redis_client()
    return bool(r.exists(f"jwt:blacklist:{jti}"))


def _extract_jti(payload: dict, token: str) -> str:
    """Return JTI claim or hash fallback (legacy tokens)."""
    return payload.get("jti") or hashlib.sha256(token.encode()).hexdigest()


def _extract_exp(payload: dict) -> Optional[int]:
    exp = payload.get("exp")
    return int(exp) if isinstance(exp, (int, float)) else None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT with embedded role and unique JTI."""
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_exp_minutes)
    )
    to_encode.update(
        {
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(tz=timezone.utc).timestamp()),
            "jti": str(uuid.uuid4()),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT, raising HTTP 401 on error."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def revoke_token(token: str) -> None:
    """Revoke the provided token (e.g., during logout)."""
    payload = decode_token(token)
    jti = _extract_jti(payload, token)
    exp = _extract_exp(payload)
    _revoke_token(jti, exp)


# ---------------------------------------------------------------------
# Current User & Role Enforcement
# ---------------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Return the current user from token, enforcing revocation and validity."""
    payload = decode_token(token)
    jti = _extract_jti(payload, token)
    if _is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    role = payload.get("role")

    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # In production, this should query a DB or secure user registry
    user_info = settings.users.get(username)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user_info.get("disabled", False):
        raise HTTPException(status_code=400, detail="Inactive user")

    return User(username=username, role=role, disabled=user_info.get("disabled"))


def requires_role(allowed_roles: List[str]):
    """FastAPI dependency enforcing user role inclusion in allowed_roles."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role",
            )
        return current_user

    return role_checker


def verify_token(token: str) -> Dict:
    """Decode and return JWT payload (raises HTTPException if invalid)."""
    return decode_token(token)
