"""TokenBudgetManager — hard caps + reconciliation."""
import pytest

from app.config import get_settings
from app.llm.budget import BudgetExhaustedError, TokenBudgetManager
from app.redis import get_redis


@pytest.fixture
async def fresh_budget():
    """Wipe today's budget keys before each test so caps are deterministic.

    Also resets the process-wide Redis singleton so each test gets a client
    bound to the current event loop (pytest-asyncio creates a new loop per test).
    """
    from app import redis as redis_module

    await redis_module.close_redis()
    r = get_redis()
    s = get_settings()
    keys = await r.keys("budget:*")
    if keys:
        await r.delete(*keys)
    yield TokenBudgetManager(r), s


async def test_daily_cap_enforced(fresh_budget):
    b, s = fresh_budget
    # First reservation: just under cap → ok.
    await b.check_and_reserve(cost_estimate=s.daily_budget_usd - 0.01, family="sonnet")
    # Second reservation that crosses cap should raise.
    with pytest.raises(BudgetExhaustedError) as exc:
        await b.check_and_reserve(cost_estimate=0.50, family="sonnet")
    assert exc.value.scope == "daily"


async def test_opus_subcap_enforced(fresh_budget):
    b, s = fresh_budget
    # Opus sub-cap is the binding constraint here ($5 vs $25 daily).
    await b.check_and_reserve(cost_estimate=s.daily_opus_budget_usd - 0.01, family="opus")
    with pytest.raises(BudgetExhaustedError) as exc:
        await b.check_and_reserve(cost_estimate=0.20, family="opus")
    assert exc.value.scope == "daily_opus"


async def test_per_run_cap_enforced(fresh_budget):
    b, s = fresh_budget
    rid = "test-run-aaa"
    await b.check_and_reserve(cost_estimate=s.per_run_budget_usd - 0.001, family="sonnet", run_id=rid)
    with pytest.raises(BudgetExhaustedError) as exc:
        await b.check_and_reserve(cost_estimate=0.10, family="sonnet", run_id=rid)
    assert exc.value.scope == "per_run"


async def test_failed_reservation_rolls_back(fresh_budget):
    b, s = fresh_budget
    # First, consume most of the daily cap.
    await b.check_and_reserve(cost_estimate=s.daily_budget_usd - 0.05, family="sonnet")
    # Attempt a reservation that will breach: it must roll back its own delta.
    used_before = (await b.usage_snapshot())["daily_used_usd"]
    with pytest.raises(BudgetExhaustedError):
        await b.check_and_reserve(cost_estimate=1.0, family="sonnet")
    used_after = (await b.usage_snapshot())["daily_used_usd"]
    assert abs(used_after - used_before) < 1e-6


async def test_reconcile_adjusts_counter(fresh_budget):
    b, _ = fresh_budget
    await b.check_and_reserve(cost_estimate=0.10, family="sonnet")
    # Actual was cheaper.
    await b.reconcile(estimated=0.10, actual=0.04, family="sonnet")
    snap = await b.usage_snapshot()
    assert abs(snap["daily_used_usd"] - 0.04) < 1e-6
