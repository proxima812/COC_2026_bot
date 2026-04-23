from __future__ import annotations

from adb_bot.actions.common import back_action, wait_action
from adb_bot.models import BotAction, RuntimeFlags, WorldState


def recover_action(state: WorldState, flags: RuntimeFlags) -> BotAction:
    if state.ui.popups_open:
        return back_action("Recovery: popup blocks view")
    if flags.same_action_repeats > 0:
        return back_action("Recovery: repeated action failed")
    if state.screen == "loading":
        return wait_action(2000, "Recovery: waiting for loading screen")
    return back_action("Recovery: return to safe navigation path")
