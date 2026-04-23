from __future__ import annotations

from adb_bot.config import AdbConfig
from adb_bot.decision.priorities import choose_priority_action
from adb_bot.models import BotAction, RuntimeFlags, WorldState


class DecisionEngine:
    def __init__(self, config: AdbConfig) -> None:
        self.config = config

    def decide(self, world_state: WorldState, runtime_flags: RuntimeFlags) -> BotAction:
        return choose_priority_action(world_state, runtime_flags, self.config)
