"""AgentEngine — the think→act→observe→log execution loop."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.agent.llm import LLMRouter
from src.app.agent.tools import ToolRegistry
from src.app.agent.session import AgentSessionManager
from src.app.agent.system_prompt import SystemPromptBuilder
from src.app.agent.audit import AgentAuditLogger
from src.app.models.user import User

MAX_ITERATIONS = 10
FALLBACK_MESSAGE = (
    "I've reached the maximum number of reasoning steps for this request. "
    "Please try rephrasing or breaking your question into smaller parts."
)


class AgentEngine:
    """The core agent execution loop.

    The loop:
        1. Add user message to session history
        2. Build context (system prompt + history + tool descriptions)
        3. Call LLM with function-calling format
        4. If LLM calls a tool → execute → log → add result → go to 2
        5. If LLM returns text → add to history → yield text
        6. If max iterations reached → yield fallback message

    EVERY step is logged to AuditLog.
    """

    def __init__(
        self,
        llm_router: LLMRouter,
        tool_registry: ToolRegistry,
        user: User,
        session_manager: AgentSessionManager,
        audit_logger: AgentAuditLogger | None = None,
    ) -> None:
        self._llm = llm_router
        self._tools = tool_registry
        self._user = user
        self._session_manager = session_manager
        self._audit = audit_logger

    async def run(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """Execute the think→act→observe→log loop for a user message.

        Yields text chunks as the assistant responds (tool call results
        are not yielded directly — only the final LLM response).
        """
        tenant_id = self._user.tenant_id
        actor_id = self._user.id

        # ── 1. Persist user message & log ──────────────────────────
        await self._session_manager.add_message(
            db, session_id, "user", user_message
        )
        if self._audit:
            await self._audit.log_user_message(
                tenant_id, actor_id, session_id, user_message
            )

        # Auto-title if this is the first message
        await self._auto_title(db, session_id, user_message)

        iterations = 0
        while iterations < MAX_ITERATIONS:
            iterations += 1

            # ── 2. Build context ───────────────────────────────────
            tool_descriptions = self._tools.tool_descriptions_for_prompt()
            system_prompt = SystemPromptBuilder.build(
                user=self._user,
                tool_descriptions=tool_descriptions,
            )
            history = await self._session_manager.get_history(db, session_id)
            messages = [
                {"role": "system", "content": system_prompt},
                *history,
            ]
            openai_tools = self._tools.list_openai_tools()

            # ── 3. Call LLM ────────────────────────────────────────
            if self._audit:
                await self._audit.log_llm_call(
                    tenant_id, actor_id, session_id,
                    self._llm.provider, self._llm.model,
                )

            text, tool_calls = await self._llm.chat_with_tool_calls(
                messages=messages,
                tools=openai_tools or None,
            )

            # ── 4. Tool calls? ────────────────────────────────────
            if tool_calls:
                for tc in tool_calls:
                    tool_name = tc["function"]["name"]
                    arguments = tc["function"]["arguments"]
                    call_id = tc.get("id", "")

                    # Log tool call
                    if self._audit:
                        await self._audit.log_tool_call(
                            tenant_id, actor_id, session_id,
                            tool_name, arguments,
                        )

                    # Execute
                    result = await self._tools.execute_tool(tool_name, arguments)

                    # Log tool result
                    if self._audit:
                        await self._audit.log_tool_result(
                            tenant_id, actor_id, session_id,
                            tool_name, result,
                        )

                    # Add tool call and result to history
                    await self._session_manager.add_message(
                        db, session_id, "assistant", "",
                        tool_calls=json.dumps(tool_calls),
                    )
                    await self._session_manager.add_message(
                        db, session_id, "tool", result,
                        tool_call_id=call_id,
                    )

                # Continue the loop — let LLM see tool results
                continue

            # ── 5. Text response ──────────────────────────────────
            response_text = text or ""

            await self._session_manager.add_message(
                db, session_id, "assistant", response_text,
            )

            if self._audit:
                await self._audit.log_agent_response(
                    tenant_id, actor_id, session_id, response_text,
                )

            yield response_text
            return  # Done

        # ── 6. Max iterations ──────────────────────────────────────
        await self._session_manager.add_message(
            db, session_id, "assistant", FALLBACK_MESSAGE,
        )
        if self._audit:
            await self._audit.log_agent_response(
                tenant_id, actor_id, session_id, FALLBACK_MESSAGE,
            )
        yield FALLBACK_MESSAGE

    async def _auto_title(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_message: str,
    ) -> None:
        """Set session title from the first user message if not already set."""
        from src.app.models.agent_session import AgentSession
        from sqlalchemy import select as sa_select

        r = await db.execute(
            sa_select(AgentSession.title).where(AgentSession.id == session_id)
        )
        current_title = r.scalar_one_or_none()
        if not current_title:
            title = user_message[:80]
            if len(user_message) > 80:
                title += "..."
            await self._session_manager.update_title(
                db, session_id, title,
            )
