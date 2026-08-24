# Media and data source catalog

**Source date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Scope:** Philippines national and regional public evidence

## Source tiers

- **Tier 1:** law, COMELEC/PSA/NPC and other official records, pollster methodology releases, verified first-party office channels.
- **Tier 2:** established newsroom, broadcast, and radio reporting with byline/time and a retrievable source record.
- **Tier 3:** public platform snapshots and aggregator feeds whose completeness, rights, or denominator is limited.
- **Tier 4:** unattributed reposts, screenshots without origin, or analyst inference; discovery only.

## Catalog

| Source | Access method | Language / geography | Refresh | Rights and limitations | Tier | Connector readiness |
|---|---|---|---|---|---:|---|
| COMELEC, PSA, NPC, official departments/LGUs | Official web/API/download | English/Filipino; national/local | On publication + daily checks in election periods | Public record; preserve attribution and terms | 1 | Ready: public web/manual import; APIs where documented |
| Pulse Asia and other qualifying pollsters | Release/PDF/manual structured import | National + reported subgroups | On publication | Store question, field dates, sample, method, uncertainty | 1 | Ready: curated import |
| Official websites and public channels of watchlist figures | Authorized API, RSS where present, timestamped snapshot | Mixed; figure-specific | 15–60 min for POC where authorized | Public availability is not blanket reuse permission | 1/3 | Partial |
| Facebook | Graph API for authorized owned assets; timestamped public snapshots otherwise | Filipino, English, regional languages | 15–60 min owned; daily public snapshot | Competitor-wide access is **incomplete unless licensed or authorized**; no private groups/Messenger | 3 | Owned partial; competitor incomplete |
| YouTube | YouTube Data API, captions/transcript where permitted | Mixed; national/regional | 15–60 min channels, daily search | Quota and API policies; metrics are cumulative snapshots | 2/3 | Ready for public metadata with key |
| TikTok | Authorized owned analytics or licensed provider | Mixed; national/regional | 15–60 min owned | Competitor-wide access is **incomplete unless licensed or authorized**; no circumvention | 3 | Not ready without authorization/license |
| Instagram | Meta-authorized owned analytics; public snapshots | Mixed | 15–60 min owned | Same ownership and completeness limits as Facebook | 3 | Owned partial |
| X | Official pay-per-use API with hard budget cap | English/Filipino; national | 15–60 min | Pay-per-use, endpoint limits, platform terms; public conversation is non-representative | 3 | Ready after credentials/budget cap |
| Google Trends | Official interface/export or approved API | National/subregion | Daily | Relative index, not search counts or voter intent | 2/3 | Curated/manual until approved API path |
| GMA News, ABS-CBN News, News5/TV5 | RSS/licensed feed/public article | English/Filipino; national/regional bureaus | 15 min | Headline/excerpt/link unless licensed for full text | 2 | RSS/public-web partial |
| Philippine Daily Inquirer, Philippine Star, Manila Bulletin, Rappler, Manila Times | RSS/licensed feed/public article | English/Filipino; national | 15–30 min | Paywall/copyright and full-text restrictions vary | 2 | RSS/public-web partial |
| SunStar and identified regional outlets | RSS/public article/licensed feed | English/regional | 30–60 min | Coverage varies by edition; preserve outlet geography | 2 | Catalog/import pending |
| Philippine News Agency | RSS/public article | English; national/regional | 15–30 min | Government newsroom; do not equate with independent corroboration | 2 | Public-web/RSS ready |
| DZBB, DZRH, Radyo Pilipinas and regional radio | Public stream, clip, licensed recording, transcript | Filipino/English/regional | Appearance-driven | Recording/transcription rights; identify speaker and program | 2/3 | Transcript pipeline partial |
| TV/radio appearances and press conferences | Licensed/public recording + transcript | Mixed | Event-driven | Retain clip URL, timecodes, transcription method and correction record | 1–3 | Manual/Deepgram-ready |

## Required Signal provenance

Every normalized Signal records connector, capture time, source URL, source tier, source-rights classification, publication time where available, platform/content format, metric denominator, geographic scope, language, classification confidence, and `observation_type` (`observed` or `inferred`). Translations and model classifications point back to the original Signal.

Missing/stale connectors remain visible in coverage diagnostics. They are never backfilled with zeroes.

