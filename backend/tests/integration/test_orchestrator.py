"""End-to-end orchestrator run with kill-switch (no external calls)."""
from sqlalchemy import select

from app.db import session_scope
from app.models.artifact import Artifact
from app.models.profile import Profile
from app.models.run import Run, RunStatus
from app.services.orchestrator import execute_run


async def test_full_dag_produces_both_artifacts():
    # Arrange: ensure seed profile exists.
    async with session_scope() as db:
        prof = (
            await db.execute(select(Profile).where(Profile.slug == "sara-duterte"))
        ).scalar_one_or_none()
        if not prof:
            prof = Profile(
                slug="sara-duterte",
                full_name="Sara Zimmerman Duterte-Carpio",
                role_title="VP",
                party="HNP",
            )
            db.add(prof)
            await db.flush()

        run = Run(
            subject_id=prof.id,
            situation_prompt="Test situation: confi funds optics.",
            status=RunStatus.queued,
        )
        db.add(run)
        await db.flush()
        rid = run.id

    # Act
    await execute_run(rid)

    # Assert: run completed and BOTH decision artifacts exist.
    async with session_scope() as db:
        run = (await db.execute(select(Run).where(Run.id == rid))).scalar_one()
        arts = (
            (await db.execute(select(Artifact).where(Artifact.run_id == rid)))
            .scalars()
            .all()
        )

    assert run.status == RunStatus.completed, f"got {run.status}, error={run.error}"
    kinds = {a.kind for a in arts}
    assert "perception_map" in kinds
    assert "action_card" in kinds
    assert "source_pack" in kinds  # SGA artifact
    # Strategist made a confident-or-fallback action card; either way, it persisted.
    ac = next(a for a in arts if a.kind == "action_card")
    assert ac.payload.get("what")
