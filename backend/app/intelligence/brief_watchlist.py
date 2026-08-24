"""Resolve the Brief watchlist through the maintained political glossary."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.watchlist import WATCHLIST
from app.models.political_figure import PoliticalFigure
from app.models.principal_identity import PrincipalIdentity
from app.models.profile import Profile
from app.schemas.intelligence import BriefWatchlistRatingOut

_NAME_SEPARATOR = re.compile(r"[^a-z0-9]+")


def normalize_public_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return _NAME_SEPARATOR.sub(" ", ascii_value.casefold()).strip()


def public_name_keys(figure: PoliticalFigure) -> set[str]:
    values = [figure.canonical_name, *(figure.aliases or [])]
    return {normalize_public_name(value) for value in values if value}


def _figure_index(figures: list[PoliticalFigure]) -> dict[str, PoliticalFigure]:
    result: dict[str, PoliticalFigure] = {}
    for figure in figures:
        for key in public_name_keys(figure):
            result.setdefault(key, figure)
    return result


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value), 1)


def _rank(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _rating_index(momentum_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    rows = momentum_payload.get("watchlist", [])
    if not isinstance(rows, list):
        return result
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("name"), str):
            result[normalize_public_name(row["name"])] = row
    return result


def _rating_for(
    display_name: str,
    figure: PoliticalFigure | None,
    ratings: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    keys = {normalize_public_name(display_name)}
    if figure:
        keys.update(public_name_keys(figure))
    return next((ratings[key] for key in keys if key in ratings), {})


def build_watchlist_rows(
    *,
    principal: Profile,
    principal_identity: PrincipalIdentity | None,
    figures: list[PoliticalFigure],
    momentum_payload: dict[str, Any],
) -> list[BriefWatchlistRatingOut]:
    """Build one race-defined watchlist with glossary-backed roles and portraits."""

    figures_by_name = _figure_index(figures)
    ratings = _rating_index(momentum_payload)
    principal_figure = figures_by_name.get(normalize_public_name(principal.full_name))
    principal_keys = {normalize_public_name(principal.full_name)}
    if principal_figure:
        principal_keys.update(public_name_keys(principal_figure))

    ordered_rows: list[tuple[int, BriefWatchlistRatingOut]] = []
    principal_was_in_watchlist = False
    for order, definition in enumerate(WATCHLIST):
        display_name = str(definition["name"])
        figure = figures_by_name.get(normalize_public_name(display_name))
        figure_keys = public_name_keys(figure) if figure else {normalize_public_name(display_name)}
        is_principal = bool(principal_keys & figure_keys)
        principal_was_in_watchlist = principal_was_in_watchlist or is_principal
        rating = _rating_for(display_name, figure, ratings)
        ordered_rows.append(
            (
                order,
                BriefWatchlistRatingOut(
                    figure_id=figure.id if figure else None,
                    is_principal=is_principal,
                    rank=(
                        _rank(momentum_payload.get("rank"))
                        if is_principal
                        else _rank(rating.get("rank"))
                    ),
                    name=principal.full_name if is_principal else display_name,
                    position=(
                        figure.current_role
                        if figure and figure.current_role
                        else principal.role_title
                        if is_principal
                        else None
                    ),
                    portrait_url=(
                        figure.portrait_url
                        if figure and figure.portrait_url
                        else principal_identity.profile_image_url
                        if is_principal and principal_identity
                        else None
                    ),
                    score=(
                        _number(momentum_payload.get("score"))
                        if is_principal
                        else _number(rating.get("score"))
                    ),
                    delta=(
                        _number(momentum_payload.get("delta"))
                        if is_principal
                        else _number(rating.get("delta"))
                    ),
                ),
            )
        )

    if not principal_was_in_watchlist:
        rating = _rating_for(principal.full_name, principal_figure, ratings)
        ordered_rows.append(
            (
                -1,
                BriefWatchlistRatingOut(
                    figure_id=principal_figure.id if principal_figure else None,
                    is_principal=True,
                    rank=_rank(momentum_payload.get("rank")) or _rank(rating.get("rank")),
                    name=principal.full_name,
                    position=(
                        principal_figure.current_role
                        if principal_figure and principal_figure.current_role
                        else principal.role_title
                    ),
                    portrait_url=(
                        principal_figure.portrait_url
                        if principal_figure and principal_figure.portrait_url
                        else principal_identity.profile_image_url
                        if principal_identity
                        else None
                    ),
                    score=_number(momentum_payload.get("score")),
                    delta=_number(momentum_payload.get("delta")),
                ),
            )
        )

    ordered_rows.sort(
        key=lambda item: (
            item[1].rank is None,
            item[1].rank if item[1].rank is not None else 10_000,
            item[0],
        )
    )
    return [row for _, row in ordered_rows]


async def resolve_brief_watchlist(
    db: AsyncSession,
    *,
    principal: Profile,
    principal_identity: PrincipalIdentity | None,
    momentum_payload: dict[str, Any],
) -> list[BriefWatchlistRatingOut]:
    figures = (
        (await db.execute(select(PoliticalFigure).where(PoliticalFigure.archived_at.is_(None))))
        .scalars()
        .all()
    )
    return build_watchlist_rows(
        principal=principal,
        principal_identity=principal_identity,
        figures=list(figures),
        momentum_payload=momentum_payload,
    )
