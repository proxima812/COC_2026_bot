
from __future__ import annotations

import os
import subprocess
import sys

IS_WINDOWS = os.name == 'nt'
IS_MACOS = sys.platform == 'darwin'

def default_adb_bin():
    if IS_WINDOWS:
        candidates = [
            r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe',
            r'C:\Program Files\BlueStacks\HD-Adb.exe',
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]
    return '/Applications/BlueStacks.app/Contents/MacOS/hd-adb'

def default_bluestacks_app_name():
    if IS_WINDOWS:
        candidates = [
            r'C:\Program Files\BlueStacks_nxt\HD-Player.exe',
            r'C:\Program Files\BlueStacks\HD-Player.exe',
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]
    return 'BlueStacks'

def default_bluestacks_process_name():
    if IS_WINDOWS:
        return 'HD-Player.exe'
    return 'BlueStacks'

def process_running(process_name: str) -> bool:
    name = str(process_name or '').strip()
    if not name:
        return False

    if IS_WINDOWS:
        try:
            completed = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {name}'],
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
            )
        except Exception:
            return False
        output = (completed.stdout or '') + '\n' + (completed.stderr or '')
        return name.lower() in output.lower()

    try:
        completed = subprocess.run(
            ['pgrep', '-x', name],
            check=False,
            capture_output=True,
            timeout=2,
        )
    except Exception:
        return False
    return completed.returncode == 0

def start_application(app_name: str) -> bool:
    target = str(app_name or '').strip()
    if not target:
        return False

    try:
        if IS_WINDOWS:
            subprocess.Popen(
                ['cmd', '/c', 'start', '', target],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        subprocess.run(['open', '-a', target], check=False, timeout=8)
        return True
    except Exception:
        return False

def terminate_process(process_name: str) -> bool:
    name = str(process_name or '').strip()
    if not name:
        return False

    try:
        if IS_WINDOWS:
            subprocess.run(
                ['taskkill', '/IM', name, '/F'],
                check=False,
                capture_output=True,
                timeout=8,
            )
            return True
        subprocess.run(['pkill', '-x', name], check=False, timeout=6)
        return True
    except Exception:
        return False
