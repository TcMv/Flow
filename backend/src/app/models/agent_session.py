"""AgentSession model — persisted conversation sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class AgentSession(Base):
    """A persisted agent conversation session belonging to a user."""

    __tablename__ = "agent_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default=None,
        comment="Auto-generated title from first user message",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    user: Mapped["User"] = relationship("User")
    tenant: Mapped["Tenant"] = relationship("Tenant")
    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )

    def __repr__(self) -> str:
        return f"<AgentSession id={self.id!r} title={self.title!r}>"
