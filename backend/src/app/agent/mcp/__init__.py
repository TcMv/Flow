"""MCP Server Adapters — Tier 1 integrations as Flow-native tools.

Each adapter wraps a service capability (filesystem, postgres, git, github,
web fetch, memory) as a Flow Tool that works in all environments including
serverless Vercel.  No subprocess or MCP protocol dependency required —
each tool uses the relevant Python library directly.

For on-prem deployments with persistent processes, the MCP bridge
(``bridge.py``) can spawn the official MCP servers as subprocesses and
discover their tools via the MCP protocol as an alternative.
"""

from __future__ import annotations

from src.app.agent.mcp.postgres import PostgresQuery, PostgresListTables, PostgresDescribeTable
from src.app.agent.mcp.filesystem import FileRead, FileWrite, FileSearch, FileListDir
from src.app.agent.mcp.git import GitStatus, GitLog, GitDiff, GitCommit
from src.app.agent.mcp.github import GitHubListIssues, GitHubCreateIssue, GitHubListPRs, GitHubGetRepo
from src.app.agent.mcp.fetch import WebFetch, WebFetchText
from src.app.agent.mcp.memory import MemoryStore, MemoryRecall, MemorySearch, MemoryList

__all__ = [
    # Postgres
    "PostgresQuery",
    "PostgresListTables",
    "PostgresDescribeTable",
    # Filesystem
    "FileRead",
    "FileWrite",
    "FileSearch",
    "FileListDir",
    # Git
    "GitStatus",
    "GitLog",
    "GitDiff",
    "GitCommit",
    # GitHub
    "GitHubListIssues",
    "GitHubCreateIssue",
    "GitHubListPRs",
    "GitHubGetRepo",
    # Web Fetch
    "WebFetch",
    "WebFetchText",
    # Memory
    "MemoryStore",
    "MemoryRecall",
    "MemorySearch",
    "MemoryList",
]

TIER_1_TOOLS = [
    PostgresQuery,
    PostgresListTables,
    PostgresDescribeTable,
    FileRead,
    FileWrite,
    FileSearch,
    FileListDir,
    GitStatus,
    GitLog,
    GitDiff,
    GitCommit,
    GitHubListIssues,
    GitHubCreateIssue,
    GitHubListPRs,
    GitHubGetRepo,
    WebFetch,
    WebFetchText,
    MemoryStore,
    MemoryRecall,
    MemorySearch,
    MemoryList,
]


def register_tier_1_tools(registry, db=None, user=None):
    """Register all Tier 1 MCP tools into the given ToolRegistry."""
    from src.app.agent.tools import ToolRegistry

    for tool_cls in TIER_1_TOOLS:
        kwargs = {}
        if db is not None:
            kwargs["db"] = db
        if user is not None:
            kwargs["user_id"] = user.id
            kwargs["tenant_id"] = user.tenant_id
        registry.register(tool_cls(**kwargs))
    return registry
