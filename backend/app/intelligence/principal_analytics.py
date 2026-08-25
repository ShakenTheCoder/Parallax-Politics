"""Project persisted evidence into principal-scoped analytics snapshots."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from app.db import SessionLocal
from app.intelligence.brief_watchlist import normalize_public_name
from app.models.intelligence import IntelligenceSnapshot, SignalEvent
from app.models.political_activity import PoliticalActivity
from app.models.political_figure import PoliticalFigure
from app.models.profile import Profile
from app.telemetry.logging import get_logger

log = get_logger(__name__)


def _same_person(profile: Profile, figure: PoliticalFigure) -> bool:
    profile_name = normalize_public_name(profile.full_name)
    names = {normalize_public_name(figure.canonical_name), *(normalize_public_name(a) for a in (figure.aliases or []))}
    return profile_name in names or any(name in profile_name or profile_name in name for name in names)


async def project_principal_analytics(_: dict[str, Any] | None = None) -> int:
    """Persist a 24-hour observed activity snapshot for every principal."""
    now = datetime.now(UTC)
    start = now - timedelta(hours=24)
    async with SessionLocal() as db:
        profiles = list((await db.execute(select(Profile))).scalars().all())
        figures = list((await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None)))).scalars().all())
        activities = list((await db.execute(select(PoliticalActivity).where(PoliticalActivity.occurred_at >= start))).scalars().all())
        signal_time = func.coalesce(SignalEvent.published_at, SignalEvent.observed_at)
        signals = list((await db.execute(select(SignalEvent).where(signal_time >= start))).scalars().all())
        created = 0
        for profile in profiles:
            figure_ids = {figure.id for figure in figures if _same_person(profile, figure)}
            principal_activities = [row for row in activities if row.figure_id in figure_ids]
            principal_signals = [row for row in signals if row.subject_id == profile.id]
            by_type = {
                "direct_appearances": sum(row.appearance_type in {"appearance", "broadcast_appearance", "interview", "public_appearance"} for row in principal_activities),
                "public_statements": sum(row.evidence_layer == "public_statement" for row in principal_activities),
                "indirect_coverage": sum(row.evidence_layer == "indirect_coverage" for row in principal_activities),
                "public_reactions": sum(row.evidence_layer == "public_reaction" for row in principal_activities),
            }
            source_counts: dict[str, int] = {}
            for row in [*principal_activities, *principal_signals]:
                source = row.publisher if isinstance(row, PoliticalActivity) else row.platform
                source_counts[source] = source_counts.get(source, 0) + 1
            payload = {
                "status": "live" if principal_activities or principal_signals else "unavailable",
                "activity_metrics": [
                    {"key": key, "label": key.replace("_", " ").title(), "value": value, "window": "24h", "source_count": len(source_counts)}
                    for key, value in by_type.items()
                ],
                "signal_count": len(principal_signals),
                "activity_count": len(principal_activities),
                "source_count": len(source_counts),
                "coverage": {"evidence_records": len(principal_activities) + len(principal_signals), "window": "24h"},
            }
            db.add(IntelligenceSnapshot(subject_id=profile.id, kind="principal_analysis", scope_key="principal", window_start=start, window_end=now, effective_at=now, payload=payload, evidence=[{"id": str(row.id), "url": row.direct_source_url if isinstance(row, PoliticalActivity) else row.url} for row in [*principal_activities, *principal_signals][:100]], produced_by="PrincipalAnalyticsService", model_version="principal-analysis-v1", confidence=1.0 if principal_activities or principal_signals else 0.0))
            created += 1
        await db.commit()
        log.info("principal.analytics.projected", principals=created)
        return created
