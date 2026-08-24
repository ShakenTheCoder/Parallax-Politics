# Third-party services and costs

**Pricing checked:** 2026-08-24  
Prices are USD, exclude tax, and must be rechecked before purchase. “Quote-only” means the vendor does not publish a stable list price suitable for this POC.

| Service | Benefit / exact POC improvement | Public price or quote | Trial/API | Integration estimate | Rights/limits | Recommendation |
|---|---|---|---|---|---|---|
| GDELT / GDELT Cloud | Broad news discovery and event clustering for earned visibility | Free/terms-dependent legacy feeds; Cloud plan/rights need confirmation | API/feed | 1–2 days | Discovery is not a full-text license; obey [acceptable use](https://gdeltcloud.com/acceptable-use) | Use RSS/GDELT discovery for POC, preserve original links |
| Event Registry / NewsAPI.ai | Deduplication, concepts, multilingual article discovery | Free 2,000 searches; 5K plan $90/mo on [official pricing](https://newsapi.ai/plans) | API key/free plan | 1 day | Full-content and retention rights depend on plan/source | Optional $90 upgrade only if free coverage fails |
| YouTube Data API | Official channel/video metadata and public metrics | Default 10,000 quota units/day, no listed API fee on [official overview](https://developers.google.com/youtube/v3/getting-started) | Google project/key | 1–2 days | Quota, captions, storage and developer policies | Use free quota |
| X API | Public post/account evidence with exact IDs and timestamps | Posts read $0.005 each on [official pricing](https://developer.twitter.com/) at check date | Prepaid pay-per-use | 1–2 days | Hard cap, terms, incomplete public-conversation representativeness | Cap new spend at $50 |
| Data365 | Potential Facebook/Instagram/TikTok/X data API | Quote/usage pricing must be confirmed with vendor | API/trial varies | 2–4 days | Platform and downstream retention/competitor rights need written review | Do not depend on it for demo |
| Isentia | Philippine/SEA media monitoring, broadcast and clipping | Quote-only | Sales-led | 1–3 weeks | Licensed-content scope and API/export rights | Post-demo procurement candidate |
| Meltwater | Cross-media/social listening and workflow | Quote-only on [official pricing](https://www.meltwater.com/en/pricing) | Sales demo | 1–3 weeks | Contract-specific sources, seats, exports and retention | Post-demo comparison |
| Talkwalker | Social listening/media monitoring | Quote-only on [official pricing](https://www.talkwalker.com/pricing) | Sales demo | 1–3 weeks | Contract/source coverage and export rights | Post-demo comparison |
| Brandwatch | Enterprise social listening and historical analysis | Quote-only | Sales demo | 1–3 weeks | Contract/source/retention limits | Post-demo comparison |
| Deepgram | Transcribe public appearances; timecodes for quote pickup | New-account $200 credit then PAYG on [official pricing](https://deepgram.com/pricing) | $200 credit | 1–2 days | Recording rights, speaker correction, language accuracy and retention | Use trial for approved demo audio |
| Pollfish | Directional 100-response calibration panel | Starts at $0.95/response for 100 on [official pricing](https://www.pollfish.com/pricing/) | Pay per complete | Questionnaire 1 day; fieldwork vendor-dependent | Directional, targeting-dependent price; disclose method and do not overclaim | Budget approximately $95 if fieldwork completes |
| PSA OpenSTAT | Primary demographic/economic aggregates | Free public statistics | Web/API/table export | 1 day/table set | Cite table/reference period; aggregation does not authorize personal inference | Use |
| Mapbox | Regional maps and source-coverage visualization | Web maps free through 50,000 monthly loads on [official pricing](https://www.mapbox.com/pricing) | Account/token | 1 day | Business-intelligence licensing and map/data terms require review | Optional; not needed for core demo |
| Google Cloud Translation | Consistent source translation with provider metadata | First 500k NMT characters/month free; then $20/million on [official pricing](https://cloud.google.com/products/translate/pricing) | Google Cloud | 1 day | Keep original; machine translation needs review for consequential claims | Optional within free credit |
| Apify | Managed collection for sources with permitted Actors | Free $5 monthly usage; Starter $29/mo on [official pricing](https://apify.com/pricing) | Free plan | 1–3 days per Actor | Actor access does not override site/platform terms; variable Actor charges | Avoid for restricted social sources; optional public-web helper |
| Model providers | Classification, narrative clustering, and synthetic qualitative runs | Usage-based; check [OpenAI](https://openai.com/api/pricing/), [Anthropic](https://www.anthropic.com/pricing), and [Gemini](https://ai.google.dev/gemini-api/docs/pricing) immediately before freeze | Existing keys/credits vary | Existing adapter 0.5–2 days/provider | No training on client data unless contracted; retention, residency, political-use and model-version review | Use existing provider with per-run cost log and frozen fallback |

## Recommended POC spend

- GDELT/RSS and YouTube default quota: $0 new spend.
- X: hard cap $50.
- Pollfish: approximately $95 for 100 directional completes, only if feasible.
- Deepgram: use trial credit.
- Event Registry 5K: optional $90.

Known recommended new spend is therefore **$145**, or **$235** with the optional Event Registry upgrade, plus existing model usage. Do not purchase quote-only enterprise monitoring for the one-week POC.

