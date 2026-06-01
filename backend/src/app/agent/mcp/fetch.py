"""Web Fetch MCP tools — fetch web pages and extract text content."""

from __future__ import annotations

from typing import Any

import httpx

from src.app.agent.tools import Tool


_MAX_CONTENT_LENGTH = 10000  # characters
_ALLOWED_SCHEMES = ("http", "https")
_TIMEOUT = 15  # seconds


class WebFetch(Tool):
    """Fetch a web page and return its content as pure text."""

    name: str = "mcp_fetch"
    description: str = (
        "Fetch a web page and return its text content. "
        "Strips HTML tags and returns readable text. "
        "Use this when the user asks you to get information from a website, "
        "check a URL, read documentation, or research something online."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch (http/https).",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum characters to return (default: 10000, max: 50000).",
            },
        },
        "required": ["url"],
    }

    async def execute(self, **kwargs: Any) -> str:
        url = kwargs.get("url", "").strip()
        max_len = min(int(kwargs.get("max_length", _MAX_CONTENT_LENGTH)), 50000)

        if not url:
            return "Error: 'url' is required."

        if not url.startswith(_ALLOWED_SCHEMES):
            return "Error: Only http and https URLs are supported."

        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT,
                follow_redirects=True,
                headers={
                    "User-Agent": "Flow-Agent/1.0 (research bot; for internal use)",
                    "Accept": "text/html,text/plain,*/*",
                },
            ) as client:
                r = await client.get(url)
                r.raise_for_status()

        except httpx.TimeoutException:
            return f"Error: Request to '{url}' timed out after {_TIMEOUT}s."
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP {e.response.status_code} when fetching '{url}'."
        except Exception as e:
            return f"Error fetching URL: {e}"

        content_type = r.headers.get("content-type", "")
        text = r.text

        # Try to extract readable text from HTML
        if "text/html" in content_type:
            text = self._html_to_text(text)

        # Truncate
        if len(text) > max_len:
            text = text[:max_len] + f"\n\n... (truncated, full page is {len(r.text)} characters)"

        return f"**Content from {url}**\n\n{text}"

    def _html_to_text(self, html: str) -> str:
        """Strip HTML tags and extract readable text."""
        import re

        # Remove scripts and styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Replace block-level tags with newlines
        html = re.sub(r"</?(?:div|p|br|h[1-6]|li|tr|td|th|blockquote|section|article|header|footer)[^>]*>", "\n", html, flags=re.IGNORECASE)

        # Strip remaining tags
        text = re.sub(r"<[^>]+>", "", html)

        # Decode common entities
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

        # Condense whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        return text.strip()


class WebFetchText(Tool):
    """Fetch raw text content from a URL (for JSON APIs, plaintext endpoints)."""

    name: str = "mcp_fetch_text"
    description: str = (
        "Fetch raw content from a URL without HTML processing. "
        "Best for APIs, JSON endpoints, plaintext, or when you want the exact content. "
        "Use this when the user asks you to check an API endpoint, get JSON data, or fetch raw text."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch (http/https).",
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum characters to return (default: 10000, max: 50000).",
            },
        },
        "required": ["url"],
    }

    async def execute(self, **kwargs: Any) -> str:
        url = kwargs.get("url", "").strip()
        max_len = min(int(kwargs.get("max_length", _MAX_CONTENT_LENGTH)), 50000)

        if not url:
            return "Error: 'url' is required."

        if not url.startswith(_ALLOWED_SCHEMES):
            return "Error: Only http and https URLs are supported."

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
                r = await client.get(
                    url,
                    headers={"User-Agent": "Flow-Agent/1.0 (research bot; for internal use)"},
                )
                r.raise_for_status()
        except httpx.TimeoutException:
            return f"Error: Request timed out after {_TIMEOUT}s."
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP {e.response.status_code}."
        except Exception as e:
            return f"Error: {e}"

        text = r.text
        if len(text) > max_len:
            text = text[:max_len] + f"\n\n... (truncated, full response is {len(r.text)} characters)"

        return f"**Raw content from {url}**\n\n```\n{text}\n```"
