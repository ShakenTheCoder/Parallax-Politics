"""Static credibility scores for PH political coverage.

Scores are a coarse 0..1 prior; the SGA / Strategist will combine them with
per-result signals (recency, primary-source flag, etc.). Tune over time.
"""

from __future__ import annotations

from urllib.parse import urlparse

# Tier 1 — official / primary
_PRIMARY = {
    "gov.ph": 0.95,
    "senate.gov.ph": 0.97,
    "congress.gov.ph": 0.97,
    "comelec.gov.ph": 0.97,
    "psa.gov.ph": 0.97,
    "officialgazette.gov.ph": 0.95,
    "op.gov.ph": 0.95,
    "ovp.gov.ph": 0.95,
    "doh.gov.ph": 0.90,
}

# Tier 2 — established broadcast & broadsheet
_ESTABLISHED = {
    "gmanetwork.com": 0.85,
    "abs-cbn.com": 0.85,
    "news.abs-cbn.com": 0.85,
    "tv5.com.ph": 0.80,
    "inquirer.net": 0.85,
    "rappler.com": 0.85,
    "philstar.com": 0.82,
    "manilatimes.net": 0.78,
    "bworldonline.com": 0.82,  # BusinessWorld
    "interaksyon.philstar.com": 0.78,
    "cnnphilippines.com": 0.82,
    "manilabulletin.com.ph": 0.78,
    "mb.com.ph": 0.78,
    "pna.gov.ph": 0.90,  # Philippine News Agency
    "sunstar.com.ph": 0.72,
}

# Tier 3 — international wire / reference
_INTERNATIONAL = {
    "reuters.com": 0.90,
    "apnews.com": 0.90,
    "bbc.com": 0.85,
    "bbc.co.uk": 0.85,
    "nytimes.com": 0.85,
    "ft.com": 0.85,
    "wsj.com": 0.83,
    "bloomberg.com": 0.83,
    "aljazeera.com": 0.80,
    "scmp.com": 0.78,
    "voanews.com": 0.75,
    "wikipedia.org": 0.55,  # cross-reference only
}

_ALL: dict[str, float] = {**_PRIMARY, **_ESTABLISHED, **_INTERNATIONAL}


def domain_of(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def credibility_for(url: str) -> float:
    d = domain_of(url)
    if d in _ALL:
        return _ALL[d]
    # match parent domain (e.g. blogs.inquirer.net -> inquirer.net)
    parts = d.split(".")
    for i in range(1, len(parts) - 1):
        parent = ".".join(parts[i:])
        if parent in _ALL:
            return _ALL[parent] * 0.92  # subdomain discount
    # Unknown: low-ish default; SGA can still surface, Strategist will weight.
    return 0.35


def is_primary(url: str) -> bool:
    return domain_of(url) in _PRIMARY or any(domain_of(url).endswith("." + d) for d in _PRIMARY)
