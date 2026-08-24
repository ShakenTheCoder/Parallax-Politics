"""Source-backed Superadmin glossary for the Philippine national power map.

The seed roster contains only office/roster facts from public authoritative sources.
Narrative dossier fields are intentionally left as gaps until a refresh retrieves and
validates evidence through Exa + the LLM. This keeps the glossary useful without
silently turning stale or invented text into product truth.
"""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select

from app.db import session_scope
from app.llm.client import get_llm_client
from app.llm.prompts import load_prompt
from app.llm.router import ModelTier
from app.models.political_figure import PoliticalFigure, PoliticalFigureSnapshot
from app.search.exa import get_exa_client
from app.utils.portraits import resolve_wikimedia_portrait, resolve_wikipedia_identity

_SLUG = re.compile(r"[^a-z0-9]+")
_SENATE_URL = "https://legacy.senate.gov.ph/senators/sen20th.asp"
_OP_URL = "https://op-proper.gov.ph/transparency-seal-2/op-officials-directory/"
_WATCHLIST_URL = "https://www.pulseasia.ph/december-2025-national-survey-presidential-preference/"

_SENATORS = (
    "Paolo Benigno Aquino IV",
    "Alan Peter Cayetano",
    "Pia Cayetano",
    "Ronald Dela Rosa",
    "Joseph Victor Ejercito",
    "Francis Escudero",
    "Jinggoy Estrada",
    "Sherwin Gatchalian",
    "Christopher Go",
    "Risa Hontiveros",
    "Panfilo Lacson",
    "Manuel Lapid",
    "Loren Legarda",
    "Rodante Marcoleta",
    "Imee Marcos",
    "Robinhood Padilla",
    "Francis Pangilinan",
    "Vicente Sotto III",
    "Erwin Tulfo",
    "Raffy Tulfo",
    "Joel Villanueva",
    "Camille Villar",
    "Mark Villar",
    "Juan Miguel Zubiri",
)
_WATCHLIST = ("Sara Duterte", "Leni Robredo", "Vince Dizon", "Benjie Magalong", "Nic Torre")
_PORTRAIT_ALIASES = {
    "Paolo Benigno Aquino IV": "Bam Aquino",
    "Ronald Dela Rosa": "Bato dela Rosa",
    "Christopher Go": "Bong Go",
    "Francis Escudero": "Chiz Escudero",
    "Sherwin Gatchalian": "Win Gatchalian",
    "Joseph Victor Ejercito": "JV Ejercito",
    "Manuel Lapid": "Lito Lapid",
    "Robinhood Padilla": "Robin Padilla",
    "Francis Pangilinan": "Kiko Pangilinan",
    "Vicente Sotto III": "Tito Sotto",
    "Juan Miguel Zubiri": "Migz Zubiri",
}


def slugify(name: str) -> str:
    return _SLUG.sub("-", name.casefold()).strip("-")


def _seed_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "name": "Ferdinand Marcos Jr.",
            "category": "executive",
            "role": "President of the Philippines",
            "office": "Office of the President",
            "source": _OP_URL,
        }
    ]
    rows.append(
        {
            "name": "Sara Duterte",
            "category": "executive",
            "role": "Vice President of the Philippines",
            "office": "Office of the Vice President",
            "source": _WATCHLIST_URL,
        }
    )
    rows.extend(
        {
            "name": name,
            "category": "senate",
            "role": "Senator of the Philippines",
            "office": "Senate of the Philippines",
            "source": _SENATE_URL,
        }
        for name in _SENATORS
    )
    rows.extend(
        {
            "name": name,
            "category": "watchlist",
            "role": None,
            "office": None,
            "source": _WATCHLIST_URL,
        }
        for name in _WATCHLIST
        if name != "Sara Duterte"
    )
    return rows


def _source(row: dict[str, Any], *, supports: list[str]) -> dict[str, Any]:
    return {
        "url": row["source"],
        "title": "Public roster source",
        "publisher": "Official/public source",
        "source_type": "public_web",
        "accessed_at": datetime.now(UTC).isoformat(),
        "supports": supports,
        "confidence": 0.9,
    }


async def seed_glossary() -> int:
    rows = _seed_rows()
    async with session_scope() as db:
        created = 0
        for row in rows:
            slug = slugify(row["name"])
            figure = (
                await db.execute(select(PoliticalFigure).where(PoliticalFigure.slug == slug))
            ).scalar_one_or_none()
            if figure is None:
                now = datetime.now(UTC)
                figure = PoliticalFigure(
                    created_at=now,
                    updated_at=now,
                    slug=slug,
                    canonical_name=row["name"],
                    aliases=[],
                    category=row["category"],
                    current_role=row["role"],
                    office=row["office"],
                    jurisdiction="Philippines",
                    status="active",
                    data={},
                    social_accounts=[],
                    relationships=[],
                    source_ledger=[_source(row, supports=["roster", "current_role"])],
                    coverage_gaps=[
                        "Biography, policy, electoral, relationship, controversy, and social-account fields require evidence refresh."
                    ],
                    confidence=0.65,
                )
                db.add(figure)
                await db.flush()
                created += 1
                db.add(
                    PoliticalFigureSnapshot(
                        created_at=now,
                        updated_at=now,
                        figure_id=figure.id,
                        version=1,
                        trigger="seed",
                        produced_by="official_roster_seed",
                        payload={
                            "canonical_name": figure.canonical_name,
                            "current_role": figure.current_role,
                            "office": figure.office,
                            "category": figure.category,
                        },
                        source_ledger=figure.source_ledger,
                        confidence=figure.confidence,
                    )
                )
            if not figure.portrait_url:
                names = [figure.canonical_name]
                if figure.canonical_name in _PORTRAIT_ALIASES:
                    names.append(_PORTRAIT_ALIASES[figure.canonical_name])
                for portrait_name in names:
                    identity = await resolve_wikipedia_identity(portrait_name)
                    if identity and identity.portrait_url:
                        figure.portrait_url = identity.portrait_url
                        figure.portrait_source_url = identity.page_url
                        figure.portrait_attribution = "Wikimedia/Wikipedia source page; verify license before external publication."
                        if (
                            portrait_name != figure.canonical_name
                            and portrait_name not in figure.aliases
                        ):
                            figure.aliases = [*figure.aliases, portrait_name]
                        break
                    commons_url = await resolve_wikimedia_portrait(portrait_name)
                    if commons_url:
                        figure.portrait_url = commons_url
                        figure.portrait_source_url = "https://commons.wikimedia.org/"
                        figure.portrait_attribution = "Wikimedia Commons file search; verify exact file attribution and license before external publication."
                        break
            figure.last_verified_at = datetime.now(UTC)
        await db.commit()
    return created


async def refresh_figure(figure_id: UUID, run_id: UUID) -> None:
    async with session_scope() as db:
        figure = (
            await db.execute(select(PoliticalFigure).where(PoliticalFigure.id == figure_id))
        ).scalar_one()
        exa = get_exa_client()
        queries = [
            f"{figure.canonical_name} Philippines official biography current role",
            f"{figure.canonical_name} Philippines policy positions election record",
            f"{figure.canonical_name} official social media account",
        ]
        results: list[Any] = []

        async def search(query: str) -> None:
            try:
                results.extend(await exa.search(query, num_results=5, text_chars=500))
            except Exception:
                return

        await asyncio.gather(*(search(q) for q in queries))
        if not results:
            raise RuntimeError("No retrievable public sources were returned for this figure")
        sources = [
            {
                "url": r.url,
                "title": r.title,
                "publisher": r.domain,
                "source_type": "public_web",
                "published_at": r.published_at,
                "accessed_at": datetime.now(UTC).isoformat(),
                "supports": ["research_context"],
                "confidence": r.credibility_score,
            }
            for r in results
        ]
        prompt = load_prompt("political_figure_glossary")
        evidence = "\n\n".join(
            f"SOURCE {i + 1}: {r.url}\n{r.title or ''}\n{r.excerpt or ''}"
            for i, r in enumerate(results[:12])
        )
        response = await get_llm_client().complete(
            agent="political_figure_glossary",
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Figure: {figure.canonical_name}\nCurrent seeded record: {figure.data}\nEvidence:\n{evidence}\nReturn JSON only.",
                }
            ],
            tier=ModelTier.cheap,
            max_tokens=1800,
            temperature=0.1,
            run_id=run_id,
            json_mode=True,
        )
        payload = response.json_payload or {}
        if not isinstance(payload, dict) or not isinstance(payload.get("data", {}), dict):
            raise RuntimeError("Glossary refresh returned invalid structured data")
        allowed_urls = {r.url for r in results}
        social = payload.get("social_accounts", [])
        if not isinstance(social, list):
            social = []
        social = [
            item for item in social if isinstance(item, dict) and item.get("url") in allowed_urls
        ]
        figure.data = payload.get("data", {})
        figure.aliases = (
            payload.get("aliases", figure.aliases)
            if isinstance(payload.get("aliases", figure.aliases), list)
            else figure.aliases
        )
        for field in (
            "current_role",
            "office",
            "jurisdiction",
            "party",
            "faction",
            "region",
            "status",
        ):
            if isinstance(payload.get(field), str) and payload[field].strip():
                setattr(figure, field, payload[field].strip())
        figure.social_accounts = social
        figure.source_ledger = sources
        figure.coverage_gaps = [str(g) for g in payload.get("coverage_gaps", []) if str(g).strip()]
        figure.confidence = min(1.0, max(0.0, float(payload.get("confidence", 0.5))))
        figure.last_verified_at = datetime.now(UTC)
        latest = (
            await db.execute(
                select(func.max(PoliticalFigureSnapshot.version)).where(
                    PoliticalFigureSnapshot.figure_id == figure.id
                )
            )
        ).scalar() or 0
        db.add(
            PoliticalFigureSnapshot(
                figure_id=figure.id,
                version=int(latest) + 1,
                trigger="refresh",
                produced_by="political_figure_glossary",
                model=response.model,
                payload={
                    "data": figure.data,
                    "social_accounts": figure.social_accounts,
                    "current_role": figure.current_role,
                    "office": figure.office,
                    "coverage_gaps": figure.coverage_gaps,
                },
                source_ledger=sources,
                confidence=figure.confidence,
            )
        )
        await db.commit()
