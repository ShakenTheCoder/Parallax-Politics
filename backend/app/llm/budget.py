"""Token / cost budget governance backed by Redis atomic counters.

Three concurrent caps:
- daily_budget_usd       (global LLM spend across all models)
- daily_opus_budget_usd  (sub-cap, only escalation calls)
- per_run_budget_usd     (orchestrator scope, identified by run_id)

Each call goes through `reserve()` *before* the API call, then `commit(actual)`
once the response is in. `reserve` uses an optimistic INCRBYFLOAT and rolls
back if any cap is exceeded — this keeps the operation atomic without locks.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from redis.asyncio import Redis

from app.config import get_settings

_DAY_TTL: Final[int] = 60 * 60 * 36   # 36h, plenty of overlap for tz boundaries
_RUN_TTL: Final[int] = 60 * 60 * 6    # 6h per-run window


class BudgetExhaustedError(Exception):
    """Raised when an LLM call would exceed any active budget cap."""

    def __init__(self, scope: str, used: float, cap: float, requested: float):
        self.scope = scope
        self.used = used
        self.cap = cap
        self.requested = requested
        super().__init__(
            f"Budget exhausted [{scope}]: used=${used:.4f} requested=${requested:.4f} cap=${cap:.2f}"
        )


def _today_key() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


class TokenBudgetManager:
    """Redis-backed per-day + per-run cost guard."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        s = get_settings()
        self.daily_cap = s.daily_budget_usd
        self.daily_opus_cap = s.daily_opus_budget_usd
        self.per_run_cap = s.per_run_budget_usd

    # --- Keys --------------------------------------------------------------

    @staticmethod
    def _daily_key(day: str | None = None) -> str:
        return f"budget:daily:{day or _today_key()}"

    @staticmethod
    def _daily_opus_key(day: str | None = None) -> str:
        return f"budget:daily:opus:{day or _today_key()}"

    @staticmethod
    def _run_key(run_id: str) -> str:
        return f"budget:run:{run_id}"

    # --- Public API --------------------------------------------------------

    async def remaining_daily(self) -> float:
        used = float(await self.redis.get(self._daily_key()) or 0.0)
        return max(0.0, self.daily_cap - used)

    async def usage_snapshot(self) -> dict[str, float]:
        day = _today_key()
        daily = float(await self.redis.get(self._daily_key(day)) or 0.0)
        opus = float(await self.redis.get(self._daily_opus_key(day)) or 0.0)
        return {
            "day": day,
            "daily_used_usd": round(daily, 6),
            "daily_cap_usd": self.daily_cap,
            "daily_opus_used_usd": round(opus, 6),
            "daily_opus_cap_usd": self.daily_opus_cap,
        }

    async def check_and_reserve(
        self,
        *,
        cost_estimate: float,
        family: str,
        run_id: str | None = None,
    ) -> None:
        """Atomically reserve `cost_estimate`. Raises if any cap would break."""
        day_key = self._daily_key()
        opus_key = self._daily_opus_key()

        # Daily cap
        new_daily = await self.redis.incrbyfloat(day_key, cost_estimate)
        await self.redis.expire(day_key, _DAY_TTL)
        if new_daily > self.daily_cap:
            await self.redis.incrbyfloat(day_key, -cost_estimate)
            raise BudgetExhaustedError("daily", float(new_daily) - cost_estimate, self.daily_cap, cost_estimate)

        # Opus sub-cap
        if family == "opus":
            new_opus = await self.redis.incrbyfloat(opus_key, cost_estimate)
            await self.redis.expire(opus_key, _DAY_TTL)
            if new_opus > self.daily_opus_cap:
                await self.redis.incrbyfloat(opus_key, -cost_estimate)
                await self.redis.incrbyfloat(day_key, -cost_estimate)
                raise BudgetExhaustedError(
                    "daily_opus", float(new_opus) - cost_estimate, self.daily_opus_cap, cost_estimate
                )

        # Per-run cap
        if run_id is not None:
            run_key = self._run_key(run_id)
            new_run = await self.redis.incrbyfloat(run_key, cost_estimate)
            await self.redis.expire(run_key, _RUN_TTL)
            if new_run > self.per_run_cap:
                await self.redis.incrbyfloat(run_key, -cost_estimate)
                if family == "opus":
                    await self.redis.incrbyfloat(opus_key, -cost_estimate)
                await self.redis.incrbyfloat(day_key, -cost_estimate)
                raise BudgetExhaustedError(
                    "per_run", float(new_run) - cost_estimate, self.per_run_cap, cost_estimate
                )

    async def reconcile(
        self,
        *,
        estimated: float,
        actual: float,
        family: str,
        run_id: str | None = None,
    ) -> None:
        """Adjust counters by (actual - estimated) once the real bill is known."""
        delta = actual - estimated
        if abs(delta) < 1e-9:
            return
        await self.redis.incrbyfloat(self._daily_key(), delta)
        if family == "opus":
            await self.redis.incrbyfloat(self._daily_opus_key(), delta)
        if run_id is not None:
            await self.redis.incrbyfloat(self._run_key(run_id), delta)

    async def run_used(self, run_id: str) -> float:
        return float(await self.redis.get(self._run_key(run_id)) or 0.0)
