from __future__ import annotations

from adb_bot.models import AttackStrategy, WorldState


def choose_attack_strategy(state: WorldState) -> AttackStrategy:
    if state.village.collectors_ready:
        return "collector_snipe"
    if state.resources.gold and state.resources.gold > 700000:
        return "full_push"
    return "edge_funnel"
