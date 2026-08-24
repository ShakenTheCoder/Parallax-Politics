"""Source-backed portrait resolution for confirmed public identities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import httpx

_WIKIMEDIA_HOST = "upload.wikimedia.org"
_NAME_TOKEN = re.compile(r"[a-z]+")


@dataclass(frozen=True)
class WikipediaIdentity:
    title: str
    description: str | None
    extract: str | None
    page_url: str
    portrait_url: str | None


def _name_tokens(value: str) -> set[str]:
    return set(_NAME_TOKEN.findall(value.casefold()))


def _select_matching_page(
    full_name: str, ordered_titles: list[str], pages: dict[str, dict]
) -> dict | None:
    """Select only a page whose title contains the identity's first name.

    Surname-only matching is unsafe for political families (e.g. Sara, Paolo,
    and Rodrigo Duterte), so first-name agreement is a hard invariant.
    """
    target_ordered = _NAME_TOKEN.findall(full_name.casefold())
    if not target_ordered:
        return None
    target = set(target_ordered)
    first_name = target_ordered[0]
    candidates: list[tuple[float, int, dict]] = []
    title_rank = {title.casefold(): rank for rank, title in enumerate(ordered_titles)}
    for page in pages.values():
        title = str(page.get("title") or "")
        title_tokens = _name_tokens(title)
        shared_tokens = target & title_tokens
        # Exact first-name agreement is strongest. Two-token agreement also
        # permits well-known nicknames present in the query (e.g. Ferdinand
        # "Bongbong" Marcos → Bongbong Marcos) without allowing surname-only
        # family collisions such as Paolo Duterte for Sara Duterte.
        if first_name not in title_tokens and len(shared_tokens) < 2:
            continue
        overlap = len(shared_tokens) / max(1, len(title_tokens))
        candidates.append((overlap, -title_rank.get(title.casefold(), 999), page))
    return max(candidates, default=(0.0, 0, None), key=lambda item: (item[0], item[1]))[2]


async def resolve_wikipedia_identity(full_name: str) -> WikipediaIdentity | None:
    """Return exact-name Wikipedia metadata for a public figure, if available.

    The resolver deliberately returns only direct Wikimedia thumbnails and never
    synthesizes an image or guesses a URL. Callers must retain provenance through
    the existing identity-source trail.
    """
    if not full_name.strip():
        return None
    search_url = "https://en.wikipedia.org/w/api.php"
    try:
        async with httpx.AsyncClient(
            timeout=1.5,
            follow_redirects=True,
            headers={
                "User-Agent": "Parallax-Politics/1.0 (source-backed identity lookup)",
                "Accept": "application/json",
            },
        ) as client:
            search = await client.get(
                search_url,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f"{full_name} Philippines politician",
                    "srlimit": 3,
                    "format": "json",
                    "utf8": 1,
                },
            )
            search.raise_for_status()
            titles = [
                item.get("title")
                for item in search.json().get("query", {}).get("search", [])
                if item.get("title")
            ]
            if not titles:
                return None
            pages = await client.get(
                search_url,
                params={
                    "action": "query",
                    "prop": "pageimages|extracts|description",
                    "piprop": "thumbnail",
                    "pithumbsize": 1200,
                    "titles": "|".join(titles),
                    "redirects": 1,
                    "exintro": 1,
                    "explaintext": 1,
                    "exsentences": 2,
                    "format": "json",
                    "utf8": 1,
                },
            )
            pages.raise_for_status()
    except (httpx.HTTPError, ValueError):
        return None

    selected = _select_matching_page(
        full_name,
        [str(title) for title in titles],
        pages.json().get("query", {}).get("pages", {}),
    )
    if selected:
        source = selected.get("thumbnail", {}).get("source")
        portrait_url = None
        if source and source.startswith("https://") and _WIKIMEDIA_HOST in source:
            parsed = urlsplit(source)
            portrait_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        title = str(selected.get("title") or full_name)
        return WikipediaIdentity(
            title=title,
            description=selected.get("description"),
            extract=selected.get("extract"),
            page_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
            portrait_url=portrait_url,
        )
    return None


async def resolve_wikimedia_portrait(full_name: str) -> str | None:
    """Return a high-resolution Wikimedia portrait for a public figure, if available."""
    identity = await resolve_wikipedia_identity(full_name)
    if identity and identity.portrait_url:
        return identity.portrait_url
    # Commons often has a file even when the English Wikipedia article is absent.
    # Keep the match conservative: the file title must contain the first name and
    # surname tokens, so a family member's portrait is not silently substituted.
    tokens = _name_tokens(full_name)
    if len(tokens) < 2:
        return None
    try:
        async with httpx.AsyncClient(timeout=1.5, follow_redirects=True) as client:
            response = await client.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": full_name,
                    "gsrnamespace": 6,
                    "gsrlimit": 5,
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "iiurlwidth": 1200,
                    "format": "json",
                    "utf8": 1,
                },
                headers={"User-Agent": "Parallax-Politics/1.0 (source-backed identity lookup)"},
            )
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {}).values()
            for page in pages:
                title_tokens = _name_tokens(str(page.get("title") or ""))
                if not tokens.issubset(title_tokens):
                    continue
                info = (page.get("imageinfo") or [{}])[0]
                source = info.get("thumburl") or info.get("url")
                if (
                    isinstance(source, str)
                    and source.startswith("https://")
                    and _WIKIMEDIA_HOST in source
                ):
                    return source
    except (httpx.HTTPError, ValueError):
        return None
    return None
