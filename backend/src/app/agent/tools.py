"""Tool Registry — register, discover, and execute tools the agent can use."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


class Tool:
    """Base class for agent-callable tools.

    Subclasses must set ``name``, ``description``, and ``parameters``
    (JSON Schema dict), and implement ``execute(**kwargs) -> str``.
    """

    name: str = ""
    description: str = ""
    parameters: dict = {}  # JSON Schema for the function parameters

    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool with the given arguments and return a text result."""
        raise NotImplementedError

    def to_openai_tool(self) -> dict:
        """Return an OpenAI-compatible tool definition."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class GetCurrentTime(Tool):
    """Returns the current UTC date and time."""

    name: str = "get_current_time"
    description: str = "Get the current date and time in UTC."
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def execute(self, **kwargs: Any) -> str:
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d %H:%M:%S UTC")


class Echo(Tool):
    """Echoes back the user's input — useful for testing."""

    name: str = "echo"
    description: str = "Echo the given message back to the user. Useful for testing tool execution."
    parameters: dict = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message to echo back.",
            },
        },
        "required": ["message"],
    }

    async def execute(self, **kwargs: Any) -> str:
        message = kwargs.get("message", "")
        return f"Echo: {message}"


class ToolRegistry:
    """Registry of tools the agent can invoke."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance by its name."""
        if tool.name in self._tools:
            raise ValueError(f"A tool named '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Retrieve a tool by name, or ``None`` if not found."""
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """Return all registered tools as a list."""
        return list(self._tools.values())

    def list_openai_tools(self) -> list[dict]:
        """Return all registered tools as OpenAI-compatible tool definitions."""
        return [t.to_openai_tool() for t in self._tools.values()]

    def tool_descriptions_for_prompt(self) -> str:
        """Return a human-readable summary of available tools for the system prompt."""
        if not self._tools:
            return "No tools are currently available."
        lines = ["Available tools:"]
        for tool in self._tools.values():
            lines.append(f"  - {tool.name}: {tool.description}")
        return "\n".join(lines)

    async def execute_tool(self, name: str, arguments: str | dict) -> str:
        """Execute a tool by name with the given arguments (JSON string or dict).

        Returns the tool's text result, or an error message if the tool
        is not found or execution fails.
        """
        tool = self.get(name)
        if tool is None:
            return f"Error: Unknown tool '{name}'."

        try:
            if isinstance(arguments, str):
                kwargs = json.loads(arguments)
            else:
                kwargs = arguments
            result = await tool.execute(**kwargs)
            return result
        except Exception as exc:
            return f"Error executing tool '{name}': {exc!s}"
