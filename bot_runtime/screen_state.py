
import glob
import os
import time

import cv2
import numpy as np
import pyautogui

import config as cfg
import live_config as lcfg

_LAST_WAIT_FAILURE = None


def _set_last_wait_failure(code, details):
    global _LAST_WAIT_FAILURE
    _LAST_WAIT_FAILURE = {
        'code': str(code or '').strip() or None,
        'details': str(details or '').strip() or None,
    }


def clear_last_wait_failure():
    global _LAST_WAIT_FAILURE
    _LAST_WAIT_FAILURE = None


def consume_last_wait_failure():
    global _LAST_WAIT_FAILURE
    payload = _LAST_WAIT_FAILURE
    _LAST_WAIT_FAILURE = None
    return payload

def resolve_image_path(config_key, default_relative_path):
    return os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            getattr(cfg, config_key, default_relative_path),
        )
    )

def resolve_image_paths(config_paths_key, fallback_config_path_key, fallback_default_relative_path):
    configured_paths = getattr(cfg, config_paths_key, None)
    resolved = []

    if isinstance(configured_paths, (list, tuple)):
        for path_value in configured_paths:
            if not isinstance(path_value, str):
                continue
            normalized = path_value.strip()
            if not normalized:
                continue
            absolute_pattern = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), normalized)
            )
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

    return [
        resolve_image_path(
            fallback_config_path_key,
            fallback_default_relative_path,
        )
    ]

def format_exc(exc):
    message = str(exc).strip() or repr(exc)
    return f"{type(exc).__name__}: {message}"

def is_image_not_found_error(exc):
    return exc.__class__.__name__ == 'ImageNotFoundException'

def locate_image(image_path, region=None, confidence=None):
    kwargs = {'grayscale': True}
    if region is not None:
        kwargs['region'] = region
    if confidence is not None:
        kwargs['confidence'] = confidence

    try:
        match = pyautogui.locateOnScreen(image_path, **kwargs)
        if match is not None:
            return match
    except TypeError:
        fallback_kwargs = {}
        if region is not None:
            fallback_kwargs['region'] = region
        match = pyautogui.locateOnScreen(image_path, **fallback_kwargs)
        if match is not None:
            return match
    except Exception as exc:
        if not is_image_not_found_error(exc):
            raise

    if not getattr(cfg, 'ENABLE_CV2_TEMPLATE_FALLBACK', True):
        return None

    cv2_confidence = confidence
    if cv2_confidence is None:
        cv2_confidence = lcfg.get_float('IMAGE_MATCH_CONFIDENCE', getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88))
    cv2_confidence = max(
        0.5,
        cv2_confidence - float(getattr(cfg, 'CV2_TEMPLATE_CONFIDENCE_DELTA', 0.05)),
    )
    scales = getattr(cfg, 'CV2_TEMPLATE_SCALES', (1.0, 0.95, 1.05, 0.9, 1.1))
    return locate_image_cv2_multiscale(
        image_path=image_path,
        region=region,
        confidence=cv2_confidence,
        scales=scales,
    )

def locate_image_cv2_multiscale(image_path, region=None, confidence=0.83, scales=(1.0,)):
    template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        return None

    screenshot = pyautogui.screenshot(region=region)
    haystack = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    hay_h, hay_w = haystack.shape[:2]

    best_score = -1.0
    best_rect = None

    for raw_scale in scales:
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
        if tpl_h < 6 or tpl_w < 6:
            continue
        if tpl_h > hay_h or tpl_w > hay_w:
            continue

        result = cv2.matchTemplate(haystack, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best_score:
            best_score = max_val
            best_rect = (max_loc[0], max_loc[1], tpl_w, tpl_h)

    if best_rect is None or best_score < confidence:
        return None

    left, top, width, height = best_rect
    if region is not None:
        left += int(region[0])
        top += int(region[1])
    return (left, top, width, height)

def cv2_best_match_for_paths(image_paths, region=None, scales=(1.0,)):
    if not image_paths:
        return None, None

    screenshot = pyautogui.screenshot(region=region)
    haystack = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
    hay_h, hay_w = haystack.shape[:2]

    best_score = -1.0
    best_path = None

    for image_path in image_paths:
        template = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            continue

        for raw_scale in scales:
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
            if tpl_h < 6 or tpl_w < 6:
                continue
            if tpl_h > hay_h or tpl_w > hay_w:
                continue

            result = cv2.matchTemplate(haystack, scaled, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_score:
                best_score = max_val
                best_path = image_path

    if best_score < 0:
        return None, None
    return best_score, best_path

def wait_for_image(
    config_enabled_key,
    config_path_key,
    default_relative_path,
    config_interval_key,
    config_log_key,
    config_region_key,
    log_prefix,
):
    if not getattr(cfg, config_enabled_key, False):
        return True

    image_path = resolve_image_path(config_path_key, default_relative_path)
    if not os.path.exists(image_path):
        print(f"{log_prefix} image not found: {image_path}")
        return False

    check_interval = lcfg.get_float(config_interval_key, 1.0)
    log_every = float(getattr(cfg, config_log_key, 15))
    max_wait = lcfg.get_float('WAIT_FOR_IMAGE_TIMEOUT_SECONDS', 0.0)
    region = getattr(cfg, config_region_key, None)
    confidence = lcfg.get_float('IMAGE_MATCH_CONFIDENCE', getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88))
    cv2_scales = getattr(cfg, 'CV2_TEMPLATE_SCALES', (1.0, 0.95, 1.05, 0.9, 1.1))
    last_log_ts = 0.0
    last_error_log_ts = 0.0
    started_at = time.time()
    attempts = 0
    max_checks = max(0, int(getattr(cfg, 'RECOVERY_GUARD_MAX_CHECKS', 25) or 0))
    clear_last_wait_failure()

    while True:
        attempts += 1
        try:
            match = locate_image(image_path, region=region, confidence=confidence)
            if match is None and confidence > 0.80:
                match = locate_image(image_path, region=region, confidence=confidence - 0.08)
        except TypeError:
            match = locate_image(image_path, region=region)
        except Exception as exc:
            if is_image_not_found_error(exc):
                match = None
            else:
                now = time.time()
                if now - last_error_log_ts >= log_every:
                    print(f"{log_prefix} locate failed: {format_exc(exc)}")
                    last_error_log_ts = now
                pyautogui.sleep(check_interval)
                continue

        if match is not None:
            clear_last_wait_failure()
            return True

        if max_checks > 0 and attempts >= max_checks:
            details = f'{log_prefix} exceeded {max_checks} checks without match'
            print(f'{log_prefix} retry limit reached after {attempts} checks.')
            _set_last_wait_failure('guard_retry_limit', details)
            return False

        if max_wait > 0 and (time.time() - started_at) >= max_wait:
            print(f"{log_prefix} timeout after {max_wait:.0f}s, continue loop.")
            _set_last_wait_failure('guard_timeout', f'{log_prefix} timed out after {max_wait:.0f}s')
            return False

        now = time.time()
        if now - last_log_ts >= log_every:
            details = ''
            if getattr(cfg, 'ENABLE_CV2_TEMPLATE_FALLBACK', True):
                try:
                    score, _ = cv2_best_match_for_paths(
                        [image_path],
                        region=region,
                        scales=cv2_scales,
                    )
                    if score is not None:
                        details = f" best_score={score:.3f}"
                except Exception:
                    pass
            print(f"{log_prefix} not found on screen yet, waiting...{details}")
            last_log_ts = now
        pyautogui.sleep(check_interval)

def wait_for_any_image(
    config_enabled_key,
    config_paths_key,
    fallback_config_path_key,
    fallback_default_relative_path,
    config_interval_key,
    config_log_key,
    config_region_key,
    log_prefix,
):
    if not getattr(cfg, config_enabled_key, False):
        return True

    image_paths = resolve_image_paths(
        config_paths_key,
        fallback_config_path_key,
        fallback_default_relative_path,
    )
    existing_image_paths = [image_path for image_path in image_paths if os.path.exists(image_path)]
    if not existing_image_paths:
        print(f"{log_prefix} images not found: {image_paths}")
        return False

    check_interval = lcfg.get_float(config_interval_key, 1.0)
    log_every = float(getattr(cfg, config_log_key, 15))
    max_wait = lcfg.get_float('WAIT_FOR_IMAGE_TIMEOUT_SECONDS', 0.0)
    region = getattr(cfg, config_region_key, None)
    confidence = lcfg.get_float('IMAGE_MATCH_CONFIDENCE', getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88))
    cv2_scales = getattr(cfg, 'CV2_TEMPLATE_SCALES', (1.0, 0.95, 1.05, 0.9, 1.1))
    last_log_ts = 0.0
    last_error_log_ts = 0.0
    started_at = time.time()
    attempts = 0
    max_checks = max(0, int(getattr(cfg, 'RECOVERY_GUARD_MAX_CHECKS', 25) or 0))
    clear_last_wait_failure()

    while True:
        attempts += 1
        try:
            for image_path in existing_image_paths:
                match = locate_image(image_path, region=region, confidence=confidence)
                if match is not None:
                    clear_last_wait_failure()
                    return True
                if confidence > 0.80:
                    match = locate_image(image_path, region=region, confidence=confidence - 0.08)
                    if match is not None:
                        clear_last_wait_failure()
                        return True
        except TypeError:
            for image_path in existing_image_paths:
                match = locate_image(image_path, region=region)
                if match is not None:
                    clear_last_wait_failure()
                    return True
        except Exception as exc:
            if not is_image_not_found_error(exc):
                now = time.time()
                if now - last_error_log_ts >= log_every:
                    print(f"{log_prefix} locate failed: {format_exc(exc)}")
                    last_error_log_ts = now
                pyautogui.sleep(check_interval)
                continue

        if max_checks > 0 and attempts >= max_checks:
            details = f'{log_prefix} exceeded {max_checks} checks without any match'
            print(f'{log_prefix} retry limit reached after {attempts} checks.')
            _set_last_wait_failure('guard_retry_limit', details)
            return False

        if max_wait > 0 and (time.time() - started_at) >= max_wait:
            print(f"{log_prefix} timeout after {max_wait:.0f}s, continue loop.")
            _set_last_wait_failure('guard_timeout', f'{log_prefix} timed out after {max_wait:.0f}s')
            return False

        now = time.time()
        if now - last_log_ts >= log_every:
            details = ''
            if getattr(cfg, 'ENABLE_CV2_TEMPLATE_FALLBACK', True):
                try:
                    score, score_path = cv2_best_match_for_paths(
                        existing_image_paths,
                        region=region,
                        scales=cv2_scales,
                    )
                    if score is not None:
                        details = f" best_score={score:.3f} template={os.path.basename(score_path)}"
                except Exception:
                    pass
            print(f"{log_prefix} not found on screen yet, waiting...{details}")
            last_log_ts = now
        pyautogui.sleep(check_interval)

def wait_for_search_button_screen():
    return wait_for_image(
        'ENABLE_SEARCH_BUTTON_GUARD',
        'SEARCH_BUTTON_IMAGE_PATH',
        'images/button_search.png',
        'SEARCH_BUTTON_CHECK_INTERVAL_SECONDS',
        'SEARCH_BUTTON_LOG_EVERY_SECONDS',
        'SEARCH_BUTTON_SEARCH_REGION',
        'Search button',
    )

def wait_for_army_ready_screen():
    return wait_for_any_image(
        'ENABLE_ARMY_READY_GUARD',
        'ARMY_READY_IMAGE_PATHS',
        'ARMY_READY_IMAGE_PATH',
        'images/army_ready.png',
        'ARMY_READY_CHECK_INTERVAL_SECONDS',
        'ARMY_READY_LOG_EVERY_SECONDS',
        'ARMY_READY_SEARCH_REGION',
        'Army ready',
    )
