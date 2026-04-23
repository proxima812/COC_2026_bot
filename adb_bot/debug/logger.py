from __future__ import annotations

from adb_bot.models import BotAction, WorldState


class DebugLogger:
    def log(self, message: str) -> None:
        print("[adb-bot] {0}".format(message), flush=True)

    def log_state(self, world_state: WorldState, action: BotAction) -> None:
        print(
            "[adb-bot] screen={0} action={1} reason={2}".format(
                world_state.screen,
                action.action_type,
                action.reason,
            ),
            flush=True,
        )
