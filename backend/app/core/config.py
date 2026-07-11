"""Application configuration with fail-fast validation."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="liquidity-platform", alias="APP_NAME")
    app_env: Literal["development", "local", "test", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )
    demo_auth_enabled: bool = Field(default=True, alias="DEMO_AUTH_ENABLED")
    feature_internal_analytics_stubs: bool = Field(
        default=False, alias="FEATURE_INTERNAL_ANALYTICS_STUBS"
    )
    contract_version: str = Field(default="1.0.0", alias="CONTRACT_VERSION")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    direct_database_url: str | None = Field(default=None, alias="DIRECT_DATABASE_URL")

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def require_database_configured(self) -> None:
        if not self.direct_database_url and not self.database_url:
            raise RuntimeError(
                "Database connection is not configured. Set DIRECT_DATABASE_URL "
                "(preferred) or DATABASE_URL in backend/.env — copy from .env.example."
            )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.require_database_configured()
    return settings
