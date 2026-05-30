# SRCA — Source Real Check Agent

**Module:** `backend/app/utils/src_validator.py`

---

## Purpose

Validates URLs to prevent AI source fabrication. SRCA performs fast HTTP HEAD/GET checks to confirm URLs are real, reachable, and contain actual content before downstream agents consume them.

---

## Design

SRCA is a **utility service**, not a BaseAgent subclass. This keeps it lightweight and callable from anywhere in the codebase without incurring agent lifecycle overhead.

---

## API Reference

### `validate_url(url, timeout=5.0, use_cache=True, client=None)`

Fast-check a single URL.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | — | URL to validate |
| `timeout` | `float` | `5.0` | Request timeout in seconds |
| `use_cache` | `bool` | `True` | Use in-memory validation cache |
| `client` | `httpx.AsyncClient \| None` | `None` | Shared client for connection pooling |

**Returns:** `URLValidationResult`

---

### `validate_urls(urls, concurrency=5, timeout=5.0, use_cache=True)`

Batch validate multiple URLs with controlled concurrency.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `urls` | `list[str]` | — | URLs to validate |
| `concurrency` | `int` | `5` | Max concurrent requests |
| `timeout` | `float` | `5.0` | Per-request timeout |
| `use_cache` | `bool` | `True` | Use in-memory cache |

**Returns:** `list[URLValidationResult]` (same order as input)

---

### `URLValidationResult`

```python
class URLValidationResult(BaseModel):
    url: str
    is_valid: bool
    status_code: int | None
    content_type: str | None
    content_length: int | None
    error: str | None
    checked_at: datetime
    response_time_ms: float
    trusted_domain: bool
```

---

## Trusted Domains

SRCA maintains a list of known-reliable Philippine news and government sources that get flagged as `trusted_domain=True`:

- Government: `gov.ph`, `senate.gov.ph`, `congress.gov.ph`, `comelec.gov.ph`, `sc.judiciary.gov.ph`
- News: `rappler.com`, `inquirer.net`, `philstar.com`, `manilatimes.net`, `abs-cbn.com`, `gmanetwork.com`, `cnnphilippines.com`, etc.

---

## Caching

- In-memory cache with 5-minute TTL
- Cache is module-level (shared across all calls in the same process)
- Use `clear_validation_cache()` to manually clear
- Use `get_cache_stats()` to inspect cache state

---

## Example Usage

### Basic single URL check
```python
from app.utils.src_validator import validate_url

result = await validate_url("https://www.rappler.com/national/politics/elections")
if result.is_valid:
    print(f"Valid: {result.url} ({result.response_time_ms:.0f}ms)")
else:
    print(f"Invalid: {result.url} - {result.error}")
```

### Batch validation in an agent
```python
from app.utils.src_validator import validate_urls
from app.schemas.agents import SourceItem

# Inside an agent's _run method
sources: list[SourceItem] = [...]  # from upstream or LLM
validations = await validate_urls([s.url for s in sources])

# Filter to valid sources only
valid_urls = {v.url for v in validations if v.is_valid}
filtered_sources = [s for s in sources if s.url in valid_urls]

# Log failures for investigation
for v in validations:
    if not v.is_valid:
        self.log.warning("source_validation_failed", url=v.url, error=v.error)
```

### Handling validation results
```python
validations = await validate_urls(urls)

valid_count = sum(1 for v in validations if v.is_valid)
invalid_count = len(validations) - valid_count

# Trusted domain boost
for v in validations:
    if v.is_valid and v.trusted_domain:
        boost_credibility_score(v.url, bonus=0.1)
```

---

## Error Handling

SRCA never raises exceptions for validation failures. All errors are captured in the `error` field:

- Network errors → `"Network error: ..."`
- Timeouts → `"Request timeout after Xs"`
- HTTP 4xx/5xx → `"Page not found (404)"`, `"Server error (500)"`, etc.
- Parse errors → `"URL parse error: ..."`
- No content → `"No content received"`

---

## Retry Logic

- Automatic retry (max 2 attempts) for network errors and timeouts
- Exponential backoff: 0.5s → 1s → 2s
- No retry for 4xx client errors (except 405/501 which trigger GET fallback)
