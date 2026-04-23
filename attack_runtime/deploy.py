
import time

import pyautogui

import config as cfg
import live_config as lcfg
import runtime_state

from .common import timing_multipliers, timing_override
from .spells import cast_spells

def deploy_troops():
    troop_mult, other_mult = timing_multipliers()
    troop_select_sleep = timing_override('TROOP_SELECT_SLEEP', cfg.TROOP_SELECT_SLEEP)
    deploy_interval = timing_override('DEPLOY_INTERVAL', cfg.DEPLOY_INTERVAL)
    hero_deploy_sleep = timing_override('HERO_DEPLOY_SLEEP', cfg.HERO_DEPLOY_SLEEP)
    hero_ability_sleep = timing_override('HERO_ABILITY_SLEEP', cfg.HERO_ABILITY_SLEEP)
    battle_machine_sleep = timing_override('BATTLE_MACHINE_DEPLOY_SLEEP', cfg.BATTLE_MACHINE_DEPLOY_SLEEP)
    spell_select_sleep = timing_override('SPELL_SELECT_SLEEP', cfg.SPELL_SELECT_SLEEP)
    spell_interval = timing_override('SPELL_INTERVAL', cfg.SPELL_INTERVAL)

    hero_deploy_times = {}
    for hero_key in cfg.HERO_KEYS:
        pyautogui.press(hero_key)
        pyautogui.sleep(hero_deploy_sleep * other_mult)
        pyautogui.press(cfg.HERO_DEPLOY_KEY)
        pyautogui.sleep(hero_deploy_sleep * other_mult)
        hero_deploy_times[str(hero_key)] = time.monotonic()

    pyautogui.press(cfg.BATTLE_MACHINE_KEY)
    pyautogui.sleep(battle_machine_sleep * other_mult)
    pyautogui.press(cfg.HERO_DEPLOY_KEY)
    pyautogui.sleep(battle_machine_sleep * other_mult)

    for troop_key in cfg.TROOP_SELECT_KEYS:
        pyautogui.press(troop_key)
        pyautogui.sleep(troop_select_sleep * troop_mult)
        deploy_count = getattr(cfg, 'DEPLOY_COUNT_BY_TROOP_KEY', {}).get(troop_key, cfg.DEPLOY_COUNT)
        for _ in range(deploy_count):
            pyautogui.press(cfg.DEPLOY_KEY)
            pyautogui.sleep(deploy_interval * troop_mult)

    for spell_key in cfg.SPELL_SELECT_KEYS:
        pyautogui.press(spell_key)
        pyautogui.sleep(spell_select_sleep * other_mult)
        cast_spells(lcfg.get_int('SPELL_COUNT', cfg.SPELL_COUNT), spell_interval, other_mult)

    ability_delays = getattr(cfg, 'HERO_ABILITY_DELAY_BY_KEY', {})
    ability_press_key = getattr(cfg, 'HERO_ABILITY_PRESS_KEY', cfg.HERO_DEPLOY_KEY)
    pending_heroes = [str(hero_key) for hero_key in cfg.HERO_KEYS if str(hero_key) in hero_deploy_times]

    while pending_heroes:
        now = time.monotonic()
        ready = []
        next_ready_in = None

        for hero_key in pending_heroes:
            delay = lcfg.get_hero_ability_delay(hero_key, ability_delays.get(hero_key, 0.0))
            elapsed = now - hero_deploy_times[hero_key]
            left = delay - elapsed
            if left <= 0:
                ready.append(hero_key)
            elif next_ready_in is None or left < next_ready_in:
                next_ready_in = left

        if not ready:
            pyautogui.sleep(max(0.01, min(0.2, next_ready_in if next_ready_in is not None else 0.1)))
            continue

        for hero_key in ready:
            pyautogui.press(hero_key)
            pyautogui.sleep(hero_ability_sleep * other_mult)
            if ability_press_key:
                pyautogui.press(ability_press_key)
                pyautogui.sleep(hero_ability_sleep * other_mult)
            pending_heroes.remove(hero_key)

        if runtime_state.timing_reload_requested():
            break
