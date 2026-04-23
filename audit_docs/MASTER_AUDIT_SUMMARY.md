# Master Audit Summary

## Scope
This summary consolidates three focused audits:
- `agent1_launch_scripts_audit.md`
- `agent2_telegram_audit.md`
- `agent3_modules_inventory.md`

## What was reviewed
- Launch and stop scripts.
- Telegram control bot, UI flows, callbacks, process controller, cleanup, account switching, fill-storages scenario.
- Main bot runtime, attack modules, OCR, recovery, storage monitoring, account switching, bot2 runtimes.

## Overall status
The project is operational and has a usable production loop for the main bot. The strongest areas are:
- Main farming loop orchestration.
- Recovery coverage for black screen, error templates, guard retry limits, and unexpected exceptions.
- Telegram control panel with single-message UI model.
- Account switching by coordinates.
- Separate `bot2` and `bot2_adb` runtime structures.

The weakest areas are:
- Telegram controller complexity and event-loop blocking.
- OCR reliability for battle loot.
- Cross-platform script parity.
- Some state/task behavior that exists only in memory.

## Priority findings

### P1
1. `scripts/stop_bot.bat` does not stop `bot2.py` and `bot2_adb.py`.
2. `telegram_control_aiogram.py` contains duplicate function definitions according to the Telegram audit.
3. Telegram UI/control uses chat context while `telegram_reporter` uses a direct configured chat target; this can split notifications from the active control chat.

### P2
1. `fill_storages_everywhere` state is only in memory and is lost if the Telegram bot restarts.
2. Long synchronous operations run inside async Telegram callbacks.
3. OCR/loot filtering remains highly sensitive to region quality and screenshot fidelity.
4. Storage monitor depends on internal helper behavior from `gold_filter.py`.

### P3
1. Accounts menu still exposes `love12steps` although current operational flows focus on 4 accounts.
2. Some launch scripts are less hardened than others (`run_bot2_adb.sh` preflight consistency).
3. There is no single startup validator for required config tuples, images, and click points.

## Recommended work order
1. Fix Windows stop coverage for secondary bots.
2. Clean and deduplicate `telegram_control_aiogram.py`.
3. Unify Telegram message routing between aiogram UI and `telegram_reporter`.
4. Persist `fill_storages_everywhere` scenario state in `runtime_state`.
5. Add startup validation for config/image prerequisites.
6. Add OCR fixture-based regression checks using saved bad loot crops.
7. Add mode-locking so conflicting foreground `pyautogui` bots cannot run together.

## Validation performed
- Shell syntax checks were reported by Agent 1 for `.sh` scripts.
- Targeted Python syntax checks were run during recent edits on changed files.
- No full end-to-end integration or emulator-driven regression test was run as part of this audit.

## Artifacts
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/audit_docs/agent1_launch_scripts_audit.md`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/audit_docs/agent2_telegram_audit.md`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/audit_docs/agent3_modules_inventory.md`
