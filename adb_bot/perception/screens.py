from __future__ import annotations

from typing import List, Tuple

from adb_bot.config import AdbConfig
from adb_bot.models import DetectionResult, ScreenName
from adb_bot.perception.templates import detect_static_template


def classify_screen(frame_png: bytes, config: AdbConfig) -> Tuple[ScreenName, List[DetectionResult]]:
    del frame_png
    detections: list[DetectionResult] = []

    home = detect_static_template("home_village", "images/here/button_search.png")
    if home is not None and home.confidence >= config.home_confidence - 0.37:
        detections.append(home)
        return "home_village", detections

    battle = detect_static_template("battle", "images/on_war/army_ready.png")
    if battle is not None and battle.confidence >= config.button_confidence - 0.37:
        detections.append(battle)
        return "battle", detections

    popup = detect_static_template("popup_generic", "images/go_home.png")
    if popup is not None and popup.confidence >= config.button_confidence - 0.37:
        detections.append(popup)
        return "popup_generic", detections

    return "unknown", detections
