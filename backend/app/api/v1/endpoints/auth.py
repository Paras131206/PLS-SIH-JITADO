from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    generate_api_key,
    get_current_user,
    get_current_user_universal,
    require_roles,
    decode_token,
)
from app.db.session import get_db
from app.db.models import User, APIKey, Role

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class APIKeyCreate(BaseModel):
    name: str
    expires_days: int = 365


class APIKeyResponse(BaseModel):
    key: str
    prefix: str
    name: str
    expires_at: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    institution_id: str | None
    is_active: bool


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/api-keys", response_model=APIKeyResponse)
def create_api_key(
    request: APIKeyCreate,
    current_user: User = Depends(require_roles(Role.INSTITUTION_ADMIN, Role.AICTE_ADMIN)),
    db: Session = Depends(get_db),
):
    full_key, prefix, key_hash = generate_api_key()
    expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_days)
    api_key = APIKey(
        user_id=current_user.id,
        key_hash=key_hash,
        prefix=prefix,
        name=request.name,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return APIKeyResponse(
        key=full_key,
        prefix=prefix,
        name=request.name,
        expires_at=expires_at.isoformat(),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user_universal)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        institution_id=str(current_user.institution_id) if current_user.institution_id else None,
        is_active=current_user.is_active,
    )