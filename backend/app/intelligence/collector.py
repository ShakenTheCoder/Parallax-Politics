"""Bounded public-web collection with Scrapling's stealth browser fetcher."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from scrapling import StealthyFetcher

from app.intelligence.policy import (
    CollectionPolicyError,
    enforce_same_source,
    validate_public_destination,
)

_ROBOTS_USER_AGENT = "ParallaxPublicIntelligence/1.0 (+authorized-public-research)"
_MAX_BODY_BYTES = 2_000_000
_MAX_TEXT_CHARS = 100_000
_MAX_REDIRECTS = 3

BrowserFetch = Callable[..., Awaitable[Any]]


@dataclass(frozen=True)
class CollectedDocument:
    url: str
    title: str | None
    text: str
    content_hash: str
    content_type: str


class _BrowserRequestGuard:
    """Keep browser navigation inside the registered source and all traffic public."""

    def __init__(self, base_url: str, allowed_paths: list[str]) -> None:
        self._base_url = base_url
        self._allowed_paths = allowed_paths
        self._navigation_count = 0
        self.violation: CollectionPolicyError | None = None

    async def install(self, page: Any) -> None:
        await page.route("**/*", self.handle)
        await page.context.route("**/*", self.handle)
        await page.context.route_web_socket("**/*", self._block_websocket)

    @staticmethod
    async def _block_websocket(route: Any) -> None:
        await route.close(code=1008, reason="collector network policy")

    async def handle(self, route: Any) -> None:
        request = route.request
        try:
            await validate_public_destination(request.url)
            if request.is_navigation_request():
                self._navigation_count += 1
                if self._navigation_count > _MAX_REDIRECTS + 1:
                    raise CollectionPolicyError("source exceeded the redirect limit")
                enforce_same_source(request.url, self._base_url, self._allowed_paths)
        except CollectionPolicyError as exc:
            self.violation = exc
            await route.abort("blockedbyclient")
            return
        # Let Scrapling's own route handler apply resource blocking after this guard.
        await route.fallback()


class SafePublicWebCollector:
    def __init__(self, *, browser_fetch: BrowserFetch | None = None) -> None:
        self._browser_fetch = browser_fetch or StealthyFetcher.async_fetch

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

        if robots_observed:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(12.0, connect=5.0),
                follow_redirects=False,
                headers={"User-Agent": _ROBOTS_USER_AGENT, "Accept": "text/plain"},
            ) as client:
                if not await self._robots_allowed(client, base_url, target):
                    raise CollectionPolicyError("robots policy does not permit this collection path")

        response = await self._stealth_get(
            target, base_url, allowed_paths, solve_cloudflare=False
        )
        if self._requires_challenge_retry(response):
            response = await self._stealth_get(
                target, base_url, allowed_paths, solve_cloudflare=True
            )

        final_url = str(response.url)
        await validate_public_destination(final_url)
        enforce_same_source(final_url, base_url, allowed_paths)
        status = int(response.status)
        if status >= 400:
            raise CollectionPolicyError(f"source returned HTTP {status}")

        content_type = str(response.headers.get("content-type", "")).split(";", 1)[0].lower()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise CollectionPolicyError(
                "registered public-web connector only accepts HTML documents"
            )
        body = response.body
        if not body or len(body) > _MAX_BODY_BYTES:
            raise CollectionPolicyError("source response is empty or exceeds the collection limit")

        title_raw = response.css("title::text").get()
        title = self._clean_text(str(title_raw))[:500] if title_raw else None
        if css_selector:
            fragments = (
                response.css(css_selector)
                .xpath(
                    ".//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::noscript)]"
                )
                .getall()
            )
        else:
            fragments = response.xpath(
                "//body//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::noscript)]"
            ).getall()
        text = self._clean_text(" ".join(str(item) for item in fragments))[:_MAX_TEXT_CHARS]
        if len(text) < 40:
            raise CollectionPolicyError("source did not contain enough readable public text")
        digest = hashlib.sha256(f"{final_url}\n{text}".encode()).hexdigest()
        return CollectedDocument(
            url=final_url,
            title=title,
            text=text,
            content_hash=digest,
            content_type=content_type,
        )

    async def _stealth_get(
        self,
        target: str,
        base_url: str,
        allowed_paths: list[str],
        *,
        solve_cloudflare: bool,
    ) -> Any:
        guard = _BrowserRequestGuard(base_url, allowed_paths)
        try:
            response = await self._browser_fetch(
                target,
                headless=True,
                disable_resources=True,
                block_ads=True,
                block_webrtc=True,
                hide_canvas=True,
                solve_cloudflare=solve_cloudflare,
                google_search=False,
                network_idle=True,
                load_dom=True,
                timeout=12_000,
                retries=1,
                page_setup=guard.install,
                additional_args={"service_workers": "block"},
                selector_config={
                    "huge_tree": False,
                    "keep_comments": False,
                    "adaptive": True,
                },
            )
        except Exception as exc:
            if guard.violation:
                raise guard.violation from exc
            raise CollectionPolicyError(f"stealth browser fetch failed: {exc}") from exc
        if guard.violation:
            raise guard.violation
        return response

    @staticmethod
    def _requires_challenge_retry(response: Any) -> bool:
        if int(response.status) in {403, 503}:
            return True
        body = bytes(response.body).lower()
        return any(
            marker in body
            for marker in (b"cf-chl-", b"checking your browser", b"just a moment...")
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
        return parser.can_fetch("*", target)

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()
