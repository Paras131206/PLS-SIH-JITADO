import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from passlib.context import CryptContext
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User, APIKey, Role

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_key() -> Tuple[str, str, str]:
    raw_key = secrets.token_urlsafe(32)
    prefix = f"apaar_{secrets.token_urlsafe(8)}"
    full_key = f"{prefix}_{raw_key}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


def verify_api_key(provided_key: str, key_hash: str) -> bool:
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return secrets.compare_digest(provided_hash, key_hash)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_from_api_key(
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not api_key:
        return None
    api_key_obj = db.query(APIKey).filter(APIKey.prefix == api_key.split("_")[1] if "_" in api_key else "").first()
    if not api_key_obj or not api_key_obj.is_active:
        return None
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
        return None
    if not verify_api_key(api_key, api_key_obj.key_hash):
        return None
    api_key_obj.last_used_at = datetime.now(timezone.utc)
    db.commit()
    user = db.query(User).filter(User.id == api_key_obj.user_id).first()
    if user and user.is_active:
        return user
    return None


async def get_current_user_universal(
    token_user: User = Depends(get_current_user),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    if token_user:
        return token_user
    if api_key_user:
        return api_key_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*allowed_roles: Role):
    def role_checker(user: User = Depends(get_current_user_universal)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {', '.join(r.value for r in allowed_roles)}",
            )
        return user
    return role_checker