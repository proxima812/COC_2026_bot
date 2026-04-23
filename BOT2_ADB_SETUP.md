# BOT2 ADB Setup

## Entry point
- `bot2_adb.py`
- shell command after installer update: `run 2-adb`

## Purpose
This preset runs `bot2` through ADB only:
- screenshots are captured from the emulator through `adb exec-out screencap -p`
- actions are sent through `adb shell input tap` and `adb shell input swipe`
- the bot does not depend on the visible desktop screen

## Files
- `bot2_adb.py`
- `bot2_adb_runtime/config.py`
- `bot2_adb_runtime/adb.py`
- `bot2_adb_runtime/detector.py`
- `bot2_adb_runtime/actions.py`
- `bot2_adb_runtime/state.py`
- `bot2_adb_runtime/main.py`
- `scripts/run_bot2_adb.sh`

## Fill These Config Fields
Open `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/config.py` and fill:

### Required tap points
- `BOT2_ADB_HOME_SEARCH_FIRST_TAP_PX`
- `BOT2_ADB_HOME_SEARCH_SECOND_TAP_PX`
- `BOT2_ADB_MACHINE_SLOT_TAP_PX`
- `BOT2_ADB_TROOP2_SLOT_TAP_PX`
- `BOT2_ADB_SLOT_1_TAP_PX`
- `BOT2_ADB_RETURN_HOME_TAP_PX`
- `BOT2_ADB_STAR_BONUS_TAP_PX`
- `BOT2_ADB_NOT_LOOT_CLOSE_TAP_PX`
- `BOT2_ADB_BASE_MACRO_L_TAP_PX`
- `BOT2_ADB_BASE_MACRO_EQUALS_TAP_PX`

### Required slot points
- `BOT2_ADB_SWEEP_SLOT_TAP_POINTS`
- `BOT2_ADB_DEPLOY_TAP_POINTS`

Expected format:
```py
BOT2_ADB_SWEEP_SLOT_TAP_POINTS = (
    (x2, y2),
    (x3, y3),
    (x4, y4),
    (x5, y5),
    (x6, y6),
    (x7, y7),
    (x8, y8),
    (x9, y9),
)
```

Expected deploy format:
```py
BOT2_ADB_DEPLOY_TAP_POINTS = (
    (x1, y1),
    (x2, y2),
    ...
)
```

### Required gesture lists
- `BOT2_ADB_ATTACK_ZOOM_GESTURES`
- `BOT2_ADB_BASE_MACRO_GESTURES`

Expected format:
```py
BOT2_ADB_ATTACK_ZOOM_GESTURES = (
    (x1, y1, x2, y2, duration_ms, pause_after_seconds),
)
```

## Optional Search Regions
These can stay `None` first, then be narrowed later for speed:
- `BOT2_ADB_HOME_REGION`
- `BOT2_ADB_ATTACK_READY_REGION`
- `BOT2_ADB_RETURN_HOME_REGION`
- `BOT2_ADB_STAR_BONUS_REGION`
- `BOT2_ADB_NOT_LOOT_REGION`

Format:
```py
(left, top, width, height)
```

## Current ADB Flow
1. Start delay
2. Find one of `home_*.png`
3. Tap search sequence
4. Find one of `attack_ready_*.png`
5. Run attack zoom gestures
6. Tap machine slot -> tap all deploy points
7. Tap troop2 slot -> tap all deploy points 10 times
8. Tap slots `2..9`
9. During battle:
   - random sweep `2..9`
   - random tap on slot `1`
   - periodic sweep `2..9` then deploy target
10. If `battle_return_home.png` appears -> tap return home
11. If `battle_star_bonus.png` appears -> tap continue
12. Every configured number of attacks -> run base macro
13. Every configured number of attacks -> if `not_loot*.png` appears, close UI and continue cycle

## Notes
- This preset keeps the current `run 2` untouched.
- `run 2-adb` is intended for background farming while the desktop stays free.
- The bot validates missing templates and missing config fields before starting.
- True pinch zoom is not available through simple ADB `input swipe`. The current attack zoom sequence is an approximation based on camera drag gestures from the same control scheme.
