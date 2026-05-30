# DisambiguationAgent

**File:** `backend/app/agents/disambiguation.py`  
**Function:** `run_disambiguation(name_query, hint)`

---

## Purpose

Lightweight, stateless identity-confirmation step. Given a fuzzy name string (and optional hint), it runs 1–2 EXA queries, feeds the top results to a cheap-tier LLM, and returns a single `IdentityCandidate` for the superadmin to review before queuing a full `PIDAA` build.

Unlike the other agents, this is a **plain async function** — not a `BaseAgent` subclass — and does **not** write to the database.

---

## Cost target

~$0.02 per call.

---

## Signature

```python
async def run_disambiguation(
    name_query: str,
    hint: str | None = None,
) -> IdentityCandidate:
```

| Parameter | Description |
|-----------|-------------|
| `name_query` | Raw name string entered by the superadmin (e.g. `"Bong Go"`) |
| `hint` | Optional extra context to narrow the search (e.g. `"Davao senator"`) |

---

## Pipeline

```
1. Build 2 EXA queries from name_query (+ hint if provided)
2. Run both queries, pool + dedupe results by URL (up to 12 sources)
3. Single LLM call (cheap tier, JSON mode) → IdentityCandidate JSON
4. Parse + return IdentityCandidate
```

### Query construction

Without hint:
```
q1 = "{name_query} Philippines politician"
q2 = "{name_query} Philippines government official biography"
```

With hint:
```
q1 = "{name_query} {hint} Philippines"
q2 = "{name_query} Philippines biography official"
```

EXA fetches 6 results per query. Errors are silently swallowed (empty pool is safe).

### LLM call parameters

| Parameter | Value |
|-----------|-------|
| `agent` | `"DisambiguationAgent"` |
| `tier` | `ModelTier.cheap` |
| `max_tokens` | `600` |
| `temperature` | `0.2` |
| `json_mode` | `True` |

---

## Output — `IdentityCandidate`

```json
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
  "top_sources": [
    { "url": "...", "title": "...", "domain": "..." }
  ],
  "confidence": 0.0–1.0,
  "ambiguity_notes": "..."
}
```

`top_sources` is capped at 3 entries.  
`confidence` defaults to `0.5` if the LLM omits it.  
`full_name` falls back to `name_query` if the LLM omits it.

### Confidence scale

| Range | Meaning |
|-------|---------|
| ≥ 0.9 | Unambiguous public figure |
| ≥ 0.7 | Likely correct match |
| < 0.5 | Ambiguous — review `ambiguity_notes` carefully |

---

## LLM system prompt rules (inline, not loaded from file)

- Return the single most likely match; note alternatives in `ambiguity_notes`.
- Never invent biographical facts — use only what the search results support.
- `photo_url`: use `og:image` or Wikipedia thumbnail if visible; otherwise `null`.
- Output only the JSON object (no prose, no fences).
