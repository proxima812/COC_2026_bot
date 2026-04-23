import json
import os
from datetime import datetime

STATE_FILENAME = '.bot_runtime_state.json'
DEFAULT_STATE = {
    'attack_count': 0,
    'spell_mode': None,
    'wall_key_cycle_enabled_override': None,
    'wall_key_cycle_every_override': None,
    'clan_cake_enabled': None,
    'bot_mode': None,
    'input_profile': None,
    'config_overrides': {},
    'timing_overrides': {},
    'timing_reload_requested': False,
    'timing_pending_item_id': None,
    'battle_report_every_override': None,
    'telegram_console_enabled': False,
    'telegram_console_message_id': None,
    'telegram_console_lines': [],
    'last_recovery_issue_code': None,
    'last_recovery_issue_details': None,
    'last_recovery_action': None,
    'last_recovery_time': None,
    'telegram_panel_view': 'root',
    'telegram_control_message_id': None,
    'telegram_attack_log_message_id': None,
    'telegram_battle_screenshot_message_ids': [],
    'current_account': None,
}

def _normalize_spell_mode_name(mode, default='stoneDick'):
    raw = str(mode or default).strip().lower()
    if raw in ('crazywalls', 'crazy_walls'):
        return 'crazyWalls'
    return 'stoneDick'

def _state_path():
    return os.path.join(os.path.dirname(__file__), STATE_FILENAME)

def _merge_with_default(raw_state):
    merged = DEFAULT_STATE.copy()
    if isinstance(raw_state, dict):
        merged.update(raw_state)
    for key in list(merged.keys()):
        if key in DEFAULT_STATE:
            continue
        if key.startswith('wall_') or key.startswith('last_wall_'):
            merged.pop(key, None)
    return merged

def load_state():
    path = _state_path()
    try:
        with open(path, 'r', encoding='utf-8') as state_file:
            parsed = json.load(state_file)
        return _merge_with_default(parsed)
    except (OSError, ValueError, TypeError):
        return DEFAULT_STATE.copy()

def save_state(state):
    path = _state_path()
    tmp_path = f'{path}.tmp'
    merged = _merge_with_default(state)

    with open(tmp_path, 'w', encoding='utf-8') as state_file:
        json.dump(merged, state_file, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

def reset_session_state():
    state = load_state()
    state['attack_count'] = 0
    save_state(state)

def set_spell_mode(mode):
    state = load_state()
    state['spell_mode'] = _normalize_spell_mode_name(mode, default='stoneDick')
    save_state(state)
    return state

def get_spell_mode(default='stoneDick'):
    state = load_state()
    return _normalize_spell_mode_name(state.get('spell_mode'), default=default)

def set_clan_cake_enabled(enabled):
    state = load_state()
    state['clan_cake_enabled'] = bool(enabled)
    save_state(state)
    return state

def clan_cake_enabled(default=False):
    state = load_state()
    value = state.get('clan_cake_enabled', None)
    if value is None:
        return bool(default)
    return bool(value)

def set_bot_mode(mode):
    state = load_state()
    state['bot_mode'] = 'default'
    save_state(state)
    return state

def get_bot_mode(default='default'):
    return 'default'

def set_input_profile(profile):
    normalized = str(profile).strip().lower()
    if normalized not in ('default', 'background'):
        normalized = 'default'

    state = load_state()
    state['input_profile'] = normalized
    save_state(state)
    return state

def get_input_profile(default='default'):
    state = load_state()
    raw = str(state.get('input_profile', '')).strip().lower()
    if raw in ('default', 'background'):
        return raw
    normalized_default = str(default).strip().lower()
    if normalized_default in ('default', 'background'):
        return normalized_default
    return 'default'

def get_timing_overrides():
    state = load_state()
    raw = state.get('timing_overrides', {})
    if not isinstance(raw, dict):
        return {}
    normalized = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        try:
            normalized[key] = float(value)
        except (TypeError, ValueError):
            continue
    return normalized


def get_config_overrides():
    state = load_state()
    raw = state.get('config_overrides', {})
    if not isinstance(raw, dict):
        return {}
    normalized = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        normalized[key] = value
    return normalized


def get_config_override(key, default=None):
    overrides = get_config_overrides()
    return overrides.get(str(key), default)


def set_config_override(key, value):
    state = load_state()
    overrides = state.get('config_overrides', {})
    if not isinstance(overrides, dict):
        overrides = {}
    overrides[str(key)] = value
    state['config_overrides'] = overrides
    save_state(state)
    return state


def clear_config_override(key):
    state = load_state()
    overrides = state.get('config_overrides', {})
    if not isinstance(overrides, dict):
        overrides = {}
    overrides.pop(str(key), None)
    state['config_overrides'] = overrides
    save_state(state)
    return state

def get_timing_override(key, default=None):
    overrides = get_timing_overrides()
    if key in overrides:
        return overrides[key]
    return default

def set_timing_override(key, value):
    state = load_state()
    overrides = state.get('timing_overrides', {})
    if not isinstance(overrides, dict):
        overrides = {}
    overrides[str(key)] = float(value)
    state['timing_overrides'] = overrides
    state['timing_reload_requested'] = True
    save_state(state)
    return state

def clear_timing_override(key):
    state = load_state()
    overrides = state.get('timing_overrides', {})
    if not isinstance(overrides, dict):
        overrides = {}
    overrides.pop(str(key), None)
    state['timing_overrides'] = overrides
    state['timing_reload_requested'] = True
    save_state(state)
    return state

def timing_reload_requested():
    state = load_state()
    return bool(state.get('timing_reload_requested', False))

def consume_timing_reload_request():
    state = load_state()
    requested = bool(state.get('timing_reload_requested', False))
    if requested:
        state['timing_reload_requested'] = False
        save_state(state)
    return requested

def get_timing_pending_item_id():
    state = load_state()
    value = state.get('timing_pending_item_id')
    if value is None:
        return None
    text = str(value).strip()
    return text or None

def set_timing_pending_item_id(item_id):
    state = load_state()
    state['timing_pending_item_id'] = str(item_id).strip()
    save_state(state)
    return state

def clear_timing_pending_item_id():
    state = load_state()
    state['timing_pending_item_id'] = None
    save_state(state)
    return state

def get_battle_report_every_override(default=None):
    state = load_state()
    raw = state.get('battle_report_every_override', default)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def wall_key_cycle_enabled(default=True):
    state = load_state()
    value = state.get('wall_key_cycle_enabled_override', None)
    if value is None:
        return bool(default)
    return bool(value)


def set_wall_key_cycle_enabled(enabled):
    state = load_state()
    state['wall_key_cycle_enabled_override'] = bool(enabled)
    save_state(state)
    return state


def get_wall_key_cycle_every_override(default=None):
    state = load_state()
    raw = state.get('wall_key_cycle_every_override', default)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, value)


def set_wall_key_cycle_every_override(value):
    state = load_state()
    state['wall_key_cycle_every_override'] = max(1, int(value))
    save_state(state)
    return state

def set_battle_report_every_override(value):
    state = load_state()
    state['battle_report_every_override'] = int(value)
    save_state(state)
    return state

def clear_battle_report_every_override():
    state = load_state()
    state['battle_report_every_override'] = None
    save_state(state)
    return state

def telegram_console_enabled(default=False):
    state = load_state()
    value = state.get('telegram_console_enabled', default)
    return bool(value)

def set_telegram_console_enabled(enabled):
    state = load_state()
    state['telegram_console_enabled'] = bool(enabled)
    save_state(state)
    return state

def get_telegram_console_message_id():
    state = load_state()
    message_id = state.get('telegram_console_message_id')
    try:
        if message_id is None:
            return None
        return int(message_id)
    except (TypeError, ValueError):
        return None

def set_telegram_console_message_id(message_id):
    state = load_state()
    state['telegram_console_message_id'] = int(message_id)
    save_state(state)

def clear_telegram_console_message_id():
    state = load_state()
    state['telegram_console_message_id'] = None
    save_state(state)

def get_telegram_console_lines():
    state = load_state()
    raw = state.get('telegram_console_lines', [])
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]

def append_telegram_console_line(text, limit=18):
    state = load_state()
    lines = state.get('telegram_console_lines', [])
    if not isinstance(lines, list):
        lines = []
    line = str(text or '').strip()
    if not line:
        return state
    lines.append(line)
    limit_i = max(1, int(limit))
    state['telegram_console_lines'] = lines[-limit_i:]
    save_state(state)
    return state

def clear_telegram_console_lines():
    state = load_state()
    state['telegram_console_lines'] = []
    save_state(state)
    return state

def record_recovery_event(issue_code, issue_details, action):
    state = load_state()
    state['last_recovery_issue_code'] = str(issue_code or '').strip() or None
    state['last_recovery_issue_details'] = str(issue_details or '').strip() or None
    state['last_recovery_action'] = str(action or '').strip() or None
    state['last_recovery_time'] = datetime.now().isoformat(timespec='seconds')
    save_state(state)
    return state

def get_last_recovery_event():
    state = load_state()
    return {
        'issue_code': state.get('last_recovery_issue_code'),
        'issue_details': state.get('last_recovery_issue_details'),
        'action': state.get('last_recovery_action'),
        'time': state.get('last_recovery_time'),
    }

def get_telegram_panel_view(default='root'):
    state = load_state()
    raw = str(state.get('telegram_panel_view', default)).strip().lower()
    return raw or (str(default).strip().lower() or 'root')


def set_telegram_panel_view(view_name):
    normalized = str(view_name).strip().lower() or 'root'
    state = load_state()
    state['telegram_panel_view'] = normalized
    save_state(state)
    return state

def get_telegram_control_message_id():
    state = load_state()
    message_id = state.get('telegram_control_message_id')
    try:
        if message_id is None:
            return None
        return int(message_id)
    except (TypeError, ValueError):
        return None

def set_telegram_control_message_id(message_id):
    state = load_state()
    state['telegram_control_message_id'] = int(message_id)
    save_state(state)

def clear_telegram_control_message_id():
    state = load_state()
    state['telegram_control_message_id'] = None
    save_state(state)


def get_current_account():
    state = load_state()
    value = state.get('current_account')
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def set_current_account(account_name):
    state = load_state()
    text = str(account_name or '').strip() or None
    state['current_account'] = text
    save_state(state)
    return state

def get_telegram_attack_log_message_id():
    state = load_state()
    message_id = state.get('telegram_attack_log_message_id')
    try:
        if message_id is None:
            return None
        return int(message_id)
    except (TypeError, ValueError):
        return None

def set_telegram_attack_log_message_id(message_id):
    state = load_state()
    state['telegram_attack_log_message_id'] = int(message_id)
    save_state(state)

def clear_telegram_attack_log_message_id():
    state = load_state()
    state['telegram_attack_log_message_id'] = None
    save_state(state)

def add_telegram_battle_screenshot_message_id(message_id):
    state = load_state()
    current = state.get('telegram_battle_screenshot_message_ids', [])
    if not isinstance(current, list):
        current = []
    try:
        message_id_i = int(message_id)
    except (TypeError, ValueError):
        return state
    if message_id_i not in current:
        current.append(message_id_i)
    state['telegram_battle_screenshot_message_ids'] = current
    save_state(state)
    return state

def get_telegram_battle_screenshot_message_ids():
    state = load_state()
    raw = state.get('telegram_battle_screenshot_message_ids', [])
    if not isinstance(raw, list):
        return []
    normalized = []
    for item in raw:
        try:
            normalized.append(int(item))
        except (TypeError, ValueError):
            continue
    return normalized

def clear_telegram_battle_screenshot_message_ids():
    state = load_state()
    state['telegram_battle_screenshot_message_ids'] = []
    save_state(state)

def record_attack():
    state = load_state()
    state['attack_count'] = int(state.get('attack_count', 0)) + 1
    save_state(state)
    return state
