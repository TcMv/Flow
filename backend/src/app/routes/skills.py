"""Skills API routes — CRUD, marketplace submission, review, and execution."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.database import get_db
from src.app.models.user import User, UserRole
from src.app.models.skill import Skill, SkillExecution
from src.app.agent.audit import AgentAuditLogger

router = APIRouter(prefix="/api/skills", tags=["skills"])


# ── Schemas ──────────────────────────────────────────────────────────


class SkillCreate(BaseModel):
    name: str
    description: str = ""
    trigger_command: str | None = None
    definition_str: str = ""


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_command: str | None = None
    definition_str: str | None = None


class SkillReview(BaseModel):
    action: str  # "approve" | "reject"
    notes: str | None = None


class SkillExecute(BaseModel):
    session_id: str
    inputs: dict[str, Any] = {}


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    trigger_command: str | None
    definition_str: str
    owner_id: str
    owner_name: str | None = None
    visibility: str
    status: str
    created_at: str
    updated_at: str

    @classmethod
    def from_orm(cls, skill: Skill) -> SkillResponse:
        return cls(
            id=str(skill.id),
            name=skill.name,
            description=skill.description,
            trigger_command=skill.trigger_command,
            definition_str=skill.definition_str,
            owner_id=str(skill.owner_id),
            owner_name=skill.owner.name if skill.owner else None,
            visibility=skill.visibility,
            status=skill.status,
            created_at=skill.created_at.isoformat() if skill.created_at else "",
            updated_at=skill.updated_at.isoformat() if skill.updated_at else "",
        )


class SkillListResponse(BaseModel):
    skills: list[SkillResponse]


class SkillExecutionResponse(BaseModel):
    id: str
    skill_id: str
    skill_name: str | None = None
    session_id: str
    inputs: str | None
    output: str | None
    status: str
    created_at: str
    completed_at: str | None


# ── Routes ───────────────────────────────────────────────────────────


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    body: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Create a new skill (called from chat via the agent)."""
    # Validate trigger_command uniqueness per user
    if body.trigger_command:
        existing = await db.execute(
            select(Skill).where(
                Skill.trigger_command == body.trigger_command,
                Skill.owner_id == current_user.id,
                Skill.visibility == "private",
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A skill with trigger command '{body.trigger_command}' already exists.",
            )

    skill = Skill(
        id=uuid.uuid4(),
        name=body.name,
        description=body.description,
        trigger_command=body.trigger_command,
        definition_str=body.definition_str,
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
        visibility="private",
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(skill)
    await db.flush()

    # Audit log
    audit = AgentAuditLogger(db)
    await audit.log(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action_type="skill.created",
        resource_type="skill",
        resource_id=str(skill.id),
        details=json.dumps({"name": skill.name, "trigger_command": skill.trigger_command}),
    )

    return SkillResponse.from_orm(skill)


@router.get("", response_model=SkillListResponse)
async def list_skills(
    scope: str = Query("mine", description="mine | marketplace | all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillListResponse:
    """List skills — user's own, marketplace, or all accessible."""
    query = select(Skill)

    if scope == "mine":
        query = query.where(Skill.owner_id == current_user.id)
    elif scope == "marketplace":
        query = query.where(Skill.visibility == "marketplace", Skill.status == "approved")
    else:
        # "all" — user's own + marketplace available to them
        query = query.where(
            or_(
                Skill.owner_id == current_user.id,
                Skill.visibility == "marketplace",
            )
        )

    query = query.order_by(Skill.updated_at.desc()).limit(100)
    result = await db.execute(query)
    skills = list(result.scalars().all())

    return SkillListResponse(skills=[SkillResponse.from_orm(s) for s in skills])


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Get a single skill by ID."""
    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill ID.")

    result = await db.execute(select(Skill).where(Skill.id == sid))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

    # Access check: private skills only visible to owner, marketplace skills visible to all
    if skill.visibility == "private" and skill.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your skill.")

    return SkillResponse.from_orm(skill)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    body: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Update a skill (owner only)."""
    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill ID.")

    result = await db.execute(select(Skill).where(Skill.id == sid))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    if skill.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can edit this skill.")

    # Update fields
    if body.name is not None:
        skill.name = body.name
    if body.description is not None:
        skill.description = body.description
    if body.trigger_command is not None:
        skill.trigger_command = body.trigger_command
    if body.definition_str is not None:
        skill.definition_str = body.definition_str
    skill.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return SkillResponse.from_orm(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a skill (owner only)."""
    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill ID.")

    result = await db.execute(select(Skill).where(Skill.id == sid))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    if skill.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete this skill.")

    await db.delete(skill)
    await db.flush()


@router.post("/{skill_id}/submit", response_model=SkillResponse)
async def submit_to_marketplace(
    skill_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Submit a skill to the marketplace for review."""
    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill ID.")

    result = await db.execute(select(Skill).where(Skill.id == sid))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")
    if skill.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can submit.")

    skill.visibility = "marketplace"
    skill.status = "under_review"
    skill.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return SkillResponse.from_orm(skill)


@router.post("/{skill_id}/review", response_model=SkillResponse)
async def review_skill(
    skill_id: str,
    body: SkillReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillResponse:
    """Approve or reject a marketplace submission (managers/admins only)."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only managers and admins can review skills.")

    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill ID.")

    result = await db.execute(select(Skill).where(Skill.id == sid))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

    if body.action == "approve":
        skill.status = "approved"
    elif body.action == "reject":
        skill.status = "rejected"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be 'approve' or 'reject'.")

    skill.review_notes = body.notes
    skill.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return SkillResponse.from_orm(skill)


@router.post("/{skill_id}/execute", response_model=SkillExecutionResponse)
async def execute_skill(
    skill_id: str,
    body: SkillExecute,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SkillExecutionResponse:
    """Execute a skill — the agent runs through the skill's definition steps.
    
    This creates an execution record and returns immediately. The actual
    execution happens via the chat endpoint (the skill definition is
    injected as context for the agent).
    """
    try:
        sid = uuid.UUID(skill_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid skill ID.")

    result = await db.execute(select(Skill).where(Skill.id == sid))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found.")

    # Create execution record
    try:
        session_uuid = uuid.UUID(body.session_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session_id.")

    execution = SkillExecution(
        id=uuid.uuid4(),
        skill_id=skill.id,
        session_id=session_uuid,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        inputs=json.dumps(body.inputs),
        status="completed",
        created_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(execution)
    await db.flush()

    # For now, the execution output is the skill's definition (the agent uses it as context)
    execution.output = f"Executing skill: {skill.name}\n\n{skill.definition_str}"
    await db.flush()

    return SkillExecutionResponse(
        id=str(execution.id),
        skill_id=str(execution.skill_id),
        skill_name=skill.name,
        session_id=str(execution.session_id),
        inputs=execution.inputs,
        output=execution.output,
        status=execution.status,
        created_at=execution.created_at.isoformat(),
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
    )


@router.get("/executions/list", response_model=list[SkillExecutionResponse])
async def list_executions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SkillExecutionResponse]:
    """List the current user's skill executions."""
    result = await db.execute(
        select(SkillExecution)
        .where(SkillExecution.user_id == current_user.id)
        .order_by(SkillExecution.created_at.desc())
        .limit(50)
    )
    executions = list(result.scalars().all())

    responses = []
    for exec_ in executions:
        responses.append(SkillExecutionResponse(
            id=str(exec_.id),
            skill_id=str(exec_.skill_id),
            skill_name=exec_.skill.name if exec_.skill else None,
            session_id=str(exec_.session_id),
            inputs=exec_.inputs,
            output=exec_.output,
            status=exec_.status,
            created_at=exec_.created_at.isoformat(),
            completed_at=exec_.completed_at.isoformat() if exec_.completed_at else None,
        ))
    return responses
