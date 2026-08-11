"""EXA search wrapper with caching, daily quota, and credibility scoring."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import orjson
import structlog
from exa_py import Exa

from app.config import get_settings
from app.redis import get_redis
from app.search.credibility import credibility_for, domain_of

log = structlog.get_logger(__name__)


_CACHE_TTL_S = 60 * 60 * 24  # 24h
_QUOTA_TTL_S = 60 * 60 * 36


class ExaQuotaExceeded(Exception):
    """Daily EXA call cap reached."""


@dataclass
class ExaSearchResult:
    url: str
    domain: str
    title: str | None
    published_at: str | None
    excerpt: str | None
    credibility_score: float
    score: float | None = None  # EXA relevance
    extra: dict[str, Any] | None = None


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def _cache_key(query: str, *, num_results: int, kind: str) -> str:
    h = hashlib.sha1(f"{kind}|{num_results}|{query.lower().strip()}".encode()).hexdigest()
    return f"exa:cache:{h}"


def _quota_key() -> str:
    return f"exa:quota:{_today()}"


class ExaClient:
    """Async-friendly thin wrapper over exa_py (which is sync under the hood)."""

    def __init__(self) -> None:
        s = get_settings()
        if not s.exa_api_key:
            raise RuntimeError("EXA_API_KEY is not set")
        self._daily_cap = s.exa_daily_call_cap
        self._exa = Exa(api_key=s.exa_api_key)
        self._redis = get_redis()

    # --- Public API --------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        include_text: bool = True,
        text_chars: int = 600,
        start_published_date: str | None = None,
    ) -> list[ExaSearchResult]:
        key = _cache_key(query, num_results=num_results, kind="search")
        cached = await self._redis.get(key)
        if cached:
            return [ExaSearchResult(**r) for r in orjson.loads(cached)]

        await self._reserve_quota()

        # exa_py is sync; run in default executor to keep the loop responsive.
        import asyncio

        loop = asyncio.get_running_loop()
        try:
            resp = await loop.run_in_executor(
                None,
                lambda: self._exa.search_and_contents(
                    query,
                    num_results=num_results,
                    text={"max_characters": text_chars} if include_text else False,
                    start_published_date=start_published_date,
                    type="auto",
                ),
            )
        except Exception as exc:
            log.warning("exa.error", error=str(exc))
            raise

        results = self._normalize(resp)
        await self._redis.setex(key, _CACHE_TTL_S, orjson.dumps([r.__dict__ for r in results]))
        return results

    async def usage_snapshot(self) -> dict[str, Any]:
        used = int(await self._redis.get(_quota_key()) or 0)
        return {"day": _today(), "calls_used": used, "calls_cap": self._daily_cap}

    # --- Internals ---------------------------------------------------------

    async def _reserve_quota(self) -> None:
        new_count = await self._redis.incr(_quota_key())
        await self._redis.expire(_quota_key(), _QUOTA_TTL_S)
        if new_count > self._daily_cap:
            await self._redis.decr(_quota_key())
            raise ExaQuotaExceeded(f"EXA daily cap reached: {new_count - 1}/{self._daily_cap}")

    def _normalize(self, resp: Any) -> list[ExaSearchResult]:
        out: list[ExaSearchResult] = []
        for r in getattr(resp, "results", []) or []:
            url = getattr(r, "url", None) or ""
            if not url:
                continue
            dom = domain_of(url)
            out.append(
                ExaSearchResult(
                    url=url,
                    domain=dom,
                    title=getattr(r, "title", None),
                    published_at=getattr(r, "published_date", None),
                    excerpt=(getattr(r, "text", None) or "")[:600] or None,
                    credibility_score=credibility_for(url),
                    score=getattr(r, "score", None),
                )
            )
        # Sort: credibility * relevance (default relevance 0.5 if missing)
        out.sort(
            key=lambda x: x.credibility_score * (x.score if x.score is not None else 0.5),
            reverse=True,
        )
        return out


_singleton: ExaClient | None = None


def get_exa_client() -> ExaClient:
    global _singleton
    if _singleton is None:
        _singleton = ExaClient()
    return _singleton
