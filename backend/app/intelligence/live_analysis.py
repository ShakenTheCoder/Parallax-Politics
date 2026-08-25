"""Evidence-only Analysis Center projection.

This module deliberately computes counts and distributions from persisted
records. It never fills unavailable analytics with demo values.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.principal_scope import resolve_principal
from app.intelligence.watchlist import WATCHLIST
from app.models.intelligence import IntelligenceSnapshot, SignalEvent
from app.models.political_activity import PoliticalActivity
from app.models.political_figure import PoliticalFigure
from app.models.poll import Poll
from app.models.user import User
from app.schemas.intelligence import ActivityWindow, AnalysisCenterOut, CommandViewOut


def _hours(window: ActivityWindow) -> int:
    return {"6h": 6, "24h": 24, "7d": 168}[window]


def _figure_name(row: PoliticalFigure | None, fallback: str) -> str:
    return row.canonical_name if row else fallback


def _evidence(row: PoliticalActivity | SignalEvent) -> dict[str, Any]:
    if isinstance(row, PoliticalActivity):
        return {
            "id": str(row.id), "title": row.summary, "url": row.direct_source_url,
            "source": row.publisher, "published_at": row.published_at.isoformat() if row.published_at else None,
            "captured_at": row.created_at.isoformat(), "layer": row.evidence_layer,
            "rights": "public_web_attribution", "geography": row.geography.get("label", "Philippines"),
            "classification_confidence": row.evidence_confidence, "observation_type": "observed",
        }
    return {
        "id": str(row.id), "title": row.title or row.content[:160], "url": row.url,
        "source": row.platform, "published_at": row.published_at.isoformat() if row.published_at else None,
        "captured_at": row.observed_at.isoformat(), "layer": (row.provenance or {}).get("layer", "observed"),
        "rights": (row.provenance or {}).get("rights", "public_web_attribution"),
        "geography": (row.geography or {}).get("label", "Philippines"),
        "classification_confidence": (row.provenance or {}).get("confidence", 0.0), "observation_type": "observed",
    }


async def build_analysis_center(
    db: AsyncSession, user: User, *, window: ActivityWindow = "7d", profile_id: UUID | None = None
) -> AnalysisCenterOut:
    principal = await resolve_principal(db, user, profile_id)
    now = datetime.now(UTC)
    hours = _hours(window)
    start = now - timedelta(hours=hours)
    previous_start = start - timedelta(hours=hours)
    figures = list((await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None)))).scalars().all())
    by_slug = {figure.slug: figure for figure in figures}
    activities = list((await db.execute(select(PoliticalActivity).where(PoliticalActivity.occurred_at >= previous_start))).scalars().all())
    signals = list((await db.execute(select(SignalEvent).where(func.coalesce(SignalEvent.published_at, SignalEvent.observed_at) >= start))).scalars().all())

    core: list[dict[str, Any]] = []
    core_ids: set[UUID] = set()
    for item in WATCHLIST:
        figure = by_slug.get(item["slug"])
        if figure:
            core_ids.add(figure.id)
        current = sum(a.figure_id == figure.id and a.occurred_at >= start for a in activities) if figure else 0
        previous = sum(a.figure_id == figure.id and previous_start <= a.occurred_at < start for a in activities) if figure else 0
        core.append({
            "slug": item["slug"], "name": _figure_name(figure, item["name"]),
            "office": figure.current_role if figure else None, "watch_status": "research_watchlist",
            "activity_current": current, "activity_previous": previous,
            "movement": current - previous if current or previous else None,
            "momentum": None, "rank": None, "strongest_channel": None,
            "issue": None, "cadence": "observed" if current else "unavailable",
            "evidence_status": "observed" if current else "unavailable",
        })
    national = [
        {"slug": f.slug, "name": f.canonical_name, "office": f.current_role,
         "activity_current": sum(a.figure_id == f.id and a.occurred_at >= start for a in activities),
         "evidence_status": "observed" if any(a.figure_id == f.id and a.occurred_at >= start for a in activities) else "unavailable"}
        for f in figures if f.id not in core_ids
    ]
    source_counts: dict[str, int] = {}
    for row in activities:
        if row.occurred_at >= start:
            source_counts[row.publisher] = source_counts.get(row.publisher, 0) + 1
    latest_snapshot = (await db.execute(select(IntelligenceSnapshot).where(IntelligenceSnapshot.subject_id == principal.id, IntelligenceSnapshot.kind == "principal_analysis").order_by(IntelligenceSnapshot.effective_at.desc()).limit(1))).scalar_one_or_none()
    latest_poll = (await db.execute(select(Poll).where(Poll.verification_status == "verified").order_by(Poll.published_at.desc()).limit(1))).scalar_one_or_none()
    evidence = [_evidence(row) for row in [*activities[-20:], *signals[-20:]]]
    evidence.sort(key=lambda row: row["captured_at"], reverse=True)
    status = "live" if activities or signals else "unavailable"
    if activities and not signals:
        status = "partial"
    payload = {
        "snapshot": {"kind": "principal_analysis", "effective_at": now.isoformat(), "produced_by": "database_projection", "mode": status, "window": window, "notice": "Only persisted source-backed evidence is included; absent analytics remain null."},
        "election": {"label": "Expected regular presidential election", "date": "2028-05-08", "watchlist_label": "Six-person research watchlist; national glossary radar is separate"},
        "command_view": {"subject": principal.full_name, "watch_status": status, "score": None, "previous_score": None, "delta": None, "rank": None, "rank_suppressed": True, "coverage_confidence": 0.0, "freshness_minutes": int((now - latest_snapshot.effective_at).total_seconds() / 60) if latest_snapshot else None, "model_version": "principal-analysis-live-v1", "headline": "Momentum and rank are unavailable until eligible snapshots and competitor-wide coverage exist."},
        "momentum_components": [{"key": key, "label": key.replace("_", " ").title(), "weight": None, "score": None, "delta": None} for key in ("public_attention", "earned_media_visibility", "search_interest", "net_favorability")],
        "timeline": [], "watchlist": core, "national_radar": national,
        "channels": [{"name": name, "score": None, "coverage": None, "comparison": f"{count} observed records"} for name, count in source_counts.items()],
        "narratives": [], "appearances": [], "audience_lab": [], "latest_poll": ({"pollster": latest_poll.pollster, "published_at": latest_poll.published_at.isoformat(), "field_dates": f"{latest_poll.field_start.isoformat()}–{latest_poll.field_end.isoformat()}", "sample": latest_poll.sample_size, "population": latest_poll.population, "mode": latest_poll.mode, "margin_of_error": latest_poll.margin_of_error, "question": latest_poll.exact_question, "source_url": latest_poll.source_url, "results": latest_poll.results, "layer": "polling"} if latest_poll else None),
        "coverage": {"status": status, "window": window, "evidence_count": len(evidence), "note": "Coverage is computed from persisted records; no denominator is inferred."},
        "evidence": evidence, "provider_status": {"status": status, "source": "database"},
    }
    return AnalysisCenterOut.model_validate(payload)


async def build_command_view(db: AsyncSession, user: User, profile_id: UUID | None = None) -> CommandViewOut:
    data = await build_analysis_center(db, user, profile_id=profile_id)
    return data.command_view
