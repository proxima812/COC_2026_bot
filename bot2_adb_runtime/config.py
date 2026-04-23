from __future__ import annotations

import os

import config as project_cfg
from platform_runtime import default_adb_bin

BOT2_ADB_CONFIDENCE = 0.82
BOT2_ADB_HOME_CONFIDENCE = 0.57
BOT2_ADB_ATTACK_READY_CONFIDENCE = 0.56
BOT2_ADB_RETURN_HOME_CONFIDENCE = 0.70
BOT2_ADB_STAR_BONUS_CONFIDENCE = 0.70
BOT2_ADB_NOT_LOOT_CONFIDENCE = 0.70
BOT2_ADB_TEMPLATE_SCALES = (1.0, 0.95, 1.05, 0.9, 1.1, 0.85, 1.15, 0.8, 1.2, 0.78, 0.75, 0.72, 0.7, 1.25)
BOT2_ADB_DEBUG_LOG_INTERVAL_SECONDS = 8.0
BOT2_ADB_START_DELAY_SECONDS = 5.0
BOT2_ADB_LOOP_SLEEP = 0.35
BOT2_ADB_ATTACK_COOLDOWN_SECONDS = 2.0
BOT2_ADB_SEARCH_STEP_DELAY = 0.25
BOT2_ADB_MACHINE_DELAY = 0.3
BOT2_ADB_DEPLOY_DELAY = 0.1
BOT2_ADB_SEARCH_RETRY_SECONDS = 4.0
BOT2_ADB_AFTER_RETURN_HOME_COOLDOWN = 2.5
BOT2_ADB_AFTER_STAR_BONUS_COOLDOWN = 2.5
BOT2_ADB_SWEEP_2_9_MIN_SECONDS = 1.0
BOT2_ADB_SWEEP_2_9_MAX_SECONDS = 5.0
BOT2_ADB_PRESS_1_MIN_SECONDS = 4.0
BOT2_ADB_PRESS_1_MAX_SECONDS = 6.0
BOT2_ADB_SWEEP_2_9_DEPLOY_MIN_SECONDS = 40.0
BOT2_ADB_SWEEP_2_9_DEPLOY_MAX_SECONDS = 50.0
BOT2_ADB_BASE_MACRO_EVERY_ATTACKS = 1
BOT2_ADB_BASE_MACRO_AFTER_MOVE_SLEEP = 0.3
BOT2_ADB_BASE_MACRO_AFTER_L_SLEEP = 0.5
BOT2_ADB_NOT_LOOT_CHECK_EVERY_ATTACKS = 10
BOT2_ADB_NOT_LOOT_CLOSE_PRESSES = 4
BOT2_ADB_NOT_LOOT_CLOSE_SLEEP = 0.15

BOT2_ADB_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', 'bot2')
BOT2_ADB_HOME_IMAGES = (
    'home_1.png',
    'home_11.png',
    'home_12.png',
    'home_13.png',
    'home_14.png',
)
BOT2_ADB_ATTACK_READY_IMAGES = (
    'attack_ready_3.png',
    'attack_ready_4.png',
    'attack_ready_5.png',
)
BOT2_ADB_RETURN_HOME_IMAGE = 'battle_return_home.png'
BOT2_ADB_STAR_BONUS_IMAGE = 'battle_star_bonus.png'
BOT2_ADB_NOT_LOOT_IMAGES = ('not_loot.png', 'not_loot1.png')

ADB_INPUT_BIN = str(getattr(project_cfg, 'ADB_INPUT_BIN', default_adb_bin())).strip()
ADB_DEVICE_SERIAL = str(getattr(project_cfg, 'ADB_DEVICE_SERIAL', '')).strip()
ADB_CMD_TIMEOUT_SECONDS = max(1.0, float(getattr(project_cfg, 'ADB_CMD_TIMEOUT_SECONDS', 5.0)))
ADB_SCREENCAP_TIMEOUT_SECONDS = max(
    1.0,
    float(getattr(project_cfg, 'ADB_SCREENCAP_TIMEOUT_SECONDS', 4.0)),
)
ADB_REMOTE_SCREENSHOT_PATH = '/sdcard/bot2_adb_screen.png'
ADB_SCREEN_SIZE = tuple(getattr(project_cfg, 'ADB_SCREEN_SIZE', (1920, 1080)))
ADB_CONNECT_PORTS = str(getattr(project_cfg, 'ADB_CONNECT_PORTS', '5555 5556 5565 5575 5585')).strip()

_ADB_SCREEN_W = int(ADB_SCREEN_SIZE[0])
_ADB_SCREEN_H = int(ADB_SCREEN_SIZE[1])


def _pct_point(x_pct: float, y_pct: float) -> tuple[int, int]:
    return (
        int(round(_ADB_SCREEN_W * float(x_pct) / 100.0)),
        int(round(_ADB_SCREEN_H * float(y_pct) / 100.0)),
    )


_FREELOOK_CENTER = _pct_point(52.07, 50.94)


def _camera_swipe(dx_px: int, dy_px: int, duration_ms: int, pause_after_seconds: float = 0.0):
    start_x, start_y = _FREELOOK_CENTER
    end_x = max(0, min(_ADB_SCREEN_W - 1, start_x + int(dx_px)))
    end_y = max(0, min(_ADB_SCREEN_H - 1, start_y + int(dy_px)))
    return (start_x, start_y, end_x, end_y, int(duration_ms), float(pause_after_seconds))

BOT2_ADB_HOME_REGION = None
BOT2_ADB_ATTACK_READY_REGION = None
BOT2_ADB_RETURN_HOME_REGION = None
BOT2_ADB_STAR_BONUS_REGION = None
BOT2_ADB_NOT_LOOT_REGION = None

# Filled from coc1.cfg percentages, converted into adb screen coordinates.
BOT2_ADB_HOME_SEARCH_FIRST_TAP_PX = _pct_point(6.61, 87.64)   # Space
BOT2_ADB_HOME_SEARCH_SECOND_TAP_PX = _pct_point(72.37, 65.23)  # E
BOT2_ADB_MACHINE_SLOT_TAP_PX = _pct_point(10.69, 91.22)        # 1
BOT2_ADB_TROOP2_SLOT_TAP_PX = _pct_point(19.09, 91.17)         # 2
BOT2_ADB_SLOT_1_TAP_PX = _pct_point(10.69, 91.22)              # 1
BOT2_ADB_RETURN_HOME_TAP_PX = _pct_point(50.37, 84.45)         # H
BOT2_ADB_STAR_BONUS_TAP_PX = _pct_point(44.88, 79.61)          # -
BOT2_ADB_NOT_LOOT_CLOSE_TAP_PX = _pct_point(92.68, 43.61)      # X
BOT2_ADB_BASE_MACRO_L_TAP_PX = _pct_point(59.91, 35.21)        # L
BOT2_ADB_BASE_MACRO_EQUALS_TAP_PX = _pct_point(73.89, 83.09)   # =

BOT2_ADB_SWEEP_SLOT_TAP_POINTS = (
    _pct_point(19.09, 91.17),  # 2
    _pct_point(27.31, 90.84),  # 3
    _pct_point(35.14, 90.89),  # 4
    _pct_point(42.98, 91.30),  # 5
    _pct_point(50.41, 90.93),  # 6
    _pct_point(58.53, 90.59),  # 7
    _pct_point(66.15, 90.45),  # 8
    _pct_point(73.46, 90.40),  # 9
)

# All G mappings from coc1.cfg. In BlueStacks one G press triggers these gameplay taps.
BOT2_ADB_DEPLOY_TAP_POINTS = (
    _pct_point(59.96, 58.11),
    _pct_point(69.62, 46.08),
    _pct_point(23.59, 27.79),
    _pct_point(30.73, 46.49),
    _pct_point(72.90, 15.88),
    _pct_point(34.52, 6.12),
    _pct_point(39.31, 58.34),
    _pct_point(80.75, 31.51),
    _pct_point(26.41, 14.53),
    _pct_point(17.15, 21.33),
    _pct_point(36.75, 49.29),
)

# ADB cannot do true pinch zoom through simple `input swipe`.
# These gestures are a best-effort camera positioning sequence derived from the same control scheme.
BOT2_ADB_ATTACK_ZOOM_GESTURES = (
    _camera_swipe(+220, 0, 400, 0.10),   # approximate A: move left
    _camera_swipe(0, -180, 400, 0.10),   # approximate S: move down
)
BOT2_ADB_BASE_MACRO_GESTURES = (
    _camera_swipe(-220, 0, 500, 0.10),   # D: move right
    _camera_swipe(0, +180, 300, 0.10),   # W: move up
)


def image_path(name: str) -> str:
    return os.path.join(BOT2_ADB_IMAGES_DIR, name)


def required_template_names() -> tuple[str, ...]:
    return tuple(BOT2_ADB_HOME_IMAGES) + tuple(BOT2_ADB_ATTACK_READY_IMAGES) + (
        BOT2_ADB_RETURN_HOME_IMAGE,
        BOT2_ADB_STAR_BONUS_IMAGE,
    )


def _is_point(value) -> bool:
    return isinstance(value, (tuple, list)) and len(value) == 2 and all(
        isinstance(item, (int, float)) for item in value
    )


def _is_swipe(value) -> bool:
    return isinstance(value, (tuple, list)) and len(value) in (5, 6) and all(
        isinstance(item, (int, float)) for item in value
    )


def missing_required_fields() -> list[str]:
    missing: list[str] = []
    required_points = {
        'BOT2_ADB_HOME_SEARCH_FIRST_TAP_PX': BOT2_ADB_HOME_SEARCH_FIRST_TAP_PX,
        'BOT2_ADB_HOME_SEARCH_SECOND_TAP_PX': BOT2_ADB_HOME_SEARCH_SECOND_TAP_PX,
        'BOT2_ADB_MACHINE_SLOT_TAP_PX': BOT2_ADB_MACHINE_SLOT_TAP_PX,
        'BOT2_ADB_TROOP2_SLOT_TAP_PX': BOT2_ADB_TROOP2_SLOT_TAP_PX,
        'BOT2_ADB_SLOT_1_TAP_PX': BOT2_ADB_SLOT_1_TAP_PX,
        'BOT2_ADB_RETURN_HOME_TAP_PX': BOT2_ADB_RETURN_HOME_TAP_PX,
        'BOT2_ADB_STAR_BONUS_TAP_PX': BOT2_ADB_STAR_BONUS_TAP_PX,
        'BOT2_ADB_NOT_LOOT_CLOSE_TAP_PX': BOT2_ADB_NOT_LOOT_CLOSE_TAP_PX,
        'BOT2_ADB_BASE_MACRO_L_TAP_PX': BOT2_ADB_BASE_MACRO_L_TAP_PX,
        'BOT2_ADB_BASE_MACRO_EQUALS_TAP_PX': BOT2_ADB_BASE_MACRO_EQUALS_TAP_PX,
    }
    for name, value in required_points.items():
        if not _is_point(value):
            missing.append(name)

    if len(BOT2_ADB_SWEEP_SLOT_TAP_POINTS) != 8 or not all(
        _is_point(point) for point in BOT2_ADB_SWEEP_SLOT_TAP_POINTS
    ):
        missing.append('BOT2_ADB_SWEEP_SLOT_TAP_POINTS (8 points for slots 2..9)')

    if not BOT2_ADB_DEPLOY_TAP_POINTS or not all(
        _is_point(point) for point in BOT2_ADB_DEPLOY_TAP_POINTS
    ):
        missing.append('BOT2_ADB_DEPLOY_TAP_POINTS')

    if not BOT2_ADB_ATTACK_ZOOM_GESTURES or not all(
        _is_swipe(item) for item in BOT2_ADB_ATTACK_ZOOM_GESTURES
    ):
        missing.append('BOT2_ADB_ATTACK_ZOOM_GESTURES')

    if not BOT2_ADB_BASE_MACRO_GESTURES or not all(
        _is_swipe(item) for item in BOT2_ADB_BASE_MACRO_GESTURES
    ):
        missing.append('BOT2_ADB_BASE_MACRO_GESTURES')

    return missing
