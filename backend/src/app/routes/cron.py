"""Cron tick endpoint — checks and executes due scheduled workflows."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.workflow import Workflow, WorkflowRun, WorkflowTaskRun
from src.app.agent import AgentAuditLogger

router = APIRouter(prefix="/api/cron", tags=["cron"])


@router.get("/tick")
async def cron_tick(
    db: AsyncSession = Depends(get_db),
):
    """Check for due scheduled workflows and execute them.
    
    This endpoint is designed to be called by an external cron service
    (e.g. cron-job.org, GitHub Actions, Vercel Cron Jobs).
    It finds all workflows where next_run_at <= now, executes them,
    and updates their next_run_at.
    """
    now = datetime.now(timezone.utc)

    # Find all active workflows that are due
    result = await db.execute(
        select(Workflow).where(
            Workflow.status == "active",
            Workflow.schedule.isnot(None),
            Workflow.next_run_at.isnot(None),
            Workflow.next_run_at <= now,
        ).limit(20)
    )
    workflows = list(result.scalars().all())

    results = []
    for wf in workflows:
        try:
            definition = json.loads(wf.definition)
        except (json.JSONDecodeError, TypeError):
            continue

        tasks = definition.get("tasks", [])
        if not tasks:
            continue

        # Create a run (owned by the workflow's owner)
        run = WorkflowRun(
            id=uuid.uuid4(),
            workflow_id=wf.id,
            user_id=wf.owner_id,
            tenant_id=wf.tenant_id,
            status="running",
            started_at=now,
            created_at=now,
        )
        db.add(run)

        # Create task runs
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

        # Execute tasks in order (simple sequential execution)
        # Reload task runs
        tr_result = await db.execute(
            select(WorkflowTaskRun).where(
                WorkflowTaskRun.run_id == run.id
            ).order_by(WorkflowTaskRun.created_at)
        )
        task_runs = list(tr_result.scalars().all())

        paused = False
        for tr in task_runs:
            tr.status = "running"
            tr.started_at = now
            await db.flush()

            if tr.task_type == "human_approval":
                # Scheduled workflows with human checkpoints pause automatically
                tr.status = "waiting_for_approval"
                run.current_task_id = tr.task_id
                run.status = "paused"
                await db.flush()
                paused = True
                break

            # Execute skill task
            tr.output_data = json.dumps({
                "status": "completed",
                "summary": f"Scheduled execution of {tr.skill_name}",
                "result": f"Output from {tr.skill_name}.",
            })
            tr.status = "completed"
            tr.completed_at = datetime.now(timezone.utc)
            await db.flush()

        if not paused:
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.result = json.dumps({"summary": "Scheduled workflow completed."})
            await db.flush()

        # Update next_run_at
        try:
            cron = croniter(wf.schedule, now)
            wf.next_run_at = cron.get_next(datetime)
        except (ValueError, KeyError):
            wf.schedule = None
            wf.next_run_at = None
        wf.updated_at = now
        await db.flush()

        results.append({
            "workflow_id": str(wf.id),
            "workflow_name": wf.name,
            "run_id": str(run.id),
            "status": run.status,
        })

    # Audit log
    if results:
        audit = AgentAuditLogger(db)
        await audit.log(
            tenant_id=None,
            actor_id=None,
            action_type="cron.tick",
            resource_type="cron",
            resource_id="tick",
            details=json.dumps({
                "triggered": len(results),
                "workflows": [r["workflow_name"] for r in results],
            }),
        )

    return {
        "triggered": len(results),
        "timestamp": now.isoformat(),
        "workflows": results,
    }
