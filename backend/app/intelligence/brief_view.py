"""Database-backed 30-second Brief projection.

This module never substitutes the POC fixture. Missing momentum, appearance,
or opinion evidence remains missing in the public contract.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competitor import Competitor
from app.models.intelligence import IntelligenceSnapshot, SignalEvent
from app.models.principal_identity import PrincipalIdentity
from app.models.profile import Profile
from app.models.user import User
from app.schemas.intelligence import (
    BriefAppearanceOut,
    BriefIdentityOut,
    BriefImportance,
    BriefMediaOpinionOut,
    BriefScoreOut,
    BriefViewOut,
    BriefWatchlistRatingOut,
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
    importance: BriefImportance = (
        raw_importance if raw_importance in _IMPORTANCE else "unrated"
    )  # type: ignore[assignment]
    return BriefMediaOpinionOut(
        id=str(snapshot.id),
        summary=summary.strip(),
        importance=importance,
        generated_at=snapshot.effective_at,
        source_count=_integer(payload.get("source_count")) or len(snapshot.evidence or []),
    )


async def _profile_visuals(
    db: AsyncSession, profile_ids: set[Any]
) -> dict[Any, tuple[Profile, PrincipalIdentity | None]]:
    if not profile_ids:
        return {}
    rows = (
        await db.execute(
            select(Profile, PrincipalIdentity)
            .outerjoin(PrincipalIdentity, PrincipalIdentity.profile_id == Profile.id)
            .where(Profile.id.in_(profile_ids))
        )
    ).all()
    return {profile.id: (profile, identity) for profile, identity in rows}


async def build_brief_view(db: AsyncSession, user: User) -> BriefViewOut:
    if not user.principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No principal linked to this account",
        )
    principal = await db.get(Profile, user.principal_id)
    if not principal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Principal not found")
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

    competitors = (
        (
            await db.execute(
                select(Competitor)
                .where(
                    Competitor.profile_id == principal.id,
                    Competitor.effective_to.is_(None),
                )
                .order_by(Competitor.name)
            )
        )
        .scalars()
        .all()
    )
    linked_ids = {
        competitor.competitor_profile_id
        for competitor in competitors
        if competitor.competitor_profile_id is not None
    }
    visuals = await _profile_visuals(db, linked_ids)
    ratings_by_name = {
        str(item.get("name", "")).casefold(): item
        for item in momentum_payload.get("watchlist", [])
        if isinstance(item, dict) and item.get("name")
    }
    watchlist: list[BriefWatchlistRatingOut] = [
        BriefWatchlistRatingOut(
            is_principal=True,
            rank=_integer(momentum_payload.get("rank")),
            name=principal.full_name,
            position=principal.role_title,
            portrait_url=principal_identity.profile_image_url if principal_identity else None,
            score=score.value,
            delta=score.delta,
        )
    ]
    for competitor in competitors:
        linked = visuals.get(competitor.competitor_profile_id)
        linked_profile = linked[0] if linked else None
        linked_identity = linked[1] if linked else None
        name = linked_profile.full_name if linked_profile else competitor.name
        rating = ratings_by_name.get(name.casefold(), {})
        watchlist.append(
            BriefWatchlistRatingOut(
                is_principal=False,
                rank=_integer(rating.get("rank")),
                name=name,
                position=linked_profile.role_title if linked_profile else None,
                portrait_url=linked_identity.profile_image_url if linked_identity else None,
                score=_number(rating.get("score")),
                delta=_number(rating.get("delta")),
            )
        )
    watchlist.sort(key=lambda item: (item.rank is None, item.rank or 10_000, item.name))

    cutoff = datetime.now(UTC) - timedelta(hours=36)
    appeared_at = func.coalesce(SignalEvent.published_at, SignalEvent.observed_at)
    appearance_rows = (
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
        for signal in appearance_rows
    ]

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
            position=principal.role_title,
            portrait_url=principal_identity.profile_image_url if principal_identity else None,
        ),
        score=score,
        watchlist=watchlist,
        appearances=appearances,
        latest_opinion=opinions[0] if opinions else None,
        previous_opinions=opinions[1:4],
        data_status="live" if is_complete else "partial" if has_intelligence else "unavailable",
        notice=(
            "Only source-backed intelligence is shown. Missing scores, appearances, or opinions "
            "remain unavailable until their evidence snapshots exist."
        ),
    )
