
import runtime_state

def current_bot_mode():
    return runtime_state.get_bot_mode(default='default')

def timing_multipliers():
    return 1.0, 1.0

def timing_override(key, fallback):
    value = runtime_state.get_timing_override(key, default=fallback)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)
