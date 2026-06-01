"""Filesystem MCP tools — read, write, search files with path restrictions."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from src.app.agent.tools import Tool


# ── Allowed base paths (configurable) ────────────────────────────────
# For government on-prem: set from env or per-tenant config
# For serverless: only /tmp is available
_ALLOWED_PATHS: list[Path] = [
    Path("/tmp").resolve(),          # serverless / general writable
    Path(os.path.expanduser("~/documents")).resolve() if os.path.expanduser("~/documents") else None,
    Path.cwd().resolve(),
]
_ALLOWED_PATHS = [p for p in _ALLOWED_PATHS if p is not None and p.exists()]

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_MAX_SEARCH_RESULTS = 30


def _resolve_path(user_path: str) -> Path:
    """Resolve a user-provided path and validate it's within allowed paths."""
    p = Path(user_path).expanduser().resolve()
    allowed = any(
        str(p).startswith(str(base))
        for base in _ALLOWED_PATHS
    )
    if not allowed:
        bases = ", ".join(str(b) for b in _ALLOWED_PATHS)
        raise PermissionError(
            f"Path '{p}' is not allowed. Allowed roots: {bases}"
        )
    return p


class FileRead(Tool):
    """Read the contents of a file from the filesystem."""

    name: str = "mcp_filesystem_read"
    description: str = (
        "Read the contents of a file from the filesystem. "
        "Returns the full file content as text. "
        "Use this when the user asks you to read a file, open a document, or show file contents. "
        "Only files within allowed directories can be accessed."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to read.",
            },
            "offset": {
                "type": "integer",
                "description": "Optional: line number to start reading from (1-indexed). Default: start of file.",
            },
            "limit": {
                "type": "integer",
                "description": "Optional: maximum number of lines to read. Max 2000.",
            },
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs: Any) -> str:
        path_str = kwargs.get("path", "").strip()
        if not path_str:
            return "Error: 'path' is required."

        try:
            resolved = _resolve_path(path_str)
        except PermissionError as e:
            return f"Error: {e}"

        if not resolved.exists():
            return f"Error: File '{resolved}' does not exist."
        if not resolved.is_file():
            return f"Error: '{resolved}' is not a file."

        size = resolved.stat().st_size
        if size > _MAX_FILE_SIZE:
            return f"Error: File is {size / 1024 / 1024:.1f} MB (max {_MAX_FILE_SIZE / 1024 / 1024:.0f} MB)."

        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
            offset = kwargs.get("offset", 1)
            limit = kwargs.get("limit", 0)

            lines = text.split("\n")
            if offset > 1 or limit:
                offset = max(1, int(offset))
                start = offset - 1
                end = start + int(limit) if limit else len(lines)
                lines = lines[start:end]

            result = "\n".join(lines)
            return f"```\n{result}\n```\n\n{len(lines)} lines shown."

        except Exception as e:
            return f"Error reading file: {e}"


class FileWrite(Tool):
    """Write content to a file on the filesystem."""

    name: str = "mcp_filesystem_write"
    description: str = (
        "Write content to a file on the filesystem. "
        "Creates parent directories if they don't exist. "
        "Overwrites the file if it already exists. "
        "Use this when the user wants to save a document, create a report, or export data."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path where the file should be written.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
        },
        "required": ["path", "content"],
    }

    async def execute(self, **kwargs: Any) -> str:
        path_str = kwargs.get("path", "").strip()
        content = kwargs.get("content", "")
        if not path_str:
            return "Error: 'path' is required."

        try:
            resolved = _resolve_path(path_str)
        except PermissionError as e:
            return f"Error: {e}"

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            return f"✅ Written {len(content)} characters to '{resolved}'"
        except Exception as e:
            return f"Error writing file: {e}"


class FileSearch(Tool):
    """Search for files by name or content pattern."""

    name: str = "mcp_filesystem_search"
    description: str = (
        "Search for files by name or search inside file contents. "
        "Use this when the user wants to find a file, search documents, or locate information."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Search pattern (glob for name search, text for content search).",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current working directory).",
            },
            "search_content": {
                "type": "boolean",
                "description": "If true, search inside file contents. If false, search file names. Default: false.",
            },
        },
        "required": ["pattern"],
    }

    async def execute(self, **kwargs: Any) -> str:
        pattern = kwargs.get("pattern", "").strip()
        search_path = kwargs.get("path", str(Path.cwd()))
        search_content = kwargs.get("search_content", False)

        if not pattern:
            return "Error: 'pattern' is required."

        try:
            resolved = _resolve_path(search_path)
        except PermissionError as e:
            return f"Error: {e}"

        if not resolved.is_dir():
            return f"Error: '{resolved}' is not a directory."

        results: list[str] = []
        try:
            if search_content:
                # Search inside files (text grep)
                for fpath in resolved.rglob("*"):
                    if fpath.is_file() and fpath.stat().st_size < 1024 * 1024:
                        try:
                            text = fpath.read_text(encoding="utf-8", errors="replace")
                            if pattern.lower() in text.lower():
                                results.append(str(fpath))
                                if len(results) >= _MAX_SEARCH_RESULTS:
                                    break
                        except (UnicodeDecodeError, OSError):
                            continue
            else:
                # Search by name (glob)
                for fpath in resolved.rglob(pattern):
                    results.append(str(fpath))
                    if len(results) >= _MAX_SEARCH_RESULTS:
                        break
        except PermissionError:
            return "Error: Permission denied when searching."

        if not results:
            return f"No files matching '{pattern}' found in '{resolved}'."

        header = f"Found {len(results)} file(s) matching '{pattern}'"
        if len(results) >= _MAX_SEARCH_RESULTS:
            header += f" (showing first {_MAX_SEARCH_RESULTS})"
        return header + ":\n" + "\n".join(results)


class FileListDir(Tool):
    """List files and directories in a directory."""

    name: str = "mcp_filesystem_list_dir"
    description: str = (
        "List files and directories in a directory on the filesystem. "
        "Returns names, sizes, and modification times. "
        "Use this when the user wants to browse files, see what's in a folder."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the directory to list.",
            },
        },
        "required": ["path"],
    }

    async def execute(self, **kwargs: Any) -> str:
        path_str = kwargs.get("path", "").strip()
        if not path_str:
            return "Error: 'path' is required."

        try:
            resolved = _resolve_path(path_str)
        except PermissionError as e:
            return f"Error: {e}"

        if not resolved.is_dir():
            return f"Error: '{resolved}' is not a directory."

        try:
            entries = list(resolved.iterdir())
        except PermissionError:
            return f"Error: Permission denied reading '{resolved}'."

        if not entries:
            return f"Directory '{resolved}' is empty."

        lines = [f"Contents of '{resolved}':\n"]
        for entry in sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower())):
            prefix = "📁 " if entry.is_dir() else "📄 "
            size = entry.stat().st_size if entry.is_file() else ""
            if size:
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / 1024 / 1024:.1f} MB"
                lines.append(f"  {prefix}{entry.name}  ({size_str})")
            else:
                lines.append(f"  {prefix}{entry.name}")

        return "\n".join(lines)
