import time

import pyautogui

import config as global_cfg

from . import config
from .logger import log


def run_search():
    log('home image detected -> press space, then e')
    pyautogui.press('space')
    pyautogui.sleep(config.BOT2_SEARCH_STEP_DELAY)
    pyautogui.press('e')


def zoom_for_attack():
    zoom_key = str(getattr(global_cfg, 'ALIGN_ZOOM_KEY', 'down')).strip() or 'down'
    zoom_duration = 1.0
    log(f'attack-ready image detected -> zoom with {zoom_key} for {zoom_duration:.1f}s, then A/S')
    pyautogui.keyDown(zoom_key)
    pyautogui.sleep(zoom_duration)
    pyautogui.keyUp(zoom_key)
    for key in ('a', 's'):
        pyautogui.keyDown(key)
        pyautogui.sleep(0.4)
        pyautogui.keyUp(key)


def deploy_attack():
    zoom_for_attack()
    log('deploy machine: 1 -> g')
    pyautogui.press('1')
    pyautogui.sleep(config.BOT2_MACHINE_DELAY)
    pyautogui.press('g')
    pyautogui.sleep(config.BOT2_DEPLOY_DELAY)

    log('deploy troop 2: 10x g')
    pyautogui.press('2')
    pyautogui.sleep(config.BOT2_DEPLOY_DELAY)
    for index in range(10):
        pyautogui.press('g')
        pyautogui.sleep(config.BOT2_DEPLOY_DELAY)
        log(f'troop 2 deploy click {index + 1}/10')

    press_2_to_9()


def return_home():
    log('detected return-home image -> press h')
    pyautogui.press('h')


def handle_star_bonus():
    log('detected star-bonus image -> press -')
    pyautogui.press('-')


def close_not_loot_ui():
    presses = max(1, int(config.BOT2_NOT_LOOT_CLOSE_X_PRESSES))
    sleep_s = max(0.0, float(config.BOT2_NOT_LOOT_CLOSE_X_SLEEP))
    log(f'detected not_loot -> press X {presses} times')
    for idx in range(presses):
        pyautogui.press('x')
        if sleep_s > 0:
            pyautogui.sleep(sleep_s)
        log(f'close loot UI click {idx + 1}/{presses}')


def press_2_to_9():
    log('press abilities: 2 3 4 5 6 7 8 9')
    for key in ('2', '3', '4', '5', '6', '7', '8', '9'):
        pyautogui.press(key)
        pyautogui.sleep(0.05)


def press_2_to_9_then_g():
    log('periodic combo: 2 3 4 5 6 7 8 9 -> g')
    for key in ('2', '3', '4', '5', '6', '7', '8', '9'):
        pyautogui.press(key)
        pyautogui.sleep(0.05)
    pyautogui.press('g')


def press_1():
    log('press key: 1')
    pyautogui.press('1')


def run_base_macro():
    log('base macro start: D(0.5) W(0.3) -> wait(0.3) -> L -> wait(0.5) -> =')
    pyautogui.keyDown('d')
    pyautogui.sleep(config.BOT2_BASE_MACRO_D_HOLD)
    pyautogui.keyUp('d')
    pyautogui.keyDown('w')
    pyautogui.sleep(config.BOT2_BASE_MACRO_W_HOLD)
    pyautogui.keyUp('w')
    pyautogui.sleep(config.BOT2_BASE_MACRO_AFTER_MOVE_SLEEP)
    pyautogui.press('l')
    pyautogui.sleep(config.BOT2_BASE_MACRO_AFTER_L_SLEEP)
    pyautogui.press('=')
    log('base macro complete')


def sleep_loop():
    pyautogui.sleep(config.BOT2_LOOP_SLEEP)


def sleep_for(seconds: float):
    if seconds > 0:
        pyautogui.sleep(seconds)


def now() -> float:
    return time.monotonic()
