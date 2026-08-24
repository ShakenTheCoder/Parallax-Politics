# Free data acquisition for the Brief

**Research date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Scope:** zero-cost and free-quota inputs for the mobile Brief; Philippines national research watchlist  
**Decision:** build the first real Brief from publisher RSS, GDELT, official YouTube feeds/API metadata, official records, manually exported Google Trends data, and locally run classification. Do not make browser or social-platform scraping part of the product.

## Executive answer

A real, evidence-backed Brief can be operated at zero vendor cost, but it will be an **open-media view**, not a complete social-listening product. The first release can reliably support:

- verified identity, office and a reusable portrait;
- a seven-day **Media Momentum Score** and same-source watchlist ranking after 14 complete days of collection;
- public media appearances discovered from newsroom/official YouTube channels, publisher feeds and official event pages;
- a rolling 36-hour media-framing brief with links to every supporting item; and
- three earlier, immutable opinion snapshots with qualitative importance.

Free, lawful access does **not** provide representative public opinion, voter intent, private-group data, all Facebook/Instagram/TikTok posts, or a complete X conversation. Those claims must not be made. News framing should not be labeled “what the public thinks,” and the score should not be presented as polling or electoral support.

The useful product promise is therefore:

> “What verifiable public media evidence changed around the watchlist, where did it appear, how unusual is it compared with the preceding week, and which underlying sources justify that conclusion?”

## What each Brief section can use

| Brief element | Authoritative zero-cost path | Refresh | Failure behavior |
|---|---|---:|---|
| Name and position | Curated profile linked to the relevant official office directory/site; COMELEC only after official filing | Weekly; daily during status events | Retain last verified value with `verified_as_of`; never infer a new office or candidacy |
| Square portrait | User-supplied licensed asset; expressly reusable government image; or Wikimedia Commons image with license metadata | Monthly rights check | Initials placeholder when rights are not established; never hotlink an unverified press image |
| Current score and movement | Fourteen days of deduplicated publisher/GDELT news, source diversity, YouTube observations and an official Trends export if included in the version | Recompute hourly; publish every 6h or on material change | `unavailable` until minimum history and coverage are met; never substitute fixture values |
| Watchlist rating | Same score version, source set, time window and coverage gate for all six people | Same as score | Suppress ranks for everyone if comparable coverage is below threshold |
| Last 36h appearances | YouTube channel notifications and metadata, publisher RSS, official press/event pages, licensed or user-provided recordings | 5–15 min discovery | Show only verified appearance links; do not convert general mentions into appearances |
| Current 36h media brief | Deduplicated titles, feed descriptions, article metadata and permitted transcripts, classified locally and reviewed when important | Recompute every 15 min; snapshot hourly | “Insufficient current coverage” when evidence is too thin |
| Previous three opinions | Immutable prior snapshots selected on material change, otherwise at six-hour boundaries | On snapshot creation | Show snapshot time and evidence links; do not silently rewrite history |

## Recommended zero-cost source mix

### 1. Philippine publisher feeds: the core evidence stream

Use feeds published by the outlets themselves. On 2026-08-24 the following endpoints returned valid RSS/XML with a title, canonical article link, publication date and description:

| Outlet feed | Access status on research date | POC use |
|---|---|---|
| [GMA News — Nation](https://data.gmanetwork.com/gno/rss/news/nation/feed.xml) and the [GMA RSS directory](https://www.gmanetwork.com/news/rss/) | HTTP 200, XML; publisher documents multiple section/show feeds | Primary national feed plus selected opinion/video/program feeds |
| [INQUIRER.net NewsInfo](https://newsinfo.inquirer.net/feed) | HTTP 200, RSS | National reporting; add its separately identified opinion feed to preserve genre |
| [Philstar headlines](https://www.philstar.com/rss/headlines) and [RSS directory](https://www.philstar.com/rss) | HTTP 200, XML; publisher advertises RSS | National headlines |
| [Rappler](https://www.rappler.com/feed/) | HTTP 200, RSS | Reporting and video discovery; retain the content genre supplied by the publisher |
| [Manila Times — News](https://www.manilatimes.net/news/feed) | HTTP 200, XML | National reporting |

GMA explicitly says its content is copyrighted, permits quoting, embedding and linking in a commercial story, and encourages a partnership for regular reuse. That supports a **headline/excerpt/link and attribution** product, not mirroring articles or audiovisual content. See the [GMA User Policy](https://www.gmanetwork.com/news/user-policy/). Availability of any other feed likewise is not a blanket full-text license: store the feed metadata necessary for evidence, a short source-attributed excerpt where permitted, and the link; do not republish the article body.

ABS-CBN, PNA, Manila Bulletin and News5 endpoints tested during research returned access-control responses from this environment. They remain useful through their official YouTube channels, newsletters, public pages and any feed endpoint the publisher documents, but a connector must not bypass Cloudflare or another access control. PNA’s terms restrict reuse and require written consent for commercial use; its public pages are therefore link/discovery evidence unless a suitable license is obtained. See [PNA Terms of Use](https://www.pna.gov.ph/terms).

Implementation rules:

- Poll feeds with conditional `If-None-Match` / `If-Modified-Since` requests every 5–10 minutes and exponential backoff.
- Sanitize feed HTML. Store title, publisher-supplied description, author/byline, time, category, media enclosure metadata and canonical link—never arbitrary scripts.
- Keep editorial, opinion/column, straight-news, video and sponsored content as separate `editorial_genre` values. An opinion column is not equivalent to newsroom reporting.
- Maintain a hand-reviewed outlet registry with source tier, geography, language, feed URL and reuse note.
- Deduplicate syndicated and updated stories before any count. Canonical URL alone is insufficient; also cluster normalized titles, quoted phrases and publication proximity.

### 2. GDELT: free cross-outlet discovery and gap filling

The [GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) is a free full-text news discovery API supporting boolean phrases, source/language operators, precise time windows, up to 200 results per request, JSON/JSONFeed/RSS output and date sorting. GDELT’s infrastructure commonly operates on a 15-minute cadence. Use one exact alias query per person and a Philippines-oriented domain/source filter where useful, for example:

```text
("Sara Duterte" OR "Inday Sara" OR "Sara Zimmerman Duterte")
```

Run `ArtList`, `format=json`, `sort=DateDesc`, and explicit start/end times every 15 minutes. Treat GDELT as discovery, not truth:

- Resolve the publisher URL and preserve the GDELT retrieval record.
- Apply the same outlet allowlist, rights class and deduplication as direct RSS.
- Do not use GDELT tone as the displayed opinion. It is a machine signal that must be independently validated for Philippine political language.
- Mark an article inaccessible when its publisher page cannot legally/technically be fetched; its URL/title may remain discovery evidence, but it cannot support a detailed claim by itself.

The [GDELT Context 2.0 API](https://blog.gdeltproject.org/announcing-the-gdelt-context-2-0-api/) can return a matching sentence from the last 72 hours. It can help an analyst locate a relevant passage but should not become an unlicensed full-text substitute.

### 3. YouTube: near-real-time appearances without scraping

**Implementation status (2026-08-24):** the Brief worker now discovers channel-ID URLs from reviewed Superadmin glossary accounts, polls the official YouTube Atom feed every 15 minutes, and stores qualifying uploads as provenance-bearing `public_appearance` Signals. A qualifying owned-channel upload must contain direct first-person or interview/speech/event evidence in its published title or description. The Brief shows the publication time, attributable channel, direct video URL, and a bounded extractive description. Headline-only mentions and live blogs remain excluded.

Create an evidence-reviewed registry of official watchlist, newsroom, TV, radio, House, Senate and government channel IDs. Then use the official [YouTube push-notification flow](https://developers.google.com/youtube/v3/guides/push_notifications): WebSub/PubSubHubbub posts an Atom notification when a registered channel uploads a video or changes its title/description. The topic is:

```text
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

This is the best zero-cost discovery path because it is official and avoids broad, repetitive searches. Reconcile missed notifications using the channel uploads playlist. [`playlistItems.list`](https://developers.google.com/youtube/v3/docs/playlistItems/list) costs one quota unit and returns up to 50 items; video metadata/statistics lookup is also a low-cost read. Projects enabling the API receive a default quota allocation documented by Google, while search has a separate daily limit; see the [official quota calculator](https://developers.google.com/youtube/v3/determine_quota_cost) and [API overview](https://developers.google.com/youtube/v3/getting-started).

Recommended flow:

1. Receive a channel-upload notification.
2. Fetch `videos.list(part=snippet,contentDetails,statistics,status)` for the ID.
3. Match the title/description against the evidence-reviewed alias set.
4. Classify as `appearance`, `mention`, `owned_statement`, or `not_relevant`; require a direct visual/audio/source-description basis for `appearance`.
5. Snapshot public metrics at 1h, 6h, 24h and 36h so equal-age comparisons have real denominators.
6. Show the original YouTube URL, publisher/channel, publication time and a short evidence-derived caption.

Caption/transcript limits are decisive. The official [`captions.download`](https://developers.google.com/youtube/v3/docs/captions/download) method requires authorization from a user who has permission to edit the video. Therefore:

- owned-channel captions are available after the owner authorizes the application;
- competitor or broadcaster captions are **not** generally downloadable through the official API;
- production use of `yt-dlp`, undocumented caption endpoints, comment-page extraction or audio downloading is not a compliant substitute—YouTube’s [Developer Policies](https://developers.google.com/youtube/terms/developer-policies) prohibit scraping YouTube applications and impose storage/refresh rules on API data; and
- for third-party video, use title/description and a link unless the publisher provides a transcript or separately licensed/downloadable recording.

YouTube non-authorized API data must be refreshed or deleted within the applicable policy period (normally no longer than 30 days), deleted videos must be reflected, and YouTube metadata must remain visibly attributed. The score derived by this product must be labeled as the product’s own metric, not a YouTube metric.

### 4. Google Trends: useful, but only through official paths

Google documents four legitimate free paths:

1. [manual CSV export](https://support.google.com/trends/answer/4365538) from Explore, with Google attribution;
2. the Trending Now page’s official CSV/RSS export, refreshed about every ten minutes and supporting a Philippines location where available ([Trending Now help](https://support.google.com/trends/answer/3076011));
3. the international Google Trends public dataset in BigQuery, whose daily top/rising tables can be queried in the BigQuery sandbox/free tier ([dataset guide](https://support.google.com/trends/answer/12764470)); and
4. the [Google Trends API alpha](https://developers.google.com/search/apis/trends), which offers consistently scaled, comparable data but still requires acceptance into a limited tester program.

The normal Explore values are a normalized 0–100 sample, not query counts; low-volume terms may be zero and statistical noise exists. See Google’s [Trends data FAQ](https://support.google.com/trends/answer/4365533).

For the initial Brief, ingest one analyst-exported, fixed comparison CSV each morning for the exact watchlist, country `PH`, category and search type. Store the source URL/query configuration and the entire comparison batch so values remain comparable. Trending Now RSS can alert on a watchlist name but cannot replace figure-specific search share. Apply for alpha API access in parallel. Do not put `pytrends`, direct Explore-page automation or undocumented Google News/Trends calls in the production connector.

### 5. Official Philippine sources: identity and event corroboration

- The Department of Budget and Management’s [2026 Government Directory](https://www.dbm.gov.ph/wp-content/uploads/AboutDBM/2026-Government-Directory.pdf) identifies Sara Z. Duterte as Vice President and provides the OVP’s official site. Use equivalent official office directories/pages for all officeholders.
- COMELEC’s certified lists and resolutions are authoritative for filed-candidate status. A watchlist member remains `polled_hypothetical`, not a candidate, until an official filing/status record exists. COMELEC’s prior [certified-list resolution](https://www.comelec.gov.ph/index.html?r=2025NLE%2FResolutions%2Fcom_res11097A) shows the form of authoritative record to monitor when 2028 materials are published.
- Official Gazette, Senate, House, OVP, PCO, LGU and agency press/event pages can corroborate hearings, speeches and appearances. Capture the URL, publication date, event date and publishing office; an official source represents that office’s account and is not independent media corroboration.
- PSA OpenSTAT offers an official API, open-data attribution terms, multiple structured formats, and a limit of ten requests per ten seconds ([API guide](https://openstat.psa.gov.ph/API-Documentation), [open-data statement](https://openstat.psa.gov.ph/About)). PSA data is valuable context, but it should not alter a person’s daily media score.

For portraits, prefer an image supplied by the client with documented rights. A government site’s generic “public domain unless otherwise stated” footer must be checked against the specific photo credit. The PCO has published presidential photo galleries under that notice, but each selected asset still needs an evidence record. A second free option is Wikimedia Commons: its [MediaWiki API](https://commons.wikimedia.org/wiki/Commons%3AAPI/MediaWiki) and [`imageinfo` metadata](https://www.mediawiki.org/wiki/API%3AImageinfo/en) expose the file URL and extended license/creator fields. Save creator, source, license, license URL and attribution text. All Creative Commons licenses require attribution; see [Creative Commons’ reuse guidance](https://creativecommons.org/reusing-cc-licensed-content/).

### 6. Facebook and Instagram: owned access only in the free product

The Meta-maintained [Instagram API documentation collection](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api) states that the API is for professional Business/Creator accounts, requires a Meta app and authorization, cannot access consumer accounts, and can manage/read the authorized professional presence. It can also expose limited metadata about other professional accounts through permitted features, but it is not a competitor-wide listening API.

For Facebook, page content and insights should be collected only when the principal’s Page grants the application the necessary Page permissions. Public Page discovery/content features require Meta app review; Meta has long documented that [Page Public Content Access requires review](https://about.fb.com/news/2018/07/a-platform-update/). Meta Content Library provides broad public Facebook/Instagram research access only to qualifying researchers and institutions, not an ordinary commercial campaign product; see Meta’s [Content Library announcement and eligibility description](https://about.fb.com/news/2023/11/new-tools-to-support-independent-research/).

Consequences for the Brief:

- Principal-owned Facebook/Instagram content and insights: feasible at zero API charge after authorization/app review.
- Competitor-wide public posts, comments and engagement: unavailable in the zero-cost commercial MVP.
- Browser automation using a staff member’s logged-in session, cookie export, HTML scraping, mobile/private endpoints or rotating accounts: brittle, privacy-sensitive and unsuitable for a production product.
- Until access exists, show `Facebook/Instagram competitor coverage: unavailable`; never insert zeroes into competitors’ scores.

### 7. TikTok: owned authorization or links, not free competitor monitoring

TikTok’s official [Display API](https://developers.tiktok.com/docs/en/display-api-get-started) can return the authorizing user’s profile and recent public videos after Login Kit, app approval and `user.info.basic` / `video.list` consent. It is suitable for the principal’s owned account. The public [oEmbed API](https://developers.tiktok.com/docs/en/embed-videos) can turn a known TikTok video URL into an attributed embed and metadata, which is useful after a source link is discovered elsewhere.

The broad [TikTok Research API](https://developers.tiktok.com/products/research-api/) is for approved academic/nonprofit public-interest research in eligible regions and explicitly excludes creators, advertisers and commercial users. It cannot be assumed for this product. TikTok also says new videos may take up to 48 hours to appear in Research API search and some statistics may lag by ten days, making it unsuitable for a 36-hour operational Brief even for an eligible project ([Research API FAQ](https://developers.tiktok.com/doc/research-api-faq)).

Do not use browser scraping, private mobile endpoints, cookie automation or downloadable-video tools for competitor coverage. With no authorization, store only an already-known public URL and oEmbed metadata; mark discovery completeness as unavailable.

### 8. X: no longer a zero-cost data source

The current official X API uses prepaid, pay-per-use credits, with no subscription or minimum commitment but no general free read allocation. See [X API introduction](https://docs.x.com/x-api/introduction) and [usage/billing](https://docs.x.com/x-api/fundamentals/post-cap). Therefore X is not part of a strictly zero-spend MVP.

Do not replace it with cookie-backed browser scraping, undocumented GraphQL endpoints or logged-in session automation. Those paths are operationally brittle and create account, privacy and terms risk. Keep X visibly missing until a capped API budget is authorized.

### 9. Google News RSS and public-web crawling: discovery-only fallbacks

On the research date, an undocumented Google News search feed such as

```text
https://news.google.com/rss/search?q=%22Sara%20Duterte%22&hl=en-PH&gl=PH&ceid=PH%3Aen
```

returned RSS. Google does not publish a stable product contract for this search endpoint, and Google News changed its publisher/feed workflow in 2025. Use it only as a non-authoritative discovery fallback, never as the only source for a metric or claim. Resolve and cite the publisher article. A response change must degrade gracefully without losing the core Brief.

Public websites without feeds may be checked only when the site terms permit it, `robots.txt` allows the relevant path, access controls/paywalls are not bypassed, the crawler has an honest user agent/contact, and request rate is conservative. `robots.txt` controls crawler access but does not grant copyright permission; Google’s [robots guide](https://developers.google.com/search/docs/crawling-indexing/robots/intro) explains that distinction. Prefer sitemap/feed metadata and Open Graph/JSON-LD fields. Do not archive full copyrighted articles merely because they are publicly readable.

## Locally digesting the evidence at zero API cost

### Text processing

Run classification locally so cost and provider outages do not block the Brief. Hugging Face Transformers is Apache-2.0 licensed and provides text-classification and zero-shot-classification pipelines ([license](https://github.com/huggingface/transformers/blob/main/LICENSE), [pipeline documentation](https://github.com/huggingface/transformers/blob/main/docs/source/en/main_classes/pipelines.md)). Model weights have their own licenses; approve and pin a specific model/version before production.

The classification pipeline should perform separate, auditable tasks:

1. subject/alias match;
2. editorial genre (`straight_news`, `editorial`, `opinion_column`, `interview`, `official_statement`, `video`, `sponsored`, `unknown`);
3. event/issue tags;
4. framing toward the subject (`supportive`, `neutral_or_mixed`, `critical`, `unclear`);
5. appearance test (`direct_speaking_or_visual_presence`, `mentioned_only`, `unclear`);
6. concise evidence-grounded caption and cluster summary; and
7. confidence plus a reason span pointing to the exact permitted source text.

Do not call a straight-news item the outlet’s “opinion.” The user-facing heading can be “Media brief” or “What coverage is saying,” with a persistent note: **news framing, not public opinion or polling**. Only items actually labeled editorial/opinion by their publisher can support a claim about expressed editorial opinion.

For Filipino, English, Taglish and regional-language evidence, create a hand-labeled validation set before publishing automated framing. Low-confidence or language-unsupported items become `unclear`; they are not forced into positive/negative. Critical and high-importance output requires analyst review.

### Audio transcription

[OpenAI Whisper](https://github.com/openai/whisper) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper) are MIT-licensed, multilingual, locally runnable transcription software. The software’s license does not grant rights to the audio. Transcribe only:

- client-owned recordings;
- official recordings with an explicit reusable/downloadable license;
- podcast/RSS enclosures whose terms allow this processing; or
- files supplied under a media-monitoring/license agreement.

Do not download third-party YouTube/TikTok/Facebook audiovisual content merely to feed Whisper. When transcript rights are absent, the Brief can still link to the appearance and describe it from publisher-supplied metadata, but it must not invent a transcript or detailed quotation.

## A score that the evidence can honestly support

Call the number **Media Momentum Score**, not popularity, favorability, electability or voter support. Version 1 should be a seven-completed-day comparison against the immediately preceding seven completed days:

| Component | Weight | Real input |
|---|---:|---|
| Earned attention | 30% | Subject’s share of deduplicated, eligible newsroom story clusters across the fixed feed/domain set |
| Source diversity | 20% | Effective number of independent publishers/source types after syndication and same-owner grouping |
| Coverage acceleration | 20% | Current seven-day source-normalized cluster velocity versus the preceding seven days |
| Public-video resonance | 20% | Equal-age YouTube views/comments/likes for qualifying newsroom/official videos, normalized inside channel and format; unavailable denominators remain null |
| Search interest | 10% | Same-batch, PH Google Trends comparison from official CSV or approved API |

Convert each component to a 0–100 percentile within the fixed watchlist and fixed source/version, then apply the weights. The displayed point change is the score difference from the preceding comparable snapshot. Do not silently redistribute a missing component’s weight.

Publication gates:

- at least 14 complete days collected;
- all watchlist figures processed through identical aliases, sources and windows;
- overall coverage confidence at least 60%;
- earned-media sources and YouTube registry both healthy;
- official Trends batch not stale if search is part of the score version; and
- no unresolved high-confidence duplicate or identity collision.

Polling, synthetic personas, owned private analytics and model-generated “favorability” stay outside this score. A high score means **more and faster open-media momentum in the observed source set**, which may be driven by favorable or unfavorable events. The adjacent media brief explains the direction and why.

## The 36-hour media brief and qualitative importance

Every 15 minutes, cluster eligible evidence published in `[now - 36h, now]`. Produce one concise current framing summary only if it can cite at least two independent items or one authoritative direct event plus one independent report. Save an immutable snapshot hourly when materially changed; otherwise save at six-hour boundaries. “Previous three opinions” should mean the previous three distinct framing snapshots, not three invented pieces of prose.

Use these displayed importance words:

| Display word | Evidence rule |
|---|---|
| **Critical** | Verified legal/status/safety event, or a fast-moving cluster independently carried across at least three established outlets/source types and requiring immediate analyst attention |
| **High** | At least three independent eligible sources, or a direct appearance/statement picked up by two independent outlets, with material change from the prior snapshot |
| **Medium** | Two independent sources on a relevant issue, or one high-quality direct source with meaningful but limited pickup |
| **Low** | Isolated, duplicative, routine or low-confidence coverage that does not materially change the current framing |
| **Needs review** | Evidence conflict, unsupported language/model, identity ambiguity or classification confidence below threshold |

The UI displays only the word, but the evidence drawer must show why it was assigned: sources, time, independence, event type and review status. Importance is urgency/salience, not positive or negative sentiment.

## Normalized records

### `SourceRegistry`

```text
source_id
publisher_name
publisher_owner_group
source_type                  # rss, gdelt, youtube, official_web, trends_csv, ...
source_tier
language_scope[]
geography_scope[]
feed_or_api_url
official_account_id
access_method
rights_class                 # link_only, metadata_excerpt, owned_authorized, cc_by, public_domain, licensed
rights_url
robots_checked_at
terms_checked_at
poll_interval_seconds
enabled
```

### `SignalEvent`

```text
signal_id
connector
external_id
canonical_url
source_id
source_domain
source_type
source_tier
rights_class
published_at
captured_at
source_updated_at
language
geography
title
publisher_description
author_or_channel
editorial_genre
content_format
subject_profile_ids[]
subject_match_basis[]        # exact name, alias, official account, reviewed match
appearance_status
observed_metrics{}           # views, likes, comments with snapshot time and denominator
observation_type             # observed or inferred
cluster_id
content_fingerprint
classification_version
topics[]
framing_label
classification_confidence
reason_spans[]
human_review_status
```

### `BriefSnapshot`

```text
snapshot_id
effective_at
window_start
window_end
method_version
principal_profile_id
score
score_delta
score_coverage
rank
rank_eligible
watchlist_scores[]
appearance_signal_ids[]
media_brief_text
media_brief_label            # supportive, neutral_or_mixed, critical, unclear
importance_word
supporting_cluster_ids[]
reviewed_by
reviewed_at
missing_sources[]
```

Every summary sentence and displayed score must resolve to its component values and Signal IDs. Raw fetched payloads should be retained only as long as rights/platform policy permits; immutable snapshots retain calculations and provenance, not an unauthorized copy of the underlying article/video.

## Collection and computation schedule

| Job | Schedule | Notes |
|---|---:|---|
| Publisher RSS | Every 5–10 min | Conditional requests; jitter/backoff; sanitize and deduplicate |
| GDELT discovery | Every 15 min | One alias query/person; overlap last interval to avoid gaps; deduplicate |
| YouTube WebSub | Event-driven | Renew subscriptions; idempotent webhook processing |
| YouTube upload reconciliation | Every 30 min, plus daily full check | Upload playlist rather than repeated broad search |
| YouTube public metric snapshots | 1h, 6h, 24h, 36h after publication; daily thereafter while retained | Respect refresh/deletion and attribution policies |
| Google Trending Now RSS | Every 10 min | Alert/discovery only, not figure search share |
| Google Trends comparison CSV | Daily, fixed operator workflow | Same terms, geography, category, type and batch |
| Official identity/status pages | Weekly; daily when filings/status events begin | Two-source review for material profile changes |
| Public government/news event pages | Every 30 min where feed exists; otherwise daily | No access-control bypass |
| Classification and clustering | On arrival; reconcile every 15 min | Pin model/rules version |
| 36h brief recomputation | Every 15 min | Publish only on material change or hourly boundary |
| Score/watchlist snapshot | Every 6h | Requires 14-day history and coverage gates |
| Link/rights health | Daily links; monthly terms/license review | Disable sources whose terms or access change |

## Supported versus unacceptable acquisition

| Classification | Methods |
|---|---|
| **Supported core** | Publisher RSS/Atom; GDELT documented APIs; YouTube WebSub and Data API; manual official Google Trends exports; accepted Trends alpha; PSA OpenSTAT; official downloadable records; client-authorized Meta/TikTok owned-account APIs; TikTok oEmbed for a known URL; licensed/CC/public-domain assets |
| **Conditional public web** | Sitemap/JSON-LD/Open Graph/headline capture where terms and robots permit it, with conservative rate, clear user agent, no paywall/access bypass and link-first storage |
| **Discovery only** | Undocumented Google News RSS; search-engine result links; GDELT context sentences; manually observed public social links |
| **Do not productize** | Logged-in browser/cookie scraping; private/mobile GraphQL endpoints; rotating identities/proxies; captcha or Cloudflare bypass; `yt-dlp`/caption scraping for production; automated Google Trends Explore scraping/`pytrends`; full-article mirroring; private groups/messages; paywall bypass; facial recognition/emotion inference |

## Concrete MVP sequence

1. Curate the six profile IDs, aliases, offices, official sites/channel IDs, portrait rights and watch status. No connector should fuzzy-match names before this registry is reviewed.
2. Enable the five validated publisher feeds and GDELT. Collect link-first evidence continuously.
3. Register the official YouTube channels for WebSub, enable a free Google Cloud API key for metadata, and start equal-age snapshots.
4. Add a once-daily, fixed Google Trends CSV import; apply for Trends API alpha access but do not block the MVP on approval.
5. Run local subject, genre, topic and framing classification; hand-label and evaluate English, Filipino and Taglish before publishing its output.
6. Accumulate 14 full days. During this period the page should show real appearances and media briefs, while score/rank says “Building baseline” rather than displaying dummy numbers.
7. Turn on score/rank only after the fixed-source coverage gate passes. Every score, appearance and brief sentence opens its evidence drawer.
8. Add owned Facebook/Instagram/TikTok only after the principal authorizes the accounts. Keep competitor social gaps visible. X remains excluded at zero spend.

## What the product team still needs from the client

- Confirm the principal and fixed comparison watchlist.
- Approve all aliases, official websites and official YouTube/social account URLs.
- Supply a portrait with reuse rights or approve a specifically licensed/public-domain asset and attribution.
- Create a Google Cloud project/API key for YouTube Data API; the key must live in a secret store, not source control.
- Decide who performs the daily Google Trends export until alpha API access exists.
- Authorize the principal’s professional Meta/TikTok accounts if owned data is desired; competitors cannot be authorized by the principal.
- Confirm the workstation/server available for local text and Whisper inference.
- Name an analyst responsible for reviewing Critical/High items and disputed classifications.
- Obtain Philippine privacy/election and source-licensing review before campaign production use.

## Acceptance evidence for “real data”

The Brief is real only when all of the following are demonstrable:

- No production endpoint imports the POC fixture or creates a score/opinion from a seeded constant.
- A new feed or YouTube item produces one normalized Signal with capture time, rights class and source link.
- A duplicate story from two feeds forms one cluster while retaining both source records.
- An appearance is supported by a direct video/event link and explicit appearance basis.
- The current media brief cites its supporting clusters; removing those Signals causes it to recompute or become unavailable.
- The previous three opinions are stored snapshots with their original windows and evidence, not regenerated text.
- Scores stay unavailable for the first 14 days and ranks remain suppressed below the coverage threshold.
- The same source set, alias rules, normalization and time windows apply to every watchlist person.
- Missing Meta, TikTok and X competitor coverage is visible and never treated as zero activity.
- Every displayed point movement can be reproduced from retained component snapshots and the pinned method version.
