"""Agent tools for workflow execution and human-in-the-loop checkpoints."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.agent.tools import Tool
from src.app.models.workflow import Workflow


class ListWorkflows(Tool):
    """List the user's saved workflows and their current status."""

    name: str = "list_workflows"
    description: str = (
        "List all workflows the current user has created. "
        "Returns workflow names, descriptions, statuses, and trigger types. "
        "Use this when the user asks 'what workflows do I have?' or wants to see available automated processes."
    )
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id

    async def execute(self, **kwargs: Any) -> str:
        if not self._db or not self._user_id:
            return "Error: Database not available."

        result = await self._db.execute(
            select(Workflow)
            .where(
                Workflow.owner_id == self._user_id,
                Workflow.status.in_(["draft", "active"]),
            )
            .order_by(Workflow.updated_at.desc())
            .limit(50)
        )
        workflows = list(result.scalars().all())

        if not workflows:
            return (
                "You don't have any workflows yet. Describe a process and I can compile one for you! "
                "Or use the Workflows page to build one."
            )

        lines = [f"Your workflows ({len(workflows)}):\n"]
        for wf in workflows:
            import json
            try:
                definition = json.loads(wf.definition)
                task_count = len(definition.get("tasks", []))
            except (json.JSONDecodeError, TypeError):
                task_count = 0
            import re
            wf_id_short = str(wf.id)[:8]
            schedule_info = f" (scheduled: {wf.schedule})" if wf.schedule else ""
            lines.append(
                f"  • **{wf.name}** — {task_count} tasks, status: {wf.status}, "
                f"trigger: {wf.trigger}{schedule_info}\n"
                f"    ID: `{wf_id_short}...`\n"
                f"    {wf.description or 'No description'}\n"
            )

        return "\n".join(lines)


class RunWorkflow(Tool):
    """Run a workflow by ID. Returns real-time progress including checkpoint status and final outputs."""

    name: str = "run_workflow"
    description: str = (
        "Execute a workflow by its ID. The workflow runs step-by-step. "
        "If it hits a human approval checkpoint, it pauses and reports back so the user can decide. "
        "If it completes, it returns the final outputs (documents, reports, results). "
        "Call this when the user says 'run this workflow' or 'execute workflow X'. "
        "Use list_workflows first to find the workflow ID if the user doesn't provide it."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "workflow_id": {
                "type": "string",
                "description": "The UUID of the workflow to run. Can be full UUID or first 8 characters (partial match).",
            },
        },
        "required": ["workflow_id"],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id

    async def execute(self, **kwargs: Any) -> str:
        raw_id = kwargs.get("workflow_id", "").strip()
        if not raw_id:
            return "Error: 'workflow_id' is required."

        if not self._db or not self._user_id:
            return "Error: Database not available."

        # Resolve workflow ID (full UUID or partial match)
        wid: uuid.UUID | None = None
        try:
            wid = uuid.UUID(raw_id)
        except ValueError:
            # Partial match — check first 8 chars
            result = await self._db.execute(
                select(Workflow).where(
                    Workflow.owner_id == self._user_id,
                    Workflow.status.in_(["draft", "active"]),
                )
            )
            for wf in list(result.scalars().all()):
                if str(wf.id).startswith(raw_id):
                    wid = wf.id
                    break

        if wid is None:
            return (
                f"Workflow '{raw_id}' not found. "
                f"Use list_workflows to see your available workflows and their IDs."
            )

        try:
            from src.app.routes.workflows import run_workflow_internal
            run_result = await run_workflow_internal(wid, self._user_id, self._db)
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error running workflow: {e}"

        return self._format_run_result(run_result)

    def _format_run_result(self, run: dict) -> str:
        """Format a run dict into a human-readable string."""
        status = run.get("status", "unknown")
        run_id_short = str(run.get("id", ""))[:8]
        workflow_id_short = str(run.get("workflow_id", ""))[:8]

        if status == "paused":
            # Find the checkpoint task
            task_runs = run.get("task_runs", [])
            checkpoint = None
            for tr in task_runs:
                if tr.get("status") == "waiting_for_approval":
                    checkpoint = tr
                    break

            paused_text = (
                f"⏸️ **Workflow paused — needs your approval**\n\n"
                f"Run: `{run_id_short}...`\n"
                f"Status: paused at a human checkpoint\n\n"
            )

            if checkpoint:
                paused_text += (
                    f"**Checkpoint task:** {checkpoint.get('skill_name', checkpoint.get('task_id', 'Unknown'))}\n"
                    f"**Description:** {checkpoint.get('task_id', '')}\n\n"
                    f"Say **'approve'** to continue, or **'reject <reason>'** to stop with feedback."
                )
            else:
                paused_text += "The workflow is paused for approval. Say **'approve'** to continue."

            return paused_text

        elif status == "completed":
            completed_text = (
                f"✅ **Workflow completed successfully!**\n\n"
                f"Run: `{run_id_short}...`\n"
                f"Status: completed\n"
            )

            # Include outputs if available
            result_raw = run.get("result")
            if result_raw:
                import json
                try:
                    result_data = json.loads(result_raw)
                    outputs = result_data.get("outputs", [])
                    if outputs:
                        completed_text += "\n**Outputs produced:**\n" + "\n".join(outputs) + "\n"
                    task_results = result_data.get("task_results", {})
                    if task_results:
                        completed_text += "\n**Task details:**\n"
                        for task_id, output in task_results.items():
                            status_val = output.get("status", "done")
                            summary = output.get("summary", "")
                            result_val = output.get("result", "")
                            completed_text += f"  • `{task_id}` → {status_val}: {summary}\n"
                            if result_val and result_val != summary:
                                completed_text += f"    Result: {result_val}\n"
                except (json.JSONDecodeError, TypeError):
                    completed_text += f"\nResult: {result_raw[:500]}"

            return completed_text

        elif status == "failed":
            return (
                f"❌ **Workflow failed**\n\n"
                f"Run: `{run_id_short}...`\n"
                f"Error: {run.get('error', 'Unknown error')}"
            )

        elif status == "running":
            return (
                f"🔄 **Workflow running...**\n\n"
                f"Run: `{run_id_short}...`\n"
                f"Status: in progress"
            )

        else:
            return (
                f"**Workflow run status:** {status}\n"
                f"Run: `{run_id_short}...`"
            )


class GetWorkflowRunStatus(Tool):
    """Check the current status of a workflow run. Useful after a run is started asynchronously."""

    name: str = "get_workflow_run_status"
    description: str = (
        "Check the current status of a workflow run by its run ID. "
        "Use this when the user wants to know if their workflow finished, "
        "or to re-check a run that was paused for approval."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "The UUID of the workflow run to check.",
            },
        },
        "required": ["run_id"],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id

    async def execute(self, **kwargs: Any) -> str:
        raw_id = kwargs.get("run_id", "").strip()
        if not raw_id:
            return "Error: 'run_id' is required."

        if not self._db or not self._user_id:
            return "Error: Database not available."

        try:
            rid = uuid.UUID(raw_id)
        except ValueError:
            return "Error: Invalid run_id format."

        from src.app.models.workflow import WorkflowRun, WorkflowTaskRun

        result = await self._db.execute(
            select(WorkflowRun).where(WorkflowRun.id == rid)
        )
        run = result.scalar_one_or_none()
        if not run:
            return f"Run `{raw_id[:8]}...` not found."
        if run.user_id != self._user_id:
            return "Error: Not your run."

        result = await self._db.execute(
            select(WorkflowTaskRun).where(
                WorkflowTaskRun.run_id == rid,
            ).order_by(WorkflowTaskRun.created_at)
        )
        task_runs = list(result.scalars().all())

        from src.app.routes.workflows import _run_to_dict
        run_dict = _run_to_dict(run, task_runs)
        return RunWorkflow._format_run_result(RunWorkflow, run_dict)


class ApproveCheckpoint(Tool):
    """Approve a paused workflow checkpoint. The workflow resumes and continues executing."""

    name: str = "approve_checkpoint"
    description: str = (
        "Approve a workflow run that is paused at a human checkpoint. "
        "The workflow resumes and continues executing remaining tasks. "
        "Optionally provide feedback that will be recorded in the audit log. "
        "Call this when the user says 'approve', 'yes go ahead', 'continue', etc. "
        "after a workflow paused for human approval."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "The UUID of the paused workflow run.",
            },
            "feedback": {
                "type": "string",
                "description": "Optional feedback or notes for the approval decision.",
            },
        },
        "required": ["run_id"],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id

    async def execute(self, **kwargs: Any) -> str:
        raw_id = kwargs.get("run_id", "").strip()
        feedback = kwargs.get("feedback", "").strip() or None

        if not raw_id:
            return "Error: 'run_id' is required."

        if not self._db or not self._user_id:
            return "Error: Database not available."

        try:
            rid = uuid.UUID(raw_id)
        except ValueError:
            return "Error: Invalid run_id format."

        try:
            from src.app.routes.workflows import resume_workflow_internal
            run_result = await resume_workflow_internal(rid, True, feedback, self._user_id, self._db)
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error approving checkpoint: {e}"

        return RunWorkflow._format_run_result(RunWorkflow, run_result)


class RejectCheckpoint(Tool):
    """Reject a paused workflow checkpoint with optional feedback. The workflow stops."""

    name: str = "reject_checkpoint"
    description: str = (
        "Reject a workflow run that is paused at a human checkpoint. "
        "Provide feedback explaining why. The workflow run is marked as failed. "
        "Call this when the user says 'reject', 'no', 'stop', 'cancel this run', etc. "
        "after a workflow paused for human approval."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "The UUID of the paused workflow run.",
            },
            "feedback": {
                "type": "string",
                "description": "Required: reason for rejection. This is recorded in the audit log and surfaced to the workflow.",
            },
        },
        "required": ["run_id", "feedback"],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id

    async def execute(self, **kwargs: Any) -> str:
        raw_id = kwargs.get("run_id", "").strip()
        feedback = kwargs.get("feedback", "").strip()

        if not raw_id:
            return "Error: 'run_id' is required."
        if not feedback:
            return "Error: 'feedback' is required for rejection."

        if not self._db or not self._user_id:
            return "Error: Database not available."

        try:
            rid = uuid.UUID(raw_id)
        except ValueError:
            return "Error: Invalid run_id format."

        try:
            from src.app.routes.workflows import resume_workflow_internal
            run_result = await resume_workflow_internal(rid, False, feedback, self._user_id, self._db)
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error rejecting checkpoint: {e}"

        status = run_result.get("status", "failed")
        return (
            f"❌ **Checkpoint rejected** — workflow marked as failed.\n\n"
            f"Run: `{str(raw_id)[:8]}...`\n"
            f"Feedback: {feedback}\n"
            f"Status: {status}"
        )
