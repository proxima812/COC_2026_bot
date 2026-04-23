
import time

import pyautogui

import config as cfg
import runtime_state

from .common import timing_multipliers, timing_override
from .guards import wait_for_go_home_button

def surrender():
    _, other_mult = timing_multipliers()
    wait_before_surrender = timing_override('SURRENDER_WAIT', getattr(cfg, 'SURRENDER_WAIT', 28))

    deadline = time.monotonic() + max(0.0, float(wait_before_surrender))
    while time.monotonic() < deadline:
        if runtime_state.timing_reload_requested():
            break
        pyautogui.sleep(0.2)

    for key, wait in cfg.SURRENDER_SEQUENCE:
        if key == 'h':
            if not wait_for_go_home_button():
                print("Skipping home key press: go-home button not available.")
                return False
        pyautogui.press(key)
        pyautogui.sleep(float(wait) * other_mult)
    return True
