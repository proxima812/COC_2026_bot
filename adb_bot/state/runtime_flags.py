from __future__ import annotations

import time

from adb_bot.models import BotAction, RuntimeFlags, WorldState


def update_runtime_flags(
    flags: RuntimeFlags,
    previous_state: WorldState,
    current_state: WorldState,
    action: BotAction,
    verified: bool,
) -> RuntimeFlags:
    same_screen_ticks = flags.same_screen_ticks + 1 if previous_state.screen == current_state.screen else 0
    same_action_repeats = (
        flags.same_action_repeats + 1 if action.action_type == flags.last_action_type and not verified else 0
    )
    last_progress_timestamp = flags.last_progress_timestamp
    if previous_state.screen != current_state.screen or verified:
        last_progress_timestamp = time.time()
    return RuntimeFlags(
        same_screen_ticks=same_screen_ticks,
        same_action_repeats=same_action_repeats,
        last_action_success=verified,
        last_progress_timestamp=last_progress_timestamp,
        last_screen=current_state.screen,
        last_action_type=action.action_type,
    )
