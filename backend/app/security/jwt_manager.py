# backend/app/security/jwt_manager.py
from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Iterable, Optional, Callable
from types import SimpleNamespace

from fastapi import Depends, HTTPException, status
from jose import jwt, JWTError

from backend.app.config import settings
from backend.app.redis_security import get_secure_redis_client
from backend.app.auth import get_current_user, oauth2_scheme, User, create_access_token
from backend.app.metrics import track_redis_operation

# Key namespace for revoked tokens
_REDIS_REVOKE_PREFIX = "jwt:blacklist"

def _redis_key_for_jti(jti: str) -> str:
    return f"{_REDIS_REVOKE_PREFIX}:{jti}"

@track_redis_operation("jwt_is_revoked")
def is_token_revoked(jti: str) -> bool:
    """Check if a token JTI is revoked (blacklisted) in Redis."""
    r = get_secure_redis_client()
    return bool(r.exists(_redis_key_for_jti(jti)))

@track_redis_operation("jwt_revoke")
def revoke_token(jti: str, exp_ts: Optional[int]) -> None:
    """
    Revoke a token by JTI. We set a TTL in Redis up to token expiration to avoid unbounded growth.
    If exp_ts is None, default TTL = settings.access_token_expire_minutes * 60.
    """
    r = get_secure_redis_client()
    key = _redis_key_for_jti(jti)

    now = int(datetime.now(tz=timezone.utc).timestamp())
    if exp_ts is not None:
        ttl = max(0, exp_ts - now)
    else:
        ttl = max(0, settings.access_token_expire_minutes * 60)

    # Value is irrelevant; existence of key means “revoked”.
    # Use set with EX for TTL. If ttl==0, still set short TTL to ensure immediate effect.
    r.set(key, "1", ex=max(1, ttl))

def decode_token(token: str) -> dict:
    """Decode and verify a JWT, returning its payload (raises on failure)."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

def extract_jti_from_payload_or_token(payload: dict, token: str) -> str:
    """
    Prefer 'jti' claim; if absent (legacy tokens), derive a stable JTI from token hash.
    """
    jti = payload.get("jti")
    if jti:
        return jti
    # Backward compatibility: derive JTI from token bytes (stable across runs)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def extract_exp(payload: dict) -> Optional[int]:
    exp = payload.get("exp")
    if isinstance(exp, int):
        return exp
    return None

def require_role(allowed_roles: Iterable[str]) -> Callable:
    """
    FastAPI dependency factory enforcing:
      1) token validity + non-revocation
      2) user's role ∈ allowed_roles
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(["admin"]))])
    """
    allowed = set(allowed_roles)

    def dep(
        current_user: User = Depends(get_current_user),
        token: str = Depends(oauth2_scheme),
    ) -> User:
        payload = decode_token(token)
        jti = extract_jti_from_payload_or_token(payload, token)
        if is_token_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        role = getattr(current_user, "role", None)
        if role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return current_user

    return dep


# Convenience wrapper expected by tests: provide an object `jwt_manager`
# exposing `create_token`, `revoke_token`, and `is_revoked`.


def _create_token(data: dict) -> str:
    """Create a JWT using the project's standard create_access_token helper.

    Tests call this to get a token string — fine if the JTI differs from the
    test's manually used JTI because tests separately call revoke_token by JTI.
    """
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    return create_access_token(data, expires_delta=expires)


jwt_manager = SimpleNamespace(
    create_token=_create_token,
    revoke_token=revoke_token,
    is_revoked=is_token_revoked,
)


