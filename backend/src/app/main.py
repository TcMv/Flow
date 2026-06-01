"""Flow backend — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.config import settings
from src.app.database import engine, Base
from src.app.routes.auth import router as auth_router
from src.app.routes.health import router as health_router
from src.app.routes.agent import router as agent_router
from src.app.routes.agent import setup_tools
from src.app.routes.debug import router as debug_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables on startup; dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Register built-in agent tools
    setup_tools()
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
app.include_router(agent_router)
app.include_router(debug_router)
