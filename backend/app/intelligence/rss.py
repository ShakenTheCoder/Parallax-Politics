"""Bounded ingestion for publisher-operated RSS and Atom feeds."""

from __future__ import annotations

import calendar
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from time import struct_time
from urllib.parse import urljoin, urlparse

import feedparser
import httpx

from app.intelligence.policy import CollectionPolicyError, validate_public_destination

_MAX_BODY_BYTES = 2_000_000
_MAX_TEXT_CHARS = 4_000
_USER_AGENT = "ParallaxPublicIntelligence/1.0 (+publisher-rss-research)"
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class FeedItem:
    external_id: str
    title: str
    summary: str
    url: str
    published_at: datetime | None
    content_hash: str


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(value)
    return _SPACE.sub(" ", " ".join(parser.parts)).strip()[:_MAX_TEXT_CHARS]


def _published(value: struct_time | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(calendar.timegm(value), tz=UTC)


def _same_origin(left: str, right: str) -> bool:
    a, b = urlparse(left), urlparse(right)
    return a.scheme == b.scheme and a.hostname == b.hostname and a.port == b.port


class PublisherFeedCollector:
    async def collect(self, feed_url: str, *, max_items: int, timeout_seconds: float) -> list[FeedItem]:
        await validate_public_destination(feed_url)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0)),
            follow_redirects=False,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            },
        ) as client:
            response = await client.get(feed_url)
            if response.is_redirect:
                location = urljoin(feed_url, response.headers.get("location", ""))
                if not location or not _same_origin(feed_url, location):
                    raise CollectionPolicyError("RSS redirects must remain on the registered origin")
                await validate_public_destination(location)
                response = await client.get(location)
            response.raise_for_status()

        if not response.content or len(response.content) > _MAX_BODY_BYTES:
            raise CollectionPolicyError("RSS response is empty or exceeds the collection limit")
        parsed = feedparser.parse(response.content, resolve_relative_uris=False, sanitize_html=True)
        if parsed.bozo and not parsed.entries:
            raise CollectionPolicyError("Publisher feed is not valid RSS or Atom")

        items: list[FeedItem] = []
        for entry in parsed.entries[:max_items]:
            title = _plain_text(str(entry.get("title") or ""))
            summary = _plain_text(str(entry.get("summary") or entry.get("description") or ""))
            url = str(entry.get("link") or "").strip()
            if not title or not url or urlparse(url).scheme not in {"http", "https"}:
                continue
            published_at = _published(entry.get("published_parsed") or entry.get("updated_parsed"))
            external_id = str(entry.get("id") or entry.get("guid") or url)[:240]
            digest = hashlib.sha256(f"{url}\n{title}\n{summary}".encode()).hexdigest()
            items.append(
                FeedItem(
                    external_id=external_id,
                    title=title,
                    summary=summary,
                    url=url,
                    published_at=published_at,
                    content_hash=digest,
                )
            )
        return items
