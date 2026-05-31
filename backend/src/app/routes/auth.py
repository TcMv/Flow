"""Auth routes — register, login, and current-user."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.auth.jwt_handler import create_access_token
from src.app.auth.utils import hash_password, verify_password
from src.app.database import get_db
from src.app.models.tenant import Tenant
from src.app.models.user import User, UserRole

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request / Response Schemas ──────────────────────────────────────


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    tenant_name: str = "Default"


class RegisterResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    tenant_id: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    tenant_id: str


# ── Routes ──────────────────────────────────────────────────────────


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    """Register a new user. Creates a default tenant if none exists."""
    # Check for duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Find or create the default tenant
    result = await db.execute(select(Tenant).where(Tenant.name == body.tenant_name))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(
            id=uuid.uuid4(),
            name=body.tenant_name,
            settings=None,
            created_at=datetime.now(timezone.utc),
        )
        db.add(tenant)

    # Create the user
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=body.email,
        name=body.name,
        role=UserRole.user,
        hashed_password=hash_password(body.password),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    # Flush so the IDs are available before the commit in get_db()
    await db.flush()

    return RegisterResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role.value,
        tenant_id=str(user.tenant_id),
    )


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    """Verify email and password, return a JWT access token."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
    )

    return LoginResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Return the currently authenticated user's profile."""
    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        tenant_id=str(current_user.tenant_id),
    )
