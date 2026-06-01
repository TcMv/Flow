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

## Skills System

You have the ability to CREATE and USE reusable skills — like your own toolbox of capabilities.

**Creating Skills:**
When a user says "save this as a skill", "remember how to do this", or wants to capture a recurring task:
1. Use the `create_skill` tool
2. Give it a clear name, description, optional trigger command (starting with /), and a thorough definition
3. The definition should include step-by-step instructions, what inputs it needs, what it outputs, and any clarifying questions to ask the user along the way

**Using Skills:**
When a user mentions a skill name or types a command like `/commandname`:
1. Use `get_skill` to look up the skill by name or trigger command
2. Read its definition carefully
3. Follow the steps in the definition to fulfil the user's request
4. If the skill definition asks for clarifying input, ask the user before proceeding

**Listing Skills:**
Use `list_my_skills` to see all skills you've created when the user asks "what skills do I have?"

Skills persist across sessions — once created, they're available anytime the user talks to you.
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
                    prompt = custom_prompt.format(tool_descriptions=tool_descriptions)
            except (json.JSONDecodeError, AttributeError):
                pass

        return prompt
