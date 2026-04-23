
from __future__ import annotations

import io
import os
import re
import subprocess
import threading
import time
from collections import namedtuple

import cv2
import numpy as np
from PIL import Image
import pyautogui

import config as cfg
from platform_runtime import default_adb_bin
import runtime_state

Box = namedtuple('Box', ['left', 'top', 'width', 'height'])
Size = namedtuple('Size', ['width', 'height'])

_CURRENT_PROFILE = None
_ORIGINAL_FUNCS = {}
_BACKEND = None
_PATCH_LOCK = threading.Lock()
_HELD_KEYS = {}

_KEY_EVENT_MAP = {
    'space': 'KEYCODE_SPACE',
    'enter': 'KEYCODE_ENTER',
    'up': 'KEYCODE_DPAD_UP',
    'down': 'KEYCODE_DPAD_DOWN',
    'left': 'KEYCODE_DPAD_LEFT',
    'right': 'KEYCODE_DPAD_RIGHT',
    '-': 'KEYCODE_MINUS',
    '=': 'KEYCODE_EQUALS',
    'backspace': 'KEYCODE_DEL',
    'esc': 'KEYCODE_ESCAPE',
    'escape': 'KEYCODE_ESCAPE',
    'tab': 'KEYCODE_TAB',
}

def _normalize_profile(profile):
    normalized = str(profile or '').strip().lower()
    if normalized not in ('default', 'background'):
        return 'default'
    return normalized

def _desired_profile():
    default_profile = _normalize_profile(getattr(cfg, 'INPUT_PROFILE_DEFAULT', 'default'))
    return runtime_state.get_input_profile(default=default_profile)

def _capture_original_functions():
    if _ORIGINAL_FUNCS:
        return
    _ORIGINAL_FUNCS.update(
        {
            'click': pyautogui.click,
            'press': pyautogui.press,
            'keyDown': pyautogui.keyDown,
            'keyUp': pyautogui.keyUp,
            'sleep': pyautogui.sleep,
            'screenshot': pyautogui.screenshot,
            'size': pyautogui.size,
            'locateOnScreen': pyautogui.locateOnScreen,
            'locateAllOnScreen': pyautogui.locateAllOnScreen,
        }
    )

def _restore_default_backend():
    for name, func in _ORIGINAL_FUNCS.items():
        setattr(pyautogui, name, func)

class _ADBBackend:
    def __init__(self):
        self.adb_bin = str(
            getattr(
                cfg,
                'ADB_INPUT_BIN',
                default_adb_bin(),
            )
        ).strip()
        self.device_serial = str(getattr(cfg, 'ADB_DEVICE_SERIAL', '')).strip()
        self.cmd_timeout = max(1.0, float(getattr(cfg, 'ADB_CMD_TIMEOUT_SECONDS', 5.0)))
        self.screencap_timeout = max(
            1.0,
            float(getattr(cfg, 'ADB_SCREENCAP_TIMEOUT_SECONDS', 4.0)),
        )
        self._screen_size = None

    def is_ready(self):
        if not self.adb_bin or not os.path.exists(self.adb_bin):
            print(f"Input profile background: adb binary not found: {self.adb_bin}")
            return False

        lines = self._devices_lines()
        return any('\tdevice' in line for line in lines)

    def _base_command(self):
        command = [self.adb_bin]
        if self.device_serial:
            command.extend(['-s', self.device_serial])
        return command

    def _run(self, args, *, binary=False, timeout=None):
        command = self._base_command() + list(args)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout or self.cmd_timeout,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore').strip()
            raise RuntimeError(f"ADB command failed: {' '.join(command)} ({stderr})")
        if binary:
            return result.stdout
        return result.stdout.decode('utf-8', errors='ignore')

    def _devices_lines(self):
        try:
            output = self._run(['devices'], timeout=self.cmd_timeout)
        except Exception:
            return []
        return [line.strip() for line in output.splitlines() if line.strip()]

    def _key_to_keyevent(self, key):
        key_text = str(key or '').strip().lower()
        if not key_text:
            return None
        if key_text in _KEY_EVENT_MAP:
            return _KEY_EVENT_MAP[key_text]
        if len(key_text) == 1 and key_text.isalpha():
            return f'KEYCODE_{key_text.upper()}'
        if len(key_text) == 1 and key_text.isdigit():
            return f'KEYCODE_{key_text}'
        return None

    def _send_keyevent(self, key):
        keyevent = self._key_to_keyevent(key)
        if keyevent is None:
            print(f"ADB input: unsupported key '{key}', skipped")
            return
        self._run(['shell', 'input', 'keyevent', keyevent])

    def _resolve_screen_size(self):
        if self._screen_size is not None:
            return self._screen_size

        configured = getattr(cfg, 'ADB_SCREEN_SIZE', (1920, 1080))
        default_size = Size(1920, 1080)
        if isinstance(configured, (list, tuple)) and len(configured) == 2:
            try:
                default_size = Size(int(configured[0]), int(configured[1]))
            except (TypeError, ValueError):
                pass

        try:
            output = self._run(['shell', 'wm', 'size'])
            match = re.search(r'(\d+)x(\d+)', output)
            if match:
                self._screen_size = Size(int(match.group(1)), int(match.group(2)))
            else:
                self._screen_size = default_size
        except Exception:
            self._screen_size = default_size
        return self._screen_size

    def click(self, x=None, y=None, clicks=1, interval=0.0, button='left'):
        size = self._resolve_screen_size()
        tap_x = int(size.width / 2) if x is None else int(float(x))
        tap_y = int(size.height / 2) if y is None else int(float(y))
        tap_x = max(0, min(size.width - 1, tap_x))
        tap_y = max(0, min(size.height - 1, tap_y))

        repeats = max(1, int(clicks))
        pause = max(0.0, float(interval))
        for idx in range(repeats):
            self._run(['shell', 'input', 'tap', str(tap_x), str(tap_y)])
            if idx < repeats - 1 and pause > 0:
                time.sleep(pause)

    def press(self, keys, presses=1, interval=0.0):
        if isinstance(keys, (list, tuple)):
            key_list = list(keys)
        else:
            key_list = [keys]

        repeats = max(1, int(presses))
        pause = max(0.0, float(interval))

        for repeat_idx in range(repeats):
            for key in key_list:
                self._send_keyevent(key)
                if pause > 0:
                    time.sleep(pause)
            if repeat_idx < repeats - 1 and pause > 0:
                time.sleep(pause)

    def key_down(self, key):
        _HELD_KEYS[str(key)] = time.monotonic()

    def key_up(self, key):
        key_name = str(key)
        started = _HELD_KEYS.pop(key_name, None)
        if started is None:
            self._send_keyevent(key)
            return

        held_for = max(0.0, time.monotonic() - started)
        repeats = max(1, min(24, int(round(held_for / 0.06))))
        self.press(key, presses=repeats, interval=0.01)

    def sleep(self, seconds):
        time.sleep(max(0.0, float(seconds)))

    def screenshot(self, region=None):
        png_bytes = self._run(
            ['exec-out', 'screencap', '-p'],
            binary=True,
            timeout=self.screencap_timeout,
        )
        if not png_bytes:
            raise RuntimeError('ADB screenshot returned empty payload')

        normalized = png_bytes.replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')
        image = Image.open(io.BytesIO(normalized)).convert('RGB')
        if region is None:
            return image

        left, top, width, height = region
        left = int(left)
        top = int(top)
        width = int(width)
        height = int(height)
        right = max(left + 1, left + width)
        bottom = max(top + 1, top + height)
        return image.crop((left, top, right, bottom))

    def size(self):
        return self._resolve_screen_size()

    def locate_on_screen(self, image_path, grayscale=True, region=None, confidence=None):
        template = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return None

        screenshot = self.screenshot(region=region)
        haystack = np.array(screenshot)
        if grayscale:
            haystack = cv2.cvtColor(haystack, cv2.COLOR_RGB2GRAY)
        else:
            template = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if template is None:
                return None
            haystack = cv2.cvtColor(haystack, cv2.COLOR_RGB2BGR)

        tpl_h, tpl_w = template.shape[:2]
        hay_h, hay_w = haystack.shape[:2]
        if tpl_w > hay_w or tpl_h > hay_h:
            return None

        result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        threshold = float(confidence) if confidence is not None else float(
            getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88)
        )
        if max_val < threshold:
            return None

        left = int(max_loc[0])
        top = int(max_loc[1])
        if region is not None:
            left += int(region[0])
            top += int(region[1])
        return Box(left, top, int(tpl_w), int(tpl_h))

    def locate_all_on_screen(self, image_path, grayscale=True, region=None, confidence=None):
        template = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            return []

        screenshot = self.screenshot(region=region)
        haystack = np.array(screenshot)
        if grayscale:
            haystack = cv2.cvtColor(haystack, cv2.COLOR_RGB2GRAY)
        else:
            template = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if template is None:
                return []
            haystack = cv2.cvtColor(haystack, cv2.COLOR_RGB2BGR)

        tpl_h, tpl_w = template.shape[:2]
        hay_h, hay_w = haystack.shape[:2]
        if tpl_w > hay_w or tpl_h > hay_h:
            return []

        result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        threshold = float(confidence) if confidence is not None else float(
            getattr(cfg, 'IMAGE_MATCH_CONFIDENCE', 0.88)
        )

        ys, xs = np.where(result >= threshold)
        if len(xs) == 0:
            return []

        boxes_with_score = []
        for x, y in zip(xs.tolist(), ys.tolist()):
            score = float(result[y, x])
            boxes_with_score.append((score, int(x), int(y)))

        boxes_with_score.sort(reverse=True)
        selected = []
        for _score, x, y in boxes_with_score:
            too_close = False
            for chosen in selected:
                if abs(chosen.left - x) < max(6, tpl_w // 2) and abs(chosen.top - y) < max(6, tpl_h // 2):
                    too_close = True
                    break
            if too_close:
                continue

            left = x
            top = y
            if region is not None:
                left += int(region[0])
                top += int(region[1])
            selected.append(Box(left, top, int(tpl_w), int(tpl_h)))
        return selected

def _install_background_backend():
    global _BACKEND
    _BACKEND = _ADBBackend()
    if not _BACKEND.is_ready():
        return False

    pyautogui.click = _BACKEND.click
    pyautogui.press = _BACKEND.press
    pyautogui.keyDown = _BACKEND.key_down
    pyautogui.keyUp = _BACKEND.key_up
    pyautogui.sleep = _BACKEND.sleep
    pyautogui.screenshot = _BACKEND.screenshot
    pyautogui.size = _BACKEND.size
    pyautogui.locateOnScreen = _BACKEND.locate_on_screen
    pyautogui.locateAllOnScreen = _BACKEND.locate_all_on_screen
    return True

def apply(profile=None, force=False):
    global _CURRENT_PROFILE

    with _PATCH_LOCK:
        _capture_original_functions()
        target_profile = _normalize_profile(profile or _desired_profile())
        if not force and _CURRENT_PROFILE == target_profile:
            return _CURRENT_PROFILE

        if target_profile == 'default':
            _restore_default_backend()
            _CURRENT_PROFILE = 'default'
            return _CURRENT_PROFILE

        if _install_background_backend():
            _CURRENT_PROFILE = 'background'
            print('Input profile: background (ADB) enabled')
            return _CURRENT_PROFILE

        print('Input profile: failed to enable background, fallback to default')
        runtime_state.set_input_profile('default')
        _restore_default_backend()
        _CURRENT_PROFILE = 'default'
        return _CURRENT_PROFILE

def refresh_if_needed():
    return apply(profile=_desired_profile(), force=False)

def current_profile():
    if _CURRENT_PROFILE is None:
        return apply(profile=_desired_profile(), force=False)
    return _CURRENT_PROFILE
