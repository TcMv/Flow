"""User model — belongs to a Tenant, has role-based access."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class UserRole(StrEnum):
    admin = "admin"
    builder = "builder"
    user = "user"


class User(Base):
    """A user within a tenant workspace."""

    __tablename__ = "users"

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
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_constraint=True),
        nullable=False,
        default=UserRole.user,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_config: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    installed_skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="user_installed_skills",
        back_populates="installed_by_users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r} role={self.role!r}>"
