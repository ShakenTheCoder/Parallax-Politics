from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.intelligence.poc import WATCHLIST, analysis_center, compare_variants
from app.schemas.intelligence import AnalysisCenterOut, ScenarioComparisonCreate


def test_frozen_analysis_contract_contains_all_watchlist_figures() -> None:
    payload = AnalysisCenterOut.model_validate(analysis_center())
    assert len(payload.watchlist) == 6
    assert {item["name"] for item in payload.watchlist} == {item["name"] for item in WATCHLIST}
    assert {item["watch_status"] for item in payload.watchlist} == {"polled_hypothetical"}
    assert payload.command_view.rank is None
    assert payload.command_view.rank_suppressed is True


def test_every_curated_evidence_item_has_provenance_contract() -> None:
    required = {
        "url",
        "published_at",
        "captured_at",
        "geography",
        "rights",
        "classification_confidence",
        "observation_type",
    }
    for item in analysis_center()["evidence"]:
        assert required <= item.keys()


def test_poll_and_synthetic_layers_remain_explicit() -> None:
    payload = analysis_center()
    assert payload["latest_poll"]["layer"] == "polling"
    assert all(item["synthetic"] is True for item in payload["audience_lab"])
    assert all("vote_share" not in item for item in payload["audience_lab"])


def test_scenario_comparison_accepts_at_most_three_unique_variants() -> None:
    with pytest.raises(ValidationError):
        ScenarioComparisonCreate.model_validate(
            {
                "variants": [
                    {
                        "id": str(index),
                        "title": f"Variant {index}",
                        "message": "A sufficiently long public message.",
                    }
                    for index in range(4)
                ]
            }
        )
    with pytest.raises(ValidationError, match="unique"):
        ScenarioComparisonCreate.model_validate(
            {
                "variants": [
                    {
                        "id": "a",
                        "title": "Variant one",
                        "message": "A sufficiently long public message.",
                    },
                    {
                        "id": "a",
                        "title": "Variant two",
                        "message": "Another sufficiently long message.",
                    },
                ]
            }
        )


def test_scenario_fallback_is_qualitative_and_records_variance() -> None:
    result = compare_variants(
        [
            {
                "id": "a",
                "title": "Service proof",
                "message": "Lead with a source-backed completed service outcome.",
            }
        ]
    )
    assert result["provider_status"] == "frozen_deterministic_fallback"
    assert result["cohorts"] == 8
    assert result["results"][0]["sample_runs_per_cohort"] == 3
    assert 1 <= result["results"][0]["consensus"] <= 5
    assert "not polling or voter intent" in result["results"][0]["label"]
