from __future__ import annotations

from adb_bot.config import AdbConfig
from adb_bot.models import RuntimeFlags, WorldState


def is_recover_needed(state: WorldState, flags: RuntimeFlags, config: AdbConfig) -> bool:
    if state.screen in ("unknown", "loading", "connection_lost"):
        return True
    if flags.same_screen_ticks > config.same_screen_threshold:
        return True
    if flags.same_action_repeats > config.same_action_threshold:
        return True
    return False


def should_return_home(state: WorldState) -> bool:
    return state.screen not in ("home_village", "unknown")


def should_attack(state: WorldState) -> bool:
    return state.screen == "home_village" and state.army.ready
