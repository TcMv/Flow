"""JWT token creation and decoding using python-jose."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt

from src.app.config import settings


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    role: str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given user."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "iat": now,
        "exp": now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes)),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns the payload dict.

    Raises JWTError on invalid/expired tokens.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
