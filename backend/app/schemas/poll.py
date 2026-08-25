from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator, model_validator


class PollCreate(BaseModel):
    pollster: str = Field(min_length=2, max_length=200)
    sponsor: str | None = Field(default=None, max_length=200)
    published_at: date
    field_start: date
    field_end: date
    sample_size: int = Field(ge=1)
    population: str = Field(min_length=2, max_length=240)
    mode: str = Field(min_length=2, max_length=160)
    margin_of_error: str = Field(min_length=1, max_length=160)
    confidence_level: str | None = Field(default=None, max_length=80)
    exact_question: str = Field(min_length=10)
    geography: str = Field(min_length=2, max_length=160)
    results: list[dict[str, Any]] = Field(default_factory=list)
    source_url: AnyHttpUrl
    methodology_notes: str | None = None

    @model_validator(mode="after")
    def dates_are_ordered(self) -> PollCreate:
        if self.field_end < self.field_start or self.published_at < self.field_end:
            raise ValueError("poll publication and field dates must be chronological")
        return self

    @field_validator("results")
    @classmethod
    def result_rows_are_named(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if any(not isinstance(row.get("name"), str) for row in rows):
            raise ValueError("each poll result needs a name")
        return rows


class PollOut(PollCreate):
    id: UUID
    source_url: str
    verification_status: str
    verified_by: UUID | None = None
    verified_at: datetime | None = None
    verification_note: str | None = None
    created_at: datetime


class PollReview(BaseModel):
    decision: str = Field(pattern=r"^(verified|rejected)$")
    note: str = Field(min_length=3, max_length=2000)
