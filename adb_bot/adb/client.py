from __future__ import annotations

import subprocess
import time
from typing import Optional, Sequence, Union

import config as legacy_config

from adb_bot.adb.capture import capture_png_bytes
from adb_bot.adb.input import adb_back, adb_long_press, adb_swipe, adb_tap
from adb_bot.config import AdbConfig


class ADBClient:
    def __init__(self, config: AdbConfig) -> None:
        self.config = config
        self.adb_bin = str(getattr(legacy_config, "ADB_INPUT_BIN", "")).strip()
        self.device_serial = str(getattr(legacy_config, "ADB_DEVICE_SERIAL", "")).strip()

    def ensure_ready(self) -> None:
        if not self.adb_bin:
            raise RuntimeError("ADB_INPUT_BIN is not configured")
        self.start_server()
        self.try_connect_localhost()
        if not self.is_device_ready():
            raise RuntimeError("ADB device is not ready")

    def start_server(self) -> None:
        self.run_command(("start-server",), timeout=max(6.0, self.config.command_timeout_seconds))

    def try_connect_localhost(self) -> None:
        ports = str(getattr(legacy_config, "ADB_CONNECT_PORTS", "5555 5556 5565 5575 5585")).split()
        for port in ports:
            if not port:
                continue
            try:
                self.run_command(("connect", "127.0.0.1:{0}".format(port)), timeout=3.0)
            except RuntimeError:
                continue

    def is_device_ready(self) -> bool:
        try:
            output = self.run_command(("devices",))
        except RuntimeError:
            return False
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        return any("\tdevice" in line for line in lines)

    def capture_png(self) -> bytes:
        return capture_png_bytes(self, timeout=self.config.screenshot_timeout_seconds)

    def tap(self, x: int, y: int) -> None:
        adb_tap(self, x, y)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> None:
        adb_swipe(self, x1, y1, x2, y2, duration_ms)

    def long_press(self, x: int, y: int, duration_ms: int) -> None:
        adb_long_press(self, x, y, duration_ms)

    def back(self) -> None:
        adb_back(self)

    def wait(self, wait_ms: int) -> None:
        time.sleep(max(0.0, float(wait_ms) / 1000.0))

    def run_command(
        self,
        args: Sequence[str],
        timeout: Optional[float] = None,
        binary: bool = False,
    ) -> Union[str, bytes]:
        command = [self.adb_bin]
        if self.device_serial:
            command.extend(["-s", self.device_serial])
        command.extend(list(args))
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            timeout=timeout or self.config.command_timeout_seconds,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.decode("utf-8", errors="ignore").strip()
            stdout = completed.stdout.decode("utf-8", errors="ignore").strip()
            raise RuntimeError("ADB command failed: {0} ({1})".format(" ".join(command), stderr or stdout))
        if binary:
            return completed.stdout
        return completed.stdout.decode("utf-8", errors="ignore")
