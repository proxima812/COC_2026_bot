from __future__ import annotations

from typing import List, Optional

from adb_bot.models import DetectionResult


def detect_wall_candidates(_frame_png: bytes) -> List[DetectionResult]:
    return []


def detect_collectors(_frame_png: bytes) -> List[DetectionResult]:
    return []


def detect_upgrade_button(_frame_png: bytes) -> Optional[DetectionResult]:
    return None
