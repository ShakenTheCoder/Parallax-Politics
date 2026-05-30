# SCDRA — Specific Candidate Data Retrieval Agent

**File:** `backend/app/agents/scdra.py`  
**Class:** `SCDRA(BaseAgent)`

---

## Purpose

Resolves coverage gaps detected by PIDAA through targeted EXA searches. Triggered automatically when PIDAA identifies gaps in a principal's identity that meet the severity threshold. Fills specific field-level data holes with surgical accuracy.

---

## Configuration

| Attribute | Value |
|-----------|-------|
| `name` | `"SCDRA"` |
| `default_tier` | `ModelTier.default` |
| `max_cost_usd` | `$0.30` per run (covers multiple gaps) |
| `max_cost_per_gap` | `$0.10` per gap |
| `max_attempts_per_gap` | 3 |
| `severity_threshold` | `medium` (processes medium and high severity) |

---

## Pipeline

```
1. Parse upstream PIDAA result → extract structured gaps
2. Filter to gaps meeting severity threshold (medium/high)
3. For each gap:
   a. Select retrieval strategy based on gap_type from taxonomy
   b. Build targeted EXA query using taxonomy templates
   c. Execute search → rank results by credibility × relevance
   d. LLM extraction call → structured field values
   e. Validate extracted data → provenance + confidence check
   f. Record attempt in gap_retrieval_attempts table
4. Merge resolved fields into PrincipalIdentity
5. Recalculate data_completeness_score
6. Emit SCDRAArtifact with resolutions + remaining gaps
```

---

## Gap Taxonomy Integration

SCDRA uses the standardized gap taxonomy defined in `app/identity/gap_taxonomy.py`:

| Gap Type | Severity | Auto-resolvable | Query Strategy |
|----------|----------|-----------------|----------------|
| `birth_record_missing` | high | yes | PSA/Comelec targeted search |
| `education_unverified` | high | yes | Institution + degree verification |
| `controversy_legal_status_unknown` | high | partial | Court records + case tracking |
| `religion_conversion_unconfirmed` | medium | yes | Interview/statement search |
| `mother_biography_missing` | medium | yes | Family background search |
| `term_dates_incomplete` | medium | yes | Oath/inauguration date search |
| `policy_direct_quote_missing` | medium | yes | Speech/statement extraction |
| `family_children_incomplete` | low | partial | Family profile search |
| `siblings_details_missing` | low | yes | Family network search |
| `electoral_votes_missing` | low | yes | Comelec results search |
| `network_strength_unverified` | low | yes | Alliance analysis search |
| `party_switch_date_unknown` | low | yes | Party history search |

---

## EXA Search Strategy

Each gap type has 1-3 query templates. SCDRA:
1. Extracts context parameters from existing identity data (e.g., institution name from partial education record)
2. Formats the query template with principal name + context
3. Executes search with `num_results=5`, `text_chars=800`
4. Selects top result by `credibility_score × relevance_score`

---

## LLM Extraction

**System prompt:** `contexts/philippines_politics/agents/scdra.md`

**User prompt format:**
```
Gap to resolve: {gap_type}
Description: {description}
Principal: {full_name}
Target fields: {affected_fields}

Source to extract from:
Title: {source_title}
URL: {source_url}
Excerpt: {source_excerpt}
```

**Response format (JSON):**
```json
{
  "found": true/false,
  "confidence": 0.0-1.0,
  "resolved_fields": {"field.path": "value", ...},
  "reasoning": "explanation"
}
```

---

## Output Artifact — `SCDRAArtifact`

```json
{
  "principal_identity_id": "uuid",
  "run_timestamp": "2026-01-15T10:30:00Z",
  "gaps_processed": 5,
  "gaps_resolved": 3,
  "gaps_remaining": 2,
  "resolutions": [
    {
      "gap_type": "education_unverified",
      "fields_resolved": ["education.degrees.0.year"],
      "source_url": "https://example.com/source",
      "confidence": 0.85
    }
  ],
  "data_completeness_before": 0.65,
  "data_completeness_after": 0.82,
  "total_cost_usd": 0.27
}
```

---

## Database Persistence

### PrincipalIdentity Updates

SCDRA updates the `PrincipalIdentity` row in-place:
- Merges resolved field values into appropriate JSONB sections
- Updates `coverage_gaps_structured` with new gap statuses
- Increments `scdra_runs` counter
- Sets `scdra_last_run` timestamp
- Updates `data_completeness_score`

### Gap Retrieval Audit Trail

Every attempt is logged to `gap_retrieval_attempts`:
- `principal_identity_id` — Link to identity
- `gap_type`, `gap_severity` — Classification
- `attempt_number` — Retry tracking
- `strategy`, `search_query` — What was attempted
- `sources_found` — Results returned
- `resolution_status` — pending/resolved/failed/manual
- `resolved_fields` — Which fields were filled
- `cost_usd` — Cost tracking

---

## PIDAA Integration (Auto-trigger)

SCDRA is triggered automatically by PIDAA when:

1. `structured_gaps` list is non-empty
2. `ctx.extra["auto_scdra"]` is `True` (default)
3. Gaps meet severity threshold

```python
# In PIDAA._run()
if structured_gaps and ctx.extra.get("auto_scdra", True):
    scdra = SCDRA()
    scdra_ctx = AgentContext(...)
    await scdra.run(scdra_ctx)
```

**Note:** SCDRA failures are logged but do not fail PIDAA. The principal identity is still persisted with gaps flagged.

---

## Manual Trigger

For manual gap resolution (e.g., superadmin reviewing gaps):

```python
from app.agents.scdra import SCDRA
from app.agents.base import AgentContext

scdra = SCDRA()
ctx = AgentContext(
    run_id=run_id,
    situation_prompt="",
    subject_slug=principal_slug,
    upstream={"PIDAA": pidaa_result},
    extra={
        "profile_id": principal_id,
        "scdra_severity_threshold": "low",  # Process all gaps
    },
)
result = await scdra.run(ctx)
```

---

## Confidence

Fixed at **0.75** if any gaps resolved, **0.50** otherwise.

---

## Context Dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `ctx.upstream["PIDAA"]` | Yes | PIDAA result with `coverage_gaps_structured` |
| `ctx.extra["profile_id"]` | Optional | UUID for DB persistence |
| `ctx.extra["auto_scdra"]` | Optional | Defaults to `True` |
| `ctx.extra["scdra_severity_threshold"]` | Optional | Defaults to `"medium"` |
| `ctx.pack_id` | Optional | Selects system prompt via `load_prompt("scdra")` |

---

## Cost Budgeting

| Level | Budget | Description |
|-------|--------|-------------|
| Per gap | $0.10 | EXA search + LLM extraction |
| Per run | $0.30 | Multiple gaps in batch |
| Per attempt | — | Tracked in `gap_retrieval_attempts.cost_usd` |

Budget exhaustion gracefully degrades: remaining gaps are left as `pending` for future runs.

---

## Success Metrics

- **Resolution rate**: ≥60% of medium severity gaps resolved
- **Completeness target**: ≥0.80 score for all processed principals
- **Cost efficiency**: <$0.10 average per resolved field
- **Source quality**: Prefer credibility_score ≥0.7 sources
