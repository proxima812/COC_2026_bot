from __future__ import annotations

from typing import Optional


def estimated_capacity(_townhall_level: Optional[int], resource_name: str) -> Optional[int]:
    defaults = {
        "gold": 20000000,
        "elixir": 20000000,
        "dark_elixir": 300000,
    }
    return defaults.get(resource_name)
