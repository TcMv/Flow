"""LLMKey model — tenant-scoped LLM provider credentials stored encrypted."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class LLMKey(Base):
    """An encrypted LLM API key for a tenant's provider."""

    __tablename__ = "llm_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="openai / anthropic / azure / custom",
    )
    api_key_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted API key",
    )
    base_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        default=None,
        comment="Base URL for custom/self-hosted providers",
    )
    model_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        default="gpt-4o",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship("Tenant")

    def __repr__(self) -> str:
        return f"<LLMKey id={self.id!r} provider={self.provider!r} model={self.model_name!r}>"
