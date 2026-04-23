
from __future__ import annotations

import glob
import hashlib
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional

import pyautogui
import numpy as np

import config as cfg
from platform_runtime import (
    default_adb_bin,
    process_running,
    start_application,
    terminate_process,
)
import runtime_state
import live_config as lcfg
import telegram_reporter

@dataclass
class RecoveryIssue:
    code: str
    details: str

class RecoveryWatchdog:
    def __init__(self, bot_entry_path: str, locate_image_fn: Optional[Callable] = None):
        self.bot_entry_path = os.path.abspath(bot_entry_path)
        self.locate_image_fn = locate_image_fn
        self.loop_started_at = time.monotonic()
        self.last_progress_at = self.loop_started_at
        self.last_stage = 'init'
        self.recovery_attempts = 0
        self.recovery_window_started_at = self.loop_started_at

        self._last_hash = None
        self._last_hash_changed_at = self.loop_started_at
        self._last_hash_sample_at = 0.0

        self.error_templates = self._resolve_error_templates()

    def _resolve_error_templates(self):
        pattern = str(getattr(cfg, 'RECOVERY_ERROR_IMAGE_GLOB', 'images/errors/*.png')).strip()
        if not pattern:
            return []
        absolute_pattern = os.path.abspath(os.path.join(os.path.dirname(__file__), pattern))
        return sorted(glob.glob(absolute_pattern))

    def heartbeat(self, stage: str):
        now = time.monotonic()
        self.last_progress_at = now
        self.last_stage = str(stage)

    def start_loop(self):
        now = time.monotonic()
        self.loop_started_at = now
        self.last_progress_at = now
        self.last_stage = 'loop_start'

    def _match_error_template(self):
        if not lcfg.get_bool('ENABLE_AUTO_RECOVERY', True):
            return None, None
        if not self.error_templates:
            return None, None

        confidence = lcfg.get_float('RECOVERY_ERROR_CONFIDENCE', 0.87)
        region = getattr(cfg, 'RECOVERY_ERROR_REGION', None)

        for image_path in self.error_templates:
            if not os.path.exists(image_path):
                continue
            match = None
            try:
                if self.locate_image_fn is not None:
                    match = self.locate_image_fn(image_path, region=region, confidence=confidence)
                else:
                    match = pyautogui.locateOnScreen(
                        image_path,
                        grayscale=True,
                        region=region,
                        confidence=confidence,
                    )
            except TypeError:
                try:
                    match = pyautogui.locateOnScreen(
                        image_path,
                        grayscale=True,
                        region=region,
                    )
                except Exception:
                    match = None
            except Exception as exc:
                if exc.__class__.__name__ == 'ImageNotFoundException':
                    match = None
                else:
                    match = None

            if match is not None:
                return image_path, match
        return None, None

    def _sample_screen_hash(self):
        interval = max(1.0, lcfg.get_float('RECOVERY_STALE_SAMPLE_INTERVAL_SECONDS', 5.0))
        now = time.monotonic()
        if now - self._last_hash_sample_at < interval:
            return
        self._last_hash_sample_at = now

        region = getattr(cfg, 'RECOVERY_STALE_REGION', None)
        try:
            screenshot = pyautogui.screenshot(region=region)
        except Exception:
            return

        tiny = screenshot.resize((96, 54))
        digest = hashlib.md5(tiny.tobytes()).hexdigest()
        if self._last_hash != digest:
            self._last_hash = digest
            self._last_hash_changed_at = now

    def _detect_black_screen(self):
        if not lcfg.get_bool('RECOVERY_BLACK_SCREEN_ENABLED', True):
            return False

        region = getattr(cfg, 'RECOVERY_BLACK_SCREEN_REGION', None)
        try:
            screenshot = pyautogui.screenshot(region=region)
        except Exception:
            return False

        frame = np.array(screenshot.convert('L'))
        if frame.size == 0:
            return False

        brightness_max = lcfg.get_float('RECOVERY_BLACK_SCREEN_BRIGHTNESS_MAX', 8.0)
        min_coverage = lcfg.get_float('RECOVERY_BLACK_SCREEN_MIN_COVERAGE', 0.96)
        dark_ratio = float((frame <= brightness_max).mean())
        return dark_ratio >= min_coverage

    def detect_issue(self):
        if not lcfg.get_bool('ENABLE_AUTO_RECOVERY', True):
            return None

        if self._detect_black_screen():
            return RecoveryIssue(
                code='black_screen',
                details='screen is almost fully black',
            )

        image_path, _match = self._match_error_template()
        if image_path:
            return RecoveryIssue(
                code='error_template',
                details=f"error template matched: {os.path.basename(image_path)}",
            )

        max_loop_seconds = max(10.0, lcfg.get_float('RECOVERY_MAX_LOOP_SECONDS', 240.0))
        now = time.monotonic()
        if now - self.loop_started_at > max_loop_seconds:
            return RecoveryIssue(
                code='loop_timeout',
                details=(
                    f'loop exceeded {max_loop_seconds:.0f}s '
                    f'(stage={self.last_stage})'
                ),
            )

        no_progress_seconds = max(10.0, lcfg.get_float('RECOVERY_NO_PROGRESS_SECONDS', 120.0))
        if now - self.last_progress_at > no_progress_seconds:
            return RecoveryIssue(
                code='no_progress',
                details=(
                    f'no progress for {no_progress_seconds:.0f}s '
                    f'(stage={self.last_stage})'
                ),
            )

        self._sample_screen_hash()
        stale_seconds = max(10.0, lcfg.get_float('RECOVERY_STALE_SCREEN_SECONDS', 80.0))
        if now - self._last_hash_changed_at > stale_seconds:
            return RecoveryIssue(
                code='stale_screen',
                details=f'screen hash unchanged for {stale_seconds:.0f}s',
            )

        return None

    def _rate_limit_allows_recovery(self):
        now = time.monotonic()
        window_seconds = max(60.0, lcfg.get_float('RECOVERY_RATE_WINDOW_SECONDS', 3600.0))
        max_attempts = max(1, lcfg.get_int('RECOVERY_MAX_ATTEMPTS_PER_WINDOW', 6))

        if now - self.recovery_window_started_at > window_seconds:
            self.recovery_window_started_at = now
            self.recovery_attempts = 0

        if self.recovery_attempts >= max_attempts:
            return False

        self.recovery_attempts += 1
        return True

    def _notify(self, issue: RecoveryIssue):
        if not lcfg.get_bool('RECOVERY_TELEGRAM_NOTIFY', True):
            return
        action_text = '♻️ Запускаю восстановление.'
        if issue.code == 'black_screen':
            action_text = '♻️ Черный экран: перезапускаю игру.'
        elif issue.code == 'error_template':
            action_text = '♻️ Критическая ошибка: перезапускаю эмулятор полностью.'
        elif issue.code == 'guard_retry_limit':
            action_text = '♻️ Долго не находится нужный экран: перезапускаю игру.'
        elif issue.code == 'guard_timeout':
            action_text = '♻️ Экран слишком долго не подтверждается: перезапускаю игру.'
        elif issue.code == 'unexpected_exception':
            action_text = '♻️ Неожиданная ошибка в цикле: перезапускаю игру.'
        text = (
            '🚨 Вождь! Обнаружена ошибка в боте.\n'
            f'Причина: {issue.code}\n'
            f'Детали: {issue.details}\n'
            f'{action_text}'
        )
        try:
            telegram_reporter.send_text_message(text)
        except Exception as exc:
            print(f'Recovery telegram notify failed: {exc}')

    def _adb_run(self, args, timeout=8.0):
        adb_bin = str(getattr(cfg, 'ADB_INPUT_BIN', default_adb_bin())).strip()
        if not adb_bin:
            return False, ''
        command = [adb_bin]
        serial = str(getattr(cfg, 'ADB_DEVICE_SERIAL', '')).strip()
        if serial:
            command.extend(['-s', serial])
        command.extend(args)

        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                timeout=timeout,
            )
        except Exception as exc:
            return False, str(exc)

        output = (completed.stdout or b'').decode('utf-8', errors='ignore')
        error = (completed.stderr or b'').decode('utf-8', errors='ignore')
        if completed.returncode != 0:
            return False, error.strip() or output.strip()
        return True, output.strip()

    def _ensure_bluestacks_running(self):
        process_name = str(getattr(cfg, 'BLUESTACKS_PROCESS_NAME', 'BlueStacks')).strip() or 'BlueStacks'
        app_name = str(getattr(cfg, 'BLUESTACKS_APP_NAME', 'BlueStacks')).strip() or 'BlueStacks'
        if process_running(process_name):
            return True
        return start_application(app_name)

    def _restart_emulator(self):
        process_name = str(getattr(cfg, 'BLUESTACKS_PROCESS_NAME', 'BlueStacks')).strip() or 'BlueStacks'
        app_name = str(getattr(cfg, 'BLUESTACKS_APP_NAME', 'BlueStacks')).strip() or 'BlueStacks'
        wait_seconds = max(3.0, float(getattr(cfg, 'RECOVERY_EMULATOR_RESTART_WAIT_SECONDS', 12.0)))

        terminate_process(process_name)

        time.sleep(3.0)

        if not start_application(app_name):
            return False

        time.sleep(wait_seconds)
        return self._ensure_bluestacks_running()

    def _restart_game(self):
        package_name = str(getattr(cfg, 'COC_PACKAGE_NAME', 'com.supercell.clashofclans')).strip()
        if not package_name:
            package_name = 'com.supercell.clashofclans'

        self._ensure_bluestacks_running()

        self._adb_run(['start-server'], timeout=6)

        ports = str(getattr(cfg, 'ADB_CONNECT_PORTS', '5555 5556 5565 5575 5585')).strip().split()
        for port in ports:
            self._adb_run(['connect', f'127.0.0.1:{port}'], timeout=3)

        device_timeout = max(10.0, float(getattr(cfg, 'RECOVERY_ADB_DEVICE_TIMEOUT_SECONDS', 40.0)))
        start_wait = time.monotonic()
        has_device = False
        while time.monotonic() - start_wait < device_timeout:
            ok, out = self._adb_run(['devices'], timeout=3)
            if ok and '\tdevice' in out:
                has_device = True
                break
            time.sleep(1.5)

        if not has_device:
            return False

        self._adb_run(['shell', 'am', 'force-stop', package_name], timeout=6)
        time.sleep(1.2)
        ok, _out = self._adb_run(
            ['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
            timeout=8,
        )
        if not ok:
            return False

        post_sleep = max(1.0, float(getattr(cfg, 'RECOVERY_POST_LAUNCH_SLEEP_SECONDS', 8.0)))
        time.sleep(post_sleep)
        return True

    def _restart_bot_process(self):
        try:
            os.execv(sys.executable, [sys.executable, self.bot_entry_path])
        except Exception as exc:
            print(f'Bot process restart failed: {exc}')

    def handle_issue(self, issue: RecoveryIssue):
        if not self._rate_limit_allows_recovery():
            print(
                'Recovery rate limit reached. '
                f'Issue: {issue.code}, details: {issue.details}'
            )
            runtime_state.record_recovery_event(issue.code, issue.details, 'rate_limited')
            return False

        print(f'Recovery triggered: {issue.code} | {issue.details}')
        telegram_reporter.append_console_log(f'Recovery issue: {issue.code} ({issue.details}).')
        self._notify(issue)

        action = 'restart_game'
        if issue.code == 'error_template':
            action = 'restart_emulator_then_game'
            emulator_ok = self._restart_emulator()
            if not emulator_ok:
                print('Recovery: emulator restart failed, trying game restart anyway.')
                action = 'restart_game_after_emulator_fail'
            game_ok = self._restart_game()
        else:
            game_ok = self._restart_game()

        if not game_ok:
            print('Recovery: game restart failed, trying bot restart anyway.')
            action = f'{action}_failed'

        runtime_state.record_recovery_event(issue.code, issue.details, action)
        telegram_reporter.append_console_log(f'Recovery action: {action}.')

        if bool(getattr(cfg, 'RECOVERY_RESTART_BOT_PROCESS', True)):
            self._restart_bot_process()
            return True

        self.start_loop()
        self.heartbeat('recovered')
        return game_ok
