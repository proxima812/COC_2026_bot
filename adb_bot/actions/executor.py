from __future__ import annotations

from adb_bot.adb.client import ADBClient
from adb_bot.models import BotAction


class ActionExecutor:
    def __init__(self, adb_client: ADBClient) -> None:
        self.adb_client = adb_client

    def execute(self, action: BotAction) -> bool:
        action_type = action.action_type
        if action_type == "tap":
            if action.x is None or action.y is None:
                return False
            self.adb_client.tap(action.x, action.y)
            return True
        if action_type == "swipe":
            if None in (action.x, action.y, action.x2, action.y2, action.duration_ms):
                return False
            self.adb_client.swipe(action.x, action.y, action.x2, action.y2, action.duration_ms or 0)
            return True
        if action_type == "long_press":
            if None in (action.x, action.y, action.duration_ms):
                return False
            self.adb_client.long_press(action.x, action.y, action.duration_ms or 0)
            return True
        if action_type == "back":
            self.adb_client.back()
            return True
        if action_type == "wait":
            self.adb_client.wait(action.wait_ms or 0)
            return True
        if action_type == "retry":
            self.adb_client.wait(500)
            return True
        if action_type == "noop":
            return True
        return False
