# Agent 3: Modules Inventory and Runtime Audit

Date: 2026-03-30
Scope: `bot.py`, `attack_runtime/*`, `bot_runtime/*`, `gold_filter.py`, `recovery_watchdog.py`, `storage_monitor.py`, `account_switcher.py`, `bot2*` runtimes.

## 1. Module Inventory

### Core bot runtime
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/common.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/navigation.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/deploy.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/spells.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/spell_modes.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/guards.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/surrender.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/attack_runtime/reporting.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot_runtime/screen_state.py`

### Recovery and safety
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/recovery_watchdog.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/storage_monitor.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/account_switcher.py`

### OCR / loot
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/gold_filter.py`

### Bot2 (foreground pyautogui)
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime/config.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime/state.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime/detector.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime/actions.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime/main.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_runtime/logger.py`

### Bot2 ADB (background)
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/config.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/adb.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/detector.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/actions.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/state.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/main.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/bot2_adb_runtime/logger.py`

## 2. Responsibilities by module (high level)

- `bot.py`: orchestrates full farm loop, watchdog integration, attack flow, storage checks, wall key cycle trigger, runtime state updates.
- `attack_runtime/navigation.py`: pre-attack alignment and search keystroke sequence.
- `attack_runtime/deploy.py`: machine/heroes/troops/spells deploy order and timing; hero ability scheduling.
- `attack_runtime/surrender.py`: post-wait surrender sequence and go-home guarded exit.
- `attack_runtime/guards.py`: go-home template wait with retry-limit diagnostics for recovery.
- `bot_runtime/screen_state.py`: shared image-path resolution, image matching, guard waits, retry-limit signaling.
- `gold_filter.py`: battle loot OCR pipeline (OCR-first with template fallback), acceptance/reroll logic, debug logging, bad-read frame dumps.
- `recovery_watchdog.py`: black-screen/error-template/staleness detection and staged restart policy.
- `storage_monitor.py`: periodic storage-full OCR check and stop notification.
- `account_switcher.py`: account switching via coordinate click first, image fallback second, home confirmation, optional okay popup handling.
- `bot2_runtime/main.py`: independent loop for secondary account strategy using pyautogui.
- `bot2_adb_runtime/main.py`: same concept as bot2 but background-safe via ADB screen capture/input.

## 3. Runtime flow (core bot)

1. Start delay and input profile apply.
2. Main loop starts, watchdog loop starts.
3. Global issue detect (`black_screen`, `error_template`, stale/no-progress/timeout).
4. Guard: wait home screen.
5. Search attack sequence.
6. Guard: wait battle-ready screen.
7. OCR loot filter; reroll until thresholds pass or policy exits.
8. Deploy (alignment + troops/heroes/spells).
9. Surrender (go-home guarded).
10. Post-battle optional `okay*.png` handling.
11. Record attack count and update Telegram attack log.
12. Periodic storage monitor.
13. Optional wall key cycle trigger.
14. Repeat.

## 4. Stable parts (currently strong)

- Core loop now has broad exception recovery path (`unexpected_exception` -> restart game).
- Recovery watchdog has multiple signals (black screen + error templates + stale/no-progress/timeout).
- Guard waits now emit explicit failure reason (`guard_retry_limit`, `guard_timeout`) used by recovery.
- Account switcher is practical: coordinate-first switching is stable for known accounts; template fallback retained.
- Bot2 ADB architecture is modular and supports background operation without active desktop focus.

## 5. Weak parts / risks

1. `check_storages_full.counter` is independent from `runtime_state.attack_count`; dual counters can diverge in edge cases.
2. OCR module (`gold_filter.py`) is complex and stateful; quality depends heavily on region tuning and template bank drift.
3. `storage_monitor.py` uses internal helpers from `gold_filter` (`_fmt_candidates`, `_fmt_raw`), creating hidden coupling.
4. Recovery notifications are chat-level side effects from multiple paths; race/duplication is possible under rapid repeated failures.
5. `account_switcher.py` still mixes two paradigms (coordinate and template) without explicit strategy flags; debugging can be noisy.
6. Bot2 and core bot share global desktop input when both pyautogui modes run; contention risk exists if run simultaneously.

## 6. Missing validations / gaps

- No explicit health assertion after game restart (only timed waits); missing strong post-restart state contract.
- No schema validation for critical config tuples (`region`, click points, fallback regions) at startup.
- No integration-level “dry-run” harness for OCR and account switching with deterministic fixtures.
- No bounded retry policy in some secondary loops (e.g., certain bot2 loops depend only on external screens, not stage watchdog).
- No single “runtime mode lock” preventing accidental simultaneous start of conflicting pyautogui bots.

## 7. Recommended next actions for future agents

1. Add startup config validator (`regions`, key names, account points, required images) and fail-fast before loop starts.
2. Replace dual counters with one authoritative attack counter source.
3. Decouple `storage_monitor.py` from private `gold_filter` helpers.
4. Add structured event log (`jsonl`) for recovery and OCR decisions to diagnose skipped-million cases quickly.
5. Add run-mode guard to prevent concurrent foreground pyautogui bots.
6. For OCR stability: promote fixture-based regression checks for top 20 problematic loot screenshots.

## 8. Quick operator summary (RU)

- Основной бот работает по циклу: база -> поиск -> бой -> фильтр лута -> высадка -> сдача -> возврат.
- Модуль восстановления уже перезапускает игру при черном экране, ошибочных экранах и затыках в guards.
- Переключение аккаунтов надежнее в режиме координат, fallback по картинкам оставлен.
- Самая чувствительная часть по качеству — OCR лута и точность регионов.
- Bot2 ADB — правильный путь для фоновой работы без захвата основного экрана.
