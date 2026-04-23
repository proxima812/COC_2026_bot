# Agent 2 Telegram Audit

## Scope
Inspected only:
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_control_aiogram.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_ui/presentation.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_ui/process_controller.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_reporter.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/runtime_state.py` (Telegram-related state)

No code changes outside this report.

## Current Functional Coverage

### Commands (message handlers)
- `/start`, `/status`, `/run`, `/stop`
- `/config`, `/shots`
- `/recovery_debug`, `/screenshot`, `/console`
- `/spell_stonedick`, `/spell_crazywalls`
- `/input_default`, `/wall`

### Panel flows (inline callbacks)
- Root/status panel rendering with single editable message (`telegram_control_message_id`).
- Menus: `control`, `spells`, `input`, `config_root`, `config_cat:*`, `accounts`.
- Action callbacks:
  - start/stop bot process
  - screenshot, console toggle
  - wall cycle toggle and period input
  - ADB game close/return
  - config toggle/edit flows
  - account pick flow
  - fill-storages scenario start

### Message deletion behavior
- Incoming command/text messages are scheduled for deletion after `MESSAGE_AUTO_DELETE_SECONDS`.
- Stop cleanup removes:
  - attack log message
  - console message
  - battle screenshot messages

### Controller interactions
- Uses `BotProcessController` (`telegram_ui/process_controller.py`) for `bot.py` process lifecycle.
- `start()` launches `bot.py` in new session (non-Windows path), stores PID file.
- `stop()` terminates process/session and clears PID file.
- Exit watcher updates panel if process exits unexpectedly.

### Account switching integration
- `menu_accounts` triggers current-account detection.
- `account_pick:*` path:
  - stop running bot if needed
  - run `account_switcher.switch_account(name)`
  - persist `current_account`
  - update panel text

### Fill-storages scenario
- Triggered by callback `fill_storages_everywhere`.
- Scenario logic:
  1. disable wall cycle override
  2. iterate configured accounts
  3. switch account
  4. start bot process
  5. wait until `attack_count >= attacks_per_account`
  6. stop process and report per-account completion
  7. after all accounts: force-stop game and notify done
- Uses one in-memory task: `fill_storages_everywhere_task`.

## State Model (Telegram-related)
Stored in `.bot_runtime_state.json` via `runtime_state.py`:
- Panel and pending input:
  - `telegram_panel_view`
  - `timing_pending_item_id`
- Message IDs:
  - `telegram_control_message_id`
  - `telegram_attack_log_message_id`
  - `telegram_console_message_id`
  - `telegram_battle_screenshot_message_ids`
- Feature flags/overrides used by TG:
  - `telegram_console_enabled`
  - `battle_report_every_override`
  - `wall_key_cycle_enabled_override`
  - `wall_key_cycle_every_override`
- Account/recovery display:
  - `current_account`
  - `last_recovery_*`

## Concrete Findings / Risks

### P1: Duplicate function definitions in Telegram controller
File: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_control_aiogram.py`
- `async def _run_fill_storages_everywhere(...)` appears duplicated consecutively.
- `async def cmd_input_default(...)` appears duplicated consecutively.

Impact:
- Runtime uses the last definition, so behavior may still work, but this is merge-noise and a maintainability risk.
- Increases chance of future edits targeting wrong copy.

Recommendation:
- Remove duplicate declarations and keep single canonical definitions.

### P1: Inconsistent chat target between aiogram UI and reporter utility
Files:
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_control_aiogram.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_reporter.py`

Details:
- UI handlers use `allowed_chat_ids` and current chat context.
- `telegram_reporter.send_*` uses `TELEGRAM_CHAT_ID` from config directly.

Impact:
- Notifications/screenshots may be sent to a different chat than control panel chat.
- Multi-chat or whitelist scenarios become inconsistent.

Recommendation:
- Unify chat-target policy: either single source of truth or explicit routing parameter.

### P2: Fill-storages task lifecycle is in-memory only
File: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_control_aiogram.py`

Details:
- `fill_storages_everywhere_task` is a module-global asyncio task.
- If TG bot process restarts, scenario state is lost.

Impact:
- No resume/recovery for long multi-account workflow.

Recommendation:
- Persist scenario state (current account index, target attacks, started_at, running flag) in `runtime_state`.

### P2: Blocking sync operations inside async handlers
Files:
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_control_aiogram.py`
- `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/account_switcher.py` (called synchronously)

Details:
- Heavy operations (account switching, ADB routines, screenshots) run sync within async callbacks.

Impact:
- Event loop stalls under slow operations.

Recommendation:
- Move long sync operations to executor/thread wrappers where practical.

### P3: Accounts menu includes `love12steps` while active operational flow focuses on 4 accounts
File: `/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v/telegram_ui/presentation.py`

Impact:
- Potential operator confusion vs configured fill-storages sequence.

Recommendation:
- Align visible menu with active operational set or mark non-used accounts explicitly.

## Stability Notes
- Core panel pattern (single editable message + view state) is solid and reduces spam.
- Incoming message auto-deletion is implemented and consistent for command/text handlers.
- Stop-side cleanup is implemented correctly for generated TG artifacts.
- Process controller is minimal and predictable for single-process management.

## Suggested Next Actions (for future agent)
1. Remove duplicate function declarations in `telegram_control_aiogram.py`.
2. Consolidate chat destination logic between aiogram handlers and `telegram_reporter`.
3. Persist fill-storages scenario state in `runtime_state` and add resume/cancel robustness.
4. Move blocking account/ADB operations off the event loop in callbacks.
5. Align accounts UI with actual active account policy.
