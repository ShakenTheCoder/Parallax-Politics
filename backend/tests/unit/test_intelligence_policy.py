from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from scrapling.engines.toolbelt.custom import Response

from app.intelligence import collector as collector_module
from app.intelligence.collector import SafePublicWebCollector, _BrowserRequestGuard
from app.intelligence.policy import (
    CollectionPolicyError,
    enforce_cohort_privacy,
    enforce_same_source,
    validate_public_destination,
)
from app.schemas.intelligence import CollectionSourceCreate


async def test_private_destination_is_rejected() -> None:
    with pytest.raises(CollectionPolicyError, match="private or reserved"):
        await validate_public_destination("http://127.0.0.1/")


def test_cross_origin_collection_is_rejected() -> None:
    with pytest.raises(CollectionPolicyError, match="registered source"):
        enforce_same_source("https://attacker.example/report", "https://official.example", [])


def test_source_path_allowlist_is_enforced() -> None:
    with pytest.raises(CollectionPolicyError, match="outside"):
        enforce_same_source(
            "https://official.example/private/report",
            "https://official.example",
            ["/news/"],
        )


def test_sparse_cohort_is_suppressed() -> None:
    with pytest.raises(CollectionPolicyError, match="minimum publishable"):
        enforce_cohort_privacy(99)
    enforce_cohort_privacy(100)


def test_collector_normalizes_untrusted_page_text() -> None:
    assert SafePublicWebCollector._clean_text("  one\n\t two   three ") == "one two three"


async def test_public_collection_uses_scrapling_stealth_fetcher(monkeypatch) -> None:
    fetch_calls: list[tuple[str, dict[str, object]]] = []

    async def fake_fetch(url: str, **kwargs: object) -> Response:
        fetch_calls.append((url, kwargs))
        challenged = len(fetch_calls) == 1
        return Response(
            url=url,
            content=(
                "<html><head><title>Just a moment...</title></head><body>cf-chl-test</body></html>"
                if challenged
                else (
                    "<html><head><title>Public report</title></head>"
                    "<body>Enough readable public text for the bounded collection test fixture.</body>"
                    "</html>"
                )
            ),
            status=403 if challenged else 200,
            reason="Forbidden" if challenged else "OK",
            cookies={},
            headers={"content-type": "text/html; charset=utf-8"},
            request_headers={},
            huge_tree=False,
            adaptive=False,
        )

    monkeypatch.setattr(collector_module, "validate_public_destination", AsyncMock())
    collector = SafePublicWebCollector(browser_fetch=fake_fetch)
    monkeypatch.setattr(collector, "_robots_allowed", AsyncMock(return_value=True))

    document = await collector.collect(
        base_url="https://official.example",
        path="/news/report",
        allowed_paths=["/news/"],
        robots_observed=True,
    )

    assert document.title == "Public report"
    assert len(fetch_calls) == 2
    _, first_options = fetch_calls[0]
    _, options = fetch_calls[1]
    assert first_options["solve_cloudflare"] is False
    assert options["solve_cloudflare"] is True
    assert options["hide_canvas"] is True
    assert options["block_webrtc"] is True
    assert options["load_dom"] is True
    assert options["google_search"] is False
    assert options["additional_args"] == {"service_workers": "block"}
    assert callable(options["page_setup"])


async def test_stealth_browser_guard_blocks_cross_origin_navigation(monkeypatch) -> None:
    monkeypatch.setattr(collector_module, "validate_public_destination", AsyncMock())
    guard = _BrowserRequestGuard("https://official.example", ["/news/"])
    route = SimpleNamespace(
        request=SimpleNamespace(
            url="https://attacker.example/news/report",
            is_navigation_request=lambda: True,
        ),
        abort=AsyncMock(),
        fallback=AsyncMock(),
    )

    await guard.handle(route)

    route.abort.assert_awaited_once_with("blockedbyclient")
    route.fallback.assert_not_awaited()
    assert guard.violation is not None
    assert "registered source" in str(guard.violation)


def test_public_collection_requires_scrapling_and_robots_policy() -> None:
    with pytest.raises(ValidationError, match="scrapling connector"):
        CollectionSourceCreate(
            name="Public source",
            base_url="https://example.com",
            authority="public_web",
            connector_kind="official_api",
            allowed_paths=["/news/"],
        )
    with pytest.raises(ValidationError, match="robots policy"):
        CollectionSourceCreate(
            name="Public source",
            base_url="https://example.com",
            authority="public_web",
            connector_kind="scrapling",
            robots_observed=False,
            allowed_paths=["/news/"],
        )


def test_representative_evidence_cannot_use_public_scraping_connector() -> None:
    with pytest.raises(ValidationError, match="licensed_feed connector"):
        CollectionSourceCreate(
            name="Representative survey",
            base_url="https://polling.example.com",
            authority="representative_poll",
            connector_kind="scrapling",
            allowed_paths=["/results/"],
        )
