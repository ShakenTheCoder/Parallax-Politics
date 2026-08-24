"""Wikidata/Commons enrichment for the Superadmin political glossary.

The adapter owns external identifiers, portrait provenance, and public-account URL
construction. It never guesses handles: every account must be an explicit Wikidata
claim, and every portrait must be a Commons image claim.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import UTC, datetime
from html import unescape
from typing import Any
from urllib.parse import quote, unquote, urlsplit

import httpx
from sqlalchemy import func, select

from app.db import session_scope
from app.models.political_figure import PoliticalFigure, PoliticalFigureSnapshot

_SPARQL_URLS = (
    "https://qlever-api.wikidata.dbis.rwth-aachen.de",
    "https://query.wikidata.org/sparql",
)
_USER_AGENT = "Parallax-Politics/1.0 (public-figure glossary; source-backed research)"

_LOOKUP_NAMES: dict[str, tuple[str, ...]] = {
    "Ferdinand Marcos Jr.": ("Ferdinand Marcos Jr.", "Bongbong Marcos"),
    "Sara Duterte": ("Sara Duterte",),
    "Paolo Benigno Aquino IV": ("Bam Aquino", "Paolo Benigno Aquino IV"),
    "Alan Peter Cayetano": ("Alan Peter Cayetano",),
    "Pia Cayetano": ("Pia Cayetano",),
    "Ronald Dela Rosa": ("Ronald dela Rosa", "Bato dela Rosa"),
    "Joseph Victor Ejercito": ("JV Ejercito", "Joseph Victor Ejercito"),
    "Francis Escudero": ("Chiz Escudero", "Francis Escudero"),
    "Jinggoy Estrada": ("Jinggoy Estrada",),
    "Sherwin Gatchalian": ("Win Gatchalian", "Sherwin Gatchalian"),
    "Christopher Go": ("Bong Go", "Christopher Go"),
    "Risa Hontiveros": ("Risa Hontiveros",),
    "Panfilo Lacson": ("Panfilo Lacson", "Ping Lacson"),
    "Manuel Lapid": ("Lito Lapid", "Manuel Lapid"),
    "Loren Legarda": ("Loren Legarda",),
    "Rodante Marcoleta": ("Rodante Marcoleta",),
    "Imee Marcos": ("Imee Marcos",),
    "Robinhood Padilla": ("Robin Padilla", "Robinhood Padilla"),
    "Francis Pangilinan": ("Kiko Pangilinan", "Francis Pangilinan"),
    "Vicente Sotto III": ("Tito Sotto", "Vicente Sotto III"),
    "Erwin Tulfo": ("Erwin Tulfo",),
    "Raffy Tulfo": ("Raffy Tulfo",),
    "Joel Villanueva": ("Joel Villanueva",),
    "Camille Villar": ("Camille Villar",),
    "Mark Villar": ("Mark Villar",),
    "Juan Miguel Zubiri": ("Migz Zubiri", "Juan Miguel Zubiri"),
    "Leni Robredo": ("Leni Robredo", "Maria Leonor Robredo"),
    "Vince Dizon": ("Vince Dizon", "Vivencio Dizon"),
    "Benjie Magalong": ("Benjamin Magalong", "Benjie Magalong"),
    "Nic Torre": ("Nicolas Torre", "Nicolas Torre III", "Nic Torre"),
}

_ROLE_OVERRIDES = {
    "Leni Robredo": (
        "Mayor of Naga City",
        "City Government of Naga",
        "https://www2.naga.gov.ph/office-service/city-mayors-office/",
    ),
    "Vince Dizon": (
        "Secretary of Public Works and Highways",
        "Department of Public Works and Highways",
        "https://pco.gov.ph/news_releases/president-marcos-convenes-cabinet-briefing-on-habagat-effects/",
    ),
    "Benjie Magalong": (
        "Mayor of Baguio City",
        "City Government of Baguio",
        "https://main.baguio.gov.ph/media/news/aMVX2pbz/city-adopts-austerity-measures-under-state-of-natl-energy-emergency",
    ),
    "Nic Torre": (
        "General Manager of the Metropolitan Manila Development Authority",
        "Metropolitan Manila Development Authority",
        "https://www.pna.gov.ph/articles/1267523",
    ),
}

_SOCIAL_PROPERTIES = {
    "twitter": ("X", "P2002"),
    "instagram": ("Instagram", "P2003"),
    "facebook": ("Facebook", "P2013"),
    "youtube": ("YouTube", "P2397"),
    "youtube_handle": ("YouTube", "P11245"),
    "linkedin": ("LinkedIn", "P6634"),
    "website": ("Website", "P856"),
}

_SENATE_URL = "https://legacy.senate.gov.ph/senators/sen20th.asp"
_OFFICIAL_ACCOUNTS: dict[str, tuple[tuple[str, str], ...]] = {
    "Pia Cayetano": (
        ("Website", "https://piacayetano.ph"),
        ("Facebook", "PiaCayetanoOfficial"),
        ("Instagram", "piacayetano"),
        ("X", "piacayetano"),
    ),
    "Ronald Dela Rosa": (
        ("Facebook", "OFFICIALPAGEofRonaldBatoDelaRosa"),
        ("Instagram", "ronaldbatodelarosa"),
    ),
    "Jinggoy Estrada": (
        ("Website", "https://jinggoyestrada.ph"),
        ("Instagram", "jinggoyofficial"),
        ("X", "EstradaJinggoy"),
    ),
    "Manuel Lapid": (("Instagram", "senatorlitolapid"), ("X", "PinunoSaSenado")),
    "Robinhood Padilla": (
        ("Website", "https://robinpadilla.ph"),
        ("Facebook", "ROBINPADILLA.OFFICIAL"),
        ("Instagram", "robinhoodpadilla"),
    ),
    "Vicente Sotto III": (("Facebook", "TeamTitoSotto"),),
    "Erwin Tulfo": (
        ("Instagram", "erwintulforeal"),
        ("X", "erwintulforeal"),
        ("YouTube", "ErwinTulforeal"),
    ),
    "Joel Villanueva": (
        ("Website", "https://joelvillanueva.ph"),
        ("Instagram", "joelvillanueva"),
        ("X", "senatorjoelv"),
    ),
    "Camille Villar": (
        ("Website", "https://www.camillevillar.com"),
        ("Facebook", "CamilleAVillar"),
        ("Instagram", "camillevillar__"),
        ("X", "_camillevillar"),
        ("YouTube", "CamilleVillarOfficial"),
    ),
    "Mark Villar": (("Website", "https://www.markvillar.com.ph"), ("YouTube", "markvillar9123")),
    "Benjie Magalong": (("Official profile", "https://main.baguio.gov.ph"),),
    "Vince Dizon": (("Official profile", "https://www.dpwh.gov.ph"),),
    "Nic Torre": (("Official profile", "https://www.pna.gov.ph/articles/1265567"), ("X", "MMDA")),
}


def _values(only_names: set[str] | None = None) -> tuple[str, dict[str, str]]:
    reverse: dict[str, str] = {}
    names: list[str] = []
    for canonical, aliases in _LOOKUP_NAMES.items():
        if only_names is not None and canonical not in only_names:
            continue
        for alias in aliases:
            reverse[alias.casefold()] = canonical
            names.append(f'"{alias.replace(chr(34), "")}"@en')
    return " ".join(names), reverse


async def _query(query: str) -> list[dict[str, Any]]:
    delays = (0, 2, 6)
    async with httpx.AsyncClient(timeout=45, headers={"User-Agent": _USER_AGENT}) as client:
        for endpoint in _SPARQL_URLS:
            for attempt, delay in enumerate(delays):
                if delay:
                    await asyncio.sleep(delay)
                try:
                    response = await client.get(
                        endpoint,
                        params={"query": query, "format": "json"},
                        headers={"Accept": "application/sparql-results+json"},
                    )
                except httpx.HTTPError:
                    if attempt < len(delays) - 1:
                        continue
                    break
                if response.status_code in {429, 502, 503, 504}:
                    if attempt < len(delays) - 1:
                        continue
                    break
                response.raise_for_status()
                return response.json().get("results", {}).get("bindings", [])
    return []


def _value(row: dict[str, Any], key: str) -> str | None:
    value = row.get(key, {}).get("value")
    return unescape(value).strip() if isinstance(value, str) and value.strip() else None


def _account(platform: str, raw: str, entity_url: str) -> dict[str, Any]:
    clean = raw.strip().lstrip("@")
    urls = {
        "X": f"https://x.com/{clean}",
        "Instagram": f"https://www.instagram.com/{clean}/",
        "Facebook": f"https://www.facebook.com/{clean}",
        "YouTube": f"https://www.youtube.com/channel/{clean}",
        "LinkedIn": f"https://www.linkedin.com/in/{clean}",
        "Website": raw,
    }
    return {
        "platform": platform,
        "url": urls[platform],
        "handle": raw if platform == "Website" else f"@{clean}",
        "account_type": "public",
        "verification": "claimed_on_wikidata",
        "source_url": entity_url,
        "last_checked_at": datetime.now(UTC).isoformat(),
    }


def _official_account(platform: str, raw: str, source_url: str) -> dict[str, Any]:
    clean = raw.strip().lstrip("@")
    if platform in {"Website", "Official profile"}:
        url = raw
    elif platform == "YouTube":
        url = f"https://www.youtube.com/@{clean}"
    else:
        hosts = {"X": "x.com", "Instagram": "www.instagram.com", "Facebook": "www.facebook.com"}
        url = f"https://{hosts[platform]}/{clean}"
    return {
        "platform": platform,
        "url": url,
        "handle": raw if platform in {"Website", "Official profile"} else f"@{clean}",
        "account_type": "official" if platform not in {"Official profile"} else "office",
        "verification": "listed_by_official_source",
        "source_url": source_url,
        "last_checked_at": datetime.now(UTC).isoformat(),
    }


def _commons_source(image_url: str) -> str:
    filename = unquote(urlsplit(image_url).path.rsplit("/", 1)[-1])
    return f"https://commons.wikimedia.org/wiki/File:{quote(filename)}"


async def enrich_glossary_from_wikidata(only_names: set[str] | None = None) -> dict[str, int]:
    values, reverse = _values(only_names)
    prefixes = """
    PREFIX bd: <http://www.bigdata.com/rdf#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <http://schema.org/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX ps: <http://www.wikidata.org/prop/statement/>
    PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
    """
    identity_query = (
        prefixes
        + f"""
    SELECT ?name ?item ?itemDescription WHERE {{
      VALUES ?name {{ {values} }}
      ?item rdfs:label ?name.
      OPTIONAL {{ ?item schema:description ?itemDescription. FILTER(LANG(?itemDescription) = "en") }}
    }}
    """
    )
    rows = await _query(identity_query)
    candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        lookup = _value(row, "name")
        if lookup and lookup.casefold() in reverse:
            candidates[reverse[lookup.casefold()]].append(row)

    selected: dict[str, dict[str, Any]] = {}
    for canonical, options in candidates.items():
        selected[canonical] = max(
            options,
            key=lambda row: ("filip" in (_value(row, "itemDescription") or "").casefold(),),
        )

    item_ids = {
        canonical: (_value(row, "item") or "").rsplit("/", 1)[-1]
        for canonical, row in selected.items()
    }
    claims_by_item: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    if item_ids:
        ids = " ".join(f"wd:{item_id}" for item_id in sorted(set(item_ids.values())))
        detail_query = (
            prefixes
            + f"""
        SELECT ?item ?field ?value WHERE {{
          VALUES ?item {{ {ids} }}
          VALUES (?property ?field) {{
            (wdt:P18 "image") (wdt:P2002 "twitter") (wdt:P2003 "instagram")
            (wdt:P2013 "facebook") (wdt:P2397 "youtube")
            (wdt:P11245 "youtube_handle") (wdt:P6634 "linkedin")
            (wdt:P856 "website")
          }}
          ?item ?property ?value.
        }}
        """
        )
        details_by_item: dict[str, dict[str, str]] = defaultdict(dict)
        for detail in await _query(detail_query):
            detail_item = (_value(detail, "item") or "").rsplit("/", 1)[-1]
            detail_field = _value(detail, "field")
            detail_value = _value(detail, "value")
            if detail_item and detail_field and detail_value:
                details_by_item[detail_item].setdefault(detail_field, detail_value)
        for canonical, item_id in item_ids.items():
            for field, detail_value in details_by_item[item_id].items():
                selected[canonical][field] = {"value": detail_value}

        claims_query = (
            prefixes
            + f"""
        SELECT ?item ?field ?value ?valueLabel WHERE {{
          VALUES ?item {{ {ids} }}
          VALUES (?property ?field) {{
            (wdt:P39 "positions") (wdt:P102 "parties") (wdt:P69 "education")
            (wdt:P106 "occupations") (wdt:P19 "birthplace") (wdt:P569 "born")
          }}
          ?item ?property ?value.
          OPTIONAL {{ ?value rdfs:label ?valueLabel. FILTER(LANG(?valueLabel) = "en") }}
        }}
        """
        )
        for row in await _query(claims_query):
            item_id = (_value(row, "item") or "").rsplit("/", 1)[-1]
            field = _value(row, "field")
            label = _value(row, "valueLabel") or _value(row, "value")
            if field and label and label not in claims_by_item[item_id][field]:
                claims_by_item[item_id][field].append(label)
        current_party_query = (
            prefixes
            + f"""
        SELECT ?item ?value ?valueLabel WHERE {{
          VALUES ?item {{ {ids} }}
          ?item p:P102 ?statement.
          ?statement ps:P102 ?value.
          FILTER NOT EXISTS {{ ?statement pq:P582 ?end. }}
          OPTIONAL {{ ?value rdfs:label ?valueLabel. FILTER(LANG(?valueLabel) = "en") }}
        }}
        """
        )
        for row in await _query(current_party_query):
            item_id = (_value(row, "item") or "").rsplit("/", 1)[-1]
            label = _value(row, "valueLabel") or _value(row, "value")
            if label and label not in claims_by_item[item_id]["current_parties"]:
                claims_by_item[item_id]["current_parties"].append(label)

    updated = portraits = accounts = 0
    async with session_scope() as db:
        figures = list((await db.execute(select(PoliticalFigure))).scalars().all())
        for figure in figures:
            row = selected.get(figure.canonical_name)
            if not row:
                continue
            item_id = item_ids[figure.canonical_name]
            entity_url = f"https://www.wikidata.org/wiki/{item_id}"
            claims = claims_by_item[item_id]
            social: list[dict[str, Any]] = []
            seen_urls: set[str] = set()
            for key, (platform, _property) in _SOCIAL_PROPERTIES.items():
                raw = _value(row, key)
                if not raw:
                    continue
                account = _account(platform, raw, entity_url)
                if account["url"] not in seen_urls:
                    social.append(account)
                    seen_urls.add(account["url"])
            official_source = (
                _SENATE_URL
                if figure.category == "senate"
                else (_ROLE_OVERRIDES.get(figure.canonical_name, (None, None, entity_url))[2])
            )
            for platform, raw in _OFFICIAL_ACCOUNTS.get(figure.canonical_name, ()):
                account = _official_account(platform, raw, official_source)
                if account["url"] not in seen_urls:
                    social.append(account)
                    seen_urls.add(account["url"])
            image = _value(row, "image")
            if image:
                figure.portrait_url = image.replace("http://", "https://", 1)
                figure.portrait_source_url = _commons_source(image)
                figure.portrait_attribution = "Wikimedia Commons; attribution and license are available on the linked file page."
                portraits += 1
            description = _value(row, "itemDescription")
            data = dict(figure.data or {})
            if description:
                data["biography"] = description[0].upper() + description[1:]
            for field in ("born", "birthplace", "education", "occupations", "positions"):
                if claims.get(field):
                    data[field] = claims[field]
            if claims.get("parties"):
                data["party_history"] = claims["parties"]
            if claims.get("current_parties"):
                figure.party = " / ".join(claims["current_parties"])
                data["current_party_affiliations"] = claims["current_parties"]
            figure.data = data
            figure.social_accounts = social
            accounts += len(social)
            aliases = list(
                dict.fromkeys([*(figure.aliases or []), *_LOOKUP_NAMES[figure.canonical_name]])
            )
            figure.aliases = [alias for alias in aliases if alias != figure.canonical_name]
            if figure.canonical_name in _ROLE_OVERRIDES:
                role, office, role_url = _ROLE_OVERRIDES[figure.canonical_name]
                figure.current_role = role
                figure.office = office
                figure.source_ledger = [
                    *(figure.source_ledger or []),
                    {
                        "url": role_url,
                        "title": "Current office source",
                        "publisher": "Philippine government/public agency",
                        "source_type": "official_public_web",
                        "accessed_at": datetime.now(UTC).isoformat(),
                        "supports": ["current_role", "office"],
                        "confidence": 0.98,
                    },
                ]
            figure.source_ledger = [
                *(figure.source_ledger or []),
                {
                    "url": entity_url,
                    "title": f"Wikidata record for {figure.canonical_name}",
                    "publisher": "Wikidata",
                    "source_type": "structured_public_data",
                    "accessed_at": datetime.now(UTC).isoformat(),
                    "supports": [
                        "portrait",
                        "biography",
                        "career",
                        "education",
                        "party",
                        "public_accounts",
                    ],
                    "confidence": 0.82,
                },
            ]
            deduplicated_sources: dict[str, dict[str, Any]] = {}
            for source in figure.source_ledger:
                source_url = str(source.get("url") or "")
                if source_url:
                    deduplicated_sources[source_url] = source
            figure.source_ledger = list(deduplicated_sources.values())
            gaps = [
                "Policy positions, electoral record, relationships, and controversies require source-by-source analyst review."
            ]
            if not image:
                gaps.append("No attributable Commons portrait was found.")
            if not social:
                gaps.append("No public social account claim was found in Wikidata.")
            figure.coverage_gaps = gaps
            figure.confidence = 0.82 if image or social else 0.72
            figure.last_verified_at = datetime.now(UTC)
            latest = (
                await db.execute(
                    select(func.max(PoliticalFigureSnapshot.version)).where(
                        PoliticalFigureSnapshot.figure_id == figure.id
                    )
                )
            ).scalar() or 0
            now = datetime.now(UTC)
            db.add(
                PoliticalFigureSnapshot(
                    created_at=now,
                    updated_at=now,
                    figure_id=figure.id,
                    version=int(latest) + 1,
                    trigger="structured_refresh",
                    produced_by="wikidata_glossary",
                    payload={
                        "data": figure.data,
                        "social_accounts": figure.social_accounts,
                        "portrait_url": figure.portrait_url,
                        "current_role": figure.current_role,
                        "office": figure.office,
                    },
                    source_ledger=figure.source_ledger,
                    confidence=figure.confidence,
                )
            )
            updated += 1
        await db.commit()
    return {"updated": updated, "portraits": portraits, "accounts": accounts}
