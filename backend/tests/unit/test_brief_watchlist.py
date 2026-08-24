from __future__ import annotations

import pytest

from app.intelligence.brief_watchlist import build_watchlist_rows
from app.intelligence.watchlist import WATCHLIST
from app.models.political_figure import PoliticalFigure
from app.models.principal_identity import PrincipalIdentity
from app.models.profile import Profile


def _figure(
    canonical_name: str,
    *,
    aliases: list[str] | None = None,
    role: str,
) -> PoliticalFigure:
    return PoliticalFigure(
        slug=canonical_name.casefold().replace(" ", "-"),
        canonical_name=canonical_name,
        aliases=aliases or [],
        category="watchlist",
        current_role=role,
        status="active",
        portrait_url=f"https://images.example/{canonical_name.casefold().replace(' ', '-')}.jpg",
        data={},
        social_accounts=[],
        relationships=[],
        source_ledger=[],
        coverage_gaps=[],
        confidence=0.9,
    )


def _figures() -> list[PoliticalFigure]:
    return [
        _figure("Sara Duterte", role="Vice President of the Philippines"),
        _figure(
            "Leni Robredo",
            aliases=["Maria Leonor Robredo"],
            role="Mayor of Naga City",
        ),
        _figure("Raffy Tulfo", role="Senator of the Philippines"),
        _figure("Vince Dizon", role="Secretary of Public Works and Highways"),
        _figure(
            "Benjie Magalong",
            aliases=["Benjamin Magalong"],
            role="Mayor of Baguio City",
        ),
        _figure(
            "Nic Torre",
            aliases=["Nicolas Torre", "Nicolas Torre III"],
            role="General Manager of the Metropolitan Manila Development Authority",
        ),
    ]


def _profile(name: str) -> Profile:
    return Profile(
        slug=name.casefold().replace(" ", "-"),
        full_name=name,
        role_title="Stale profile role",
        pack_id="philippines_politics",
        identity={},
        career={},
        stances={},
        voice_patterns={},
        vulnerabilities={},
        allies_rivals={},
        media_footprint={},
    )


def test_watchlist_uses_glossary_roles_portraits_and_aliases() -> None:
    rows = build_watchlist_rows(
        principal=_profile("Sara Duterte"),
        principal_identity=PrincipalIdentity(profile_image_url="https://stale.example/sara.jpg"),
        figures=_figures(),
        momentum_payload={
            "watchlist": [{"name": "Benjie Magalong", "rank": 4, "score": 42.5, "delta": 1.2}]
        },
    )

    assert {row.name for row in rows} == {str(item["name"]) for item in WATCHLIST}
    assert len(rows) == 6
    assert sum(row.is_principal for row in rows) == 1
    assert all(row.portrait_url for row in rows)
    assert next(row for row in rows if row.name == "Sara Duterte").portrait_url == (
        "https://images.example/sara-duterte.jpg"
    )
    magalong = next(row for row in rows if row.name == "Benjamin Magalong")
    assert magalong.position == "Mayor of Baguio City"
    assert magalong.rank == 4
    assert magalong.score == 42.5


@pytest.mark.parametrize(
    ("account_name", "excluded_competitor_name"),
    [
        ("Sara Duterte", "Sara Duterte"),
        ("Maria Leonor Robredo", "Leni Robredo"),
        ("Raffy Tulfo", "Raffy Tulfo"),
        ("Vince Dizon", "Vince Dizon"),
        ("Benjie Magalong", "Benjamin Magalong"),
        ("Nicolas Torre III", "Nicolas Torre III"),
    ],
)
def test_signed_in_watchlist_figure_is_not_duplicated_as_a_competitor(
    account_name: str, excluded_competitor_name: str
) -> None:
    rows = build_watchlist_rows(
        principal=_profile(account_name),
        principal_identity=None,
        figures=_figures(),
        momentum_payload={"rank": 2, "score": 61.0, "delta": -0.4},
    )

    assert len(rows) == 6
    principal = next(row for row in rows if row.is_principal)
    assert principal.name == account_name
    assert principal.rank == 2
    assert principal.portrait_url is not None
    assert all(row.name != excluded_competitor_name for row in rows if not row.is_principal)
