"""Admin / observability endpoints."""
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.llm.budget import TokenBudgetManager
from app.models.llm_call import LLMCall
from app.redis import get_redis

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/usage")
async def usage(db: DbSession, _user: CurrentUser) -> dict:
    """Token & cost rollups — last 24h, last 7d, plus live Redis budget snapshot."""
    budget = TokenBudgetManager(get_redis())
    snapshot = await budget.usage_snapshot()

    now = datetime.now(UTC)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    async def _rollup(since: datetime) -> dict:
        stmt = (
            select(
                LLMCall.model,
                LLMCall.agent,
                func.count(LLMCall.id),
                func.sum(LLMCall.input_tokens),
                func.sum(LLMCall.output_tokens),
                func.sum(LLMCall.cache_read_tokens),
                func.sum(LLMCall.cache_write_tokens),
                func.sum(LLMCall.cost_usd),
            )
            .where(LLMCall.created_at >= since)
            .group_by(LLMCall.model, LLMCall.agent)
        )
        rows = (await db.execute(stmt)).all()
        return {
            "by_model_agent": [
                {
                    "model": r[0],
                    "agent": r[1],
                    "calls": r[2],
                    "input_tokens": int(r[3] or 0),
                    "output_tokens": int(r[4] or 0),
                    "cache_read_tokens": int(r[5] or 0),
                    "cache_write_tokens": int(r[6] or 0),
                    "cost_usd": round(float(r[7] or 0.0), 6),
                }
                for r in rows
            ],
            "total_cost_usd": round(sum(float(r[7] or 0.0) for r in rows), 6),
        }

    return {
        "now": now.isoformat(),
        "budget": snapshot,
        "last_24h": await _rollup(since_24h),
        "last_7d": await _rollup(since_7d),
    }
