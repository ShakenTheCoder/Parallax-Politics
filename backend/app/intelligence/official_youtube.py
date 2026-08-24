"""Collect attributable public appearances from official YouTube Atom feeds."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.appearance_classifier import classify_owned_youtube_appearance
from app.intelligence.brief_watchlist import normalize_public_name, public_name_keys
from app.intelligence.policy import CollectionPolicyError
from app.intelligence.rss import PublisherFeedCollector
from app.models.intelligence import CollectionSource, SignalEvent
from app.models.political_figure import PoliticalFigure
from app.models.profile import Profile
from app.models.source import Source

_CHANNEL_ID = re.compile(r"youtube\.com/channel/(UC[A-Za-z0-9_-]{20,})", re.I)


@dataclass
class YouTubeCollectionResult:
    feeds_checked: int = 0
    entries_seen: int = 0
    signals_created: int = 0
    duplicates: int = 0
    unmatched: int = 0
    appearances_created: int = 0
    errors: list[str] = field(default_factory=list)


def _youtube_channels(figure: PoliticalFigure) -> list[tuple[str, str]]:
    channels: list[tuple[str, str]] = []
    for account in figure.social_accounts or []:
        if str(account.get("platform") or "").casefold() != "youtube":
            continue
        url = str(account.get("url") or "")
        match = _CHANNEL_ID.search(url)
        if match:
            channels.append((match.group(1), url))
    return list(dict.fromkeys(channels))


def _profile_figure_pairs(
    profiles: list[Profile], figures: list[PoliticalFigure]
) -> list[tuple[Profile, PoliticalFigure]]:
    index = {key: figure for figure in figures for key in public_name_keys(figure)}
    return [
        (profile, figure)
        for profile in profiles
        if (figure := index.get(normalize_public_name(profile.full_name))) is not None
    ]


async def _collection_source(
    db: AsyncSession,
    *,
    figure: PoliticalFigure,
    channel_id: str,
    account_url: str,
) -> CollectionSource:
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    source = (
        await db.execute(select(CollectionSource).where(CollectionSource.base_url == feed_url))
    ).scalar_one_or_none()
    if source:
        return source
    source = CollectionSource(
        name=f"YouTube · {figure.canonical_name}",
        base_url=feed_url,
        connector_kind="official_api",
        authority="official_api",
        status="active",
        schedule_minutes=15,
        robots_observed=True,
        allowed_paths=[],
        source_metadata={
            "policy_version": "youtube-atom-appearance-v1",
            "channel_id": channel_id,
            "account_url": account_url,
            "figure_id": str(figure.id),
            "source_rights": "youtube_metadata_and_link",
        },
    )
    db.add(source)
    await db.flush()
    return source


async def _source_record(
    db: AsyncSession,
    source: CollectionSource,
    *,
    url: str,
    title: str,
    excerpt: str,
    published_at: datetime | None,
    content_hash: str,
) -> Source:
    row = (await db.execute(select(Source).where(Source.url == url))).scalar_one_or_none()
    if row:
        return row
    row = Source(
        url=url,
        domain=urlparse(url).hostname or "youtube.com",
        title=title,
        excerpt=excerpt[:1000],
        published_at=published_at.isoformat() if published_at else None,
        credibility_score=0.8,
        content_hash=content_hash,
        extra={
            "authority": "official_youtube_atom",
            "collection_source_id": str(source.id),
            "rights": "youtube_metadata_and_link",
        },
    )
    db.add(row)
    await db.flush()
    return row


async def collect_official_youtube_appearances(
    db: AsyncSession,
    *,
    max_items_per_feed: int,
    timeout_seconds: float,
) -> YouTubeCollectionResult:
    result = YouTubeCollectionResult()
    profiles = list((await db.execute(select(Profile))).scalars().all())
    figures = list(
        (await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None))))
        .scalars()
        .all()
    )
    collector = PublisherFeedCollector()
    now = datetime.now(UTC)

    for profile, figure in _profile_figure_pairs(profiles, figures):
        for channel_id, account_url in _youtube_channels(figure):
            source = await _collection_source(
                db,
                figure=figure,
                channel_id=channel_id,
                account_url=account_url,
            )
            try:
                items = await collector.collect(
                    source.base_url,
                    max_items=max_items_per_feed,
                    timeout_seconds=timeout_seconds,
                )
            except (CollectionPolicyError, httpx.HTTPError) as exc:
                result.errors.append(f"{source.name}: {type(exc).__name__}")
                continue
            result.feeds_checked += 1
            result.entries_seen += len(items)
            for item in items:
                decision = classify_owned_youtube_appearance(item, figure.canonical_name)
                if not decision:
                    result.unmatched += 1
                    continue
                duplicate = (
                    await db.execute(
                        select(SignalEvent.id).where(
                            SignalEvent.subject_id == profile.id,
                            or_(
                                SignalEvent.content_hash == item.content_hash,
                                SignalEvent.url == item.url,
                            ),
                        )
                    )
                ).scalar_one_or_none()
                if duplicate:
                    result.duplicates += 1
                    continue
                source_row = await _source_record(
                    db,
                    source,
                    url=item.url,
                    title=item.title,
                    excerpt=item.summary,
                    published_at=item.published_at,
                    content_hash=item.content_hash,
                )
                db.add(
                    SignalEvent(
                        subject_id=profile.id,
                        collection_source_id=source.id,
                        source_id=source_row.id,
                        external_id=item.external_id,
                        platform=source.name,
                        event_type="public_appearance",
                        language="und",
                        title=item.title,
                        content=item.summary or item.title,
                        url=item.url,
                        published_at=item.published_at,
                        observed_at=now,
                        engagement={},
                        geography={"scope": "Philippines", "basis": "public_figure_channel"},
                        provenance={
                            "authority": "official_youtube_atom",
                            "connector": "official_api",
                            "captured_at": now.isoformat(),
                            "source_rights": "youtube_metadata_and_link",
                            "classification_confidence": decision.confidence,
                            "classification_basis": decision.basis,
                            "appearance_kind": decision.kind,
                            "appearance_description": decision.description,
                            "observation_type": "inferred_from_attributable_metadata",
                            "is_inference": True,
                            "account_url": account_url,
                        },
                        content_hash=item.content_hash,
                        is_public=True,
                    )
                )
                result.signals_created += 1
                result.appearances_created += 1
            source.last_collected_at = now
            await db.flush()
    return result
