"""Persist sources + evidence rows so every claim is traceable."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evidence import Evidence
from app.models.source import Source
from app.schemas.agents import AgentResult


async def upsert_source(db: AsyncSession, *, url: str, domain: str, title: str | None,
                         excerpt: str | None, published_at: str | None,
                         credibility: float) -> Source:
    res = await db.execute(select(Source).where(Source.url == url))
    s = res.scalar_one_or_none()
    if s:
        return s
    s = Source(
        url=url, domain=domain, title=title, excerpt=excerpt,
        published_at=published_at, credibility_score=credibility,
    )
    db.add(s)
    await db.flush()
    return s


async def persist_evidence(
    db: AsyncSession,
    *,
    run_id: UUID,
    artifact_id: UUID | None,
    result: AgentResult,
) -> None:
    if not result.evidence:
        return
        
    # Collect all unique URLs first to batch fetch existing sources
    urls_to_check = {ev.source_url for ev in result.evidence if ev.source_url}
    existing_sources = {}
    
    if urls_to_check:
        from sqlalchemy import select
        res = await db.execute(select(Source).where(Source.url.in_(urls_to_check)))
        existing_sources = {s.url: s for s in res.scalars()}
    
    # Process evidence and batch upsert sources
    for ev in result.evidence:
        source_id: UUID | None = None
        if ev.source_url:
            if ev.source_url in existing_sources:
                source_id = existing_sources[ev.source_url].id
            else:
                # Create new source
                from urllib.parse import urlparse
                netloc = urlparse(ev.source_url).netloc.lower()
                domain = netloc[4:] if netloc.startswith("www.") else netloc
                s = Source(
                    url=ev.source_url,
                    domain=domain,
                    title=None,
                    excerpt=ev.quote,
                    published_at=None,
                    credibility_score=ev.confidence,
                )
                db.add(s)
                await db.flush()  # Get the ID for this source
                source_id = s.id
                
        db.add(
            Evidence(
                run_id=run_id,
                artifact_id=artifact_id,
                source_id=source_id,
                agent=result.agent,
                claim=ev.claim,
                quote=ev.quote,
                extra=ev.extra,
            )
        )
