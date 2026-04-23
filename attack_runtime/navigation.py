
import pyautogui

import config as cfg
import live_config as lcfg
from .common import timing_multipliers

def align_screen():
    pyautogui.keyDown(cfg.ALIGN_ZOOM_KEY)
    pyautogui.sleep(cfg.ALIGN_ZOOM_DURATION)
    pyautogui.keyUp(cfg.ALIGN_ZOOM_KEY)
    for key, wait in cfg.ALIGN_KEYS:
        pyautogui.keyDown(key)
        pyautogui.sleep(wait)
        pyautogui.keyUp(key)


def align_wall_screen():
    zoom_key = 'down'
    zoom_duration = max(0.0, float(getattr(cfg, 'ALIGN_ZOOM_DURATION', 1.2)))
    align_keys = [('a', 0.6), ('w', 0.6)]
    pyautogui.keyDown(zoom_key)
    pyautogui.sleep(zoom_duration)
    pyautogui.keyUp(zoom_key)
    for key, wait in align_keys:
        pyautogui.keyDown(key)
        pyautogui.sleep(wait)
        pyautogui.keyUp(key)

def search_attack():
    _, other_mult = timing_multipliers()
    search_sequence = [
        ('space', lcfg.get_float('SEARCH_WAIT_SPACE', float(cfg.SEARCH_SEQUENCE[0][1]))),
        ('e', lcfg.get_float('SEARCH_WAIT_E', float(cfg.SEARCH_SEQUENCE[1][1]))),
        ('i', lcfg.get_float('SEARCH_WAIT_I', float(cfg.SEARCH_SEQUENCE[2][1]))),
    ]
    for key, wait in search_sequence:
        pyautogui.press(key)
        pyautogui.sleep(float(wait) * other_mult)
