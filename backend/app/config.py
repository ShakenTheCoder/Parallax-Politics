"""Application settings loaded from env (12-factor)."""
from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Core
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_port: int = 8000
    log_level: str = "INFO"

    # Database
    database_url: str = (
        "postgresql+asyncpg://parallax:parallax@localhost:5432/parallax"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 30  # 30d default for MVP

    # LLM / budget
    openrouter_api_key: str = ""
    llm_disabled: bool = False
    daily_budget_usd: float = 25.0
    per_run_budget_usd: float = 1.20
    daily_opus_budget_usd: float = 8.0

    # EXA
    exa_api_key: str = ""
    exa_daily_call_cap: int = 500

    # CORS
    cors_origins: str = "http://localhost:3000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # In development, ensure common localhost origins are included
        if self.app_env == "development":
            dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
            origins.extend([o for o in dev_origins if o not in origins])
        return list(dict.fromkeys(origins))  # dedupe while preserving order

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
