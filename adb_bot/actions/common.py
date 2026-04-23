from __future__ import annotations

from adb_bot.models import BotAction


def tap_action(x: int, y: int, reason: str, **metadata: str) -> BotAction:
    return BotAction(action_type="tap", reason=reason, x=x, y=y, metadata=metadata)


def swipe_action(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration_ms: int,
    reason: str,
    **metadata: str
) -> BotAction:
    return BotAction(
        action_type="swipe",
        reason=reason,
        x=x1,
        y=y1,
        x2=x2,
        y2=y2,
        duration_ms=duration_ms,
        metadata=metadata,
    )


def long_press_action(x: int, y: int, duration_ms: int, reason: str, **metadata: str) -> BotAction:
    return BotAction(
        action_type="long_press",
        reason=reason,
        x=x,
        y=y,
        duration_ms=duration_ms,
        metadata=metadata,
    )


def wait_action(wait_ms: int, reason: str, **metadata: str) -> BotAction:
    return BotAction(action_type="wait", reason=reason, wait_ms=wait_ms, metadata=metadata)


def back_action(reason: str, **metadata: str) -> BotAction:
    return BotAction(action_type="back", reason=reason, metadata=metadata)


def retry_action(reason: str, **metadata: str) -> BotAction:
    return BotAction(action_type="retry", reason=reason, metadata=metadata)


def noop_action(reason: str, **metadata: str) -> BotAction:
    return BotAction(action_type="noop", reason=reason, metadata=metadata)
