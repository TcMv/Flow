"""Agent API routes — chat, sessions, and session management."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.llm_key import LLMKey
from src.app.agent import (
    LLMRouter,
    ToolRegistry,
    AgentSessionManager,
    AgentAuditLogger,
    AgentEngine,
)
from src.app.agent.tools import GetCurrentTime, Echo
from src.app.agent.skill_tools import CreateSkill, GetSkill, ListMySkills
from src.app.agent.workflow_tools import ListWorkflows, RunWorkflow, GetWorkflowRunStatus, ApproveCheckpoint, RejectCheckpoint
from src.app.agent.mcp import register_tier_1_tools

router = APIRouter(prefix="/api/agent", tags=["agent"])

# ── Singleton tool registries ─────────────────────────────────────────

_base_tool_registry: ToolRegistry | None = None


def get_base_tool_registry() -> ToolRegistry:
    """Return the base tool registry with static tools (no DB dependency)."""
    global _base_tool_registry
    if _base_tool_registry is None:
        _base_tool_registry = ToolRegistry()
        _base_tool_registry.register(GetCurrentTime())
        _base_tool_registry.register(Echo())
    return _base_tool_registry


def get_request_tool_registry(db, user) -> ToolRegistry:
    """Return a tool registry for a specific request, including DB-backed tools."""
    registry = ToolRegistry()
    # Copy base tools
    for tool in get_base_tool_registry().list_tools():
        registry.register(tool)
    # Register DB-backed skill tools with request context
    registry.register(CreateSkill(db=db, user_id=user.id, tenant_id=user.tenant_id))
    registry.register(GetSkill(db=db, user_id=user.id, tenant_id=user.tenant_id))
    registry.register(ListMySkills(db=db, user_id=user.id))
    # Register DB-backed workflow tools with request context
    registry.register(ListWorkflows(db=db, user_id=user.id))
    registry.register(RunWorkflow(db=db, user_id=user.id))
    registry.register(GetWorkflowRunStatus(db=db, user_id=user.id))
    registry.register(ApproveCheckpoint(db=db, user_id=user.id))
    registry.register(RejectCheckpoint(db=db, user_id=user.id))
    # Register Tier 1 MCP tools (filesystem, postgres, git, github, fetch, memory)
    register_tier_1_tools(registry, db=db, user=user)
    return registry


def setup_tools() -> None:
    """Called at app startup to pre-register built-in tools."""
    get_base_tool_registry()


# ── Request / Response Schemas ──────────────────────────────────────


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


class SessionInfo(BaseModel):
    id: str
    title: str | None
    created_at: str
    updated_at: str
    message_count: int = 0


class SessionListResponse(BaseModel):
    sessions: list[SessionInfo]


# ── Routes ──────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Start or continue an agent conversation session.

    If ``session_id`` is provided, the conversation continues from
    that session.  Otherwise a new session is created.

    Uses the user's tenant's active LLM key for inference.
    """
    # 1. Find the tenant's active LLM key
    llm_key = await _get_active_llm_key(db, current_user.tenant_id)
    if llm_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active LLM key configured for your tenant. "
                   "Please add an API key in settings.",
        )

    # 2. Get or create session
    session_id: uuid.UUID | None = None
    if body.session_id:
        try:
            session_id = uuid.UUID(body.session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session_id format — must be a UUID.",
            )

    session, created = await AgentSessionManager.get_or_create_session(
        db, session_id, current_user.id, current_user.tenant_id,
    )

    # 3. Build the engine and run
    llm_router = LLMRouter(llm_key)
    tool_registry = get_request_tool_registry(db, current_user)
    audit_logger = AgentAuditLogger(db)
    session_manager = AgentSessionManager()

    engine = AgentEngine(
        llm_router=llm_router,
        tool_registry=tool_registry,
        user=current_user,
        session_manager=session_manager,
        audit_logger=audit_logger,
    )

    response_parts: list[str] = []
    async for chunk in engine.run(
        db=db,
        session_id=session.id,
        user_message=body.message,
    ):
        response_parts.append(chunk)

    # 4. Return
    return ChatResponse(
        session_id=str(session.id),
        response="".join(response_parts),
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List the current user's agent sessions."""
    sessions = await AgentSessionManager.list_sessions(db, current_user.id)

    result: list[SessionInfo] = []
    for s in sessions:
        # Count messages
        from src.app.models.agent_message import AgentMessage
        from sqlalchemy import func

        count_result = await db.execute(
            select(func.count(AgentMessage.id)).where(
                AgentMessage.session_id == s.id,
            )
        )
        msg_count = count_result.scalar() or 0

        result.append(SessionInfo(
            id=str(s.id),
            title=s.title,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
            message_count=msg_count,
        ))

    return SessionListResponse(sessions=result)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an agent session and all its messages."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format.",
        )

    deleted = await AgentSessionManager.delete_session(db, sid, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )


# ── Helpers ──────────────────────────────────────────────────────────


async def _get_active_llm_key(
    db: AsyncSession,
    tenant_id: uuid.UUID,
) -> LLMKey | None:
    """Find the active LLM key for a tenant.

    Falls back to ``settings.flow_api_key`` if no key is stored in the
    database — this lets users get started by just setting an env var.
    When the env-var fallback is used, a lightweight in-memory key
    object is returned (it won't be persisted).
    """
    result = await db.execute(
        select(LLMKey).where(
            LLMKey.tenant_id == tenant_id,
            LLMKey.is_active == True,  # noqa: E712
        ).order_by(LLMKey.created_at.desc()).limit(1)
    )
    db_key = result.scalar_one_or_none()
    if db_key:
        return db_key

    # Fallback to env var
    from src.app.config import settings

    if settings.flow_api_key:
        from src.app.agent.llm import encrypt_api_key

        # Build a lightweight object with just enough for LLMRouter
        fallback = LLMKey(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            provider=settings.flow_llm_provider,
            api_key_encrypted=encrypt_api_key(settings.flow_api_key),
            base_url=settings.flow_llm_base_url,
            model_name=settings.flow_llm_model,
            is_active=True,
        )
        return fallback

    return None
