import random

import pyautogui

import config as cfg
import live_config as lcfg
import runtime_state


def normalize_spell_mode(mode, default='stoneDick'):
    raw = str(mode or default).strip().lower()
    if raw in ('crazywalls', 'crazy_walls'):
        return 'crazyWalls'
    return 'stoneDick'


def current_spell_mode():
    return normalize_spell_mode(runtime_state.get_spell_mode(default=getattr(cfg, 'SPELL_MODE_DEFAULT', 'stoneDick')))


def spell_mode_label(mode=None):
    normalized = current_spell_mode() if mode is None else normalize_spell_mode(mode, default=getattr(cfg, 'SPELL_MODE_DEFAULT', 'stoneDick'))
    if normalized == 'crazyWalls':
        return '💥 crazyWalls'
    return '🪨 stoneDick'


def _stone_dick_targets(spell_count):
    screen_width, screen_height = pyautogui.size()
    map_points = getattr(cfg, 'SPELL_MAP_POINTS', [])
    if not isinstance(map_points, (list, tuple)) or not map_points:
        map_points = [{'x_frac': 0.50, 'y_frac': 0.50}]

    jitter_x = max(0, lcfg.get_int('SPELL_POINT_JITTER_X_PX', 30))
    jitter_y = max(0, lcfg.get_int('SPELL_POINT_JITTER_Y_PX', 26))
    targets = []
    for cast_index in range(max(0, int(spell_count))):
        point = map_points[cast_index % len(map_points)]
        base_x = int(screen_width * float(point['x_frac']))
        base_y = int(screen_height * float(point['y_frac']))
        targets.append(
            (
                base_x + random.randint(-jitter_x, jitter_x),
                base_y + random.randint(-jitter_y, jitter_y),
            )
        )
    return targets


def _crazy_walls_targets(spell_count):
    screen_width, screen_height = pyautogui.size()
    center = getattr(cfg, 'SPELL_CRAZYWALLS_CENTER', {'x_frac': 0.50, 'y_frac': 0.38})
    center_x = int(screen_width * float(center.get('x_frac', 0.50)))
    center_y = int(screen_height * float(center.get('y_frac', 0.38)))
    offset = max(1, lcfg.get_int('SPELL_CRAZYWALLS_OFFSET_PX', 40))
    square_points = (
        (center_x - offset, center_y + offset),
        (center_x + offset, center_y + offset),
        (center_x + offset, center_y - offset),
        (center_x - offset, center_y - offset),
    )
    pattern = tuple(int(item) for item in getattr(cfg, 'SPELL_CRAZYWALLS_CAST_PATTERN', (0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3)))
    if not pattern:
        pattern = (0, 1, 2, 3)
    targets = []
    for cast_index in range(max(0, int(spell_count))):
        point_index = pattern[cast_index % len(pattern)] % len(square_points)
        targets.append(square_points[point_index])
    return targets


def build_spell_targets(spell_count):
    if current_spell_mode() == 'crazyWalls':
        return _crazy_walls_targets(spell_count)
    return _stone_dick_targets(spell_count)


def spell_interval_seconds(default_interval, other_mult):
    if current_spell_mode() == 'crazyWalls':
        spell_count = max(1, lcfg.get_int('SPELL_COUNT', 11))
        total_seconds = max(0.0, lcfg.get_float('SPELL_CRAZYWALLS_TOTAL_SECONDS', 2.0))
        if spell_count <= 1:
            return 0.0
        return total_seconds / float(spell_count - 1)
    return max(0.0, float(default_interval)) * float(other_mult)
