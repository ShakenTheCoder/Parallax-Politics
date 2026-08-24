from app.agents._helpers import identity_query_seeds
from app.agents.base import AgentContext
from app.services.brief_runs import _ACTIVE_STATUSES
from app.worker import WorkerSettings


def test_brief_uses_confirmed_name_as_a_search_seed_while_pidaa_runs() -> None:
    ctx = AgentContext(
        run_id="run",
        situation_prompt="",
        subject_slug="sara-duterte",
        extra={"full_name": "Sara Duterte"},
    )

    assert identity_query_seeds(ctx)[:3] == [
        "Sara Duterte latest news",
        "Sara Duterte controversy",
        "Sara Duterte statement this week",
    ]


def test_daily_brief_cron_is_registered() -> None:
    assert any(job.coroutine.__name__ == "run_daily_briefs" for job in WorkerSettings.cron_jobs)
    assert len(_ACTIVE_STATUSES) == 2
