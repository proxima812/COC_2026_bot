from __future__ import annotations

from typing import List

from adb_bot.models import DetectionResult, WorldState


def build_world_state(
    screen_name: str,
    detections: List[DetectionResult],
    timestamp: float,
) -> WorldState:
    available_actions = [item.name for item in detections]
    state = WorldState(timestamp=timestamp, screen=screen_name, available_actions=available_actions)
    state.ui.popups_open = screen_name == "popup_generic"
    state.ui.connection_lost = screen_name == "connection_lost"
    state.ui.confirm_visible = "confirm_button" in available_actions
    state.ui.back_visible = screen_name not in ("home_village", "unknown")
    state.army.ready = screen_name in ("home_village", "attack_find_match")
    state.battle.started = screen_name == "battle"
    return state
