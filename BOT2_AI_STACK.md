# BOT2 AI Agent Stack

## Scope for AI Agent
This document describes only the isolated `bot2` automation module.

## Tech Stack
- Language: Python 3
- Input automation: `pyautogui`
- Image detection: shared `screen_state.locate_image` from `bot_runtime`
- Runtime style: loop + state machine (minimal)
- Logging: stdout console logs
- Trigger templates (prefixed):
  - `home_*`
  - `attack_ready_*`
  - `battle_return_home`
  - `battle_star_bonus`

## Module Structure
Folder: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime`

Modules:
- `config.py`: bot2 constants and template names
- `logger.py`: log helper
- `detector.py`: image matching helpers and required template checks
- `actions.py`: keyboard actions and timed steps
- `state.py`: small runtime state model
- `main.py`: orchestration loop
- `__init__.py`: package marker

Entrypoint wrapper:
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2.py`

## Operational Dependencies
- BlueStacks window visible and active for keyboard input workflow
- template files in `images/bot2`
- `run 2` command configured in shell

## Agent Change Rules
1. Keep bot2 isolated from main `bot.py` logic.
2. Do not mix bot2 templates with other image folders.
3. Keep key sequence behavior deterministic unless user requests randomization.
4. Prefer editing `bot2_runtime/*` modules instead of growing `bot2.py`.
5. If adding new phases, update both:
- `BOT2_DOCUMENTATION.md`
- `BOT2_AI_STACK.md`

## Recommended Next Improvements
1. Add optional file logging (rotating log file).
2. Add per-phase counters for diagnostics.
3. Add optional Telegram panel dedicated to bot2 lifecycle.
