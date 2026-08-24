# Metrics and ranking methodology

**Method version:** `cmi-2028-poc-v1`  
**Source date:** 2026-08-24  
**Scope:** seven-day national research watchlist comparison

## Evidence layers

Metrics always retain one of four mutually visible layers:

1. **Observed performance:** public posts, articles, appearances, search indices, and public engagement snapshots.
2. **Owned analytics:** explicitly authorized first-party insights with known denominators.
3. **Polling:** representative survey records with methodology.
4. **Synthetic simulation:** artificial cohort/archetype runs over a frozen Context Pack.

Polling and synthetic output are excluded from Campaign Momentum. Owned and public metrics are not mixed at the raw denominator level.

## Campaign Momentum Index

For the current seven complete days compared with the immediately preceding seven complete days:

`CMI = .25 attention + .20 channel-normalized resonance + .20 net favorability + .15 earned visibility + .10 search interest + .10 issue ownership`

Each component is a 0–100 normalized index. The final score is rounded to one decimal. Normalization happens inside platform, content format, and equal-age window before aggregation. The index version is stored on every snapshot.

Rank is suppressed when coverage confidence is below 60%. The API then returns `rank: null`, `rank_suppressed: true`, and the missing/degraded source list.

## Definitions

| Metric | Definition / denominator |
|---|---|
| Attention share | Figure’s eligible mentions/views/search-presence numerator divided by total eligible watchlist attention within the same source/window; source-normalized before aggregation |
| Engagement velocity | Change in eligible interactions per hour for equal-age content |
| Reaction rate | Reactions / eligible impressions when owned denominator exists; otherwise reactions / views or followers, explicitly labeled |
| Discussion rate | Comments or replies / stated denominator |
| Amplification rate | Shares, reposts, or quote posts / stated denominator |
| Audience growth | Net follower/subscriber change / starting audience for authorized channels |
| Stance | Classified supportive, neutral/mixed, critical, or unknown; not a demographic trait |
| Net favorability | Weighted supportive share minus weighted critical share among classifiable eligible observations; unknowns remain in coverage |
| Issue ownership | Share of source-diverse, figure-associated eligible discussion for a named issue after duplicate suppression |
| Message penetration | Share of eligible coverage/audience observations repeating a defined message element |
| Earned visibility | Eligible third-party editorial/broadcast visibility, weighted by source tier and deduplicated story cluster |
| Source diversity | Effective number of independent source domains/types contributing to a claim or narrative |
| Search share | Relative Google Trends share across the exact comparison set and geography; not absolute query volume |
| Appearance lift | Difference between pre-event baseline and 6h/24h/72h post-event normalized attention/resonance |
| Quote pickup | Independent outlets/channels carrying a materially matching attributable quote |
| Poll trend | Change between comparable poll questions/methods; outside CMI |
| Coverage confidence | Weighted availability × freshness × denominator quality × classification quality across required connectors |

## Coverage and missing data

Required POC source families and default weights are news/RSS 25%, public video/social 25%, search 15%, polling 15%, official records 10%, appearances/transcripts 10%. Coverage is the weighted mean of each family’s availability, freshness, rights usability, and denominator quality. Polling coverage affects product confidence but never the CMI score.

- Missing is `null`, never zero.
- Stale evidence remains displayed with age and reduces coverage.
- A component with insufficient inputs is omitted and remaining CMI weights are **not** silently rescaled; the index is withheld if the required minimum is not met.
- Duplicate syndication is clustered by canonical URL/content fingerprint/quote overlap before counts.
- Classification below the configured confidence threshold becomes unknown.

## Source weights and examples

Official records and pollster releases support status/method claims, not public resonance. Earned-media visibility weights independent Tier 2 reporting above reposts. Platform metrics are z-scored or percentile-normalized within platform and format, then clipped to avoid one viral item dominating the index.

Example: if components are attention 62, resonance 58, favorability 54, earned 66, search 60, ownership 57, the index is `59.6`. If coverage is 57%, the score may be shown as provisional but rank is suppressed with missing sources named.

## Versioning

Any weight, normalization, deduplication, classifier, inclusion, or source-tier change creates a new `model_version`. Historical snapshots are immutable. Comparisons use the same version or are labeled non-comparable and recomputed from retained Signals.

