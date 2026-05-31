"""AuditLog model — immutable event log with hash-chain integrity."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class AuditLog(Base):
    """
    Immutable audit event.

    Each record stores its own hash (SHA-256 of its serialised content)
    and the previous record's hash, forming a tamper-evident chain.
    """

    __tablename__ = "audit_logs"

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
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    # ── Hash chain ───────────────────────────────────────────────
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, default=None)

    # ── Relationships ────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_logs")

    @classmethod
    def compute_hash(
        cls,
        record_id: uuid.UUID,
        tenant_id: uuid.UUID,
        timestamp: datetime,
        actor_id: uuid.UUID,
        action_type: str,
        resource_type: str,
        resource_id: str,
        details: str | None,
        prev_hash: str | None,
    ) -> str:
        """Compute the SHA-256 hash for an audit record's content."""
        payload = {
            "id": str(record_id),
            "tenant_id": str(tenant_id),
            "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp,
            "actor_id": str(actor_id),
            "action_type": action_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "prev_hash": prev_hash,
        }
        serialised = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(serialised).hexdigest()

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id!r} action={self.action_type!r}>"
