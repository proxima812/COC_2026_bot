from __future__ import annotations

import time

from . import config
from .logger import log


def _tap(adb, point, label: str):
    adb.tap(point)
    log(f'tap: {label} -> {tuple(int(v) for v in point)}')


def _tap_many(adb, points, label: str, per_tap_sleep: float = 0.05):
    for index, point in enumerate(points, start=1):
        _tap(adb, point, f'{label} {index}/{len(points)}')
        if per_tap_sleep > 0:
            adb.sleep(per_tap_sleep)


def _run_gestures(adb, gestures, label: str):
    for index, gesture in enumerate(gestures, start=1):
        adb.swipe(gesture)
        log(f'{label}: swipe {index}/{len(gestures)} -> {gesture[:5]}')


def run_search(adb):
    log('home image detected -> run adb search sequence')
    _tap(adb, config.BOT2_ADB_HOME_SEARCH_FIRST_TAP_PX, 'search first')
    adb.sleep(config.BOT2_ADB_SEARCH_STEP_DELAY)
    _tap(adb, config.BOT2_ADB_HOME_SEARCH_SECOND_TAP_PX, 'search second')


def zoom_for_attack(adb):
    log('attack-ready image detected -> run attack zoom gestures')
    _run_gestures(adb, config.BOT2_ADB_ATTACK_ZOOM_GESTURES, 'attack zoom')


def deploy_attack(adb):
    zoom_for_attack(adb)

    _tap(adb, config.BOT2_ADB_MACHINE_SLOT_TAP_PX, 'machine slot')
    adb.sleep(config.BOT2_ADB_MACHINE_DELAY)
    _tap_many(adb, config.BOT2_ADB_DEPLOY_TAP_POINTS, 'deploy target for machine')
    adb.sleep(config.BOT2_ADB_DEPLOY_DELAY)

    _tap(adb, config.BOT2_ADB_TROOP2_SLOT_TAP_PX, 'troop2 slot')
    adb.sleep(config.BOT2_ADB_DEPLOY_DELAY)
    for index in range(10):
        _tap_many(adb, config.BOT2_ADB_DEPLOY_TAP_POINTS, f'troop2 deploy sweep {index + 1}/10')
        adb.sleep(config.BOT2_ADB_DEPLOY_DELAY)

    press_2_to_9(adb)


def return_home(adb):
    _tap(adb, config.BOT2_ADB_RETURN_HOME_TAP_PX, 'return home')


def handle_star_bonus(adb):
    _tap(adb, config.BOT2_ADB_STAR_BONUS_TAP_PX, 'star bonus continue')


def close_not_loot_ui(adb):
    presses = max(1, int(config.BOT2_ADB_NOT_LOOT_CLOSE_PRESSES))
    for index in range(presses):
        _tap(adb, config.BOT2_ADB_NOT_LOOT_CLOSE_TAP_PX, f'close not_loot {index + 1}/{presses}')
        adb.sleep(config.BOT2_ADB_NOT_LOOT_CLOSE_SLEEP)


def press_2_to_9(adb):
    log('tap sweep slots: 2..9')
    for index, point in enumerate(config.BOT2_ADB_SWEEP_SLOT_TAP_POINTS, start=2):
        _tap(adb, point, f'slot {index}')
        adb.sleep(0.05)


def press_2_to_9_then_deploy(adb):
    press_2_to_9(adb)
    _tap_many(adb, config.BOT2_ADB_DEPLOY_TAP_POINTS, 'deploy target after sweep')


def press_1(adb):
    _tap(adb, config.BOT2_ADB_SLOT_1_TAP_PX, 'slot 1')


def run_base_macro(adb):
    log('run base macro gestures')
    _run_gestures(adb, config.BOT2_ADB_BASE_MACRO_GESTURES, 'base macro')
    adb.sleep(config.BOT2_ADB_BASE_MACRO_AFTER_MOVE_SLEEP)
    _tap(adb, config.BOT2_ADB_BASE_MACRO_L_TAP_PX, 'base macro L')
    adb.sleep(config.BOT2_ADB_BASE_MACRO_AFTER_L_SLEEP)
    _tap(adb, config.BOT2_ADB_BASE_MACRO_EQUALS_TAP_PX, 'base macro =')
    log('base macro complete')


def sleep_loop(adb):
    adb.sleep(config.BOT2_ADB_LOOP_SLEEP)


def sleep_for(adb, seconds: float):
    adb.sleep(seconds)


def now() -> float:
    return time.monotonic()
