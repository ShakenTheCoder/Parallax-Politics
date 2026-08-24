"""BaseAgent — common run lifecycle for every Parallax Politics agent.

Each agent declares:
- `name`: registry id used in logs / event bus / DB.
- `default_tier`: which model tier it lives on (override per-call when needed).
- `max_cost_usd`: per-run hard cap; exceeded calls raise BudgetExhaustedError.

Subclasses implement `_run(ctx)` returning an AgentResult.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import structlog

from app.eventbus.bus import publish_event
from app.llm.router import ModelTier
from app.schemas.agents import AgentResult


@dataclass
class AgentContext:
    """Shared per-run state passed between agents."""

    run_id: UUID | str | None
    situation_prompt: str
    subject_slug: str | None = None
    pack_id: str | None = None
    upstream: dict[str, AgentResult] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str) -> AgentResult | None:
        return self.upstream.get(name)


class BaseAgent(ABC):
    name: str = "base"
    default_tier: ModelTier = ModelTier.default
    max_cost_usd: float = 0.20

    def __init__(self) -> None:
        self.log = structlog.get_logger(self.name)

    @abstractmethod
    async def _run(self, ctx: AgentContext) -> AgentResult: ...

    async def run(self, ctx: AgentContext) -> AgentResult:
        await publish_event(
            f"run.{ctx.run_id}",
            {"type": "agent.started", "agent": self.name},
        )
        t0 = time.perf_counter()
        try:
            result = await self._run(ctx)
        except Exception as exc:
            self.log.exception("agent.failed", error=str(exc))
            await publish_event(
                f"run.{ctx.run_id}",
                {"type": "agent.failed", "agent": self.name, "error": str(exc)},
            )
            raise
        result.agent = self.name
        latency_ms = int((time.perf_counter() - t0) * 1000)
        await publish_event(
            f"run.{ctx.run_id}",
            {
                "type": "agent.completed",
                "agent": self.name,
                "model": result.model,
                "cost_usd": result.cost_usd,
                "latency_ms": latency_ms,
            },
        )
        return result
