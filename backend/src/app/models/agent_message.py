"""AgentMessage model — individual messages within a conversation session."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class AgentMessage(Base):
    """A single message in an agent conversation session."""

    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="user / assistant / tool",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    tool_calls: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="JSON-encoded tool call metadata (if any)",
    )
    tool_call_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default=None,
        comment="ID of the tool call this message is a result of",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    session: Mapped["AgentSession"] = relationship(
        "AgentSession",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<AgentMessage id={self.id!r} role={self.role!r} content_len={len(self.content)}>"
