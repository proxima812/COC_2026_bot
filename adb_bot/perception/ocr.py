from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class OCRRead:
    value: Optional[int]
    raw_text: str
    confidence: float


def read_numeric_region(_frame_png: bytes, _region: Optional[Tuple[int, int, int, int]] = None) -> OCRRead:
    return OCRRead(value=None, raw_text="", confidence=0.0)
