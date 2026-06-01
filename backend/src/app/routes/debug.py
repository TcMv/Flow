"""Debug routes — for local testing & diagnostics."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.app.auth import get_current_user
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
