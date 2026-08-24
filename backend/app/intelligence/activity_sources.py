"""Approved source registry for the glossary-wide political activity monitor.

The registry is deliberately conservative. Public websites and publisher feeds
can be activated without credentials. Social-platform URLs remain visible but
disabled until a supported API or explicit account authorization is present.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.free_feeds import DEFAULT_FREE_FEEDS
from app.models.political_activity import PoliticalActivitySource
from app.models.political_figure import PoliticalFigure

_YOUTUBE_CHANNEL = re.compile(r"youtube\.com/channel/(UC[A-Za-z0-9_-]{20,})", re.I)
_CREDENTIALLED_PLATFORMS = {"facebook", "instagram", "tiktok", "x", "twitter"}


@dataclass(frozen=True)
class InstitutionalSource:
    name: str
    url: str
    publisher: str
    status: str
    figure_slug: str | None = None
    reliability_tier: str = "primary"


INSTITUTIONAL_SOURCES = (
    InstitutionalSource(
        "Senate press releases",
        "https://senate.gov.ph/media/news-release",
        "Senate of the Philippines",
        "blocked",
    ),
    InstitutionalSource(
        "House press releases",
        "https://www.congress.gov.ph/media/press-releases",
        "House of Representatives",
        "blocked",
    ),
    InstitutionalSource(
        "Philippine Information Agency press releases",
        "https://pia.gov.ph/press-releases/",
        "Philippine Information Agency",
        "review",
    ),
    InstitutionalSource(
        "Philippine News Agency national desk",
        "https://www.pna.gov.ph/categories/national",
        "Philippine News Agency",
        "blocked",
    ),
    InstitutionalSource(
        "Naga City News",
        "https://www2.naga.gov.ph/naga-city-news/",
        "City Government of Naga",
        "active",
        "leni-robredo",
    ),
    InstitutionalSource(
        "Baguio City News",
        "https://main.baguio.gov.ph/media/news",
        "City Government of Baguio",
        "active",
        "benjie-magalong",
    ),
)

MANDATORY_PUBLICATION_CATALOG = (
    ("ABS-CBN News", "https://www.abs-cbn.com/news", "review"),
    ("News5", "https://news.tv5.com.ph/", "review"),
    ("Manila Bulletin", "https://mb.com.ph/rss", "blocked"),
    ("SunStar", "https://www.sunstar.com.ph/", "review"),
    ("PCIJ", "https://pcij.org/", "review"),
    ("VERA Files", "https://verafiles.org/", "review"),
    ("Manila Standard", "https://manilastandard.net/", "review"),
    ("Presidential Communications Office", "https://pco.gov.ph/", "blocked"),
)


def _platform(account: dict[str, object]) -> str:
    raw = str(account.get("platform") or "website").strip().casefold()
    return "x" if raw == "twitter" else raw


def _account_source(
    figure: PoliticalFigure, account: dict[str, object]
) -> dict[str, object] | None:
    account_url = str(account.get("url") or "").strip()
    if not account_url.startswith(("https://", "http://")):
        return None
    platform = _platform(account)
    if platform == "youtube":
        match = _YOUTUBE_CHANNEL.search(account_url)
        if match:
            return {
                "url": f"https://www.youtube.com/feeds/videos.xml?channel_id={match.group(1)}",
                "name": f"YouTube · {figure.canonical_name}",
                "source_class": "official_account",
                "platform": "youtube",
                "access_method": "youtube_atom",
                "publisher": figure.canonical_name,
                "status": "needs_review",
                "rights": "youtube_metadata_excerpt_and_link",
                "reliability_tier": "primary",
                "metadata": {
                    "account_url": account_url,
                    "channel_id": match.group(1),
                    "verification": account.get("verification"),
                    "gap": "Superadmin must approve the account-to-person edge",
                },
            }
        return {
            "url": account_url,
            "name": f"YouTube · {figure.canonical_name}",
            "source_class": "official_account",
            "platform": "youtube",
            "access_method": "official_api",
            "publisher": figure.canonical_name,
            "status": "needs_channel_id",
            "rights": "youtube_metadata_excerpt_and_link",
            "reliability_tier": "primary",
            "metadata": {"account_url": account_url, "gap": "Canonical channel ID not verified"},
        }
    if platform in _CREDENTIALLED_PLATFORMS:
        return {
            "url": account_url,
            "name": f"{platform.title()} · {figure.canonical_name}",
            "source_class": "official_account",
            "platform": platform,
            "access_method": "official_api",
            "publisher": figure.canonical_name,
            "status": "authorization_required",
            "rights": "account_metadata_only_until_authorized",
            "reliability_tier": "primary",
            "metadata": {"account_url": account_url, "gap": "Supported API authorization required"},
        }
    return {
        "url": account_url,
        "name": f"Official website · {figure.canonical_name}",
        "source_class": "official_account",
        "platform": "website",
        "access_method": "scrapling",
        "publisher": figure.canonical_name,
        "status": "needs_review",
        "rights": "public_page_excerpt_and_link",
        "reliability_tier": "primary",
        "metadata": {
            "account_url": account_url,
            "allowed_path": urlparse(account_url).path or "/",
            "verification": account.get("verification"),
            "gap": "Public website connector requires access and selector review",
        },
    }


async def bootstrap_activity_sources(db: AsyncSession) -> list[PoliticalActivitySource]:
    """Synchronize evidence-backed glossary accounts and the publication allowlist."""

    existing = {
        row.url: row
        for row in ((await db.execute(select(PoliticalActivitySource))).scalars().all())
    }
    figures = list(
        (await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None))))
        .scalars()
        .all()
    )
    desired: list[tuple[PoliticalFigure | None, dict[str, object]]] = []
    for figure in figures:
        for account in figure.social_accounts or []:
            if source := _account_source(figure, account):
                desired.append((figure, source))

    for feed in DEFAULT_FREE_FEEDS:
        desired.append(
            (
                None,
                {
                    "url": feed.url,
                    "name": feed.name,
                    "source_class": "publisher",
                    "platform": "news",
                    "access_method": "rss",
                    "publisher": feed.name,
                    "status": "active",
                    "rights": "headline_excerpt_and_link",
                    "reliability_tier": "secondary",
                    "metadata": {"discovery_url": feed.discovery_url, "language": feed.language},
                },
            )
        )
    figures_by_slug = {figure.slug: figure for figure in figures}
    for source in INSTITUTIONAL_SOURCES:
        desired.append(
            (
                figures_by_slug.get(source.figure_slug) if source.figure_slug else None,
                {
                    "url": source.url,
                    "name": source.name,
                    "source_class": "institutional",
                    "platform": "website",
                    "access_method": "scrapling",
                    "publisher": source.publisher,
                    "status": source.status,
                    "rights": "public_page_excerpt_and_link",
                    "reliability_tier": source.reliability_tier,
                    "metadata": {"allowed_path": urlparse(source.url).path or "/"},
                },
            )
        )
    for name, url, source_status in MANDATORY_PUBLICATION_CATALOG:
        desired.append(
            (
                None,
                {
                    "url": url,
                    "name": name,
                    "source_class": "publisher",
                    "platform": "news",
                    "access_method": "scrapling",
                    "publisher": name,
                    "status": source_status,
                    "rights": "discovery_link_only_until_terms_review",
                    "reliability_tier": "secondary",
                    "metadata": {"allowed_path": urlparse(url).path or "/"},
                },
            )
        )

    rows: list[PoliticalActivitySource] = []
    now = datetime.now(UTC)
    for figure, definition in desired:
        url = str(definition["url"])
        row = existing.get(url)
        values = {
            "figure_id": figure.id if figure else None,
            "name": str(definition["name"]),
            "source_class": str(definition["source_class"]),
            "platform": str(definition["platform"]),
            "access_method": str(definition["access_method"]),
            "publisher": str(definition["publisher"]),
            "status": str(definition["status"]),
            "schedule_minutes": 15,
            "rights": str(definition["rights"]),
            "reliability_tier": str(definition["reliability_tier"]),
            "robots_observed": True,
            "source_metadata": dict(definition.get("metadata") or {}),
        }
        if row is None:
            row = PoliticalActivitySource(created_at=now, updated_at=now, url=url, **values)
            db.add(row)
            existing[url] = row
        else:
            for key, value in values.items():
                setattr(row, key, value)
        rows.append(row)
    await db.flush()
    return rows
