"""DisambiguationAgent — lightweight identity-confirmation step.

Given a fuzzy name query, produce a single IdentityCandidate card for the
superadmin to confirm before the full PIDAA build is queued.

Pipeline:
1. Run 1-2 EXA queries.
2. Cheap-tier LLM reads top results → emits IdentityCandidate JSON.

Cost cap: ~$0.02 per call.
"""
from __future__ import annotations

import json
from typing import Any

from app.contexts import default_pack_id, get_pack
from app.llm.client import get_llm_client
from app.llm.router import ModelTier
from app.schemas.superadmin import IdentityCandidate
from app.search.exa import get_exa_client

_SYSTEM = """You are a quick-disambiguation assistant for Parallax AI, a Philippine political intelligence platform.

Given a name query and a small set of search results, identify the most likely Philippine political principal and produce a single IdentityCandidate JSON object.

Output contract (strict JSON, no fences, no prose):
{
  "full_name": "...",
  "aliases": ["..."],
  "current_role": "...",
  "party": "...",
  "region": "...",
  "born": "YYYY-MM-DD or null",
  "birthplace": "...",
  "photo_url": "...",
  "one_line_bio": "...",
  "top_sources": [{"url": "...", "title": "...", "domain": "..."}],
  "confidence": 0.0-1.0,
  "ambiguity_notes": "..."
}

Rules:
- Return the single most likely match. If multiple candidates exist, return the highest-confidence one and note alternatives in ambiguity_notes.
- Never invent biographical facts. Use only what the search results support.
- photo_url: use the og:image or Wikipedia thumbnail if visible in results; otherwise null.
- confidence: 0.9 = unambiguous public figure; 0.7 = likely correct; <0.5 = ambiguous.
- Output only the JSON object.
"""


async def run_disambiguation(
    name_query: str,
    hint: str | None = None,
) -> IdentityCandidate:
    """Stateless — does not write to DB. Returns IdentityCandidate for admin confirmation."""
    llm = get_llm_client()
    exa = get_exa_client()

    q1 = f"{name_query} Philippines politician"
    q2 = f"{name_query} Philippines government official biography"
    if hint:
        q1 = f"{name_query} {hint} Philippines"
        q2 = f"{name_query} Philippines biography official"

    pool: dict[str, Any] = {}
    for q in [q1, q2]:
        try:
            for r in await exa.search(q, num_results=6):
                pool.setdefault(r.url, r)
        except Exception:
            pass

    candidates_payload = [
        {
            "url": r.url,
            "title": r.title,
            "domain": r.domain,
            "published_at": r.published_at,
            "excerpt": r.excerpt,
        }
        for r in list(pool.values())[:12]
    ]

    user_msg = (
        f"Name query: {name_query}\n"
        + (f"Hint: {hint}\n" if hint else "")
        + f"\nSearch results:\n{json.dumps(candidates_payload, ensure_ascii=False)}\n\n"
        "Produce the IdentityCandidate JSON object."
    )

    resp = await llm.complete(
        agent="DisambiguationAgent",
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
        tier=ModelTier.cheap,
        max_tokens=600,
        run_id=None,
        json_mode=True,
        temperature=0.2,
    )

    payload = resp.json_payload or {}
    return IdentityCandidate(
        full_name=str(payload.get("full_name") or name_query),
        aliases=list(payload.get("aliases") or []),
        current_role=payload.get("current_role"),
        party=payload.get("party"),
        region=payload.get("region"),
        born=payload.get("born"),
        birthplace=payload.get("birthplace"),
        photo_url=payload.get("photo_url"),
        one_line_bio=payload.get("one_line_bio"),
        top_sources=list(payload.get("top_sources") or [])[:3],
        confidence=float(payload.get("confidence") or 0.5),
        ambiguity_notes=payload.get("ambiguity_notes"),
    )
