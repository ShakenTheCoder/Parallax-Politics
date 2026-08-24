"""Shared helpers for context-layer agents."""

from __future__ import annotations

import json
from typing import Any

from app.agents.base import AgentContext


def upstream_sources(ctx: AgentContext) -> list[dict[str, Any]]:
    sga = ctx.get("SGA")
    if not sga:
        return []
    return list(sga.payload.get("sources") or [])


def upstream_brief(ctx: AgentContext, max_chars: int = 4000) -> str:
    """Compact textual summary of upstream agent outputs for an LLM prompt."""
    blocks: list[str] = []
    for name, res in ctx.upstream.items():
        text = json.dumps(res.payload, ensure_ascii=False)
        if len(text) > 1800:
            text = text[:1800] + "...<truncated>"
        blocks.append(f"## {name} output\n{text}")
    out = "\n\n".join(blocks)
    return out[:max_chars]


def identity_brief(ctx: AgentContext, max_chars: int = 2500) -> str:
    """Compact textual summary of the principal's PIDAA identity (for non-PIDAA agents).

    Reads ctx.upstream["PIDAA"] (an AgentResult) if present and returns a digest of the
    most decision-relevant sections (basics, current_position, party_history,
    policy_stances, controversies, network).
    """
    pidaa = ctx.get("PIDAA")
    if not pidaa:
        return "(no principal identity available)"
    p = pidaa.payload or {}
    keep = [
        "full_name",
        "basics",
        "current_position",
        "party_history",
        "policy_stances",
        "controversies",
        "network",
    ]
    digest = {k: p.get(k) for k in keep if p.get(k)}
    text = json.dumps(digest, ensure_ascii=False)
    if len(text) > max_chars:
        text = text[:max_chars] + "...<truncated>"
    return text


def identity_query_seeds(ctx: AgentContext) -> list[str]:
    """Derive search-query seeds from the principal's identity (no situation prompt).

    Used by SGA when running inside the Brief pipeline.
    """
    pidaa = ctx.get("PIDAA")
    p = pidaa.payload if pidaa else {}
    # A concurrent Brief may start before PIDAA persists. The confirmed profile
    # name is only a retrieval key; it is never presented as analytical output.
    name = p.get("full_name") or str(ctx.extra.get("full_name") or "")
    seeds: list[str] = []
    if name:
        seeds.append(f"{name} latest news")
        seeds.append(f"{name} controversy")
        seeds.append(f"{name} statement this week")
    cp = p.get("current_position") or {}
    role = cp.get("role") or cp.get("title") or ""
    if name and role:
        seeds.append(f"{name} {role}")
    stances = p.get("policy_stances") or {}
    if name and isinstance(stances, dict):
        for topic in list(stances.keys())[:3]:
            seeds.append(f"{name} {topic.replace('_', ' ')}")
    return [s for s in seeds if s.strip()][:6]
