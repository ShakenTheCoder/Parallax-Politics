"""Queue and execute provider-backed qualitative audience experiments."""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select

from app.db import session_scope
from app.llm.client import get_llm_client
from app.llm.router import ModelTier
from app.models.artifact import Artifact
from app.models.audience_experiment import AudienceExperimentRun
from app.models.profile import Profile
from app.models.run import Run, RunStatus
from app.schemas.audience_experiment import AudienceExperimentCreate

CRITERIA = ("clarity", "relevance", "credibility", "objection_risk", "recall", "sharing_inclination")
COHORTS = (
    {"id": "metro_young", "label": "Metro young adults", "basis": "NCR, ages 18–30"},
    {"id": "luzon_working", "label": "Luzon working adults", "basis": "Balance Luzon, ages 31–59"},
    {"id": "luzon_rural", "label": "Luzon rural households", "basis": "Balance Luzon, rural adults"},
    {"id": "visayas_youth", "label": "Visayas young adults", "basis": "Visayas, ages 18–30"},
    {"id": "visayas_families", "label": "Visayas working families", "basis": "Visayas, ages 31–59"},
    {"id": "mindanao_youth", "label": "Mindanao young adults", "basis": "Mindanao, ages 18–30"},
    {"id": "mindanao_communities", "label": "Mindanao working communities", "basis": "Mindanao, mixed adult ages"},
    {"id": "older_news", "label": "Older news followers", "basis": "Philippines, ages 60+"},
)


def _out(row: AudienceExperimentRun) -> dict[str, Any]:
    return {key: getattr(row, key) for key in ("id", "run_id", "profile_id", "variants", "cohorts", "status", "provider_status", "samples", "aggregate", "error", "created_at", "started_at", "finished_at")}


async def enqueue_experiment(db, *, profile: Profile, requested_by: UUID, payload: AudienceExperimentCreate) -> AudienceExperimentRun:
    run = Run(subject_id=profile.id, requested_by=requested_by, situation_prompt="Audience Lab qualitative experiment", meta={"kind": "audience_experiment", "profile_id": str(profile.id), "full_name": profile.full_name})
    db.add(run)
    await db.flush()
    experiment = AudienceExperimentRun(profile_id=profile.id, run_id=run.id, variants=[item.model_dump() for item in payload.variants], cohorts=[dict(cohort) for cohort in COHORTS])
    db.add(experiment)
    await db.flush()
    return experiment


def _validate_sample(payload: dict[str, Any], variants: list[dict[str, Any]], cohorts: list[dict[str, Any]]) -> dict[str, Any]:
    evaluations = payload.get("evaluations")
    if not isinstance(evaluations, list):
        raise ValueError("provider response did not include evaluations")
    expected = {(variant["id"], cohort["id"]) for variant in variants for cohort in cohorts}
    seen: set[tuple[str, str]] = set()
    clean: list[dict[str, Any]] = []
    for row in evaluations:
        if not isinstance(row, dict) or (row.get("variant_id"), row.get("cohort_id")) not in expected:
            continue
        key = (row["variant_id"], row["cohort_id"])
        if key in seen:
            continue
        scores = row.get("criteria")
        if not isinstance(scores, dict) or any(not isinstance(scores.get(name), (int, float)) or not 1 <= float(scores[name]) <= 5 for name in CRITERIA):
            raise ValueError("provider returned an incomplete audience rubric")
        seen.add(key)
        clean.append({"variant_id": key[0], "cohort_id": key[1], "criteria": {name: float(scores[name]) for name in CRITERIA}, "note": str(row.get("note") or "")[:1000]})
    if seen != expected:
        raise ValueError("provider did not evaluate every configured cohort and variant")
    return {"evaluations": clean}


def _aggregate(samples: list[dict[str, Any]], variants: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {"samples": len(samples), "criteria": list(CRITERIA), "variants": {variant["id"]: {} for variant in variants}}
    for variant in variants:
        rows = [row for sample in samples for row in sample["evaluations"] if row["variant_id"] == variant["id"]]
        for criterion in CRITERIA:
            values = [row["criteria"][criterion] for row in rows]
            result["variants"][variant["id"]][criterion] = {"consensus": round(statistics.fmean(values), 2), "variance": round(statistics.pvariance(values), 3) if len(values) > 1 else 0.0, "observations": len(values)}
    return result


async def execute_audience_experiment(experiment_id: UUID) -> None:
    async with session_scope() as db:
        experiment = await db.get(AudienceExperimentRun, experiment_id)
        if not experiment:
            return
        experiment.status = "running"
        experiment.provider_status = "running"
        experiment.started_at = datetime.now(UTC)
        await db.flush()
        try:
            system = "You are Audience Scenario Agent. Evaluate message clarity, relevance, credibility, objection risk, recall, and sharing inclination on a 1-5 qualitative rubric. Do not predict individuals, vote share, targeting, or best segments. Return JSON with evaluations containing every variant/cohort pair."
            user_prompt = {"variants": experiment.variants, "cohorts": experiment.cohorts, "criteria": list(CRITERIA)}
            client = get_llm_client()
            samples: list[dict[str, Any]] = []
            for sample_index in range(3):
                response = await client.complete(agent="AudienceScenarioAgent", system=system, messages=[{"role": "user", "content": f"Sample {sample_index + 1}. Evaluate all pairs.\n{user_prompt}"}], tier=ModelTier.default, max_tokens=5000, temperature=0.4, run_id=experiment.run_id, json_mode=True)
                samples.append(_validate_sample(response.json_payload or {}, experiment.variants, experiment.cohorts))
            experiment.samples = samples
            experiment.aggregate = _aggregate(samples, experiment.variants)
            experiment.status = "completed"
            experiment.provider_status = "available"
            experiment.finished_at = datetime.now(UTC)
            run = await db.get(Run, experiment.run_id)
            if run:
                run.status = RunStatus.completed
                run.finished_at = experiment.finished_at
            db.add(Artifact(run_id=experiment.run_id, kind="audience_experiment", payload={"aggregate": experiment.aggregate, "samples": samples}, produced_by="AudienceScenarioAgent", confidence=None))
        except Exception as exc:
            experiment.status = "failed"
            experiment.provider_status = "unavailable"
            experiment.error = str(exc)[:2000]
            experiment.finished_at = datetime.now(UTC)
            run = await db.get(Run, experiment.run_id)
            if run:
                run.status = RunStatus.failed
                run.error = experiment.error
                run.finished_at = experiment.finished_at


async def list_experiments(db, profile_id: UUID) -> list[AudienceExperimentRun]:
    return list((await db.execute(select(AudienceExperimentRun).where(AudienceExperimentRun.profile_id == profile_id).order_by(desc(AudienceExperimentRun.created_at)).limit(50))).scalars().all())
