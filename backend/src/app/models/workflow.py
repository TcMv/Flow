"""Workflow models — compiled process definitions and their executions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.database import Base


class Workflow(Base):
    """A compiled structured workflow — ordered tasks with dependencies and checkpoints."""

    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    trigger = Column(String(16), nullable=False, default="chat")  # chat | scheduled
    definition = Column(Text, nullable=False, default="{}")  # JSON — the full task list
    source_text = Column(Text, nullable=True)  # original user input (process description)
    status = Column(String(16), nullable=False, default="draft")  # draft | active | archived
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", backref="workflows", lazy="selectin")
    runs = relationship("WorkflowRun", back_populates="workflow", lazy="selectin", cascade="all, delete-orphan")


class WorkflowRun(Base):
    """A single execution run of a workflow."""

    __tablename__ = "workflow_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | running | paused | completed | failed | cancelled
    current_task_id = Column(String(64), nullable=True)  # which task is currently active
    result = Column(Text, nullable=True)  # final output
    error = Column(Text, nullable=True)  # error details if failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workflow = relationship("Workflow", back_populates="runs", lazy="selectin")
    user = relationship("User", lazy="selectin")


class WorkflowTaskRun(Base):
    """A single task execution within a workflow run."""

    __tablename__ = "workflow_task_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(64), nullable=False)  # matches id in the workflow definition
    skill_name = Column(String(128), nullable=True)  # name of the skill this task uses
    task_type = Column(String(20), nullable=False, default="skill")  # skill | human_approval
    status = Column(String(20), nullable=False, default="pending")  # pending | running | completed | failed | skipped | waiting_for_approval
    input_data = Column(Text, nullable=True)  # JSON — resolved inputs
    output_data = Column(Text, nullable=True)  # JSON — task output
    feedback = Column(Text, nullable=True)  # human feedback on rejection
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    run = relationship("WorkflowRun", backref="task_runs_ref", lazy="noload")
