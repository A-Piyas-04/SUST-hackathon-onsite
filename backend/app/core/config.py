"""Environment/config loading for the backend.

Owner: Member 1. Every secret is loaded from the environment (via .env locally) —
never hardcode a connection string, API key, or credential here or anywhere else.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, sourced from environment variables / .env.

    See backend/.env.example for the full list of variable names and comments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

    # Async SQLAlchemy connection string (asyncpg driver). Points at local
    # Postgres (docker-compose.yml) in dev; swap for the Supabase pooled
    # connection string in later phases without changing any code.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/liquidity_platform"

    # Sync driver variant used only by migrations/run_migrations.py.
    MIGRATIONS_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/liquidity_platform"

    # Supabase — optional in this phase, wired for later phases.
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the environment is only parsed once."""
    return Settings()
