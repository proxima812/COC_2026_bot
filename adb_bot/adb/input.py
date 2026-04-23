from __future__ import annotations


def adb_tap(adb_client, x: int, y: int) -> None:
    adb_client.run_command(("shell", "input", "tap", str(int(x)), str(int(y))))


def adb_swipe(adb_client, x1: int, y1: int, x2: int, y2: int, duration_ms: int) -> None:
    adb_client.run_command(
        (
            "shell",
            "input",
            "swipe",
            str(int(x1)),
            str(int(y1)),
            str(int(x2)),
            str(int(y2)),
            str(int(duration_ms)),
        )
    )


def adb_long_press(adb_client, x: int, y: int, duration_ms: int) -> None:
    adb_swipe(adb_client, x, y, x, y, duration_ms)


def adb_back(adb_client) -> None:
    adb_client.run_command(("shell", "input", "keyevent", "KEYCODE_BACK"))
