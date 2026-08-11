"""DisambiguationAgent — lightweight identity-confirmation step.

Given a fuzzy name query, produce a single IdentityCandidate card for the
superadmin to confirm before the full PIDAA build is queued.

Pipeline:
1. Resolve an exact-name Wikipedia identity card.
2. Run one bounded EXA query for corroborating sources.

Cost cap: ~$0.02 per call.
"""

from __future__ import annotations

import asyncio

from app.schemas.superadmin import IdentityCandidate
from app.search.exa import get_exa_client
from app.utils.portraits import resolve_wikipedia_identity


async def run_disambiguation(
    name_query: str,
    hint: str | None = None,
) -> IdentityCandidate:
    """Stateless — does not write to DB. Returns IdentityCandidate for admin confirmation."""
    exa = get_exa_client()
    query = f"{name_query} {hint or ''} Philippines politician biography".strip()
    resolved = await asyncio.gather(
        resolve_wikipedia_identity(name_query),
        asyncio.wait_for(exa.search(query, num_results=4, text_chars=240), timeout=1.5),
        return_exceptions=True,
    )
    identity = resolved[0] if not isinstance(resolved[0], BaseException) else None
    results = resolved[1] if not isinstance(resolved[1], BaseException) else []

    sources = []
    if identity:
        sources.append(
            {"url": identity.page_url, "title": identity.title, "domain": "en.wikipedia.org"}
        )
    sources.extend(
        {"url": item.url, "title": item.title or "", "domain": item.domain} for item in results[:2]
    )
    aliases = (
        [identity.title] if identity and identity.title.casefold() != name_query.casefold() else []
    )
    return IdentityCandidate(
        full_name=name_query.strip(),
        aliases=aliases,
        current_role=identity.description if identity else None,
        party=None,
        region=None,
        born=None,
        birthplace=None,
        photo_url=identity.portrait_url if identity else None,
        one_line_bio=identity.extract if identity else None,
        top_sources=sources[:3],
        confidence=0.95 if identity else (0.35 if results else 0.0),
        ambiguity_notes="Exact first-name identity match; confirm before creating the dossier."
        if identity
        else "No exact Wikipedia identity match; review corroborating sources before confirmation.",
    )
