# Product blueprint and POC roadmap

**Blueprint date:** 2026-08-24  
**Demo target:** 2026-08-31

## Information architecture

`/brief` is the mobile-first 30-second **Brief**. `/intelligence` is the full **Analysis Center** and owns the Audience Lab. `/audience` redirects to `/intelligence#audience-lab`. Identity and administration remain supporting surfaces.

Data flow:

`authorized connector → normalized Signal → deduplication/classification → versioned IntelligenceSnapshot → Brief/Analysis APIs → evidence drill-down`

Scenario flow:

`up to three variants + frozen Context Pack → three synthetic samples per cohort → consensus/variance rubric → analyst review`

Provider failure is a visible state. The demo may use a clearly labeled frozen snapshot and one completed scenario, never fabricated live output.

## Brief wire description

1. **Election context line:** “May 8, 2028 expected · research watchlist · not filed candidates.”
2. **Momentum ledger:** rank or suppression, index/version, seven-day movement, coverage confidence, freshness, and largest-change headline.
3. **Five evidence tiles:** attention, net favorability, earned visibility, search interest, strongest appearance/message. Each opens the Evidence Explorer.
4. **Decision row:** one opportunity, one risk, and one analyst-reviewed next move.
5. **Latest poll:** pollster, field dates, sample, exact question summary, margin of error, and separate polling-layer label.
6. **Coverage strip:** missing/stale sources remain present, including incomplete Meta/TikTok competitor coverage.

The cached response target is under two seconds.

## Analysis Center modules and drill-down

| Module | Wire-level content | Evidence drill-down |
|---|---|---|
| Performance | 14-day timeline, figure overlay, current/prior windows | Point → normalized source contributions |
| Momentum breakdown | Six weighted components, delta, methodology version | Component → eligible Signals and exclusions |
| Channels | Platform/format cards and equal-age comparisons | Metric → denominator and capture timestamps |
| Narratives | Lifecycle stage, velocity, ownership, source diversity | Narrative → clustered Signals and classifier confidence |
| Appearances | Recording/transcript, topic allocation, consistency, quote pickup, clip response, 6h/24h/72h lift | Claim/timecode → Signal/clip/source |
| Competitor matrix | Strongest channel, issue ownership, cadence, earned performance, movement | Cell → comparison evidence |
| Audience Lab | Eight friendly synthetic archetypes; three runs each; consensus/variance across six qualitative criteria | Card → cohort basis, Context Pack, model/version, run variance |
| Scenario comparison | Up to three message/strategy variants | Result → frozen context and per-cohort run |
| Polling center | Comparable polls, exact questions and methodology | Point → pollster release |
| Evidence Explorer | Search/filter Signals by layer/source/figure | Signal → original URL/provenance |
| Coverage | Family availability/freshness/rights/denominator quality | Missing family → connector action |

## Acceptance criteria

- All six watchlist figures appear and are labeled `polled_hypothetical`, not candidates.
- The Brief identifies the principal, shows the current score and movement, compares the same evidence window across the watchlist, lists verified public appearances from the last 36 hours, and presents the latest media opinion plus the preceding three. Each opinion uses a word-based importance rating.
- The Brief is optimized for a narrow mobile viewport and never substitutes fixture metrics when its evidence snapshots are missing.
- CMI formula, previous-window delta, deduplication, normalization, low-coverage rank suppression, and poll/synthetic exclusion have unit tests.
- API keeps previous overview and brief fields while adding command/momentum/coverage data.
- Evidence, appearance, methodology, and scenario-comparison endpoints are authenticated and expose provider failures.
- Audience Lab never outputs vote share, individual prediction, or “best target segment.”
- Keyboard focus, heading order, contrast, mobile overflow, and reduced motion are checked.
- Frozen demo data names its capture/effective time and source limitations.

## One-week schedule

- **Aug 24:** source-check knowledge bundle; freeze vocabulary, watchlist, metrics, demo story.
- **Aug 25:** import provenance-bearing snapshot; connect GDELT/RSS, YouTube, PSA, polling and capped X; owned exports only if authorization arrives.
- **Aug 26:** metrics, coverage, seven-day comparison, gating, snapshots.
- **Aug 27:** mobile Brief and evidence drill-down; cache target.
- **Aug 28:** Analysis Center, appearances, competitor matrix, Audience Lab.
- **Aug 29:** optional 100-response directional panel if completed; compliance/accessibility/API/E2E checks.
- **Aug 30:** freeze dataset, rehearse primary flows, retain provider-outage scenario, fix release blockers only.
- **Aug 31:** curated-plus-live demo with freshness and source-coverage disclosure.

## Risks and post-demo roadmap

Primary risks are platform access/rights, late official calendar changes, non-comparable metrics, unrepresentative online activity, transcription/classification error, poll overinterpretation, and provider outage. Mitigate with evidence layers, source contracts, immutable snapshots, gating, human review, budget caps, and frozen fallbacks.

After the demo: replace curated inputs with authorized connectors, validate Tagalog/Cebuano classifiers, add formal COC reconciliation, procure licensed monitoring only after a rights review, run calibration studies, and obtain Philippine election/privacy counsel approval before campaign production use.
