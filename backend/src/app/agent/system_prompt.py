"""System Prompt — default agent persona builder."""

from __future__ import annotations

from src.app.models.user import User


DEFAULT_SYSTEM_PROMPT = """You are a friendly, helpful AI assistant running on the Flow platform.

You have access to tools that can help you answer questions and perform tasks.
When you need to use a tool, call it directly — the system will execute it and return the result.
You can call multiple tools if needed to accomplish a task.

Always respond in the same language the user is speaking to you.
Be concise, accurate, and helpful. If you don't know something, say so rather than making things up.

{tool_descriptions}
"""


class SystemPromptBuilder:
    """Builds the system prompt for the agent's context window.

    Combines the default persona with per-user agent_config overrides
    and the current tool descriptions.
    """

    @staticmethod
    def build(
        user: User | None = None,
        tool_descriptions: str = "",
    ) -> str:
        """Assemble the final system prompt.

        Args:
            user: The current user (may have custom ``agent_config``).
            tool_descriptions: Human-readable tool descriptions string.

        Returns:
            The complete system prompt text.
        """
        prompt = DEFAULT_SYSTEM_PROMPT.format(tool_descriptions=tool_descriptions)

        # Apply per-user custom system prompt if configured
        if user and user.agent_config:
            try:
                import json

                config = json.loads(user.agent_config)
                custom_prompt = config.get("system_prompt")
                if custom_prompt:
                    # Merge: custom prompt replaces or augments default
                    prompt = custom_prompt.format(tool_descriptions=tool_descriptions)
            except (json.JSONDecodeError, AttributeError):
                pass

        return prompt
