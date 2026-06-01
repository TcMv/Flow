"""GitHub MCP tools — issues, PRs, and repo info via GitHub API."""

from __future__ import annotations

import os
from typing import Any

import httpx

from src.app.agent.tools import Tool


# GitHub token — set from env var or per-tenant config
_GITHUB_TOKEN: str | None = os.environ.get("FLOW_GITHUB_TOKEN", None)
_GITHUB_API = "https://api.github.com"


def _headers() -> dict:
    h = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Flow-Agent/1.0",
    }
    if _GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {_GITHUB_TOKEN}"
    return h


def _parse_repo(repo_str: str) -> tuple[str, str]:
    """Parse 'owner/repo' from a string."""
    parts = repo_str.replace("https://github.com/", "").replace("github.com:", "").strip("/").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1].replace(".git", "")
    raise ValueError("Repository must be in 'owner/repo' format.")


async def _get(path: str, params: dict | None = None) -> dict | list:
    """Make an authenticated GET request to the GitHub API."""
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{_GITHUB_API}{path}", headers=_headers(), params=params)
        r.raise_for_status()
        return r.json()


class GitHubListIssues(Tool):
    """List issues for a GitHub repository."""

    name: str = "mcp_github_list_issues"
    description: str = (
        "List open issues for a GitHub repository. "
        "Use this when the user asks about open tickets, bugs, or feature requests. "
        "Returns issue titles, numbers, and labels."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository in 'owner/repo' format, e.g. 'TcMv/Flow'.",
            },
            "state": {
                "type": "string",
                "description": "Issue state filter: 'open', 'closed', 'all'. Default: 'open'.",
                "enum": ["open", "closed", "all"],
            },
            "limit": {
                "type": "integer",
                "description": "Maximum issues to return (default: 10, max: 30).",
            },
        },
        "required": ["repo"],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo_str = kwargs.get("repo", "").strip()
        state = kwargs.get("state", "open")
        limit = min(int(kwargs.get("limit", 10)), 30)

        if not repo_str:
            return "Error: 'repo' is required."

        try:
            owner, repo = _parse_repo(repo_str)
        except ValueError as e:
            return f"Error: {e}"

        if not _GITHUB_TOKEN:
            return "Error: GitHub token not configured. Set FLOW_GITHUB_TOKEN env var."

        try:
            data = await _get(f"/repos/{owner}/{repo}/issues", {
                "state": state,
                "per_page": limit,
                "sort": "updated",
                "direction": "desc",
            })
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Repository '{owner}/{repo}' not found. Check the name and access token."
            return f"GitHub API error: {e.response.status_code} - {e.response.text[:200]}"
        except Exception as e:
            return f"Error: {e}"

        # Filter out pull requests (GitHub API returns PRs as issues too)
        issues = [i for i in data if "pull_request" not in i]

        if not issues:
            return f"No {state} issues in {owner}/{repo}."

        lines = [f"Issues in {owner}/{repo} ({state}, {len(issues)}):\n"]
        for issue in issues[:limit]:
            labels = ", ".join(l["name"] for l in issue.get("labels", []))
            label_str = f" [{labels}]" if labels else ""
            lines.append(
                f"  • **#{issue['number']}** {issue['title']}{label_str}\n"
                f"    Updated: {issue.get('updated_at', '')[:10]}"
            )

        return "\n".join(lines)


class GitHubCreateIssue(Tool):
    """Create an issue in a GitHub repository."""

    name: str = "mcp_github_create_issue"
    description: str = (
        "Create a new issue in a GitHub repository. "
        "Use this when the user wants to file a bug report, feature request, or task. "
        "Requires a configured GitHub token with repo scope."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository in 'owner/repo' format.",
            },
            "title": {
                "type": "string",
                "description": "Issue title.",
            },
            "body": {
                "type": "string",
                "description": "Issue body/description.",
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of label names to apply.",
            },
        },
        "required": ["repo", "title"],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo_str = kwargs.get("repo", "").strip()
        title = kwargs.get("title", "").strip()
        body = kwargs.get("body", "")
        labels = kwargs.get("labels", [])

        if not repo_str or not title:
            return "Error: 'repo' and 'title' are required."

        if not _GITHUB_TOKEN:
            return "Error: GitHub token not configured."

        try:
            owner, repo = _parse_repo(repo_str)
        except ValueError as e:
            return f"Error: {e}"

        payload = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    f"{_GITHUB_API}/repos/{owner}/{repo}/issues",
                    headers=_headers(),
                    json=payload,
                )
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPStatusError as e:
            return f"Error creating issue: {e.response.status_code} - {e.response.text[:200]}"
        except Exception as e:
            return f"Error: {e}"

        return f"✅ Issue created: **{data['title']}** (#{data['number']})\n{data['html_url']}"


class GitHubListPRs(Tool):
    """List pull requests for a repository."""

    name: str = "mcp_github_list_prs"
    description: str = (
        "List pull requests for a GitHub repository. "
        "Returns PR numbers, titles, and status. "
        "Use this when the user wants to check open pull requests."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository in 'owner/repo' format.",
            },
            "state": {
                "type": "string",
                "description": "PR state: 'open', 'closed', 'all'. Default: 'open'.",
                "enum": ["open", "closed", "all"],
            },
            "limit": {
                "type": "integer",
                "description": "Maximum PRs to return (default: 10, max: 30).",
            },
        },
        "required": ["repo"],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo_str = kwargs.get("repo", "").strip()
        state = kwargs.get("state", "open")
        limit = min(int(kwargs.get("limit", 10)), 30)

        if not repo_str:
            return "Error: 'repo' is required."

        if not _GITHUB_TOKEN:
            return "Error: GitHub token not configured."

        try:
            owner, repo = _parse_repo(repo_str)
        except ValueError as e:
            return f"Error: {e}"

        try:
            data = await _get(f"/repos/{owner}/{repo}/pulls", {
                "state": state,
                "per_page": limit,
                "sort": "updated",
                "direction": "desc",
            })
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Repository '{owner}/{repo}' not found."
            return f"GitHub API error: {e.response.status_code}"
        except Exception as e:
            return f"Error: {e}"

        if not data:
            return f"No {state} pull requests in {owner}/{repo}."

        lines = [f"Pull requests in {owner}/{repo} ({state}, {len(data)}):\n"]
        for pr in data[:limit]:
            labels = ", ".join(l["name"] for l in pr.get("labels", []))
            label_str = f" [{labels}]" if labels else ""
            lines.append(
                f"  • **#{pr['number']}** {pr['title']}{label_str}\n"
                f"    By {pr['user']['login']} · {pr.get('state', '')}"
            )

        return "\n".join(lines)


class GitHubGetRepo(Tool):
    """Get information about a GitHub repository."""

    name: str = "mcp_github_get_repo"
    description: str = (
        "Get details about a GitHub repository — description, stars, forks, language, topics, last update. "
        "Use this when the user asks about a repo or wants to find project info."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository in 'owner/repo' format.",
            },
        },
        "required": ["repo"],
    }

    async def execute(self, **kwargs: Any) -> str:
        repo_str = kwargs.get("repo", "").strip()
        if not repo_str:
            return "Error: 'repo' is required."

        if not _GITHUB_TOKEN:
            return "Error: GitHub token not configured."

        try:
            owner, repo = _parse_repo(repo_str)
        except ValueError as e:
            return f"Error: {e}"

        try:
            data = await _get(f"/repos/{owner}/{repo}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Repository '{owner}/{repo}' not found."
            return f"GitHub API error: {e.response.status_code}"
        except Exception as e:
            return f"Error: {e}"

        return (
            f"**{data['full_name']}**\n"
            f"{data.get('description', 'No description')}\n\n"
            f"🌟 Stars: {data['stargazers_count']}  "
            f"🍴 Forks: {data['forks_count']}  "
            f"🐛 Issues: {data['open_issues_count']}\n"
            f"📚 Language: {data.get('language', 'N/A')}  "
            f"📅 Updated: {data.get('updated_at', '')[:10]}\n"
            f"🔗 {data['html_url']}\n"
            f"📝 License: {data['license']['spdx_id'] if data.get('license') else 'N/A'}"
        )
