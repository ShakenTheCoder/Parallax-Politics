# SGA — Source Gathering Agent

**File:** `backend/app/agents/sga.py`  
**Class:** `SGA(BaseAgent)`

---

## Purpose

First agent in the main situation pipeline. Given a situation prompt, it gathers, deduplicates, ranks, and selects the most decision-relevant web sources via EXA search, then emits a `SourcePack` artifact for downstream agents to consume.

---

## Configuration

| Attribute | Value |
|-----------|-------|
| `name` | `"SGA"` |
| `default_tier` | `ModelTier.default` |
| `max_cost_usd` | `$0.08` |

---

## Pipeline

```
1. LLM (cheap tier) → proposes 3–6 EXA search queries
2. EXA search → sequential fetch per query (8 results each, 24 h cache)
3. Pool + dedupe by URL → rank by credibility × relevance score → top 25
4. LLM (default tier) → selects top 8, identifies coverage gaps
5. Emit SourcePack artifact
```

### Step 1 — Query proposal

Uses `ModelTier.cheap` with `max_tokens=400, temperature=0.3`.  
Returns `{ "queries": [...] }`. Falls back to the first 160 chars of `situation_prompt` if the LLM output is empty or malformed.

### Step 2 — EXA search

Up to 6 queries, 8 results each. Results are pooled and deduped by URL. EXA errors per-query are logged as warnings and do not abort the run.

### Step 3 — Ranking

```python
rank_key = credibility_score × (score or 0.5)
```

Top 25 results are forwarded to the LLM selection step.

### Step 4 — LLM selection

Uses `ModelTier.default` with `max_tokens=1200, temperature=0.2`.  
Instructs the LLM to pick the **top 8** most decision-relevant sources and identify `coverage_gaps`.

Invented URLs (not present in the candidate pool) are silently rejected.

### Step 5 — Fallback

If the LLM returns no valid selection, the top 8 ranked candidates are used directly.

---

## Output artifact — `SourcePack`

```json
{
  "query": "<first 200 chars of situation_prompt>",
  "sources": [
    {
      "url": "...",
      "title": "...",
      "domain": "...",
      "published_at": "...",
      "excerpt": "...",
      "credibility_score": 0.0–1.0
    }
  ],
  "coverage_gaps": ["..."]
}
```

Each source is also emitted as an `EvidenceRef` in `AgentResult.evidence`.

---

## Confidence formula

```python
confidence = min(1.0, 0.4 + 0.05 * len(sources))
```

Ranges from `0.40` (0 sources) to `1.0` (≥12 sources).

---

## Context dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ctx.situation_prompt` | Yes | Drives both query proposal and LLM selection |
| `ctx.subject_slug` | Optional | Prepended to prompts when present |
| `ctx.pack_id` | Optional | Selects the system prompt variant via `load_prompt("sga")` |

SGA does **not** read from `ctx.upstream`.
