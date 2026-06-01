"""Documents API — render workflow outputs as downloadable PDF/DOCX."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.workflow import Workflow, WorkflowRun, WorkflowTaskRun
from src.app.services.document_generator import (
    render_document,
    workflow_output_to_sections,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/render/{run_id}")
async def render_workflow_document(
    run_id: str,
    format: str = Query("pdf", pattern="^(pdf|docx)$"),
    title: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Render a completed workflow run's results as a downloadable document.

    Args:
        run_id: UUID of the workflow run
        format: Output format — ``pdf`` (default) or ``docx``
        title: Optional document title (defaults to workflow name)

    Returns:
        A streaming download of the rendered document.
    """
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid run_id format.",
        )

    # Fetch the run
    result = await db.execute(
        select(WorkflowRun).where(WorkflowRun.id == rid)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    if run.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your run.")

    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot render document: run status is '{run.status}'. "
                   f"Only completed runs can be rendered.",
        )

    # Fetch workflow for name and definition
    wf_result = await db.execute(
        select(Workflow).where(Workflow.id == run.workflow_id)
    )
    wf = wf_result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    # Parse workflow definition for output descriptions
    output_defs: list[str] = []
    try:
        definition = json.loads(wf.definition)
        for t in definition.get("tasks", []):
            task_outputs = t.get("outputs", {})
            for key, val in task_outputs.items():
                output_defs.append(f"**{key}**: {val}")
    except (json.JSONDecodeError, TypeError):
        pass

    # Fetch task runs
    tr_result = await db.execute(
        select(WorkflowTaskRun).where(
            WorkflowTaskRun.run_id == rid,
        ).order_by(WorkflowTaskRun.created_at)
    )
    task_runs = list(tr_result.scalars().all())

    # Build task_results dict
    task_results: dict = {}
    for tr in task_runs:
        if tr.output_data:
            try:
                task_results[tr.task_id] = json.loads(tr.output_data)
            except (json.JSONDecodeError, TypeError):
                task_results[tr.task_id] = {"result": tr.output_data}

    doc_title = title or f"{wf.name} — Flow Report"
    sections = workflow_output_to_sections(doc_title, task_results, output_defs)

    content, filename, mime = render_document(
        title=doc_title,
        sections=sections,
        format=format,
        author=current_user.name or current_user.email,
    )

    return Response(
        content=content,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )
