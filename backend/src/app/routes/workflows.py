"""Workflow API routes — compile, CRUD, execute, and human checkpoints."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.llm_key import LLMKey
from src.app.models.workflow import Workflow, WorkflowRun, WorkflowTaskRun
from src.app.agent import LLMRouter, AgentAuditLogger
from src.app.routes.agent import _get_active_llm_key

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# ── Schemas ──────────────────────────────────────────────────────────


class CompileRequest(BaseModel):
    description: str
    name: str | None = None


class CompileResponse(BaseModel):
    name: str
    definition: dict
    raw_response: str | None = None


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    trigger: str = "chat"
    definition: dict


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger: str | None = None
    definition: dict | None = None
    status: str | None = None


class CheckpointDecision(BaseModel):
    approved: bool
    feedback: str | None = None


# ── Response helpers ────────────────────────────────────────────────


def _wf_to_dict(wf: Workflow) -> dict:
    return {
        "id": str(wf.id),
        "name": wf.name,
        "description": wf.description,
        "trigger": wf.trigger,
        "definition": json.loads(wf.definition) if wf.definition else {},
        "source_text": wf.source_text,
        "status": wf.status,
        "owner_id": str(wf.owner_id),
        "owner_name": wf.owner.name if wf.owner else None,
        "created_at": wf.created_at.isoformat() if wf.created_at else "",
        "updated_at": wf.updated_at.isoformat() if wf.updated_at else "",
    }


def _run_to_dict(run: WorkflowRun) -> dict:
    return {
        "id": str(run.id),
        "workflow_id": str(run.workflow_id),
        "user_id": str(run.user_id),
        "status": run.status,
        "current_task_id": run.current_task_id,
        "result": run.result,
        "error": run.error,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "created_at": run.created_at.isoformat() if run.created_at else "",
        "task_runs": [_task_to_dict(t) for t in (run.task_runs or [])],
    }


def _task_to_dict(task: WorkflowTaskRun) -> dict:
    return {
        "id": str(task.id),
        "run_id": str(task.run_id),
        "task_id": task.task_id,
        "skill_name": task.skill_name,
        "task_type": task.task_type,
        "status": task.status,
        "input_data": json.loads(task.input_data) if task.input_data else None,
        "output_data": json.loads(task.output_data) if task.output_data else None,
        "feedback": task.feedback,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


# ── Compile ──────────────────────────────────────────────────────────

WORKFLOW_COMPILER_SYSTEM = """You are a workflow compiler for the Flow platform. Your job is to take a user's process description and convert it into a structured workflow definition.

The workflow definition must follow this JSON schema:
{
  "name": "string — short name for the workflow",
  "trigger": "chat",
  "tasks": [
    {
      "id": "task_1, task_2, ... (unique ID string)",
      "type": "skill" or "human_approval",
      "skill": "string — name of the skill to execute (only for skill type)",
      "description": "string — what this task does",
      "depends_on": ["task_id_1", ...],  // task IDs this depends on (empty for first task)
      "inputs": {
        "key": "value or {{task_X.output_key}} reference"
      },
      "outputs": {
        "key": "type description"
      },
      "assignee": "requestor" // only for human_approval tasks
    }
  ],
  "checkpoints": [
    {
      "task_id": "task_X",
      "on_approve": "what happens next on approval",
      "on_reject": "what happens on rejection (e.g. return_to_task_X_with_feedback)"
    }
  ]
}

Rules:
1. Break the user's process into sequential tasks
2. Each task should reference an existing skill or a reasonable skill name
3. Use human_approval tasks for any decision points or QA steps
4. Express data flow between tasks using {{task_X.output_key}} references in inputs
5. Dependencies define task ordering — task_1 has no dependencies, later tasks depend on previous ones
6. Keep it simple — don't add unnecessary complexity
7. Output ONLY valid JSON, no markdown, no code fences, no commentary

Analyse the following process description and output the workflow definition as pure JSON:"""


@router.post("/compile", response_model=CompileResponse)
async def compile_workflow(
    body: CompileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompileResponse:
    """Take a process description and compile it into a structured workflow definition."""
    # Get LLM key
    llm_key = await _get_active_llm_key(db, current_user.tenant_id)
    if llm_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active LLM key configured. Please add an API key in settings.",
        )

    llm_router = LLMRouter(llm_key)

    # Build the compile prompt
    user_prompt = body.description
    if body.name:
        user_prompt = f"Workflow name: {body.name}\n\n{body.description}"

    messages = [
        {"role": "system", "content": WORKFLOW_COMPILER_SYSTEM},
        {"role": "user", "content": user_prompt},
    ]

    try:
        raw_response = await llm_router.chat(messages, max_tokens=4096, temperature=0.3)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM compilation failed: {e}",
        )

    # Parse the response — try to extract JSON
    stripped = raw_response.strip()
    # Remove code fences if present
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Find the first ``` and last ```
        fence_start = -1
        fence_end = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("```") and fence_start == -1:
                fence_start = i
            elif line.strip().startswith("```") and fence_start > -1:
                fence_end = i
                break
        if fence_end > fence_start:
            stripped = "\n".join(lines[fence_start + 1 : fence_end])
        elif fence_start > -1:
            stripped = "\n".join(lines[fence_start + 1 :])

    stripped = stripped.strip()

    # Parse JSON
    try:
        definition = json.loads(stripped)
    except json.JSONDecodeError:
        # Try to find JSON block within the response
        import re
        match = re.search(r"\{[\s\S]*\}", stripped)
        if match:
            try:
                definition = json.loads(match.group())
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Could not parse LLM response as JSON. Raw: {raw_response[:500]}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not parse LLM response as JSON. Raw: {raw_response[:500]}",
            )

    # Ensure required fields
    if "name" not in definition:
        definition["name"] = body.name or "Unnamed Workflow"
    if "tasks" not in definition:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="LLM response missing 'tasks' array.",
        )

    return CompileResponse(
        name=definition.get("name", body.name or "Unnamed Workflow"),
        definition=definition,
        raw_response=raw_response,
    )


# ── CRUD ─────────────────────────────────────────────────────────────


@router.get("")
async def list_workflows(
    scope: str = Query("mine", description="mine | active | archived"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List the current user's workflows."""
    query = select(Workflow).where(Workflow.owner_id == current_user.id)

    if scope == "active":
        query = query.where(Workflow.status == "active")
    elif scope == "archived":
        query = query.where(Workflow.status == "archived")
    else:
        query = query.where(Workflow.status.in_(["draft", "active"]))

    query = query.order_by(Workflow.updated_at.desc()).limit(50)
    result = await db.execute(query)
    workflows = list(result.scalars().all())

    return {"workflows": [_wf_to_dict(w) for w in workflows]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Save a new workflow (from compiled definition or manual creation)."""
    wf = Workflow(
        id=uuid.uuid4(),
        name=body.name,
        description=body.description,
        trigger=body.trigger,
        definition=json.dumps(body.definition),
        source_text=None,
        status="active",
        owner_id=current_user.id,
        tenant_id=current_user.tenant_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(wf)

    # Audit log
    audit = AgentAuditLogger(db)
    await audit.log(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action_type="workflow.created",
        resource_type="workflow",
        resource_id=str(wf.id),
        details=json.dumps({"name": wf.name}),
    )

    await db.flush()
    return _wf_to_dict(wf)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single workflow with its details."""
    try:
        wid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID.")

    result = await db.execute(select(Workflow).where(Workflow.id == wid))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    if wf.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workflow.")

    return _wf_to_dict(wf)


@router.patch("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a workflow's details."""
    try:
        wid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID.")

    result = await db.execute(select(Workflow).where(Workflow.id == wid))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    if wf.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workflow.")

    if body.name is not None:
        wf.name = body.name
    if body.description is not None:
        wf.description = body.description
    if body.trigger is not None:
        wf.trigger = body.trigger
    if body.definition is not None:
        wf.definition = json.dumps(body.definition)
    if body.status is not None:
        wf.status = body.status
    wf.updated_at = datetime.now(timezone.utc)
    await db.flush()

    return _wf_to_dict(wf)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Archive a workflow (soft delete — sets status to 'archived')."""
    try:
        wid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID.")

    result = await db.execute(select(Workflow).where(Workflow.id == wid))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    if wf.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workflow.")

    wf.status = "archived"
    wf.updated_at = datetime.now(timezone.utc)
    await db.flush()


# ── Run & Execution ──────────────────────────────────────────────────


@router.post("/{workflow_id}/run", status_code=status.HTTP_201_CREATED)
async def run_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Execute a workflow — creates a run and begins executing tasks."""
    try:
        wid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID.")

    result = await db.execute(select(Workflow).where(Workflow.id == wid))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    if wf.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workflow.")

    # Parse the definition
    try:
        definition = json.loads(wf.definition)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Workflow definition is invalid JSON.")

    tasks = definition.get("tasks", [])
    if not tasks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow has no tasks.")

    # Create the run
    now = datetime.now(timezone.utc)
    run = WorkflowRun(
        id=uuid.uuid4(),
        workflow_id=wf.id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        status="running",
        started_at=now,
        created_at=now,
    )
    db.add(run)

    # Create task runs for all tasks
    for task_def in tasks:
        task_run = WorkflowTaskRun(
            id=uuid.uuid4(),
            run_id=run.id,
            task_id=task_def.get("id", f"task_{tasks.index(task_def) + 1}"),
            skill_name=task_def.get("skill"),
            task_type=task_def.get("type", "skill"),
            status="pending",
            input_data=json.dumps(task_def.get("inputs", {})),
        )
        db.add(task_run)

    await db.flush()

    # ── Execute step-by-step ──────────────────────────────────────
    # Resolve and execute tasks in dependency order
    executed = set()
    task_run_map = {}
    # Reload task runs with their IDs
    result = await db.execute(
        select(WorkflowTaskRun).where(
            WorkflowTaskRun.run_id == run.id
        ).order_by(WorkflowTaskRun.created_at)
    )
    task_runs = list(result.scalars().all())
    for tr in task_runs:
        task_run_map[tr.task_id] = tr

    # Find the task def for each task run
    task_def_map = {}
    for t in tasks:
        task_def_map[t.get("id")] = t

    max_iterations = 50
    iteration = 0
    all_completed = False

    while not all_completed and iteration < max_iterations:
        iteration += 1
        all_completed = True

        for tr in task_runs:
            if tr.task_id in executed or tr.status in ("completed", "failed", "skipped", "waiting_for_approval"):
                continue

            task_def = task_def_map.get(tr.task_id)
            if not task_def:
                tr.status = "failed"
                tr.output_data = json.dumps({"error": "Task definition not found"})
                await db.flush()
                continue

            # Check dependencies
            depends_on = task_def.get("depends_on", [])
            deps_met = all(dep in executed for dep in depends_on)

            if not deps_met:
                all_completed = False
                continue  # Wait for dependencies

            all_completed = False

            # Execute the task
            tr.status = "running"
            tr.started_at = datetime.now(timezone.utc)
            await db.flush()

            # Resolve inputs (replace {{references}})
            resolved_inputs = {}
            raw_inputs = task_def.get("inputs", {})
            for key, value in raw_inputs.items():
                if isinstance(value, str) and "{{" in value:
                    resolved = value
                    for dep_task_id in depends_on:
                        dep_task_run = task_run_map.get(dep_task_id)
                        if dep_task_run and dep_task_run.output_data:
                            try:
                                dep_output = json.loads(dep_task_run.output_data)
                                for out_key, out_val in (dep_output or {}).items():
                                    resolved = resolved.replace(f"{{{{{dep_task_id}.{out_key}}}}}", str(out_val))
                                    resolved = resolved.replace(f"{{{{task.{out_key}}}}}", str(out_val))
                            except (json.JSONDecodeError, TypeError):
                                pass
                    resolved_inputs[key] = resolved
                else:
                    resolved_inputs[key] = value

            tr.input_data = json.dumps(resolved_inputs)

            # Handle human approval tasks
            if tr.task_type == "human_approval":
                tr.status = "waiting_for_approval"
                run.current_task_id = tr.task_id
                run.status = "paused"
                await db.flush()

                # Audit — paused for human checkpoint
                audit = AgentAuditLogger(db)
                await audit.log(
                    tenant_id=current_user.tenant_id,
                    actor_id=current_user.id,
                    action_type="workflow.checkpoint_paused",
                    resource_type="workflow_run",
                    resource_id=str(run.id),
                    details=json.dumps({"task_id": tr.task_id, "skill": tr.skill_name}),
                )
                return _run_to_dict(run)

            # For skill-type tasks, simulate execution (v1 — agent will handle actual skill calls)
            # In a real scenario, this would call the skill execution engine
            tr.output_data = json.dumps({
                "status": "completed",
                "summary": f"Executed {tr.skill_name} with inputs: {resolved_inputs}",
                "result": f"Output from {tr.skill_name} completed successfully.",
            })
            tr.status = "completed"
            tr.completed_at = datetime.now(timezone.utc)
            executed.add(tr.task_id)
            await db.flush()

    # Check if we hit a checkpoint that paused
    run_with_tasks = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run.id))
    run = run_with_tasks.scalar_one_or_none()

    if run and run.status == "paused":
        return _run_to_dict(run)

    # All done (or failed)
    if run:
        run.completed_at = datetime.now(timezone.utc)
        run.status = "completed"
        run.result = json.dumps({"summary": "Workflow completed successfully."})
        await db.flush()

        audit = AgentAuditLogger(db)
        await audit.log(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            action_type="workflow.completed",
            resource_type="workflow_run",
            resource_id=str(run.id),
            details=json.dumps({"status": "completed", "workflow": wf.name}),
        )

    return _run_to_dict(run)


@router.get("/{workflow_id}/runs")
async def list_runs(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all runs for a workflow."""
    try:
        wid = uuid.UUID(workflow_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID.")

    result = await db.execute(select(Workflow).where(Workflow.id == wid))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    if wf.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workflow.")

    result = await db.execute(
        select(WorkflowRun).where(
            WorkflowRun.workflow_id == wid
        ).order_by(WorkflowRun.created_at.desc()).limit(20)
    )
    runs = list(result.scalars().all())

    return {"runs": [_run_to_dict(r) for r in runs]}


# ── Run details & checkpoints ─────────────────────────────────────────


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a single workflow run with full task execution trace."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid run ID.")

    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == rid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your run.")

    return _run_to_dict(run)


@router.post("/runs/{run_id}/checkpoint")
async def handle_checkpoint(
    run_id: str,
    body: CheckpointDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle a human checkpoint decision (approve or reject with feedback)."""
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid run ID.")

    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == rid))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.")

    if run.status != "paused":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run is not paused at a checkpoint.")

    # Find the checkpoint task
    checkpoint_task_id = run.current_task_id
    if not checkpoint_task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No checkpoint task found.")

    result = await db.execute(
        select(WorkflowTaskRun).where(
            WorkflowTaskRun.run_id == run.id,
            WorkflowTaskRun.task_id == checkpoint_task_id,
        )
    )
    task_run = result.scalar_one_or_none()
    if not task_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkpoint task not found.")

    # Record checkpoint decision
    now = datetime.now(timezone.utc)
    task_run.completed_at = now
    task_run.feedback = body.feedback
    task_run.output_data = json.dumps({
        "approved": body.approved,
        "feedback": body.feedback,
    })

    # Audit log
    audit = AgentAuditLogger(db)
    await audit.log(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        action_type="workflow.checkpoint_decision",
        resource_type="workflow_run",
        resource_id=str(run.id),
        details=json.dumps({
            "task_id": checkpoint_task_id,
            "approved": body.approved,
            "feedback": body.feedback,
        }),
    )

    if body.approved:
        task_run.status = "completed"

        # Resume the workflow — execute remaining tasks
        run.status = "running"
        run.current_task_id = None
        await db.flush()

        # Get workflow definition to continue execution
        wf_result = await db.execute(select(Workflow).where(Workflow.id == run.workflow_id))
        wf = wf_result.scalar_one_or_none()
        if not wf:
            run.status = "failed"
            run.error = "Workflow deleted during run."
            await db.flush()
            return _run_to_dict(run)

        definition = json.loads(wf.definition)
        tasks = definition.get("tasks", [])

        # Get all task runs for this run
        result = await db.execute(
            select(WorkflowTaskRun).where(
                WorkflowTaskRun.run_id == run.id
            ).order_by(WorkflowTaskRun.created_at)
        )
        task_runs = list(result.scalars().all())
        task_run_map = {tr.task_id: tr for tr in task_runs}

        # Mark checkpoint task as executed
        executed = {tr.task_id for tr in task_runs if tr.status == "completed"}

        max_iterations = 50
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            progressed = False

            for tr in task_runs:
                if tr.task_id in executed or tr.status in ("completed", "failed", "skipped", "waiting_for_approval"):
                    continue

                task_def = None
                for t in tasks:
                    if t.get("id") == tr.task_id:
                        task_def = t
                        break
                if not task_def:
                    tr.status = "failed"
                    await db.flush()
                    continue

                depends_on = task_def.get("depends_on", [])
                deps_met = all(dep in executed for dep in depends_on)
                if not deps_met:
                    continue

                progressed = True
                tr.status = "running"
                tr.started_at = datetime.now(timezone.utc)
                await db.flush()

                # Resolve inputs
                resolved_inputs = {}
                raw_inputs = task_def.get("inputs", {})
                for key, value in raw_inputs.items():
                    if isinstance(value, str) and "{{" in value:
                        resolved = value
                        for dep_task_id in depends_on:
                            dep_tr = task_run_map.get(dep_task_id)
                            if dep_tr and dep_tr.output_data:
                                try:
                                    dep_output = json.loads(dep_tr.output_data)
                                    for out_key, out_val in (dep_output or {}).items():
                                        resolved = resolved.replace(f"{{{{{dep_task_id}.{out_key}}}}}", str(out_val))
                                except (json.JSONDecodeError, TypeError):
                                    pass
                        resolved_inputs[key] = resolved
                    else:
                        resolved_inputs[key] = value

                tr.input_data = json.dumps(resolved_inputs)

                # Handle human approval tasks
                if tr.task_type == "human_approval":
                    tr.status = "waiting_for_approval"
                    run.current_task_id = tr.task_id
                    run.status = "paused"
                    await db.flush()
                    return _run_to_dict(run)

                # Execute skill task
                tr.output_data = json.dumps({
                    "status": "completed",
                    "summary": f"Executed {tr.skill_name} with inputs: {resolved_inputs}",
                    "result": f"Output from {tr.skill_name}.",
                })
                tr.status = "completed"
                tr.completed_at = datetime.now(timezone.utc)
                executed.add(tr.task_id)
                await db.flush()

            if not progressed:
                break

        # All tasks processed
        run.completed_at = datetime.now(timezone.utc)
        run.status = "completed"
        run.result = json.dumps({"summary": "Workflow completed successfully."})
        await db.flush()

        await audit.log(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            action_type="workflow.completed",
            resource_type="workflow_run",
            resource_id=str(run.id),
            details=json.dumps({"status": "completed", "approved": True}),
        )

        return _run_to_dict(run)

    else:
        # Rejected
        task_run.status = "failed"
        run.status = "failed"
        run.error = body.feedback or "Rejected by user"
        run.completed_at = now
        run.current_task_id = None
        await db.flush()

        return _run_to_dict(run)
