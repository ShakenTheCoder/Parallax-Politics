# PIDAA — Person Identity Deep Analyzer Agent

**File:** `backend/app/agents/pidaa.py`  
**Class:** `PIDAA(BaseAgent)`

---

## Purpose

Builds a full 11-section identity knowledge base for a confirmed Philippine political principal. Invoked once at principal-creation time (after superadmin confirmation via `DisambiguationAgent`), not in the main situation pipeline. Persists results to the `PrincipalIdentity` DB table.

---

## Configuration

| Attribute | Value |
|-----------|-------|
| `name` | `"PIDAA"` |
| `default_tier` | `ModelTier.default` |
| `max_cost_usd` | `$0.50` |

---

## Pipeline

```
1. EXA fan-out — 8 facet queries run in parallel (8 results each → up to 64 raw)
2. Rank + deduplicate → top 40 sources by credibility × score
3. Four sequential LLM calls (section groups A–D, default tier)
4. Merge all group outputs into a single 11-section dict
5. Build source_index (top 12 sources) + aggregate coverage_gaps
6. Persist PrincipalIdentity row to DB (if profile_id present)
7. Emit PrincipalIdentityArtifact
```

---

## EXA Facets

Eight parallel queries are constructed by formatting `_EXA_FACETS` with the principal's `full_name`:

1. `{name} Philippines politician biography`
2. `{name} Philippines birthplace education career`
3. `{name} Philippines party affiliation`
4. `{name} Philippines Comelec election results votes`
5. `{name} Philippines Senate hearing controversy`
6. `{name} Philippines West Philippine Sea ICC stance`
7. `{name} Philippines allies rivals political network`
8. `{name} Philippines social media speech interview`

---

## Section Groups

LLM calls are sequential (rate-limit safe), each producing a subset of sections:

| Group | Sections |
|-------|----------|
| A | `basics`, `family`, `education` |
| B | `career_timeline`, `current_position`, `party_history`, `electoral_record` |
| C | `policy_stances`, `voice_signature` |
| D | `controversies`, `network` |

Each group receives a **different 15-source slice** of the ranked pool for breadth of coverage. `max_tokens=2000, temperature=0.25`.

---

## Output artifact — `PrincipalIdentityArtifact`

```json
{
  "full_name": "...",
  "basics": {},
  "family": {},
  "education": {},
  "career_timeline": {},
  "current_position": {},
  "party_history": {},
  "electoral_record": {},
  "policy_stances": {},
  "voice_signature": {},
  "controversies": {},
  "network": {},
  "source_index": {
    "sources": [{ "url": "...", "title": "...", "domain": "...", "published_at": "...", "credibility_score": 0.0 }]
  },
  "coverage_gaps": ["..."]
}
```

---

## DB Persistence

If `ctx.extra["profile_id"]` is set, `_persist()` upserts a `PrincipalIdentity` row:

- Creates a new row if none exists for `profile_id`.
- Writes all 11 sections + `source_index` + `coverage_gaps` + `raw_dossier`.
- Sets `status = "ready"` and stamps `built_at` with UTC now.

---

## Confidence

Fixed at **0.75**.

---

## Context dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ctx.extra["confirmed_candidate"]` | Yes | Dict with at least `full_name`; falls back to first 100 chars of `situation_prompt` |
| `ctx.extra["profile_id"]` | Optional | UUID; if present, triggers DB persistence |
| `ctx.pack_id` | Optional | Selects system prompt via `load_prompt("pidaa")` |
| `ctx.upstream` | Not used | PIDAA runs standalone, not in the main pipeline |
