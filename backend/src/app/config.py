"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Flow backend settings — loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "Flow"
    app_version: str = "0.1.1"
    debug: bool = False

    # ── Security ─────────────────────────────────────────────────
    secret_key: str = "change-me-to-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./flow_dev.db"

    # ── LLM Key Encryption ───────────────────────────────────────
    # Fernet master key for encrypting LLM API keys at rest.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str | None = None

    # ── LLM Env Var Fallback ─────────────────────────────────────
    # If no LLM key is stored in the DB, fall back to these env vars.
    # This makes it easy to get started without the key management UI.
    flow_api_key: str | None = None
    flow_llm_provider: str = "openai"
    flow_llm_model: str = "gpt-4o-mini"
    flow_llm_base_url: str | None = None
    # For DeepSeek: provider=custom, model=deepseek-chat, base_url=https://api.deepseek.com


settings = Settings()
