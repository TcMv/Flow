"""Git MCP tools — status, log, diff, commit operations."""

from __future__ import annotations

import os
import subprocess as sp
from pathlib import Path
from typing import Any

from src.app.agent.tools import Tool


_GIT_REPO_PATH: str | None = None  # Set from env or config


def _find_repo(repo_path: str | None = None) -> str:
    """Resolve the git repository path."""
    if repo_path:
        p = Path(repo_path).expanduser().resolve()
        if p.is_dir():
            return str(p)
    if _GIT_REPO_PATH:
        return _GIT_REPO_PATH
    # Fall back to cwd and walk up
    cwd = Path.cwd().resolve()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").is_dir():
            return str(parent)
    return str(cwd)


def _run_git(cmd: list[str], repo_path: str | None = None) -> tuple[str, str, int]:
    """Run a git command and return (stdout, stderr, exit_code)."""
    try:
        r = sp.run(
            ["git", *cmd],
            capture_output=True,
            text=True,
            cwd=_find_repo(repo_path),
            timeout=15,
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except sp.TimeoutExpired:
        return "", "Git command timed out", -1
    except FileNotFoundError:
        return "", "Git not found. Ensure git is installed.", -1


class GitStatus(Tool):
    """Show the working tree status of the current git repository."""

    name: str = "mcp_git_status"
    description: str = (
        "Show the working tree status of the current git repository. "
        "Returns modified files, staged changes, untracked files, and branch info. "
        "Use this when the user asks about the state of their repo."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Optional path to the git repository. Defaults to current directory.",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo = kwargs.get("repo_path")
        stdout, stderr, code = _run_git(["status", "--porcelain", "-b"], repo)
        if code != 0:
            return f"Error: {stderr or 'Not a git repository.'}"

        lines = stdout.split("\n")
        branch_line = lines[0] if lines else ""
        branch = branch_line.replace("## ", "").split("...")[0] if branch_line else "unknown"

        staged = [l[3:] for l in lines[1:] if len(l) > 3 and l[0] in "MARD"]
        unstaged = [l[3:] for l in lines[1:] if len(l) > 3 and l[1] in "MARD"]
        untracked = [l[3:] for l in lines[1:] if l.startswith("??")]

        result = [f"**Branch:** {branch}\n"]
        if not staged and not unstaged and not untracked:
            result.append("Clean working tree — nothing modified.")

        if staged:
            result.append(f"\n**Staged changes ({len(staged)}):**")
            for f in staged[:30]:
                result.append(f"  • {f}")

        if unstaged:
            result.append(f"\n**Unstaged changes ({len(unstaged)}):**")
            for f in unstaged[:30]:
                result.append(f"  • {f}")

        if untracked:
            result.append(f"\n**Untracked files ({len(untracked)}):**")
            for f in untracked[:30]:
                result.append(f"  • {f}")

        return "\n".join(result)


class GitLog(Tool):
    """Show commit history of the git repository."""

    name: str = "mcp_git_log"
    description: str = (
        "Show the commit log of the current git repository. "
        "Returns recent commits with hash, author, date, and message. "
        "Use this when the user asks about what has changed recently."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Optional path to the git repository.",
            },
            "count": {
                "type": "integer",
                "description": "Number of commits to show (default: 10, max: 50).",
            },
            "branch": {
                "type": "string",
                "description": "Branch name to show logs for (default: current branch).",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo = kwargs.get("repo_path")
        count = min(int(kwargs.get("count", 10)), 50)
        branch = kwargs.get("branch", "HEAD")

        stdout, stderr, code = _run_git(
            ["log", branch, f"-{count}", "--format=%h||%an||%ar||%s"],
            repo,
        )
        if code != 0:
            return f"Error: {stderr or 'Not a git repository.'}"

        lines = [f"Recent commits (last {count}):\n"]
        for entry in stdout.split("\n"):
            if not entry.strip():
                continue
            parts = entry.split("||", 3)
            if len(parts) == 4:
                hash_s, author, date, msg = parts
                lines.append(f"  `{hash_s}`  {msg[:80]}")
                lines.append(f"         {author} · {date}")

        return "\n".join(lines)


class GitDiff(Tool):
    """Show uncommitted changes or diff between commits."""

    name: str = "mcp_git_diff"
    description: str = (
        "Show the diff of changes in the working tree. "
        "Can show unstaged changes (default), staged changes, or a diff between two commits. "
        "Use this when the user wants to review changes before committing."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "Optional path to the git repository.",
            },
            "staged": {
                "type": "boolean",
                "description": "If true, show staged changes (diff --cached). Default: false (unstaged changes).",
            },
            "file": {
                "type": "string",
                "description": "Optional specific file path to show diff for.",
            },
            "from_commit": {
                "type": "string",
                "description": "Optional: show changes from this commit.",
            },
            "to_commit": {
                "type": "string",
                "description": "Optional: show changes to this commit (default: HEAD).",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo = kwargs.get("repo_path")
        staged = kwargs.get("staged", False)
        file_path = kwargs.get("file")
        from_c = kwargs.get("from_commit")
        to_c = kwargs.get("to_commit", "HEAD")

        cmd = ["diff"]
        if from_c:
            cmd.append(f"{from_c}..{to_c}" if to_c else from_c)
        elif staged:
            cmd.append("--cached")
        else:
            cmd.append("HEAD")  # diff working tree vs HEAD

        if file_path:
            cmd.append("--")
            cmd.append(file_path)

        stdout, stderr, code = _run_git(cmd, repo)
        if code != 0:
            return f"Error: {stderr or 'Nothing to diff.'}"

        if not stdout:
            return "No differences found."

        # Truncate if too long
        if len(stdout) > 5000:
            stdout = stdout[:5000] + "\n... (truncated, full diff too long)"

        return f"```diff\n{stdout}\n```"


class GitCommit(Tool):
    """Create a commit with the given message (stages tracked files first)."""

    name: str = "mcp_git_commit"
    description: str = (
        "Stage all tracked changes and create a commit with the given message. "
        "Only stages files that are already tracked (not untracked files). "
        "Requires owner approval before executing. "
        "Use this when the user asks you to commit their changes."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The commit message.",
            },
            "repo_path": {
                "type": "string",
                "description": "Optional path to the git repository.",
            },
        },
        "required": ["message"],
    }

    async def execute(self, **kwargs: Any) -> str:
        message = kwargs.get("message", "").strip()
        repo = kwargs.get("repo_path")

        if not message:
            return "Error: 'message' is required."

        # Stage tracked changes
        stdout, stderr, code = _run_git(["add", "-u"], repo)
        if code != 0:
            return f"Error staging files: {stderr}"

        # Commit
        stdout, stderr, code = _run_git(["commit", "-m", message], repo)
        if code != 0:
            return f"Error committing: {stderr or 'No changes to commit.'}"

        return f"✅ {stdout}"
