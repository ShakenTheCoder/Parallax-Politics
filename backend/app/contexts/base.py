"""ContextPack — the universal domain-knowledge container for Parallax Politics agents.

Every agent is domain-agnostic code; all domain knowledge lives here.
Swap pack_id to extend from Philippines → US politics, football, music, etc.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ContextPack:
    id: str
    label: str
    principal_archetype: str

    base_system_md: str
    agent_prompts: dict[str, str]

    emotions: tuple[str, ...]
    dimensions: tuple[str, ...]

    source_domain_hints: tuple[str, ...]
    cohort_template: tuple[str, ...]

    _intake_prompt_fn: Callable[[str], str]

    def intake_situation_prompt(self, full_name: str) -> str:
        return self._intake_prompt_fn(full_name)

    def get_agent_system(self, agent_name: str) -> str:
        """Return base + role overlay for agent_name (case-insensitive)."""
        overlay = self.agent_prompts.get(agent_name.lower(), "")
        if not overlay:
            raise KeyError(
                f"ContextPack '{self.id}' has no agent overlay for '{agent_name}'. "
                f"Available: {sorted(self.agent_prompts)}"
            )
        return f"{self.base_system_md}\n\n---\n\n{overlay}"


def _load_md(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_pack(pack_dir: Path) -> ContextPack:
    """Construct a ContextPack by reading markdown files from a pack directory.

    Expected layout:
        <pack_dir>/
          pack.py        (defines PACK_META dict with id, label, principal_archetype,
                          emotions, dimensions, source_domain_hints, cohort_template,
                          and an optional intake_prompt_template str)
          base.md
          agents/
            sga.md
            dcaa.md
            demcaa.md
            ppa.md
            strategist.md
    """
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        f"_pack_meta_{pack_dir.name}", pack_dir / "pack.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load pack.py from {pack_dir}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    meta: dict = mod.PACK_META  # type: ignore[attr-defined]

    base_md = _load_md(pack_dir / "base.md")

    agents_dir = pack_dir / "agents"
    agent_prompts: dict[str, str] = {}
    for md_file in agents_dir.glob("*.md"):
        agent_prompts[md_file.stem.lower()] = _load_md(md_file)

    template: str = meta.get(
        "intake_prompt_template",
        "Build a complete intelligence dossier for: {name}. "
        "This is the principal's intake run. Use all available sources.",
    )

    return ContextPack(
        id=meta["id"],
        label=meta["label"],
        principal_archetype=meta["principal_archetype"],
        base_system_md=base_md,
        agent_prompts=agent_prompts,
        emotions=tuple(meta["emotions"]),
        dimensions=tuple(meta["dimensions"]),
        source_domain_hints=tuple(meta.get("source_domain_hints", [])),
        cohort_template=tuple(meta.get("cohort_template", [])),
        _intake_prompt_fn=lambda name, t=template: t.format(name=name),
    )
