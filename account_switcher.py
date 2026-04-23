from __future__ import annotations

import glob
import os
import random
import time
from dataclasses import dataclass

import pyautogui

import config as cfg
from bot_runtime import screen_state
import telegram_reporter


ACCOUNT_NAMES = (
    'old_proxima',
    'yung_proxima',
    'proxima',
    'samgold',
    'love12steps',
)


@dataclass
class AccountSwitchResult:
    ok: bool
    message: str
    account_name: str | None = None


@dataclass
class AccountTemplateHit:
    image_path: str
    match: object
    used_relaxed_confidence: bool = False


def _log(message: str):
    text = f'Account switcher: {message}'
    print(text, flush=True)
    try:
        telegram_reporter.append_console_log(text)
    except Exception:
        pass


def _project_root():
    return os.path.dirname(__file__)


def _account_templates(account_name: str) -> list[str]:
    pattern = os.path.join(_project_root(), 'images', 'accs', account_name, '*')
    return sorted(path for path in glob.glob(pattern) if os.path.isfile(path))


def _is_home_visible(confidence: float | None = None):
    image_paths = screen_state.resolve_image_paths(
        'SEARCH_BUTTON_IMAGE_PATHS',
        'SEARCH_BUTTON_IMAGE_PATH',
        'images/here/button_search.png',
    )
    region = getattr(cfg, 'SEARCH_BUTTON_SEARCH_REGION', None)
    for image_path in image_paths:
        if not os.path.exists(image_path):
            continue
        match = screen_state.locate_image(image_path, region=region, confidence=confidence)
        if match is not None:
            return True
    return False


def wait_until_home(timeout_seconds: float = 20.0, poll_interval: float = 0.5):
    deadline = time.time() + max(1.0, float(timeout_seconds))
    while time.time() <= deadline:
        if _is_home_visible():
            return True
        pyautogui.sleep(max(0.1, float(poll_interval)))
    return False


def _handle_post_switch_okay():
    image_paths = screen_state.resolve_image_paths(
        'OKAY_AFTER_BATTLE_IMAGE_PATHS',
        'OKAY_AFTER_BATTLE_IMAGE_PATH',
        'images/okay.png',
    )
    existing_paths = [image_path for image_path in image_paths if image_path and os.path.exists(image_path)]
    if not existing_paths:
        return False

    region = getattr(cfg, 'OKAY_AFTER_BATTLE_SEARCH_REGION', None)
    confidence = float(getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88))
    deadline = time.time() + max(0.0, float(getattr(cfg, 'OKAY_AFTER_BATTLE_CHECK_SECONDS', 4.0)))
    poll_interval = max(0.1, float(getattr(cfg, 'OKAY_AFTER_BATTLE_POLL_INTERVAL_SECONDS', 0.4)))

    while time.time() <= deadline:
        for image_path in existing_paths:
            match = screen_state.locate_image(image_path, region=region, confidence=confidence)
            if match is None:
                continue
            left, top, width, height = _match_box(match)
            click_x = left + max(1, width // 2)
            click_y = top + max(1, height // 2)
            _log(
                f'post-switch okay detected template={os.path.basename(image_path)} '
                f'click=({click_x},{click_y})'
            )
            pyautogui.click(click_x, click_y)
            pyautogui.sleep(0.5)
            return True
        pyautogui.sleep(poll_interval)
    return False


def ensure_home(timeout_seconds: float = 20.0):
    if _is_home_visible():
        return True

    deadline = time.time() + max(1.0, float(timeout_seconds))
    while time.time() <= deadline:
        pyautogui.press(getattr(cfg, 'ACCOUNT_SWITCH_RETURN_HOME_KEY', 'h'))
        pyautogui.sleep(float(getattr(cfg, 'ACCOUNT_SWITCH_RETURN_HOME_PRESS_SLEEP', 1.2)))
        if _is_home_visible():
            return True
    return False


def detect_current_account():
    region = getattr(cfg, 'ACCOUNT_SWITCH_CURRENT_ACCOUNT_REGION', (150, 90, 170, 30))
    confidence = float(getattr(cfg, 'ACCOUNT_SWITCH_DETECT_CONFIDENCE', 0.82))

    best_name = None
    best_score = -1.0
    scales = getattr(cfg, 'CV2_TEMPLATE_SCALES', (1.0, 0.95, 1.05, 0.9, 1.1))

    for account_name in ACCOUNT_NAMES:
        template_paths = _account_templates(account_name)
        if not template_paths:
            continue
        score, template_path = screen_state.cv2_best_match_for_paths(
            template_paths,
            region=region,
            scales=scales,
        )
        if score is None:
            continue
        if float(score) > best_score:
            best_score = float(score)
            best_name = account_name
            best_template_path = template_path

    if best_name is None or best_score < confidence:
        _log(f'current account not confirmed. best={best_name or "n/a"} score={best_score:.3f}')
        return None
    _log(
        f'current account detected: {best_name} '
        f'score={best_score:.3f} '
        f'template={os.path.basename(best_template_path) if best_template_path else "n/a"}'
    )
    return best_name


def _open_account_list():
    pyautogui.press(getattr(cfg, 'ACCOUNT_SWITCH_OPEN_MENU_KEY', '0'))
    pyautogui.sleep(float(getattr(cfg, 'ACCOUNT_SWITCH_OPEN_MENU_SLEEP', 0.3)))
    pyautogui.press(getattr(cfg, 'ACCOUNT_SWITCH_OPEN_LIST_KEY', '9'))
    pyautogui.sleep(float(getattr(cfg, 'ACCOUNT_SWITCH_AFTER_OPEN_LIST_SLEEP', 1.0)))


def _find_account_in_list(account_name: str):
    region = getattr(cfg, 'ACCOUNT_SWITCH_LIST_REGION', (1020, 470, 435, 425))
    return _find_account_in_region(account_name, region)


def _find_account_in_region(account_name: str, region):
    confidence = float(getattr(cfg, 'ACCOUNT_SWITCH_LIST_CONFIDENCE', 0.80))
    template_paths = _account_templates(account_name)

    for image_path in template_paths:
        try:
            match = screen_state.locate_image(image_path, region=region, confidence=confidence)
            if match is not None:
                return AccountTemplateHit(image_path=image_path, match=match, used_relaxed_confidence=False)
            if confidence > 0.72:
                match = screen_state.locate_image(image_path, region=region, confidence=confidence - 0.08)
                if match is not None:
                    return AccountTemplateHit(image_path=image_path, match=match, used_relaxed_confidence=True)
        except ValueError:
            continue
    return None


def _best_account_match_in_region(account_name: str, region):
    template_paths = _account_templates(account_name)
    if not template_paths:
        return None, None
    scales = getattr(cfg, 'CV2_TEMPLATE_SCALES', (1.0, 0.95, 1.05, 0.9, 1.1))
    return screen_state.cv2_best_match_for_paths(template_paths, region=region, scales=scales)


def _scroll_account_list_once(region=None):
    left, top, width, height = region or getattr(cfg, 'ACCOUNT_SWITCH_LIST_REGION', (1020, 470, 435, 425))
    center_x = int(left + width / 2)
    start_y = int(top + height - 20)
    end_y = int(top + 30)
    pyautogui.moveTo(center_x, start_y)
    pyautogui.dragTo(
        center_x,
        end_y,
        duration=float(getattr(cfg, 'ACCOUNT_SWITCH_SCROLL_DURATION', 0.35)),
        button='left',
    )
    pyautogui.sleep(float(getattr(cfg, 'ACCOUNT_SWITCH_AFTER_SCROLL_SLEEP', 0.7)))


def _match_box(match):
    return (
        int(getattr(match, 'left', match[0])),
        int(getattr(match, 'top', match[1])),
        int(getattr(match, 'width', match[2])),
        int(getattr(match, 'height', match[3])),
    )


def _click_match(hit: AccountTemplateHit, region=None):
    left, top, width, height = _match_box(hit.match)
    region_left, region_top, region_width, region_height = region or getattr(
        cfg,
        'ACCOUNT_SWITCH_LIST_REGION',
        (1020, 470, 435, 425),
    )
    region_right = int(region_left + region_width)
    region_bottom = int(region_top + region_height)

    pad_x = max(24, min(110, width))
    pad_y = max(10, min(28, height))

    click_left = max(int(region_left), left - pad_x)
    click_top = max(int(region_top), top - pad_y)
    click_right = min(region_right, left + width + pad_x)
    click_bottom = min(region_bottom, top + height + pad_y)

    if click_right <= click_left:
        click_right = min(region_right, click_left + max(6, width))
    if click_bottom <= click_top:
        click_bottom = min(region_bottom, click_top + max(6, height))

    click_x = random.randint(click_left, max(click_left, click_right - 1))
    click_y = random.randint(click_top, max(click_top, click_bottom - 1))

    _log(
        'click account template '
        f'template={os.path.basename(hit.image_path)} '
        f'box=({left},{top},{width},{height}) '
        f'expanded=({click_left},{click_top})-({click_right},{click_bottom}) '
        f'click=({click_x},{click_y}) '
        f'relaxed={"yes" if hit.used_relaxed_confidence else "no"}'
    )
    pyautogui.click(click_x, click_y)


def _coordinate_click_point(account_name: str):
    configured = getattr(cfg, 'ACCOUNT_SWITCH_CLICK_POINTS', {}) or {}
    point = configured.get(account_name)
    if not point or len(point) != 2:
        return None
    try:
        base_x = int(point[0])
        base_y = int(point[1])
    except (TypeError, ValueError):
        return None

    jitter = max(0, int(getattr(cfg, 'ACCOUNT_SWITCH_COORDINATE_JITTER_PX', 8)))
    click_x = base_x + random.randint(-jitter, jitter)
    click_y = base_y + random.randint(-jitter, jitter)
    return click_x, click_y


def _click_account_coordinate(account_name: str):
    point = _coordinate_click_point(account_name)
    if point is None:
        return False
    click_x, click_y = point
    _log(f'click account by coordinates account={account_name} click=({click_x},{click_y})')
    pyautogui.click(click_x, click_y)
    return True


def switch_account(account_name: str) -> AccountSwitchResult:
    target = str(account_name or '').strip()
    if target not in ACCOUNT_NAMES:
        return AccountSwitchResult(False, 'Неизвестный аккаунт.')

    current_account = detect_current_account()
    if current_account == target and ensure_home(timeout_seconds=8.0):
        return AccountSwitchResult(True, f'Бот на аккаунте <b>{target}</b>.', account_name=target)

    if not ensure_home(timeout_seconds=float(getattr(cfg, 'ACCOUNT_SWITCH_HOME_TIMEOUT_SECONDS', 20.0))):
        _log(f'failed to return home before switching to {target}')
        return AccountSwitchResult(False, 'Не удалось вернуться домой перед переключением.')

    _log(f'start switching to {target}')
    _open_account_list()

    if _click_account_coordinate(target):
        pyautogui.sleep(float(getattr(cfg, 'ACCOUNT_SWITCH_AFTER_CLICK_SLEEP', 3.0)))
        if wait_until_home(timeout_seconds=float(getattr(cfg, 'ACCOUNT_SWITCH_CONFIRM_HOME_TIMEOUT_SECONDS', 25.0))):
            _handle_post_switch_okay()
            _log(f'successfully switched to {target} by coordinates')
            return AccountSwitchResult(True, f'Бот на аккаунте <b>{target}</b>.', account_name=target)
        _log(f'clicked {target} by coordinates, but home did not confirm; falling back to image search')

    search_regions = [
        getattr(cfg, 'ACCOUNT_SWITCH_LIST_REGION', (1020, 470, 435, 425)),
        getattr(
            cfg,
            'ACCOUNT_SWITCH_LIST_REGION_AFTER_SCROLL',
            getattr(cfg, 'ACCOUNT_SWITCH_LIST_REGION', (1020, 470, 435, 425)),
        ),
    ]

    template_paths = _account_templates(target)
    _log(
        f'target={target} templates={len(template_paths)} '
        f'files={[os.path.basename(path) for path in template_paths]}'
    )

    for attempt, search_region in enumerate(search_regions, start=1):
        best_score, best_path = _best_account_match_in_region(target, search_region)
        _log(
            f'search attempt {attempt}/{len(search_regions)} '
            f'region={search_region} '
            f'best_score={f"{best_score:.3f}" if best_score is not None else "n/a"} '
            f'best_template={os.path.basename(best_path) if best_path else "n/a"} '
            f'threshold={float(getattr(cfg, "ACCOUNT_SWITCH_LIST_CONFIDENCE", 0.80)):.3f}'
        )
        hit = _find_account_in_region(target, search_region)
        if hit is not None:
            _log(
                f'found account {target} on attempt {attempt}/{len(search_regions)} '
                f'using template={os.path.basename(hit.image_path)} '
                f'region={search_region}'
            )
            _click_match(hit, search_region)
            pyautogui.sleep(float(getattr(cfg, 'ACCOUNT_SWITCH_AFTER_CLICK_SLEEP', 3.0)))
            if wait_until_home(timeout_seconds=float(getattr(cfg, 'ACCOUNT_SWITCH_CONFIRM_HOME_TIMEOUT_SECONDS', 25.0))):
                _handle_post_switch_okay()
                _log(f'successfully switched to {target}')
                return AccountSwitchResult(True, f'Бот на аккаунте <b>{target}</b>.', account_name=target)
            _log(f'clicked {target}, but home did not confirm')
            return AccountSwitchResult(False, f'Аккаунт <b>{target}</b> выбран, но база не подтвердилась.')
        if attempt == 1:
            _log(f'account {target} not found in first region={search_region}; scrolling list once')
            _scroll_account_list_once(search_region)

    _log(f'account {target} was not found after {len(search_regions)} attempts')
    return AccountSwitchResult(False, f'Не удалось найти аккаунт <b>{target}</b> в списке.')
