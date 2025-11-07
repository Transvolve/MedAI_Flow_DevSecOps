from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Header, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from .config import settings


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


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def truncate_bytes(data: bytes) -> bytes:
    """Truncate bytes to 72 bytes, the maximum allowed by bcrypt."""
    return data[:72]


def truncate_password(password: str) -> str:
    """
    Truncate a password to 72 bytes for bcrypt.
    Returns a UTF-8 string representation of the truncated bytes.
    """
    try:
        if isinstance(password, str):
            pass_bytes = password.encode('utf-8')
        else:
            pass_bytes = str(password).encode('utf-8')
        return pass_bytes[:72].decode('utf-8')
    except Exception as e:
        print(f"Error in truncate_password: {e}")
        return str(password)[:72]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        print(f"Attempting to verify password: {plain_password}")
        print(f"Against hash: {hashed_password}")
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Validate the token data
        TokenData(username=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    # In production, this should query a database
    if username in settings.users:
        user_data = settings.users[username]
        user = User(username=username, role=user_data["role"], disabled=user_data.get("disabled", False))
    else:
        raise credentials_exception

    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def requires_role(allowed_roles: list[str]):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role"
            )
        return current_user
    return role_checker


def verify_token(token: str) -> Dict:
    """Verify a JWT token and return its payload."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
            headers={"WWW-Authenticate": "Bearer"},
        )

