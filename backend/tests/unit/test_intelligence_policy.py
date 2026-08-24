from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.intelligence.collector import SafePublicWebCollector
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
