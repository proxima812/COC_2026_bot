from __future__ import annotations

import os
from dataclasses import dataclass

import cv2

from . import config


@dataclass
class TemplateMatch:
    name: str
    score: float
    left: int
    top: int
    width: int
    height: int
    scale: float = 1.0


class TemplateDetector:
    def __init__(self):
        self._cache: dict[str, object] = {}

    def image_path(self, name: str) -> str:
        return os.path.join(config.BOT2_ADB_IMAGES_DIR, name)

    def missing_required_templates(self) -> list[str]:
        return [name for name in config.required_template_names() if not os.path.exists(self.image_path(name))]

    def _template(self, name: str):
        template = self._cache.get(name)
        if template is not None:
            return template
        path = self.image_path(name)
        if not os.path.exists(path):
            return None
        template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            return None
        self._cache[name] = template
        return template

    def best_any(self, frame_rgb, names, region=None):
        frame_gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        origin_x = 0
        origin_y = 0
        haystack = frame_gray
        if region is not None:
            left, top, width, height = [int(value) for value in region]
            right = max(left + 1, left + width)
            bottom = max(top + 1, top + height)
            haystack = frame_gray[top:bottom, left:right]
            origin_x = left
            origin_y = top

        best_match = None
        for name in names:
            template = self._template(name)
            if template is None:
                continue
            for raw_scale in getattr(config, 'BOT2_ADB_TEMPLATE_SCALES', (1.0,)):
                try:
                    scale = float(raw_scale)
                except (TypeError, ValueError):
                    continue
                if scale <= 0:
                    continue
                if abs(scale - 1.0) < 1e-6:
                    scaled = template
                else:
                    scaled = cv2.resize(
                        template,
                        None,
                        fx=scale,
                        fy=scale,
                        interpolation=cv2.INTER_LINEAR,
                    )

                tpl_h, tpl_w = scaled.shape[:2]
                hay_h, hay_w = haystack.shape[:2]
                if tpl_w < 6 or tpl_h < 6:
                    continue
                if tpl_w > hay_w or tpl_h > hay_h:
                    continue
                result = cv2.matchTemplate(haystack, scaled, cv2.TM_CCOEFF_NORMED)
                _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
                candidate = TemplateMatch(
                    name=name,
                    score=float(max_val),
                    left=origin_x + int(max_loc[0]),
                    top=origin_y + int(max_loc[1]),
                    width=int(tpl_w),
                    height=int(tpl_h),
                    scale=float(scale),
                )
                if best_match is None or candidate.score > best_match.score:
                    best_match = candidate
        return best_match

    def find_any(self, frame_rgb, names, region=None, confidence=None):
        threshold = float(confidence) if confidence is not None else float(config.BOT2_ADB_CONFIDENCE)
        best_match = self.best_any(frame_rgb, names, region=region)
        if best_match is None or best_match.score < threshold:
            return None
        return best_match
