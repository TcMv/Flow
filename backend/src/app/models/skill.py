"""Skill model — an atomic, reusable capability the agent can invoke."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.database import Base


class Skill(Base):
    """An atomic, reusable capability created via chat and invocable by the agent."""

    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, index=True)
    description = Column(String(512), nullable=False, default="")
    trigger_command = Column(String(64), nullable=True, index=True)  # e.g. "/brief"
    definition_str = Column(Text, nullable=False, default="")
    # Visibility & governance
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    visibility = Column(String(16), nullable=False, default="private")  # private | marketplace
    status = Column(String(16), nullable=False, default="active")       # active | under_review | approved | rejected
    review_notes = Column(Text, nullable=True)
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Who has installed this skill (many-to-many)
    installed_by_users = relationship("User", secondary="user_installed_skills", back_populates="installed_skills", lazy="selectin")

    # Relationships
    owner = relationship("User", backref="skills", lazy="selectin")


class UserInstalledSkill(Base):
    """Tracks which users have installed which marketplace skills."""

    __tablename__ = "user_installed_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    installed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", lazy="selectin")
    skill = relationship("Skill", backref="installations", lazy="selectin")


class SkillExecution(Base):
    """A record of a skill being executed."""

    __tablename__ = "skill_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("agent_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    inputs = Column(Text, nullable=True)          # JSON
    output = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="running")  # running | completed | failed
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    skill = relationship("Skill", backref="executions", lazy="selectin")
