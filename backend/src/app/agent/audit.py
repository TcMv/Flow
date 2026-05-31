"""AgentAuditLogger — structured audit logging for agent operations."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.audit_log import AuditLog


class AgentAuditLogger:
    """Logs agent operations to the AuditLog table with hash-chain integrity.

    Each log entry is chained to the previous entry for the same tenant,
    forming a tamper-evident sequence.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log(
        self,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        action_type: str,
        resource_type: str,
        resource_id: str,
        details: str | None = None,
    ) -> AuditLog:
        """Write an audit log entry with hash-chain integrity.

        Returns the created AuditLog record.
        """
        # Find the previous hash for this tenant
        prev_hash = await self._get_latest_hash(tenant_id)

        now = datetime.now(timezone.utc)
        record_id = uuid.uuid4()

        entry_hash = AuditLog.compute_hash(
            record_id=record_id,
            tenant_id=tenant_id,
            timestamp=now,
            actor_id=actor_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            prev_hash=prev_hash,
        )

        log_entry = AuditLog(
            id=record_id,
            tenant_id=tenant_id,
            timestamp=now,
            actor_id=actor_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            hash=entry_hash,
            prev_hash=prev_hash,
        )
        self._db.add(log_entry)
        await self._db.flush()
        return log_entry

    async def _get_latest_hash(self, tenant_id: uuid.UUID) -> str | None:
        """Get the hash of the most recent audit log entry for this tenant."""
        result = await self._db.execute(
            select(AuditLog.hash)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ── Convenience loggers for agent operations ──────────────────

    async def log_user_message(
        self,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        message: str,
    ) -> AuditLog:
        return await self.log(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type="agent.user_message",
            resource_type="agent_session",
            resource_id=str(session_id),
            details=json.dumps({"content_preview": message[:500]}),
        )

    async def log_llm_call(
        self,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        provider: str,
        model: str,
        prompt_tokens: int | None = None,
    ) -> AuditLog:
        return await self.log(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type="agent.llm_call",
            resource_type="agent_session",
            resource_id=str(session_id),
            details=json.dumps({
                "provider": provider,
                "model": model,
                "prompt_tokens": prompt_tokens,
            }),
        )

    async def log_tool_call(
        self,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        tool_name: str,
        arguments: str,
    ) -> AuditLog:
        return await self.log(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type="agent.tool_call",
            resource_type="tool",
            resource_id=tool_name,
            details=json.dumps({
                "session_id": str(session_id),
                "tool": tool_name,
                "arguments": arguments[:1000],
            }),
        )

    async def log_tool_result(
        self,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        tool_name: str,
        result_preview: str,
    ) -> AuditLog:
        return await self.log(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type="agent.tool_result",
            resource_type="tool",
            resource_id=tool_name,
            details=json.dumps({
                "session_id": str(session_id),
                "tool": tool_name,
                "result_preview": result_preview[:500],
            }),
        )

    async def log_agent_response(
        self,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        session_id: uuid.UUID,
        response_preview: str,
    ) -> AuditLog:
        return await self.log(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_type="agent.response",
            resource_type="agent_session",
            resource_id=str(session_id),
            details=json.dumps({"response_preview": response_preview[:500]}),
        )
