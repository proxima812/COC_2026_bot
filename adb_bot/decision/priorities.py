from __future__ import annotations

from adb_bot.actions.common import wait_action
from adb_bot.actions.navigation import close_popup_action, return_home_action
from adb_bot.attack.engine import start_attack_action
from adb_bot.models import BotAction, RuntimeFlags, WorldState
from adb_bot.recovery.engine import recover_action


def choose_priority_action(state: WorldState, flags: RuntimeFlags, config) -> BotAction:
    from adb_bot.decision.policies import is_recover_needed, should_attack, should_return_home

    if is_recover_needed(state, flags, config):
        return recover_action(state, flags)
    if state.ui.popups_open:
        return close_popup_action()
    if should_return_home(state):
        return return_home_action(state)
    if should_attack(state):
        return start_attack_action(state)
    return wait_action(1500, "No high-priority action available")
