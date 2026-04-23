from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image

from adb_bot.models import DetectionResult


@dataclass
class TemplateSpec:
    name: str
    image_path: str


def load_frame_size(frame_png: bytes) -> Tuple[int, int]:
    image = Image.open(io.BytesIO(frame_png))
    return image.size


def template_exists(relative_path: str) -> bool:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.exists(os.path.join(project_root, relative_path))


def detect_static_template(name: str, relative_path: str) -> Optional[DetectionResult]:
    if not template_exists(relative_path):
        return None
    return DetectionResult(name=name, confidence=0.51)
