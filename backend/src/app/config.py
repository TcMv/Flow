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
    app_version: str = "0.1.0"
    debug: bool = False

    # ── Security ─────────────────────────────────────────────────
    secret_key: str = "change-me-to-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./flow_dev.db"


settings = Settings()
