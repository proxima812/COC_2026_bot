from __future__ import annotations

from adb_bot.actions.common import back_action, wait_action
from adb_bot.models import BotAction, WorldState


def close_popup_action() -> BotAction:
    return back_action("Close popup or modal")


def return_home_action(state: WorldState) -> BotAction:
    if state.ui.back_visible:
        return back_action("Return to home village")
    return wait_action(1200, "Waiting for safe path home")


def idle_action() -> BotAction:
    return wait_action(1500, "Idle on stable screen")
