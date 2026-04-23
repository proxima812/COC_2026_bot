from __future__ import annotations

from adb_bot.models import RuntimeFlags


def is_stuck(flags: RuntimeFlags, same_screen_limit: int, repeat_limit: int) -> bool:
    return flags.same_screen_ticks > same_screen_limit or flags.same_action_repeats > repeat_limit
