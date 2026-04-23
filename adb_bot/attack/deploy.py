from __future__ import annotations

from adb_bot.actions.common import wait_action
from adb_bot.models import BotAction


def deploy_stub_action() -> BotAction:
    return wait_action(1200, "Deploy routine is not implemented yet")
