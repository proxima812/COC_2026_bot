from __future__ import annotations

import io
import re
import subprocess
import time

import numpy as np
from PIL import Image

from . import config


class ADBClient:
    def __init__(self):
        self.adb_bin = config.ADB_INPUT_BIN
        self.device_serial = config.ADB_DEVICE_SERIAL
        self.cmd_timeout = config.ADB_CMD_TIMEOUT_SECONDS
        self.screencap_timeout = config.ADB_SCREENCAP_TIMEOUT_SECONDS
        self._screen_size = None

    def _base_command(self):
        command = [self.adb_bin]
        if self.device_serial:
            command.extend(['-s', self.device_serial])
        return command

    def _run(self, args, *, binary=False, timeout=None):
        command = self._base_command() + list(args)
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout or self.cmd_timeout,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.decode('utf-8', errors='ignore').strip()
            raise RuntimeError(f"ADB command failed: {' '.join(command)} ({stderr})")
        if binary:
            return completed.stdout
        return completed.stdout.decode('utf-8', errors='ignore')

    def prepare(self):
        self._run(['start-server'], timeout=max(6.0, self.cmd_timeout))
        for port in str(config.ADB_CONNECT_PORTS).split():
            if not port:
                continue
            try:
                self._run(['connect', f'127.0.0.1:{port}'], timeout=3.0)
            except Exception:
                pass

    def is_ready(self) -> bool:
        try:
            output = self._run(['devices'], timeout=self.cmd_timeout)
        except Exception:
            return False
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return any('\tdevice' in line for line in lines)

    def screen_size(self):
        if self._screen_size is not None:
            return self._screen_size
        default_width, default_height = config.ADB_SCREEN_SIZE
        try:
            output = self._run(['shell', 'wm', 'size'], timeout=self.cmd_timeout)
            match = re.search(r'(\d+)x(\d+)', output)
            if match:
                self._screen_size = (int(match.group(1)), int(match.group(2)))
            else:
                self._screen_size = (int(default_width), int(default_height))
        except Exception:
            self._screen_size = (int(default_width), int(default_height))
        return self._screen_size

    def _normalize_png_payload(self, payload: bytes) -> bytes:
        if not payload:
            return b''
        normalized = payload
        png_signature = b'\x89PNG\r\n\x1a\n'
        start = normalized.find(png_signature)
        if start > 0:
            normalized = normalized[start:]

        iend = normalized.rfind(b'IEND')
        if iend != -1:
            trailer_end = iend + 8
            if trailer_end <= len(normalized):
                normalized = normalized[:trailer_end]
        return normalized

    def _decode_png_bytes(self, payload: bytes):
        attempts = [
            ('raw', payload),
            ('normalized', self._normalize_png_payload(payload)),
            ('newline-fixed', payload.replace(b'\r\r\n', b'\n').replace(b'\r\n', b'\n')),
        ]
        last_error = None
        for _label, candidate in attempts:
            if not candidate:
                continue
            try:
                image = Image.open(io.BytesIO(candidate))
                image.load()
                return image.convert('RGB')
            except Exception as exc:
                last_error = exc
        raise last_error or RuntimeError('ADB screenshot returned empty payload')

    def _capture_exec_out_png(self):
        png_bytes = self._run(
            ['exec-out', 'screencap', '-p'],
            binary=True,
            timeout=self.screencap_timeout,
        )
        return self._decode_png_bytes(png_bytes)

    def _capture_via_remote_file(self):
        remote_path = str(config.ADB_REMOTE_SCREENSHOT_PATH).strip() or '/sdcard/bot2_adb_screen.png'
        self._run(['shell', 'rm', '-f', remote_path], timeout=self.cmd_timeout)
        self._run(['shell', 'screencap', '-p', remote_path], timeout=max(self.screencap_timeout, 8.0))
        png_bytes = self._run(
            ['exec-out', 'sh', '-c', f'cat {remote_path}'],
            binary=True,
            timeout=max(self.screencap_timeout, 8.0),
        )
        return self._decode_png_bytes(png_bytes)

    def capture_frame_rgb(self):
        try:
            image = self._capture_exec_out_png()
        except Exception as first_exc:
            try:
                image = self._capture_via_remote_file()
            except Exception as second_exc:
                raise RuntimeError(
                    f'exec-out screencap failed ({first_exc}); remote-file fallback failed ({second_exc})'
                ) from second_exc
        return np.array(image)

    def tap(self, point):
        if point is None:
            raise RuntimeError('tap point is not configured')
        width, height = self.screen_size()
        tap_x = max(0, min(width - 1, int(float(point[0]))))
        tap_y = max(0, min(height - 1, int(float(point[1]))))
        self._run(['shell', 'input', 'tap', str(tap_x), str(tap_y)])

    def swipe(self, spec):
        if spec is None or len(spec) not in (5, 6):
            raise RuntimeError(f'invalid swipe spec: {spec!r}')
        x1, y1, x2, y2, duration_ms = spec[:5]
        self._run(
            [
                'shell',
                'input',
                'swipe',
                str(int(float(x1))),
                str(int(float(y1))),
                str(int(float(x2))),
                str(int(float(y2))),
                str(int(float(duration_ms))),
            ]
        )
        if len(spec) == 6 and float(spec[5]) > 0:
            time.sleep(float(spec[5]))

    def sleep(self, seconds: float):
        time.sleep(max(0.0, float(seconds)))
