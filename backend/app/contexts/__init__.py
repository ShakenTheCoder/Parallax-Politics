"""Context pack registry — load and cache ContextPack instances by ID."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.contexts.base import ContextPack, build_pack

_PACKS_DIR = Path(__file__).parent

_DEFAULT_PACK_ID = "philippines_politics"


@lru_cache(maxsize=32)
def get_pack(pack_id: str) -> ContextPack:
    pack_dir = _PACKS_DIR / pack_id
    if not pack_dir.is_dir():
        raise ValueError(
            f"ContextPack '{pack_id}' not found at {pack_dir}. "
            f"Available: {[d.name for d in _PACKS_DIR.iterdir() if d.is_dir() and not d.name.startswith('_')]}"
        )
    return build_pack(pack_dir)


def default_pack_id() -> str:
    return _DEFAULT_PACK_ID
