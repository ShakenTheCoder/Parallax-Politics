"""SRCA — Source Real Check Agent (Validator).

Lightweight URL validation utility that fast-checks whether URLs are reachable
and contain actual content. Agents import this module to verify sources before
using them in analysis.

Example:
    from app.utils.src_validator import validate_urls

    validations = await validate_urls(["https://example.com/article"])
    for v in validations:
        if v.is_valid:
            print(f"{v.url} is valid")
        else:
            print(f"{v.url} failed: {v.error}")
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar
from urllib.parse import urlparse

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = structlog.get_logger("SRCA")

# Cache of recently validated URLs: {url: (is_valid, timestamp)}
_validation_cache: dict[str, tuple[bool, float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes

# Known-good domains that get a small credibility boost
_TRUSTED_DOMAINS: set[str] = {
    "gov.ph",
    "senate.gov.ph",
    "congress.gov.ph",
    "comelec.gov.ph",
    "sc.judiciary.gov.ph",
    "rappler.com",
    "inquirer.net",
    "philstar.com",
    "manilatimes.net",
    "abs-cbn.com",
    "gmanetwork.com",
    "cnnphilippines.com",
    "newsinfo.inquirer.net",
    "mb.com.ph",
    "bworldonline.com",
}


@dataclass
class URLValidationResult:
    """Result of validating a single URL."""

    url: str
    is_valid: bool
    status_code: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    error: str | None = None
    checked_at: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    trusted_domain: bool = False

    # Class-level cache for known-good domains (fast path)
    _domain_cache: ClassVar[dict[str, bool]] = {}


@retry(
    retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=0.5, max=3),
    reraise=True,
)
async def _head_with_fallback(
    client: httpx.AsyncClient,
    url: str,
    timeout: float,  # noqa: ASYNC109
) -> httpx.Response:
    """Attempt HEAD request, fallback to GET if not supported."""
    try:
        response = await client.head(url, timeout=timeout, follow_redirects=True)
        # If HEAD returns 405 Method Not Allowed or 501 Not Implemented, try GET
        if response.status_code in (405, 501):
            response = await client.get(
                url, timeout=timeout, follow_redirects=True, headers={"Range": "bytes=0-1023"}
            )
        return response
    except httpx.HTTPStatusError as e:
        # For 4xx/5xx errors on HEAD, try GET as fallback for certain status codes
        if e.response.status_code in (405, 501, 503):
            return await client.get(
                url, timeout=timeout, follow_redirects=True, headers={"Range": "bytes=0-1023"}
            )
        raise


async def validate_url(
    url: str,
    timeout: float = 5.0,  # noqa: ASYNC109
    use_cache: bool = True,
    client: httpx.AsyncClient | None = None,
) -> URLValidationResult:
    """Fast-check a single URL for reachability and content presence.

    Args:
        url: The URL to validate.
        timeout: Request timeout in seconds (default: 5.0).
        use_cache: Whether to use/check the in-memory cache (default: True).
        client: Optional shared httpx client for connection pooling.

    Returns:
        URLValidationResult with validity status and metadata.
    """
    t0 = time.perf_counter()

    # Check cache first
    if use_cache and url in _validation_cache:
        is_valid, timestamp = _validation_cache[url]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            return URLValidationResult(
                url=url,
                is_valid=is_valid,
                error=None if is_valid else "Cached invalid result",
                response_time_ms=0.0,
            )

    # Parse and check domain trust
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        # Check for trusted TLDs/domains
        is_trusted = any(
            domain == trusted or domain.endswith(f".{trusted}") for trusted in _TRUSTED_DOMAINS
        )
    except Exception as e:
        return URLValidationResult(
            url=url,
            is_valid=False,
            error=f"URL parse error: {e}",
            response_time_ms=(time.perf_counter() - t0) * 1000,
        )

    # Validate URL has required components
    if not parsed.scheme or not parsed.netloc:
        return URLValidationResult(
            url=url,
            is_valid=False,
            error="Invalid URL: missing scheme or domain",
            response_time_ms=(time.perf_counter() - t0) * 1000,
        )

    # Only allow http/https
    if parsed.scheme not in ("http", "https"):
        return URLValidationResult(
            url=url,
            is_valid=False,
            error=f"Unsupported protocol: {parsed.scheme}",
            response_time_ms=(time.perf_counter() - t0) * 1000,
        )

    own_client = client is None
    try:
        if client is None:
            client = httpx.AsyncClient(
                http2=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                headers={
                    "User-Agent": "Parallax-SRCA/1.0 (Source Validation Bot)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "identity",  # Avoid compression issues
                },
            )

        try:
            response = await _head_with_fallback(client, url, timeout)
            response.raise_for_status()

            elapsed_ms = (time.perf_counter() - t0) * 1000

            # Check content type (should be text/* or application/*, not empty)
            content_type = response.headers.get("content-type", "").lower()

            # Check for content (either Content-Length or Transfer-Encoding)
            has_content = (
                response.headers.get("content-length") is not None
                or response.headers.get("transfer-encoding") == "chunked"
                or len(response.content) > 0  # For GET fallback
            )

            if not has_content and response.status_code == 200:
                # Try a small GET to verify content exists
                try:
                    get_resp = await client.get(
                        url,
                        timeout=timeout,
                        follow_redirects=True,
                        headers={"Range": "bytes=0-1023"},
                    )
                    has_content = len(get_resp.content) > 0
                except Exception:
                    has_content = False

            is_valid = response.status_code < 400 and has_content

            result = URLValidationResult(
                url=url,
                is_valid=is_valid,
                status_code=response.status_code,
                content_type=content_type.split(";")[0] if content_type else None,
                content_length=response.headers.get("content-length"),
                error=None if is_valid else "No content received",
                response_time_ms=elapsed_ms,
                trusted_domain=is_trusted,
            )

            # Update cache
            if use_cache:
                _validation_cache[url] = (is_valid, time.time())

            logger.debug(
                "url_validated",
                url=url,
                is_valid=is_valid,
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                trusted=is_trusted,
            )

            return result

        except httpx.HTTPStatusError as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            error_msg = f"HTTP {e.response.status_code}"

            # Special handling for common codes
            if e.response.status_code == 404:
                error_msg = "Page not found (404)"
            elif e.response.status_code == 403:
                error_msg = "Access forbidden (403) - may require authentication"
            elif e.response.status_code == 429:
                error_msg = "Rate limited (429)"
            elif e.response.status_code >= 500:
                error_msg = f"Server error ({e.response.status_code})"

            result = URLValidationResult(
                url=url,
                is_valid=False,
                status_code=e.response.status_code,
                error=error_msg,
                response_time_ms=elapsed_ms,
                trusted_domain=is_trusted,
            )

            if use_cache:
                _validation_cache[url] = (False, time.time())

            return result

        except httpx.TimeoutException:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return URLValidationResult(
                url=url,
                is_valid=False,
                error=f"Request timeout after {timeout}s",
                response_time_ms=elapsed_ms,
                trusted_domain=is_trusted,
            )

        except httpx.NetworkError as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return URLValidationResult(
                url=url,
                is_valid=False,
                error=f"Network error: {e}",
                response_time_ms=elapsed_ms,
                trusted_domain=is_trusted,
            )

    except Exception as e:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return URLValidationResult(
            url=url,
            is_valid=False,
            error=f"Validation error: {type(e).__name__}: {e}",
            response_time_ms=elapsed_ms,
            trusted_domain=is_trusted,
        )

    finally:
        if own_client:
            await client.aclose()


async def validate_urls(
    urls: list[str],
    *,
    concurrency: int = 5,
    timeout: float = 5.0,  # noqa: ASYNC109
    use_cache: bool = True,
) -> list[URLValidationResult]:
    """Validate multiple URLs with controlled concurrency.

    Args:
        urls: List of URLs to validate.
        concurrency: Maximum concurrent requests (default: 5).
        timeout: Per-request timeout in seconds (default: 5.0).
        use_cache: Whether to use the in-memory cache (default: True).

    Returns:
        List of URLValidationResult in the same order as input.
    """
    import asyncio

    if not urls:
        return []

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_urls: list[str] = []
    url_to_indices: dict[str, list[int]] = {}

    for i, url in enumerate(urls):
        url = url.strip()
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
            url_to_indices[url] = []
        url_to_indices[url].append(i)

    # Use shared client for connection pooling
    client = httpx.AsyncClient(
        http2=True,
        limits=httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency * 2),
        headers={
            "User-Agent": "Parallax-SRCA/1.0 (Source Validation Bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "identity",
        },
    )

    semaphore = asyncio.Semaphore(concurrency)

    async def _validate_with_semaphore(url: str) -> URLValidationResult:
        async with semaphore:
            return await validate_url(url, timeout=timeout, use_cache=use_cache, client=client)

    try:
        # Run all validations concurrently with semaphore control
        unique_results = await asyncio.gather(
            *[_validate_with_semaphore(url) for url in unique_urls],
            return_exceptions=True,
        )

        # Map exceptions to failed results
        processed_results: list[URLValidationResult] = []
        for url, result in zip(unique_urls, unique_results, strict=True):
            if isinstance(result, Exception):
                processed_results.append(
                    URLValidationResult(
                        url=url,
                        is_valid=False,
                        error=f"Exception during validation: {result}",
                    )
                )
            else:
                processed_results.append(result)

        # Expand back to original order with deduplicated results
        final_results: list[URLValidationResult | None] = [None] * len(urls)
        for url, result in zip(unique_urls, processed_results, strict=True):
            for idx in url_to_indices[url]:
                final_results[idx] = result

        return [r for r in final_results if r is not None]

    finally:
        await client.aclose()


def clear_validation_cache() -> None:
    """Clear the in-memory URL validation cache."""
    _validation_cache.clear()
    logger.info("validation_cache_cleared")


def get_cache_stats() -> dict[str, int]:
    """Get current cache statistics."""
    now = time.time()
    valid_count = sum(
        1 for v, t in _validation_cache.values() if v and now - t < _CACHE_TTL_SECONDS
    )
    invalid_count = sum(
        1 for v, t in _validation_cache.values() if not v and now - t < _CACHE_TTL_SECONDS
    )
    return {
        "total_entries": len(_validation_cache),
        "valid_entries": valid_count,
        "invalid_entries": invalid_count,
    }
