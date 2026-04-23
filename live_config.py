import config as cfg
import runtime_state

_MISSING = object()


def get(name, default=None):
    value = runtime_state.get_config_override(name, default=_MISSING)
    if value is not _MISSING:
        return value
    return getattr(cfg, name, default)


def get_bool(name, default=False):
    value = get(name, default)
    return bool(value)


def get_int(name, default=0):
    value = get(name, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def get_float(name, default=0.0):
    value = get(name, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def get_str(name, default=''):
    value = get(name, default)
    return str(value)


def get_region(name, default=None):
    value = get(name, default)
    if isinstance(value, (list, tuple)) and len(value) == 4:
        try:
            return tuple(int(float(item)) for item in value)
        except (TypeError, ValueError):
            return tuple(default) if isinstance(default, (list, tuple)) and len(default) == 4 else default
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ('', 'none', 'null', 'off'):
            return None
        parts = [part.strip() for part in value.split(',')]
        if len(parts) == 4:
            try:
                return tuple(int(float(part)) for part in parts)
            except (TypeError, ValueError):
                pass
    if isinstance(default, (list, tuple)) and len(default) == 4:
        return tuple(int(float(item)) for item in default)
    return default


def get_hero_ability_delay(hero_key, default=0.0):
    override_key = f'HERO_ABILITY_DELAY_{str(hero_key)}'
    value = runtime_state.get_config_override(override_key, default=_MISSING)
    if value is _MISSING:
        return float(default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)
