# BOT2 Documentation

## Purpose
`bot2` is a separate automation loop for another Clash of Clans village.
It is intentionally isolated from the main `bot.py` flow.

## Entry Point
- Terminal command: `run 2`
- Script: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/scripts/run_bot2.sh`
- Python entrypoint: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2.py`

## Runtime Flow
1. Startup delay: 5 seconds.
2. Home detection: if any of `home_1.png`, `home_11.png`, `home_12.png`, `home_13.png`, `home_14.png` is visible.
3. Search action: press `space`, then `e`.
4. Attack-ready detection: if any of `attack_ready_3.png`, `attack_ready_4.png`, `attack_ready_5.png` is visible.
5. Attack deploy:
- zoom using `ALIGN_ZOOM_KEY` for 2 seconds
- press `1`, then `g`
- select `2`
- press `g` 10 times
- immediately after deploy press `2..9` once
6. Battle phase repeats until exit condition:
- press `2..9` every random 1..5 seconds
- press `1` every random 4..6 seconds
7. If `battle_return_home.png` appears: press `h`.
8. If `battle_star_bonus.png` appears: press `-`.
9. Loop repeats forever until process stop.

## Required Templates
Folder: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/images/bot2`

Required files:
- `1.png`
- `home_1.png`
- `home_11.png`
- `home_12.png`
- `home_13.png`
- `home_14.png`
- `attack_ready_3.png`
- `attack_ready_4.png`
- `attack_ready_5.png`
- `battle_return_home.png`
- `battle_star_bonus.png`

If any required template is missing, bot2 logs missing files and exits.

## Logging
All actions and errors are printed with `bot2:` prefix.
Examples:
- detected triggers
- deploy steps
- retry search
- image locate errors

## Stop Behavior
Global stop command also stops bot2:
- `run stop`
- `stop`

`stop_bot.sh` now includes `bot2.py` process matching.
