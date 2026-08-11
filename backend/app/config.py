"""Application settings loaded from env (12-factor)."""
from functools import lru_cache
from typing import Literal

from pydantic import computed_field, model_validator
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

    # Intelligence data plane (optional in local MVP, required for scaled ingestion)
    redpanda_brokers: str = "localhost:9092"
    object_store_endpoint: str = "http://127.0.0.1:9000"
    clickhouse_url: str = "http://127.0.0.1:8123"
    opensearch_url: str = "https://127.0.0.1:9200"

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60
    jwt_privileged_expires_minutes: int = 15
    jwt_issuer: str = "parallax-politics"
    jwt_audience: str = "parallax-web"
    login_attempt_limit: int = 5
    login_attempt_window_seconds: int = 900

    # LLM / budget
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_disabled: bool = False
    daily_budget_usd: float = 25.0
    per_run_budget_usd: float = 1.20
    daily_opus_budget_usd: float = 8.0

    # EXA
    exa_api_key: str = ""
    exa_daily_call_cap: int = 500

    # Meta Graph API
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_access_token: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1"

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
    def allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        placeholder = self.jwt_secret.lower().startswith(("change-me", "replace-"))
        if self.app_env == "production" and (placeholder or len(self.jwt_secret) < 32):
            raise ValueError("production JWT_SECRET must be a unique value of at least 32 characters")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
