"""Health-check endpoint."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from src.app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return service status, version, and current timestamp."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
