"""Flow backend — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.app.config import settings
from src.app.database import engine, Base
from src.app.routes.auth import router as auth_router
from src.app.routes.health import router as health_router
from src.app.routes.agent import router as agent_router
from src.app.routes.agent import setup_tools
from src.app.routes.skills import router as skills_router
from src.app.routes.workflows import router as workflows_router
from src.app.routes.cron import router as cron_router
from src.app.routes.debug import router as debug_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables on startup; dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Run deferred migrations (adding columns to existing tables)
        await _run_deferred_migrations(conn)
    # Register built-in agent tools
    setup_tools()
    yield
    await engine.dispose()


async def _run_deferred_migrations(conn):
    """Apply schema changes that can't go in the model definitions."""
    for stmt in [
        "ALTER TABLE agent_messages ADD COLUMN IF NOT EXISTS tool_call_id VARCHAR(64)",
        # Installed skills tracking (PostgreSQL)
        "CREATE TABLE IF NOT EXISTS user_installed_skills ("
        "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),"
        "  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
        "  skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,"
        "  installed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),"
        "  UNIQUE(user_id, skill_id)"
        ")",
        # Schedule columns for workflows (PostgreSQL)
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS schedule VARCHAR(64)",
        "ALTER TABLE workflows ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMPTZ",
    ]:
        try:
            await conn.execute(text(stmt))
        except Exception:
            pass  # Column already exists or DB doesn't support IF NOT EXISTS yet


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://frontend-nine-red-8p7qrnvoce.vercel.app",
        "https://flow-delta-topaz.vercel.app",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(skills_router)
app.include_router(workflows_router)
app.include_router(cron_router)
app.include_router(debug_router)
