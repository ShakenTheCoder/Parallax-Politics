"""Conservative, evidence-derived classification for public appearances."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.intelligence.rss import FeedItem

_SPACE = re.compile(r"\s+")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_KINDS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("interview", re.compile(r"\b(interview|panayam|one[- ]on[- ]one|guest)\b", re.I)),
    (
        "press_conference",
        re.compile(r"\b(press conference|media briefing|news conference)\b", re.I),
    ),
    (
        "speech",
        re.compile(
            r"\b(speech|keynote|remarks|address(?:es|ed)?|talumpati|mensahe|paalala|pahayag)\b",
            re.I,
        ),
    ),
    (
        "hearing",
        re.compile(r"\b(testif(?:y|ies|ied)|testimony|appears before|attends? hearing)\b", re.I),
    ),
    (
        "public_event",
        re.compile(r"\b(joins?|attends?|leads?|launches?|hosts?|forum|town hall)\b", re.I),
    ),
)
_GREETING_PREFIXES = (
    "mga kababayan",
    "assalamu alaykum",
    "madayaw ug maayong adlaw",
    "magandang araw",
    "good morning",
    "good afternoon",
    "good evening",
)


@dataclass(frozen=True)
class AppearanceDecision:
    kind: str
    confidence: float
    description: str
    basis: str


def _bounded_description(prefix: str, summary: str, *, limit: int = 260) -> str:
    normalized = _SPACE.sub(" ", summary).strip()
    sentences = [part.strip() for part in _SENTENCE.split(normalized) if part.strip()]
    meaningful = [
        sentence
        for sentence in sentences
        if len(sentence) >= 35 and not sentence.casefold().startswith(_GREETING_PREFIXES)
    ]
    detail = meaningful[0] if meaningful else normalized
    value = f"{prefix} {detail}".strip()
    return f"{value[: limit - 1].rstrip()}…" if len(value) > limit else value


def _kind(text: str) -> str | None:
    return next((name for name, pattern in _KINDS if pattern.search(text)), None)


def classify_publisher_appearance(
    item: FeedItem, aliases: tuple[str, ...]
) -> AppearanceDecision | None:
    """Require the subject and a direct appearance cue in the publisher headline."""

    headline = item.title.casefold()
    subject_named = any(
        re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", headline) for alias in aliases
    )
    kind = _kind(item.title)
    if not subject_named or not kind:
        return None
    return AppearanceDecision(
        kind=kind,
        confidence=0.88,
        description=_bounded_description(item.title, item.summary),
        basis="publisher_headline_names_subject_and_direct_appearance",
    )


def classify_owned_youtube_appearance(
    item: FeedItem, figure_name: str
) -> AppearanceDecision | None:
    """Classify attributable channel uploads with direct first-person or event evidence."""

    combined = f"{item.title}\n{item.summary}"
    kind = _kind(combined)
    first_person = bool(
        re.search(
            r"\b(ako|atin|ating|natin|kami|namin|our|we|i am|i will|my)\b",
            item.summary,
            re.I,
        )
    )
    if not kind and not first_person:
        return None
    label = kind or "video_message"
    return AppearanceDecision(
        kind=label,
        confidence=0.9 if kind and first_person else 0.82,
        description=_bounded_description(f"{figure_name} published “{item.title}.”", item.summary),
        basis="attributable_youtube_channel_with_direct_message_metadata",
    )
