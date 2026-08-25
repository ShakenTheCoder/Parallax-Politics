"""Database-backed 30-second Brief projection.

This module never substitutes the POC fixture. Missing momentum, appearance,
or opinion evidence remains missing in the public contract.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.activity_monitor import monitoring_state, window_hours
from app.intelligence.brief_watchlist import resolve_brief_watchlist
from app.intelligence.principal_scope import resolve_principal
from app.models.intelligence import IntelligenceSnapshot, SignalEvent
from app.models.political_activity import PoliticalActivity
from app.models.principal_identity import PrincipalIdentity
from app.models.user import User
from app.schemas.intelligence import (
    ActivityWindow,
    BriefAppearanceOut,
    BriefIdentityOut,
    BriefImportance,
    BriefMediaOpinionOut,
    BriefScoreOut,
    BriefViewOut,
)

_APPEARANCE_EVENT_TYPES = {
    "appearance",
    "broadcast_appearance",
    "interview",
    "public_appearance",
    "speech",
}
_IMPORTANCE = {"critical", "high", "medium", "low"}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value), 1)


def _integer(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _caption(signal: SignalEvent) -> str:
    appearance_description = (signal.provenance or {}).get("appearance_description")
    if isinstance(appearance_description, str) and appearance_description.strip():
        return appearance_description.strip()
    if signal.title and signal.title.strip():
        return signal.title.strip()
    content = " ".join(signal.content.split())
    return f"{content[:157]}…" if len(content) > 160 else content


def _opinion(snapshot: IntelligenceSnapshot) -> BriefMediaOpinionOut | None:
    payload = dict(snapshot.payload or {})
    summary = payload.get("summary") or payload.get("opinion")
    if not isinstance(summary, str) or not summary.strip() or not snapshot.evidence:
        return None
    raw_importance = str(payload.get("importance") or "").lower()
    importance: BriefImportance = raw_importance if raw_importance in _IMPORTANCE else "unrated"  # type: ignore[assignment]
    return BriefMediaOpinionOut(
        id=str(snapshot.id),
        summary=summary.strip(),
        importance=importance,
        generated_at=snapshot.effective_at,
        source_count=_integer(payload.get("source_count")) or len(snapshot.evidence or []),
    )


async def build_brief_view(
    db: AsyncSession,
    user: User,
    *,
    activity_window: ActivityWindow = "24h",
    profile_id=None,
) -> BriefViewOut:
    principal = await resolve_principal(db, user, profile_id)
    principal_identity = (
        await db.execute(
            select(PrincipalIdentity).where(PrincipalIdentity.profile_id == principal.id)
        )
    ).scalar_one_or_none()

    momentum = (
        await db.execute(
            select(IntelligenceSnapshot)
            .where(
                IntelligenceSnapshot.subject_id == principal.id,
                IntelligenceSnapshot.kind == "campaign_momentum",
            )
            .order_by(IntelligenceSnapshot.effective_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    momentum_payload = dict(momentum.payload or {}) if momentum and momentum.evidence else {}
    score = BriefScoreOut(
        value=_number(momentum_payload.get("score")),
        delta=_number(momentum_payload.get("delta")),
        updated_at=momentum.effective_at if momentum_payload else None,
    )

    watchlist = await resolve_brief_watchlist(
        db,
        principal=principal,
        principal_identity=principal_identity,
        momentum_payload=momentum_payload,
    )
    selected_hours = window_hours(activity_window)
    activity_now = datetime.now(UTC)
    current_start = activity_now - timedelta(hours=selected_hours)
    previous_start = current_start - timedelta(hours=selected_hours)
    figure_ids = [row.figure_id for row in watchlist if row.figure_id]
    activity_rows = (
        (
            await db.execute(
                select(PoliticalActivity).where(
                    PoliticalActivity.figure_id.in_(figure_ids),
                    PoliticalActivity.evidence_layer.in_({"direct_appearance", "public_statement"}),
                    PoliticalActivity.occurred_at >= previous_start,
                    PoliticalActivity.occurred_at <= activity_now,
                )
            )
        )
        .scalars()
        .all()
        if figure_ids
        else []
    )
    for row in watchlist:
        if not row.figure_id:
            continue
        current_count = sum(
            item.figure_id == row.figure_id and item.occurred_at >= current_start
            for item in activity_rows
        )
        previous_count = sum(
            item.figure_id == row.figure_id and item.occurred_at < current_start
            for item in activity_rows
        )
        row.analyzed_appearances = current_count
        row.monitoring_state = monitoring_state(current_count, previous_count)  # type: ignore[assignment]
    principal_row = next(item for item in watchlist if item.is_principal)

    cutoff = datetime.now(UTC) - timedelta(hours=36)
    appeared_at = func.coalesce(SignalEvent.published_at, SignalEvent.observed_at)
    signal_appearance_rows = (
        (
            await db.execute(
                select(SignalEvent)
                .where(
                    SignalEvent.subject_id == principal.id,
                    SignalEvent.event_type.in_(_APPEARANCE_EVENT_TYPES),
                    appeared_at >= cutoff,
                    appeared_at <= datetime.now(UTC),
                )
                .order_by(appeared_at.desc())
                .limit(20)
            )
        )
        .scalars()
        .all()
    )
    appearances = [
        BriefAppearanceOut(
            id=str(signal.id),
            caption=_caption(signal),
            source_name=signal.platform,
            source_url=signal.url,
            appeared_at=signal.published_at or signal.observed_at,
        )
        for signal in signal_appearance_rows
    ]
    activity_appearance_rows = (
        (
            await db.execute(
                select(PoliticalActivity)
                .where(
                    PoliticalActivity.figure_id == principal_row.figure_id,
                    PoliticalActivity.evidence_layer.in_({"direct_appearance", "public_statement"}),
                    PoliticalActivity.occurred_at >= cutoff,
                    PoliticalActivity.occurred_at <= datetime.now(UTC),
                )
                .order_by(PoliticalActivity.occurred_at.desc())
                .limit(20)
            )
        )
        .scalars()
        .all()
        if principal_row.figure_id
        else []
    )
    seen_urls = {item.source_url for item in appearances}
    appearances.extend(
        BriefAppearanceOut(
            id=str(activity.id),
            caption=activity.summary,
            source_name=activity.publisher,
            source_url=activity.direct_source_url,
            appeared_at=activity.occurred_at,
        )
        for activity in activity_appearance_rows
        if activity.direct_source_url not in seen_urls
    )
    appearances.sort(key=lambda item: item.appeared_at, reverse=True)
    appearances = appearances[:20]

    opinion_rows = (
        (
            await db.execute(
                select(IntelligenceSnapshot)
                .where(
                    IntelligenceSnapshot.subject_id == principal.id,
                    IntelligenceSnapshot.kind == "media_opinion_36h",
                )
                .order_by(IntelligenceSnapshot.effective_at.desc())
                .limit(4)
            )
        )
        .scalars()
        .all()
    )
    opinions = [item for row in opinion_rows if (item := _opinion(row)) is not None]
    has_intelligence = score.value is not None or bool(appearances) or bool(opinions)
    is_complete = (
        score.value is not None and len(watchlist) > 1 and bool(appearances) and bool(opinions)
    )

    return BriefViewOut(
        identity=BriefIdentityOut(
            name=principal.full_name,
            position=principal_row.position,
            portrait_url=principal_row.portrait_url,
        ),
        score=score,
        watchlist=watchlist,
        activity_window=activity_window,
        activity_window_hours=selected_hours,
        appearances=appearances,
        latest_opinion=opinions[0] if opinions else None,
        previous_opinions=opinions[1:4],
        data_status="live" if is_complete else "partial" if has_intelligence else "unavailable",
        notice=(
            "Only source-backed intelligence is shown. Missing scores, appearances, or opinions "
            "remain unavailable until their evidence snapshots exist."
        ),
    )
