"""Application settings, loaded from environment variables / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FinGuard AI"
    environment: str = "development"
    api_prefix: str = "/api"

    # Default to local SQLite so the stack runs with zero external services.
    # Docker Compose overrides this with a PostgreSQL URL.
    database_url: str = "sqlite:///./finguard.db"

    # Comma-separated list of allowed CORS origins.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Uploads
    max_upload_mb: int = 10
    max_batch_rows: int = 50_000

    # Risk tiers (probability cut-offs for the UI)
    risk_medium_cutoff: float = 0.30
    risk_high_cutoff: float = 0.70

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
