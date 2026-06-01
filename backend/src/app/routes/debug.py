"""Debug routes — for local testing & diagnostics."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from src.app.auth import get_current_user
from src.app.config import settings
from src.app.models.user import User

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/me")
async def debug_me(current_user: User = Depends(get_current_user)) -> dict:
    """Return the current user's info (requires auth)."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": str(current_user.role),
        "tenant_id": str(current_user.tenant_id),
    }


@router.post("/me")
async def debug_me_post(current_user: User = Depends(get_current_user)) -> dict:
    """Same as GET but via POST."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": str(current_user.role),
        "tenant_id": str(current_user.tenant_id),
    }


@router.get("/config")
async def debug_config() -> dict:
    """Show the active config (NO AUTH required — DEBUG ONLY)."""
    return {
        "secret_key_prefix": settings.secret_key[:12] + "...",
        "secret_key_length": len(settings.secret_key),
        "algorithm": settings.algorithm,
        "app_version": settings.app_version,
        "db_url_prefix": settings.database_url[:20] + "...",
    }


class TokenTestRequest(BaseModel):
    token: str


@router.post("/verify-token")
async def debug_verify_token(body: TokenTestRequest) -> dict:
    """Verify a token directly (NO AUTH required — DEBUG ONLY)."""
    from src.app.auth.jwt_handler import decode_token
    from jose import JWTError
    try:
        payload = decode_token(body.token)
        return {
            "valid": True,
            "payload": {
                "sub": payload.get("sub"),
                "tenant_id": payload.get("tenant_id"),
                "role": payload.get("role"),
                "iat": payload.get("iat"),
                "exp": payload.get("exp"),
            },
        }
    except JWTError as e:
        return {"valid": False, "error": str(e)}
