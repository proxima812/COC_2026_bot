from __future__ import annotations

from adb_bot.models import BotAction, WorldState


def verify_action_result(previous_state: WorldState, current_state: WorldState, action: BotAction) -> bool:
    if action.action_type in ("wait", "noop", "retry"):
        return True
    if action.action_type == "back":
        return previous_state.screen != current_state.screen or current_state.screen == "home_village"
    if action.action_type == "tap":
        return previous_state.screen != current_state.screen or bool(current_state.available_actions)
    if action.action_type in ("swipe", "long_press"):
        return True
    return False
