from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AudienceVariant(BaseModel):
    id: str = Field(min_length=1, max_length=60, pattern=r"^[A-Za-z0-9_-]+$")
    title: str = Field(min_length=3, max_length=120)
    message: str = Field(min_length=20, max_length=2000)


class AudienceExperimentCreate(BaseModel):
    profile_id: UUID | None = None
    variants: list[AudienceVariant] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def unique_ids(self) -> AudienceExperimentCreate:
        if len({item.id for item in self.variants}) != len(self.variants):
            raise ValueError("variant ids must be unique")
        return self


class AudienceExperimentOut(BaseModel):
    id: UUID
    run_id: UUID
    profile_id: UUID
    variants: list[dict[str, Any]]
    cohorts: list[dict[str, Any]]
    status: str
    provider_status: str
    samples: list[dict[str, Any]]
    aggregate: dict[str, Any]
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
