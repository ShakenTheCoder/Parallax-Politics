# Political activity monitor: source registry and connector policy

**Research date:** 2026-08-24  
**Publication date:** 2026-08-24  
**Retrieval date:** 2026-08-24  
**Geographic scope:** Philippines; national sources plus the Naga and Baguio LGU sources attached to glossary members  
**Document confidence:** high (0.90) for connector tests and official access rules; medium-high (0.82) for current account completeness because many stored accounts originate in Wikidata and still require first-party verification  
**Scope:** the 30 active people currently seeded in the Superadmin political glossary  
**Decision status:** source-control specification for implementation; an entry marked `ready` may be collected, while `review` and `blocked` entries must not silently enter production

## Decision

The monitor should be one structured public-activity ledger for all 30 glossary people. It should not be 30 independently assembled profile pages and it should not treat every article mentioning a person as an appearance.

The first production-safe collection set is:

1. publisher-operated RSS feeds that returned valid XML on the retrieval date;
2. official YouTube Atom feeds for reviewed channel IDs;
3. public Naga and Baguio pages collected with a bounded, identifiable Scrapling HTTP fetcher, with Senate, House and PCO retained as mandatory-but-blocked sources until an approved access path is available; and
4. the official X API only after prepaid credits and credentials are supplied.

Facebook, Instagram and TikTok competitor-wide collection is **not ready**. Their official access paths require app review, business verification, a person's authorization, or research eligibility that a commercial political product cannot assume. Scrapling must not be used to evade those gates.

This decision is deliberately narrower than “scrape everything public.” It creates a defensible activity product that can answer: who directly appeared, who issued a public statement, what topic was attached to the event, which publishers independently corroborated it, and how activity changed against an equal preceding period.

## Authoritative record and evidence layers

Every normalized record must preserve these fields:

| Field | Required rule |
|---|---|
| Person | Foreign key to `PoliticalFigure`; never a free-text name |
| Occurred at | Event time when stated; otherwise null, never silently copied from publication time |
| Published at / observed at | Both retained separately |
| Activity kind | `speech_or_statement`, `interview`, `debate`, `hearing_or_session`, `press_conference`, `public_event`, `social_video`, `written_statement`, or `official_announcement` |
| Evidence layer | `direct_appearance`, `public_statement`, `indirect_coverage`, or `public_reaction` |
| Venue / program | Extracted only when directly supported; otherwise null |
| Topic | Controlled topic plus evidence span |
| Summary | Short source-grounded paraphrase; no unsupported facts |
| Direct source | Canonical event, recording, statement, or publisher URL |
| Publisher/source | Registry source ID and displayed publisher name |
| Initiation | `self_initiated`, `earned_appearance`, `institutional_proceeding`, or `indirect` |
| Identity basis | Alias, official account, office, location/program context, or analyst review |
| Confidence | Score plus human-readable basis and source tier |
| Rights | Metadata/link, short excerpt, transcript-authorized, or discovery-only |
| Provenance | Connector, capture time, response hash, source URL, model/version, and review state |

The system must preserve four different evidence layers. A television interview is a `direct_appearance`; a signed press release is a `public_statement`; an article discussing a person who did not participate is `indirect_coverage`; reactions to the event are `public_reaction`. These layers may be linked to one event cluster, but never collapsed into one count.

## Registry vocabulary

### Confidence tiers

| Tier | Meaning | Default confidence range |
|---|---|---:|
| T1 | First-party official account, official proceeding, or direct recording with explicit attribution | 0.85–1.00 |
| T2 | Reputable publisher with named program/byline and direct quotation or recording | 0.70–0.89 |
| T3 | Reputable publisher mention without direct participation evidence, discovery service, or independently maintained structured data | 0.45–0.74 |
| T4 | Unverified handle, ambiguous name match, repost, or inaccessible item | below 0.60; cannot independently publish an appearance |

### Connector readiness

- `ready`: URL, access path and rights class are known and a live request succeeded on 2026-08-24.
- `review`: potentially useful, but an account, feed, robots rule, rights term, channel ID or extraction contract still requires review.
- `credential`: official API is suitable but credentials, consent, app review or paid credits are absent.
- `blocked`: access control, terms, malformed identifier or eligibility makes automated collection inappropriate.
- `manual`: analysts may add a known public link, but it is not a continuous connector.

## The 30-person glossary registry

This table is an audit of the live local glossary database on 2026-08-24. The roster comes from [`political_glossary.py`](../../../backend/app/services/political_glossary.py), and stored account enrichment comes from [`wikidata_glossary.py`](../../../backend/app/services/wikidata_glossary.py). `S` means the local record says `listed_by_official_source`; `W` means only `claimed_on_wikidata`. Neither mark is a guarantee that the handle remains controlled by the person today. `W` entries are discovery candidates and remain `review` until an official office page or the account itself provides a reciprocal identity signal.

No TikTok account is currently stored for any of the 30 people. That is a coverage gap, not evidence that a person has no TikTok account. Office pages for Magalong, Torre and Dizon are institutional sources, not personal accounts.

| Person | Current glossary role | Accounts currently stored | Required account gaps |
|---|---|---|---|
| Ferdinand Marcos Jr. | President of the Philippines | [X](https://x.com/bongbongmarcos) (W)<br>[Instagram](https://www.instagram.com/bongbongmarcos/) (W)<br>[Facebook](https://www.facebook.com/bongbongmarcos) (W)<br>[YouTube](https://www.youtube.com/channel/UCqgTKnYIeu4DNXGN5fBCY9Q) (W) | Website, TikTok |
| Sara Duterte | Vice President of the Philippines | [X](https://x.com/indaysara) (W)<br>[Instagram](https://www.instagram.com/indaysaraduterte/) (W)<br>[Facebook](https://www.facebook.com/MayorIndaySaraDuterteOfficial) (W)<br>[YouTube](https://www.youtube.com/channel/UCHLaFflr6CfArNMkjqFUzVA) (W) | Website, TikTok |
| Alan Peter Cayetano | Senator of the Philippines | [X](https://x.com/alanpcayetano) (W)<br>[Website](http://alanpetercayetano.com) (W) | Facebook, Instagram, YouTube, TikTok |
| Camille Villar | Senator of the Philippines | [Website](https://www.camillevillar.com) (S)<br>[Facebook](https://www.facebook.com/CamilleAVillar) (S)<br>[Instagram](https://www.instagram.com/camillevillar__) (S)<br>[X](https://x.com/_camillevillar) (S)<br>[YouTube](https://www.youtube.com/@CamilleVillarOfficial) (S) | TikTok |
| Christopher Go | Senator of the Philippines | [Website](https://kuyabonggo.ph/) (W) | Facebook, Instagram, YouTube, TikTok, X |
| Erwin Tulfo | Senator of the Philippines | [Instagram](https://www.instagram.com/erwintulforeal) (S)<br>[X](https://x.com/erwintulforeal) (S)<br>[YouTube](https://www.youtube.com/@ErwinTulforeal) (S) | Website, Facebook, TikTok |
| Francis Escudero | Senator of the Philippines | [Website](http://chizescudero.com) (W) | Facebook, Instagram, YouTube, TikTok, X |
| Francis Pangilinan | Senator of the Philippines | [X](https://x.com/kikopangilinan) (W) | Website, Facebook, Instagram, YouTube, TikTok |
| Imee Marcos | Senator of the Philippines | [X](https://x.com/SenImeeMarcos) (W) | Website, Facebook, Instagram, YouTube, TikTok |
| Jinggoy Estrada | Senator of the Philippines | [Website](https://jinggoyestrada.ph) (S)<br>[Instagram](https://www.instagram.com/jinggoyofficial) (S)<br>[X](https://x.com/EstradaJinggoy) (S) | Facebook, YouTube, TikTok |
| Joel Villanueva | Senator of the Philippines | [Website](https://joelvillanueva.ph) (S)<br>[Instagram](https://www.instagram.com/joelvillanueva) (S)<br>[X](https://x.com/senatorjoelv) (S) | Facebook, YouTube, TikTok |
| Joseph Victor Ejercito | Senator of the Philippines | [X](https://x.com/jvejercito) (W) | Website, Facebook, Instagram, YouTube, TikTok |
| Juan Miguel Zubiri | Senator of the Philippines | [Facebook](https://www.facebook.com/migzzubiri) (W) | Website, Instagram, YouTube, TikTok, X |
| Loren Legarda | Senator of the Philippines | [LinkedIn](https://www.linkedin.com/in/senatorlorenlegarda) (W)<br>[Website](https://lorenlegarda.com.ph/) (W) | Facebook, Instagram, YouTube, TikTok, X |
| Manuel Lapid | Senator of the Philippines | [Instagram](https://www.instagram.com/senatorlitolapid) (S)<br>[X](https://x.com/PinunoSaSenado) (S) | Website, Facebook, YouTube, TikTok |
| Mark Villar | Senator of the Philippines | [Website](https://www.markvillar.com.ph) (S)<br>[YouTube](https://www.youtube.com/@markvillar9123) (S) | Facebook, Instagram, TikTok, X |
| Panfilo Lacson | Senator of the Philippines | [X](https://x.com/iampinglacson) (W)<br>[Instagram](https://www.instagram.com/iampinglacson/) (W)<br>[Facebook](https://www.facebook.com/PingLacsonOfficial) (W)<br>[Website](https://www.pinglacson.net/) (W) | YouTube, TikTok |
| Paolo Benigno Aquino IV | Senator of the Philippines | [X](https://x.com/bamaquino) (W)<br>[Instagram](https://www.instagram.com/bamaquino/) (W)<br>[Facebook](https://www.facebook.com/BenignoBamAquino) (W)<br>[Website](http://www.bamaquino.com/) (W) | YouTube, TikTok |
| Pia Cayetano | Senator of the Philippines | [Website](https://piacayetano.ph) (S)<br>[Facebook](https://www.facebook.com/PiaCayetanoOfficial) (S)<br>[Instagram](https://www.instagram.com/piacayetano) (S)<br>[X](https://x.com/piacayetano) (S) | YouTube, TikTok |
| Raffy Tulfo | Senator of the Philippines | [Facebook](https://www.facebook.com/raffytulfoinaction) (W)<br>[YouTube](https://www.youtube.com/channel/UCxhygwqQ1ZMoBGQM2yEcNug) (W)<br>[YouTube](https://www.youtube.com/channel/raffytulfoinaction) (W) | Website, Instagram, TikTok, X |
| Risa Hontiveros | Senator of the Philippines | [X](https://x.com/risahontiveros) (W)<br>[Instagram](https://www.instagram.com/hontiverosrisa/) (W) | Website, Facebook, YouTube, TikTok |
| Robinhood Padilla | Senator of the Philippines | [Website](https://robinpadilla.ph) (S)<br>[Facebook](https://www.facebook.com/ROBINPADILLA.OFFICIAL) (S)<br>[Instagram](https://www.instagram.com/robinhoodpadilla) (S) | YouTube, TikTok, X |
| Rodante Marcoleta | Senator of the Philippines | [Facebook](https://www.facebook.com/Cong.RodanteMarcoleta) (W) | Website, Instagram, YouTube, TikTok, X |
| Ronald Dela Rosa | Senator of the Philippines | [Facebook](https://www.facebook.com/OFFICIALPAGEofRonaldBatoDelaRosa) (S)<br>[Instagram](https://www.instagram.com/ronaldbatodelarosa) (S) | Website, YouTube, TikTok, X |
| Sherwin Gatchalian | Senator of the Philippines | [Website](http://wingatchalian.com) (W) | Facebook, Instagram, YouTube, TikTok, X |
| Vicente Sotto III | Senator of the Philippines | [Facebook](https://www.facebook.com/TeamTitoSotto) (S) | Website, Instagram, YouTube, TikTok, X |
| Benjie Magalong | Mayor of Baguio City | [Baguio City website](https://main.baguio.gov.ph) (S) | Personal Website, Facebook, Instagram, YouTube, TikTok, X |
| Leni Robredo | Mayor of Naga City | [X](https://x.com/lenirobredo) (W)<br>[Facebook](https://www.facebook.com/VPLeniRobredoPH) (W)<br>[YouTube](https://www.youtube.com/channel/UCvlZWzCZfRb1PZcpU21Sp5Q) (W)<br>[Website](https://lenirobredo.com/) (W) | Instagram, TikTok |
| Nic Torre | General Manager of the Metropolitan Manila Development Authority | [PNA profile/article](https://www.pna.gov.ph/articles/1265567) (S)<br>[MMDA X](https://x.com/MMDA) (S) | Personal Website, Facebook, Instagram, YouTube, TikTok |
| Vince Dizon | Secretary of Public Works and Highways | [DPWH website](https://www.dpwh.gov.ph) (S) | Personal Website, Facebook, Instagram, YouTube, TikTok, X |

Two corrections are mandatory before these records drive collection:

- `https://www.youtube.com/channel/raffytulfoinaction` is not a valid channel-ID URL. Keep the valid `UCxhygwqQ1ZMoBGQM2yEcNug` record and quarantine the malformed duplicate.
- YouTube handle URLs for Camille Villar, Erwin Tulfo and Mark Villar must be resolved to immutable channel IDs through the official YouTube Data API or a reviewed channel page before Atom collection. The current collector correctly accepts only `UC…` channel IDs in [`official_youtube.py`](../../../backend/app/intelligence/official_youtube.py).

### Account verification work queue

For each person, Superadmin must record one of these evidence paths before an account becomes `active`:

1. the official Senate roster links the account (the [20th Congress roster](https://legacy.senate.gov.ph/senators/sen20th.asp) publishes many senators' websites and social handles);
2. an official agency/LGU bio links the account;
3. the person's official website links the account and the account reciprocally identifies the person/office; or
4. two independent official sources agree, followed by analyst approval.

A verification job should refresh this registry weekly and whenever an office or account redirects. A missing platform remains a visible coverage gap. It must never become an inferred URL.

## Exact initial source allowlist

### A. Active publisher and video sources

These are the only zero-credential media feeds recommended for immediate activation. Direct HTTP retrieval on 2026-08-24 returned valid RSS/XML for every row. Feed availability does not grant article-body republication; store publisher-supplied feed metadata, a short attributed excerpt where permitted, a content hash and the canonical link.

| Source URL | Access method | Source class | Refresh | Rights/access note | Tier | Readiness |
|---|---|---|---:|---|---:|---|
| [GMA News](https://data.gmanetwork.com/gno/rss/news/feed.xml) | Publisher RSS; conditional GET | Reputable national publisher | 10 min | Headline/feed description/link only; [GMA User Policy](https://www.gmanetwork.com/news/user-policy/) reserves copyright and points regular reuse to partnership | T2 | ready |
| [GMA News Video](https://data.gmanetwork.com/gno/rss/video/feed.xml) | Publisher RSS; conditional GET | Reputable national broadcast publisher | 10 min | Metadata/link; do not download or mirror video | T2 | ready |
| [Philstar Headlines](https://www.philstar.com/rss/headlines) | Publisher RSS; conditional GET | National newspaper/digital publisher | 10 min | Headline/feed description/link only | T2 | ready |
| [Philstar Nation](https://www.philstar.com/rss/nation) | Publisher RSS; conditional GET | National newspaper/digital publisher | 10 min | Headline/feed description/link only | T2 | ready |
| [INQUIRER.net NewsInfo](https://newsinfo.inquirer.net/feed) | Publisher RSS; conditional GET | National newspaper/digital publisher | 10 min | Headline/feed description/link only; preserve editorial genre | T2 | ready |
| [Rappler](https://www.rappler.com/feed/) | Publisher RSS; conditional GET | Digital newsroom | 10 min | Headline/feed description/link only; keep opinion and straight news separate | T2 | ready |
| [Manila Times News](https://www.manilatimes.net/news/feed) | Publisher RSS; conditional GET | National newspaper/digital publisher | 10 min | Headline/feed description/link only | T2 | ready |
| [BusinessWorld](https://bworldonline.com/feed/) | Publisher RSS; conditional GET | National business newspaper/digital publisher | 15 min | Headline/feed description/link only | T2 | ready; add to code allowlist |
| `https://www.youtube.com/feeds/videos.xml?channel_id=UCqgTKnYIeu4DNXGN5fBCY9Q` | Official YouTube Atom/WebSub | Stored Ferdinand Marcos Jr. channel | WebSub plus 15-min reconciliation | Metadata/link only; identity still requires Superadmin review because current provenance is Wikidata | T1 after review | review |
| `https://www.youtube.com/feeds/videos.xml?channel_id=UCHLaFflr6CfArNMkjqFUzVA` | Official YouTube Atom/WebSub | Stored Sara Duterte channel | WebSub plus 15-min reconciliation | Metadata/link only; identity still requires Superadmin review because current provenance is Wikidata | T1 after review | review |
| `https://www.youtube.com/feeds/videos.xml?channel_id=UCxhygwqQ1ZMoBGQM2yEcNug` | Official YouTube Atom/WebSub | Stored Raffy Tulfo channel | WebSub plus 15-min reconciliation | Metadata/link only; identity still requires Superadmin review because current provenance is Wikidata | T1 after review | review |
| `https://www.youtube.com/feeds/videos.xml?channel_id=UCvlZWzCZfRb1PZcpU21Sp5Q` | Official YouTube Atom/WebSub | Stored Leni Robredo channel | WebSub plus 15-min reconciliation | Metadata/link only; identity still requires Superadmin review because current provenance is Wikidata | T1 after review | review |

Google documents the channel topic URL and says WebSub notifications fire for uploads and title/description changes in its [YouTube push-notification guide](https://developers.google.com/youtube/v3/guides/push_notifications). Reconcile notifications with the official Data API; do not scrape YouTube pages. The [YouTube Developer Policies](https://developers.google.com/youtube/terms/developer-policies) impose attribution, storage/refresh and scraping restrictions, while [`captions.download`](https://developers.google.com/youtube/v3/docs/captions/download) requires authorization by a user who can edit the video. Therefore broadcaster/competitor transcripts are unavailable unless independently published or licensed.

### B. Official proceedings, office and LGU sources

Use Scrapling's normal HTTP fetcher only for the rows marked `ready`. The Senate, House and PCO `robots.txt` files returned `Allow: /` with `Content-Signal: search=yes, ai-train=no, use=reference` on the retrieval date, but ordinary HTTP requests to their content pages returned Cloudflare 403 responses from this environment. Robots permission does not cancel that access control. Store links and bounded evidence excerpts; do not use collected material to train a model. Recheck `robots.txt` and source terms before every activation and at least daily thereafter.

| Source URL | Access method | Source class | Refresh | Rights/access note | Tier | Readiness |
|---|---|---|---:|---|---:|---|
| [Senate news releases](https://senate.gov.ph/media/news-release) | Official feed/API or authorized access required; do not stealth-fetch | Official legislature | 10 min in session when enabled | `robots.txt` permits reference/search, but the content page returned Cloudflare 403; government statement is not independent corroboration | T1 | blocked for Scrapling; mandatory registry source |
| [Senate 20th Congress roster](https://legacy.senate.gov.ph/senators/sen20th.asp) | Manual verification until ordinary access succeeds | Official legislature/identity | Weekly manual | Account and office verification only; preserve retrieval date; current environment returned 403 | T1 | blocked/manual |
| [Senate home/live schedule](https://senate.gov.ph/) | Reviewed official YouTube channel/feed preferred | Official legislature/proceeding | 10 min in session when enabled | Content page returned Cloudflare 403. Schedule is not proof a named senator spoke; verify participant in agenda/recording | T1 | blocked for Scrapling; review YouTube |
| [House video streamings](https://www.congress.gov.ph/index.php/media/video-streamings) | Reviewed official YouTube channel/feed preferred | Official legislature/proceeding | 10 min in session when enabled | Page returned Cloudflare 403 from this environment. A linked Facebook item remains metadata/link unless official API access exists | T1 | blocked for Scrapling; review YouTube |
| [PCO news releases](https://pco.gov.ph/) | Reviewed official RSS/API/YouTube path required; do not stealth-fetch | Official executive communications | 15 min when enabled | `robots.txt` permits reference/search, but the content page returned Cloudflare 403; official account of presidency, not independent corroboration | T1 | blocked for Scrapling; review YouTube |
| [Naga City News](https://www2.naga.gov.ph/naga-city-news/) | Scrapling GET; same-origin article links | Official LGU newsroom | 30 min | Empty `robots.txt` response on retrieval date is not a copyright license; link + short evidence excerpt; monitor terms changes | T1 | ready |
| [Baguio City news](https://main.baguio.gov.ph/media/news) | Scrapling GET; same-origin article links | Official LGU newsroom | 30 min | Empty `robots.txt` response on retrieval date is not a copyright license; link + short evidence excerpt | T1 | ready |
| [DPWH](https://www.dpwh.gov.ph) | None until access control and a documented feed/API are available | Official agency | — | Current environment received an Incapsula access-control page, including for `robots.txt`; do not bypass it with stealth tooling | T1 if obtained | blocked |
| [MMDA](https://mmda.gov.ph/) | None until a documented feed/API or authorized X access is available | Official agency | — | Current environment received a Cloudflare challenge; do not bypass it with stealth tooling | T1 if obtained | blocked |
| [Philippine News Agency](https://www.pna.gov.ph/) | Manual link discovery or licensed feed | Government newsroom | 30 min manual | Current environment received access control; [PNA Terms](https://www.pna.gov.ph/terms) restrict reuse. Keep URL/title/discovery metadata unless licensed | T2 | blocked for Scrapling; manual |
| Office of the Vice President official web source | None | Official executive office | — | No current official website/feed URL is stored in the glossary. Verify it from an authoritative government directory before activation | T1 if verified | gap |

House/Senate proceedings identify that an event occurred; participant identification still needs a roster/agenda/name cue or analyst review. The [House video page](https://www.congress.gov.ph/index.php/media/video-streamings) explicitly separates plenary, press conferences and special events, which maps cleanly to the activity taxonomy. The [Senate roster](https://legacy.senate.gov.ph/senators/sen20th.asp) is also the preferred first-party account-verification source for the 24 senators.

### C. Mandatory Philippine publisher catalog beyond the active feeds

These publications must remain in the source registry even when their continuous connector is not ready. “Mandatory” means coverage and connector state are visible, not that access controls may be bypassed.

| Source URL | Access method | Source class / geography | Refresh | Rights/access note | Tier | Readiness |
|---|---|---|---:|---|---:|---|
| [ABS-CBN News](https://www.abs-cbn.com/news) / [RSS page](https://www.abs-cbn.com/rss.aspx/news) | Scrapling public-page discovery or reviewed official YouTube channel | National broadcast/digital | 15 min after selector review | The RSS URL returned HTML rather than an RSS document on 2026-08-24; do not label it RSS or mirror article/video | T2 | review |
| [News5](https://news.tv5.com.ph/) | Scrapling public-page discovery; reviewed official YouTube channel preferred | National broadcast/digital | 15 min | Public page exposes program and publication metadata; store link/excerpt only | T2 | review |
| [Manila Bulletin RSS directory](https://mb.com.ph/rss) | Publisher RSS after endpoint is reachable; otherwise public-page discovery | National newspaper/digital | 15 min | Publisher describes RSS as title/summary/link, but `/rss/articles` returned 403 in this environment; no bypass | T2 | blocked for feed; review |
| [SunStar](https://www.sunstar.com.ph/) | Publisher feed if documented; otherwise public-page discovery | Regional/national editions | 30 min | Preserve edition/geography; `/rss` returned 404 on retrieval date | T2 | review |
| [PNA](https://www.pna.gov.ph/) | Licensed feed or manual link | Government newsroom; national/regional | 30 min | Government perspective; access/rights restrictions above | T2 | blocked/manual |
| [PCIJ](https://pcij.org/) | Publisher feed/public page after terms review | Investigative publication | 30 min | Long-form investigative work; link + bounded excerpt, not article-body ingestion | T2 | review |
| [VERA Files](https://verafiles.org/) | Publisher feed/public page after terms review | Investigative/fact-check publication | 30 min | Preserve fact-check genre and claim-review status | T2 | review |
| [Manila Standard](https://manilastandard.net/) | Publisher feed/public page after terms review | National newspaper/digital | 30 min | Link + bounded excerpt only | T2 | review |

The system should additionally maintain outlet-owner and syndication-group metadata so that three sites copying one wire report do not count as three independent sources.

## Platform connector policy

| Platform | Official path | What it supports | Current decision |
|---|---|---|---|
| YouTube | Atom/WebSub plus YouTube Data API | New uploads, title/description, channel attribution and public metadata | Activate reviewed immutable channel IDs. Never use Scrapling on YouTube pages or download third-party media/transcripts without authorization/license. |
| X | [X API user timelines](https://docs.x.com/x-api/posts/timelines/introduction) with app-only bearer token | Authored public posts and mentions; public metrics | Credential-gated. X documents pay-per-use pricing and prepaid credits in its [API introduction](https://docs.x.com/x-api/introduction). Use a hard spend cap; no cookie/GraphQL scraping. |
| Facebook | Meta Graph API Page Public Content Access | Public Page posts/comments and Page search where approved | Credential-gated. Meta states [Page Public Content Access](https://developers.facebook.com/docs/features-reference/page-public-content-access) requires App Review and business verification for Pages the app does not manage. Do not scrape logged-in or public pages with Scrapling. |
| Instagram | Instagram Graph API/public-content features | Authorized professional accounts; approved hashtag/public-content use cases | Credential-gated and incomplete for person-wide competitor monitoring. Meta's [Instagram Public Content Access](https://developers.facebook.com/docs/features-reference/instagram-public-content-access) requires App Review and business verification and is centered on approved hashtag use cases. |
| TikTok | Display API for authorizing user; oEmbed for a known URL | An authorizing user's recent public videos or metadata for an already-known URL | Not a competitor-wide connector. TikTok requires app approval, Login Kit and `user.info.basic`/`video.list` in its [Display API guide](https://developers.tiktok.com/docs/en/display-api-get-started). Research access is approval- and eligibility-gated and excludes ordinary commercial use, per [Research Tools eligibility](https://developers.tiktok.com/products/research-api/). Do not scrape TikTok pages. |
| Websites | Publisher RSS first; Scrapling normal HTTP fetcher second | Public article/event metadata and explicitly permitted excerpts | Allowed only for reviewed domains/paths with current robots/terms record, honest user agent, conservative rate and no access-control bypass. |

## Scrapling implementation boundary

Scrapling is already a pinned backend dependency (`scrapling>=0.4.12,<0.5`) in [`backend/pyproject.toml`](../../../backend/pyproject.toml). Its official repository describes normal HTTP fetchers, browser-based dynamic fetchers and stealth/anti-bot features in the [Scrapling README](https://github.com/D4Vinci/Scrapling/blob/main/README.md). The existence of an anti-bot feature is not permission to defeat an access control.

The monitor must enforce this policy in a single connector boundary:

1. `Fetcher`/`AsyncFetcher` HTTP GET only for allowlisted public domains and paths.
2. No `StealthyFetcher`, proxy rotation, CAPTCHA solving, fingerprint impersonation, logged-in session reuse or cookie import.
3. The connector checks `robots.txt`, source-specific terms and a registry kill switch before collection. RFC 9309 defines the [Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309); robots permission is an access signal, not a copyright license.
4. One honest user agent with product/contact identity; same-origin redirects only; DNS/IP and response-size protections; no private-network targets.
5. Default 15-minute publisher polling and 30-minute government/LGU polling, with `ETag`/`Last-Modified`, jitter, exponential backoff and a per-domain concurrency of one.
6. A 401, 403, 429, challenge page, changed robots rule or terms conflict moves the source to `blocked`; it does not trigger a stealth retry.
7. Store canonical URL, permitted metadata/excerpt, response hash, retrieval time and extraction evidence. Do not retain arbitrary scripts or full copyrighted article bodies.
8. Selectors are versioned and tested against saved, rights-permitted fixtures. Parser failure creates a visible connector error, not an empty “Quiet” status for affected people.

## Ollama extraction boundary

Ollama should extract structure after deterministic source capture, not decide what the evidence was. The local endpoint is appropriate for the POC because Ollama supports a JSON schema in the `format` field of `/api/chat`; its [Structured Outputs guide](https://docs.ollama.com/capabilities/structured-outputs) recommends Pydantic/Zod validation and temperature `0`, and the [chat API](https://docs.ollama.com/api/chat) documents `format` as JSON or JSON schema.

Required extraction contract:

- input: allowed source metadata/excerpt, source tier, publication time, candidate names/aliases/office, and no unrelated personal data;
- output schema: candidate entity IDs, evidence layer, appearance kind, occurred time, venue/program, topic IDs, summary, identity evidence spans, classification evidence spans, and per-field confidence;
- validation: Pydantic schema validation, allowed-enum validation, timestamps bounded by source publication/known event context, URL equality to the captured source, and alias/office checks;
- grounding: each non-null extracted claim must point to a character span in the permitted input or a linked official metadata field;
- failure: invalid JSON/schema, absent Ollama, timeout, unsupported language or low confidence becomes `needs_review`; no speculative record is published;
- versioning: retain model name/digest, prompt/schema version and extraction time. A later API provider implements the same interface and cannot rewrite historical records silently.

Identity resolution should start with exact official-account attribution, canonical names, reviewed aliases, current office, program/venue, and location context. Automated facial recognition is out of scope for this POC: it introduces biometric/privacy and false-match risk and is unnecessary for the initial source set. Visual presence may be confirmed manually from a linked frame or publisher caption and recorded as `analyst_review`; no face embedding or face database should be created.

## Identity, deduplication and confidence rules

### Person resolution

Publish an attribution only when one of these conditions is met:

- T1 official account/source names the person and the stored source-to-person relationship is active;
- a T2 publisher title/description/byline explicitly names a canonical name or reviewed alias and the office/program context is consistent; or
- two independent T2 sources agree and an analyst reviews an otherwise ambiguous alias.

Common surnames, office-only references and location alone cannot create an identity match. A source discussing “Tulfo” without a first name or unique program context is ambiguous because the glossary contains Raffy and Erwin Tulfo.

### Event clustering

Create one appearance event with many evidence edges. The first pass clusters by person, normalized occurred-time bucket, venue/program, activity kind and normalized title/quoted claim. Then use Ollama only to suggest merges. A merge is automatic only when deterministic fields agree and confidence is high; otherwise an analyst accepts it.

Each event retains:

- one primary direct source when available;
- all corroborating publisher/source links;
- publisher-owner grouping and source diversity;
- the earliest publication/observation and all update timestamps; and
- separate direct appearance, statement, indirect coverage and reaction counts.

### Confidence

A T1 direct recording or official proceeding with an explicit participant starts at high confidence. A T2 article with a direct quote or named interview can reach high confidence. A name-only article remains indirect coverage. Source count increases corroboration confidence but never changes an indirect mention into an appearance. An Ollama probability is not source confidence; it is classification confidence and must be displayed separately in the evidence inspector.

## Monitoring state and period comparison

The user-facing periods are rolling 6 hours, 24 hours and 7 days. Compare each selected period with the immediately preceding equal-length period using only verified `direct_appearance` and `public_statement` events for the appearance count.

- `Emerging`: at least two verified current-period events and either zero in the prior period or at least double the prior count.
- `Active`: at least one verified current-period event that does not meet `Emerging`.
- `Quiet`: zero verified current-period events while the required source-family health gate passes.
- `Unknown coverage`: zero events but one or more mandatory source families are stale, blocked or below the coverage gate. Never label this state `Quiet`.

The competitors table should show the selected period, state badge, verified appearance count, change against the preceding equal period, main topic, last verified appearance, and source confidence/source count. Indirect coverage and reaction may explain attention change beside the count but must not inflate it.

## Activation order

### Stage 0 — registry gate

1. Load the 30 glossary people and aliases.
2. Quarantine malformed/stale account URLs.
3. Require Superadmin approval for every account-to-person edge.
4. Resolve all approved YouTube handles to immutable channel IDs.
5. Show a coverage matrix for Website, Facebook, Instagram, YouTube, TikTok, X and institutional office sources. Missing stays missing.

### Stage 1 — zero-credential core

1. Activate the seven RSS feeds already in code plus BusinessWorld.
2. Activate reviewed YouTube Atom feeds.
3. Activate Naga and Baguio public-page connectors with Scrapling's normal HTTP fetcher.
4. Keep Senate, House and PCO mandatory and visible as blocked until a documented feed/API, reviewed official YouTube channel, or source-authorized access path is available; never escalate a 403 to stealth mode.
5. Backfill 14 days where feeds/pages expose it; retain exact capture/provenance.
6. Keep ABS-CBN, News5, Manila Bulletin, SunStar, PNA, PCIJ and VERA Files visible as `review`/`blocked` until each connector contract passes.

### Stage 2 — structured extraction and review

1. Deterministic alias/official-source match.
2. Ollama JSON-schema extraction and Pydantic validation.
3. Deterministic event clustering followed by analyst review for ambiguous merges.
4. Publish direct appearances/statements separately from indirect coverage/reaction.
5. Compute 6h/24h/7d state only after the source-health gate passes.

### Stage 3 — credentialed platform sources

1. Add X API user timelines with a hard prepaid budget and usage alarms.
2. Add owned Facebook/Instagram only after authorization and Meta review.
3. Add owned TikTok only after the person authorizes `video.list`; a known public video URL may use official oEmbed.
4. Do not represent unlicensed competitor social coverage as complete.

## Acceptance and stop conditions

The source registry is ready for a 30-person monitor when:

- all 30 people have at least one active official institutional or account source, or are explicitly marked as a gap;
- every active source has the URL, method, class, cadence, rights note, tier, robots/terms check and owner recorded;
- all official YouTube sources use immutable channel IDs;
- the eight publisher feeds, reviewed YouTube feeds, and the two currently reachable LGU connectors complete two consecutive healthy runs; blocked institutional sources remain visibly excluded from the health denominator until an approved connector exists;
- no connector uses stealth, logged-in browser state, cookies, CAPTCHA bypass or unapproved proxying;
- every published appearance has a direct evidence link and a separate identity/classification confidence basis;
- one event reported by five publishers remains one appearance with five evidence edges;
- “Quiet” is impossible while mandatory source health is insufficient; and
- Ollama unavailability or schema failure is visible and leaves evidence queued, never fabricated.

## Remaining risks and explicit gaps

- The current account registry is sparse: zero stored TikTok accounts, only seven stored YouTube records (one malformed), and many people with a single website or social handle.
- `claimed_on_wikidata` is not enough for automated activation. It is a discovery provenance tier, not proof of current control.
- The Senate roster contains richer account data than the database currently stores for several senators; reconciliation should happen before declaring source coverage complete.
- Free official access cannot provide comprehensive competitor Facebook, Instagram or TikTok timelines. X is official but paid.
- Publisher and official-site availability can change without notice. Source health and last successful collection must be visible in the Intelligence Center.
- Official sources prove what an office published; they are not independent verification. Publisher diversity and source ownership must remain visible.
- Multilingual Tagalog, English, Taglish and regional-language classification requires a reviewed validation set. Low-confidence topic/framing output stays `unclear`.
- This source policy does not grant a media-monitoring license. Philippine legal/privacy and publisher-rights review remains required before production campaign deployment.

## Source notes

Primary external sources used for this registry were retrieved on 2026-08-24: the [Senate 20th Congress roster](https://legacy.senate.gov.ph/senators/sen20th.asp), [House video streamings](https://www.congress.gov.ph/index.php/media/video-streamings), [PCO news releases](https://pco.gov.ph/), [Naga City News](https://www2.naga.gov.ph/naga-city-news/), [Baguio City news](https://main.baguio.gov.ph/media/news), [YouTube push notifications](https://developers.google.com/youtube/v3/guides/push_notifications), [YouTube Developer Policies](https://developers.google.com/youtube/terms/developer-policies), [X API documentation](https://docs.x.com/x-api/introduction), [Meta Page Public Content Access](https://developers.facebook.com/docs/features-reference/page-public-content-access), [Meta Instagram Public Content Access](https://developers.facebook.com/docs/features-reference/instagram-public-content-access), [TikTok Display API](https://developers.tiktok.com/docs/en/display-api-get-started), [TikTok Research Tools](https://developers.tiktok.com/products/research-api/), [Scrapling](https://github.com/D4Vinci/Scrapling), [Ollama Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs), and [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309).
