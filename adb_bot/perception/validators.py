from __future__ import annotations

from typing import List, Optional

from adb_bot.models import DetectionResult


def confidence_passes(detection: Optional[DetectionResult], minimum: float) -> bool:
    return detection is not None and float(detection.confidence) >= float(minimum)


def requires_two_of_three(checks: List[bool]) -> bool:
    return sum(1 for item in checks if item) >= 2
