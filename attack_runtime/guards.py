
import glob
import os
import time

import pyautogui

import config as cfg
import live_config as lcfg

_LAST_GO_HOME_FAILURE = None


def _set_last_go_home_failure(code, details):
    global _LAST_GO_HOME_FAILURE
    _LAST_GO_HOME_FAILURE = {
        'code': str(code or '').strip() or None,
        'details': str(details or '').strip() or None,
    }


def consume_last_go_home_failure():
    global _LAST_GO_HOME_FAILURE
    payload = _LAST_GO_HOME_FAILURE
    _LAST_GO_HOME_FAILURE = None
    return payload


def _clear_last_go_home_failure():
    global _LAST_GO_HOME_FAILURE
    _LAST_GO_HOME_FAILURE = None

def _resolve_image_paths(config_paths_key, fallback_config_path_key, fallback_default_relative_path):
    configured_paths = getattr(cfg, config_paths_key, None)
    resolved = []

    if isinstance(configured_paths, (list, tuple)):
        for path_value in configured_paths:
            if not isinstance(path_value, str):
                continue
            normalized = path_value.strip()
            if not normalized:
                continue
            absolute_pattern = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), normalized))
            if any(char in absolute_pattern for char in ['*', '?', '[']):
                resolved.extend(sorted(glob.glob(absolute_pattern)))
            else:
                resolved.append(absolute_pattern)

    if resolved:
        unique = []
        seen = set()
        for image_path in resolved:
            if image_path in seen:
                continue
            seen.add(image_path)
            unique.append(image_path)
        return unique

    fallback_path = getattr(cfg, fallback_config_path_key, fallback_default_relative_path)
    return [os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), fallback_path))]

def _format_exc(exc):
    message = str(exc).strip() or repr(exc)
    return f"{type(exc).__name__}: {message}"

def _is_image_not_found_error(exc):
    return exc.__class__.__name__ == 'ImageNotFoundException'

def wait_for_go_home_button():
    if not getattr(cfg, 'ENABLE_GO_HOME_GUARD', False):
        return True

    image_paths = _resolve_image_paths(
        'GO_HOME_IMAGE_PATHS',
        'GO_HOME_IMAGE_PATH',
        'images/go_home.png',
    )
    existing_paths = [image_path for image_path in image_paths if os.path.exists(image_path)]
    if not existing_paths:
        print(f"Go-home images not found: {image_paths}")
        return False

    check_interval = float(lcfg.get_float('GO_HOME_CHECK_INTERVAL_SECONDS', getattr(cfg, 'GO_HOME_CHECK_INTERVAL_SECONDS', 1.0)))
    log_every = float(getattr(cfg, 'GO_HOME_LOG_EVERY_SECONDS', 15))
    region = getattr(cfg, 'GO_HOME_SEARCH_REGION', None)
    last_log_ts = 0.0
    last_error_log_ts = 0.0
    started_at = time.time()
    attempts = 0
    max_checks = max(0, int(getattr(cfg, 'RECOVERY_GUARD_MAX_CHECKS', 25) or 0))
    max_wait = float(lcfg.get_float('WAIT_FOR_IMAGE_TIMEOUT_SECONDS', 0.0))
    _clear_last_go_home_failure()

    while True:
        attempts += 1
        try:
            for image_path in existing_paths:
                match = pyautogui.locateOnScreen(image_path, grayscale=True, region=region)
                if match is not None:
                    _clear_last_go_home_failure()
                    return True
        except TypeError:
            for image_path in existing_paths:
                match = pyautogui.locateOnScreen(image_path)
                if match is not None:
                    _clear_last_go_home_failure()
                    return True
        except Exception as exc:
            if not _is_image_not_found_error(exc):
                now = time.time()
                if now - last_error_log_ts >= log_every:
                    print(f"Go-home locate failed: {_format_exc(exc)}")
                    last_error_log_ts = now
                pyautogui.sleep(check_interval)
                continue

        if max_checks > 0 and attempts >= max_checks:
            details = f'Go-home exceeded {max_checks} checks without match'
            print(f'Go-home retry limit reached after {attempts} checks.')
            _set_last_go_home_failure('guard_retry_limit', details)
            return False

        if max_wait > 0 and (time.time() - started_at) >= max_wait:
            print(f'Go-home timeout after {max_wait:.0f}s, continue loop.')
            _set_last_go_home_failure('guard_timeout', f'Go-home timed out after {max_wait:.0f}s')
            return False

        now = time.time()
        if now - last_log_ts >= log_every:
            print("Go-home button not found yet, waiting...")
            last_log_ts = now
        pyautogui.sleep(check_interval)
