from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.api.v1.intelligence import get_brief_view
from app.intelligence.brief_view import _number, _opinion
from app.models.intelligence import IntelligenceSnapshot
from app.schemas.intelligence import BriefViewOut


def test_brief_allows_honest_missing_intelligence() -> None:
    payload = BriefViewOut.model_validate(
        {
            "identity": {"name": "Test Principal", "position": None, "portrait_url": None},
            "score": {"value": None, "delta": None, "updated_at": None},
            "watchlist": [],
            "appearances": [],
            "latest_opinion": None,
            "previous_opinions": [],
            "data_status": "unavailable",
            "notice": "No evidence snapshot exists.",
        }
    )
    assert payload.score.value is None
    assert payload.appearances_window_hours == 36
    assert payload.data_status == "unavailable"


def test_brief_opinion_importance_is_a_word_rubric() -> None:
    now = datetime.now(UTC)
    base = {
        "identity": {"name": "Test Principal"},
        "score": {},
        "watchlist": [],
        "appearances": [],
        "latest_opinion": {
            "id": "opinion-1",
            "summary": "A source-backed summary.",
            "importance": "high",
            "generated_at": now,
            "source_count": 2,
        },
        "previous_opinions": [],
        "data_status": "partial",
        "notice": "Partial evidence.",
    }
    assert BriefViewOut.model_validate(base).latest_opinion.importance == "high"  # type: ignore[union-attr]
    base["latest_opinion"]["importance"] = 82  # type: ignore[index]
    with pytest.raises(ValidationError):
        BriefViewOut.model_validate(base)


def test_brief_keeps_only_three_previous_opinions() -> None:
    opinion = {
        "id": "opinion",
        "summary": "A source-backed summary.",
        "importance": "medium",
        "generated_at": datetime.now(UTC),
        "source_count": 1,
    }
    with pytest.raises(ValidationError):
        BriefViewOut.model_validate(
            {
                "identity": {"name": "Test Principal"},
                "score": {},
                "watchlist": [],
                "appearances": [],
                "latest_opinion": opinion,
                "previous_opinions": [{**opinion, "id": str(index)} for index in range(4)],
                "data_status": "partial",
                "notice": "Partial evidence.",
            }
        )


def test_brief_route_does_not_call_poc_fixture() -> None:
    source = inspect.getsource(get_brief_view)
    assert "build_brief_view" in source
    assert "command_view" not in source
    assert "analysis_center" not in source


def test_boolean_is_not_accepted_as_a_numeric_score() -> None:
    assert _number(True) is None


def test_opinion_reports_publishers_not_evidence_item_count() -> None:
    now = datetime.now(UTC)
    snapshot = IntelligenceSnapshot(
        subject_id=None,
        kind="media_opinion_36h",
        scope_key="philippines:public-media:36h",
        window_start=now,
        window_end=now,
        effective_at=now,
        payload={"summary": "Source-backed assessment.", "source_count": 3},
        evidence=[{"signal_id": str(index)} for index in range(13)],
        produced_by="test",
        model_version="test-v1",
        confidence=0.75,
    )

    opinion = _opinion(snapshot)

    assert opinion is not None
    assert opinion.source_count == 3
