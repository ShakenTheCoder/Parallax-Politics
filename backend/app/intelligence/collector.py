"""Safe public-web collection with Scrapling parsing.

The fetch boundary intentionally does not expose stealth, CAPTCHA, proxy
rotation, authentication, or anti-bot bypass features.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from scrapling import Selector

from app.intelligence.policy import (
    CollectionPolicyError,
    enforce_same_source,
    validate_public_destination,
)

_USER_AGENT = "ParallaxPublicIntelligence/1.0 (+authorized-public-research)"
_MAX_BODY_BYTES = 2_000_000
_MAX_TEXT_CHARS = 100_000
_MAX_REDIRECTS = 3


@dataclass(frozen=True)
class CollectedDocument:
    url: str
    title: str | None
    text: str
    content_hash: str
    content_type: str


class SafePublicWebCollector:
    async def collect(
        self,
        *,
        base_url: str,
        path: str,
        allowed_paths: list[str],
        robots_observed: bool,
        css_selector: str | None = None,
    ) -> CollectedDocument:
        target = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        enforce_same_source(target, base_url, allowed_paths)
        await validate_public_destination(target)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(12.0, connect=5.0),
            follow_redirects=False,
            headers={"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        ) as client:
            if robots_observed and not await self._robots_allowed(client, base_url, target):
                raise CollectionPolicyError("robots policy does not permit this collection path")
            response = await self._bounded_get(client, target, base_url, allowed_paths)

        content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise CollectionPolicyError(
                "registered public-web connector only accepts HTML documents"
            )
        body = response.content
        if not body or len(body) > _MAX_BODY_BYTES:
            raise CollectionPolicyError("source response is empty or exceeds the collection limit")

        page = Selector(
            body, url=str(response.url), huge_tree=False, keep_comments=False, adaptive=False
        )
        title_raw = page.css("title::text").get()
        title = self._clean_text(str(title_raw))[:500] if title_raw else None
        if css_selector:
            fragments = (
                page.css(css_selector)
                .xpath(
                    ".//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::noscript)]"
                )
                .getall()
            )
        else:
            fragments = page.xpath(
                "//body//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::noscript)]"
            ).getall()
        text = self._clean_text(" ".join(str(item) for item in fragments))[:_MAX_TEXT_CHARS]
        if len(text) < 40:
            raise CollectionPolicyError("source did not contain enough readable public text")
        digest = hashlib.sha256(f"{response.url}\n{text}".encode()).hexdigest()
        return CollectedDocument(
            url=str(response.url),
            title=title,
            text=text,
            content_hash=digest,
            content_type=content_type,
        )

    async def _bounded_get(
        self,
        client: httpx.AsyncClient,
        url: str,
        base_url: str,
        allowed_paths: list[str],
    ) -> httpx.Response:
        current = url
        for _ in range(_MAX_REDIRECTS + 1):
            await validate_public_destination(current)
            enforce_same_source(current, base_url, allowed_paths)
            response = await client.get(current)
            if response.status_code not in {301, 302, 303, 307, 308}:
                response.raise_for_status()
                return response
            location = response.headers.get("location")
            if not location:
                raise CollectionPolicyError("source returned an invalid redirect")
            current = urljoin(current, location)
        raise CollectionPolicyError("source exceeded the redirect limit")

    async def _robots_allowed(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        target: str,
    ) -> bool:
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            response = await self._bounded_get(client, robots_url, base_url, [])
        except (httpx.HTTPError, CollectionPolicyError):
            return False
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(response.text.splitlines())
        return parser.can_fetch(_USER_AGENT, target)

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
