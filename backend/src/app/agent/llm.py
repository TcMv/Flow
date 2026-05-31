"""LLM Router — routes messages to OpenAI, Anthropic, or custom providers."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from src.app.config import settings
from src.app.models.llm_key import LLMKey


# ── Encryption helpers ───────────────────────────────────────────────

def _get_fernet() -> "Fernet":
    """Lazy-import Fernet and return an instance keyed from settings."""
    from cryptography.fernet import Fernet

    key = settings.encryption_key
    if not key:
        raise RuntimeError(
            "encryption_key is not configured. "
            "Set FLOW_ENCRYPTION_KEY or encryption_key in .env"
        )
    return Fernet(key.encode("utf-8") if isinstance(key, str) else key)


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt an API key for storage."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_api_key(encrypted: str) -> str:
    """Decrypt a stored API key."""
    f = _get_fernet()
    return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")


# ── Provider clients ──────────────────────────────────────────────────


class LLMRouter:
    """Routes chat completion requests to the correct LLM provider.

    Reads provider configuration from a stored LLMKey record and
    returns textual responses.  Supports streaming via ``stream()``.
    """

    def __init__(self, llm_key: LLMKey) -> None:
        self._llm_key = llm_key
        self._provider = llm_key.provider
        self._model = llm_key.model_name
        api_key = decrypt_api_key(llm_key.api_key_encrypted)
        self._base_url = llm_key.base_url

        if self._provider == "openai":
            client_kwargs: dict = {"api_key": api_key, "timeout": 60.0}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._client: AsyncOpenAI | AsyncAnthropic = AsyncOpenAI(**client_kwargs)

        elif self._provider == "anthropic":
            client_kwargs = {"api_key": api_key, "timeout": 60.0}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._client = AsyncAnthropic(**client_kwargs)

        elif self._provider == "custom":
            # OpenAI-compatible custom provider
            client_kwargs = {"api_key": api_key, "timeout": 60.0}
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            self._client = AsyncOpenAI(**client_kwargs)

        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider}")

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    # ── Non-streaming chat ─────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Send messages to the LLM and return the text response.

        If *tools* are provided, the LLM may respond with a tool call
        instead of text — the caller is responsible for routing those.
        """
        if self._provider == "anthropic":
            return await self._anthropic_chat(messages, tools, max_tokens, temperature)
        # OpenAI / custom
        return await self._openai_chat(messages, tools, max_tokens, temperature)

    async def chat_with_tool_calls(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> tuple[str | None, list[dict] | None]:
        """Send messages and return (text_response, tool_calls).

        *tool_calls* is a list of dicts with keys ``id``, ``type``,
        ``function`` (``name``, ``arguments``) or ``None``.
        """
        if self._provider == "anthropic":
            return await self._anthropic_chat_with_tools(messages, tools, max_tokens, temperature)
        return await self._openai_chat_with_tools(messages, tools, max_tokens, temperature)

    # ── OpenAI helpers ─────────────────────────────────────────────

    async def _openai_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
        temperature: float,
    ) -> str:
        kwargs = dict(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = await self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
        return resp.choices[0].message.content or ""

    async def _openai_chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
        temperature: float,
    ) -> tuple[str | None, list[dict] | None]:
        kwargs = dict(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = await self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
        choice = resp.choices[0]
        msg = choice.message

        text = msg.content
        tool_calls_raw = msg.tool_calls
        tool_calls = None
        if tool_calls_raw:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls_raw
            ]
        return text, tool_calls

    # ── Anthropic helpers ──────────────────────────────────────────

    async def _anthropic_chat(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
        temperature: float,
    ) -> str:
        system_msg = None
        anthropic_messages = messages[:]
        if anthropic_messages and anthropic_messages[0].get("role") == "system":
            system_msg = anthropic_messages.pop(0)["content"]

        kwargs = dict(
            model=self._model,
            messages=anthropic_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = self._convert_tools_anthropic(tools)

        resp = await self._client.messages.create(**kwargs)  # type: ignore[union-attr]
        content_blocks = resp.content
        text_parts = [b.text for b in content_blocks if hasattr(b, "text") and b.text]
        return "\n".join(text_parts)

    async def _anthropic_chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
        temperature: float,
    ) -> tuple[str | None, list[dict] | None]:
        system_msg = None
        anthropic_messages = messages[:]
        if anthropic_messages and anthropic_messages[0].get("role") == "system":
            system_msg = anthropic_messages.pop(0)["content"]

        kwargs = dict(
            model=self._model,
            messages=anthropic_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = self._convert_tools_anthropic(tools)

        resp = await self._client.messages.create(**kwargs)  # type: ignore[union-attr]
        content_blocks = resp.content

        text = None
        tool_calls = []

        for block in content_blocks:
            if hasattr(block, "text") and block.text:
                text = (text or "") + block.text
            if hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        return text, tool_calls if tool_calls else None

    @staticmethod
    def _convert_tools_anthropic(openai_tools: list[dict]) -> list[dict]:
        """Convert OpenAI-format tool definitions to Anthropic format."""
        anthropic_tools = []
        for tool in openai_tools:
            if tool.get("type") == "function":
                fn = tool["function"]
                anthropic_tools.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {}),
                })
        return anthropic_tools

    # ── Streaming (OpenAI / custom only for now) ───────────────────

    async def stream(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from the LLM."""
        if self._provider == "anthropic":
            async for chunk in self._anthropic_stream(messages, tools, max_tokens, temperature):
                yield chunk
        else:
            async for chunk in self._openai_stream(messages, tools, max_tokens, temperature):
                yield chunk

    async def _openai_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        kwargs = dict(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        stream = await self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    async def _anthropic_stream(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        system_msg = None
        anthropic_messages = messages[:]
        if anthropic_messages and anthropic_messages[0].get("role") == "system":
            system_msg = anthropic_messages.pop(0)["content"]

        kwargs = dict(
            model=self._model,
            messages=anthropic_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )
        if system_msg:
            kwargs["system"] = system_msg
        if tools:
            kwargs["tools"] = self._convert_tools_anthropic(tools)

        async with self._client.messages.stream(**kwargs) as stream:  # type: ignore[union-attr]
            async for text in stream.text_stream:
                yield text
