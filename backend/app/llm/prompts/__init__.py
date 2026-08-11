"""Pack-aware system-prompt loader.

Delegates to the ContextPack registry so every agent gets:
    base.md (shared PH political-system knowledge)
    +
    agents/<name>.md (role-specific overlay)

Pass pack_id to select a non-default pack (future packs: us_politics,
football_manager, musician, etc.).
"""

from app.contexts import default_pack_id, get_pack


def load_prompt(name: str, pack_id: str | None = None) -> str:
    pack = get_pack(pack_id or default_pack_id())
    return pack.get_agent_system(name)
