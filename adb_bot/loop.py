from __future__ import annotations

import time

from adb_bot.actions.executor import ActionExecutor
from adb_bot.actions.verify import verify_action_result
from adb_bot.config import AdbConfig
from adb_bot.debug.logger import DebugLogger
from adb_bot.debug.screenshots import save_unknown_screen
from adb_bot.decision.engine import DecisionEngine
from adb_bot.models import RuntimeFlags
from adb_bot.perception.screens import classify_screen
from adb_bot.state.builder import build_world_state
from adb_bot.state.runtime_flags import update_runtime_flags
from adb_bot.adb.client import ADBClient


def run_loop() -> None:
    config = AdbConfig()
    adb_client = ADBClient(config)
    adb_client.ensure_ready()

    logger = DebugLogger()
    decision_engine = DecisionEngine(config)
    executor = ActionExecutor(adb_client)
    runtime_flags = RuntimeFlags(last_progress_timestamp=time.time())

    logger.log("ADB bot loop started")
    while True:
        frame = adb_client.capture_png()
        screen_name, detections = classify_screen(frame, config)
        world_state = build_world_state(
            screen_name=screen_name,
            detections=detections,
            timestamp=time.time(),
        )
        action = decision_engine.decide(world_state, runtime_flags)
        logger.log_state(world_state, action)

        if world_state.screen == "unknown":
            save_unknown_screen(frame)

        previous_state = world_state
        success = executor.execute(action)
        adb_client.wait(int(config.loop_interval_seconds * 1000))

        frame_after = adb_client.capture_png()
        next_screen, next_detections = classify_screen(frame_after, config)
        next_state = build_world_state(
            screen_name=next_screen,
            detections=next_detections,
            timestamp=time.time(),
        )
        verified = success and verify_action_result(previous_state, next_state, action)
        runtime_flags = update_runtime_flags(runtime_flags, previous_state, next_state, action, verified)
