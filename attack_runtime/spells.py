
import random

import pyautogui

import config as cfg
from .spell_modes import build_spell_targets, spell_interval_seconds

def _cast_spells_by_default_zones(spell_count, spell_interval, other_mult):
    delay = spell_interval_seconds(spell_interval, other_mult)
    for x, y in build_spell_targets(spell_count):
        pyautogui.click(x, y)
        if delay > 0:
            pyautogui.sleep(delay)

def cast_spells(spell_count, spell_interval, other_mult):
    _cast_spells_by_default_zones(spell_count, spell_interval, other_mult)
