"""Flow backend — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.config import settings
from src.app.database import engine, Base
from src.app.routes.auth import router as auth_router
from src.app.routes.health import router as health_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables on startup; dispose engine on shutdown."""
    # For SQLite / simple dev, create tables on startup.
    # In production, use Alembic migrations instead.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# ── Routes ──────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(auth_router)
