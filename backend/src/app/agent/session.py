"""AgentSessionManager — manages conversation state in memory and DB."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.agent_session import AgentSession
from src.app.models.agent_message import AgentMessage


class AgentSessionManager:
    """Manages conversation sessions — create, retrieve, update, and delete.

    Each session stores its message history in the ``agent_messages``
    table, loaded lazily on access.
    """

    MAX_HISTORY_MESSAGES: int = 50

    # ── Lifecycle ─────────────────────────────────────────────────

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        title: str | None = None,
    ) -> AgentSession:
        """Create a new agent session for the given user."""
        session = AgentSession(
            id=uuid.uuid4(),
            user_id=user_id,
            tenant_id=tenant_id,
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def get_session(
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> AgentSession | None:
        """Retrieve a session by ID, scoped to the given user."""
        result = await db.execute(
            select(AgentSession).where(
                AgentSession.id == session_id,
                AgentSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_sessions(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List the user's sessions, most recent first."""
        result = await db.execute(
            select(AgentSession)
            .where(AgentSession.user_id == user_id)
            .order_by(AgentSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a session and its messages. Returns True if deleted."""
        session = await AgentSessionManager.get_session(db, session_id, user_id)
        if session is None:
            return False
        await db.delete(session)
        await db.flush()
        return True

    @staticmethod
    async def update_title(
        db: AsyncSession,
        session_id: uuid.UUID,
        title: str,
    ) -> None:
        """Update the session title."""
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.title = title[:255]
            session.updated_at = datetime.now(timezone.utc)
            await db.flush()

    # ── Messages ──────────────────────────────────────────────────

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: uuid.UUID,
        role: str,
        content: str,
        tool_calls: str | None = None,
        tool_call_id: str | None = None,
    ) -> AgentMessage:
        """Append a message to the session history."""
        msg = AgentMessage(
            id=uuid.uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(msg)

        # Touch the session's updated_at
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.updated_at = datetime.now(timezone.utc)

        await db.flush()
        return msg

    @staticmethod
    async def get_history(
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int | None = None,
    ) -> list[dict]:
        """Retrieve message history for the LLM context window.

        Returns a list of ``{"role": ..., "content": ...}`` dicts,
        limited to the most recent *limit* messages (defaults to
        ``MAX_HISTORY_MESSAGES``).
        """
        if limit is None:
            limit = AgentSessionManager.MAX_HISTORY_MESSAGES

        result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.session_id == session_id)
            .order_by(AgentMessage.created_at.asc())
        )
        msgs = result.scalars().all()

        # Take only the last N for context window
        recent = msgs[-limit:] if len(msgs) > limit else msgs

        history = []
        for msg in recent:
            entry: dict = {"role": msg.role, "content": msg.content}

            # Include tool_calls for assistant messages that called tools
            if msg.role == "assistant" and msg.tool_calls:
                try:
                    entry["tool_calls"] = json.loads(msg.tool_calls)
                    entry["content"] = None  # OpenAI spec: null content when tools present
                except (json.JSONDecodeError, TypeError):
                    pass

            # Include tool_call_id for tool result messages
            if msg.role == "tool" and msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id

            history.append(entry)

        return history

    @staticmethod
    async def get_or_create_session(
        db: AsyncSession,
        session_id: uuid.UUID | None,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> tuple[AgentSession, bool]:
        """Get an existing session or create a new one.

        Returns ``(session, created)`` where *created* is ``True``
        if a new session was created.
        """
        if session_id:
            existing = await AgentSessionManager.get_session(db, session_id, user_id)
            if existing:
                return existing, False

        new_session = await AgentSessionManager.create_session(db, user_id, tenant_id)
        return new_session, True
