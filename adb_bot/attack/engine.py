from __future__ import annotations

from adb_bot.actions.common import wait_action
from adb_bot.models import BotAction, WorldState


def start_attack_action(state: WorldState) -> BotAction:
    if state.screen == "home_village":
        return wait_action(500, "Attack flow placeholder: attack button detection pending")
    return wait_action(500, "Attack flow placeholder")
