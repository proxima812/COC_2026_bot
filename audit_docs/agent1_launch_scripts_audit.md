# Agent 1 Audit: Launch Scripts

## Scope
- Checked only launch/stop/install scripts:
  - `scripts/install_run_command.sh`
  - `scripts/run_bot.sh`
  - `scripts/run_tg.sh`
  - `scripts/run_bot2.sh`
  - `scripts/run_bot2_adb.sh`
  - `scripts/run_farm.sh`
  - `scripts/stop_bot.sh`
  - `scripts/run_bot.bat`
  - `scripts/run_farm.bat`
  - `scripts/stop_bot.bat`

## Read-only checks performed
- `bash -n` syntax check for all `.sh` scripts: **PASS**.
- Static consistency review of command routing and process stop behavior.

## Command routing coverage (`run ...`)
Defined in `scripts/install_run_command.sh`:
- `run bot` -> `scripts/run_bot.sh`
- `run tg` -> `scripts/run_tg.sh`
- `run 2` -> `scripts/run_bot2.sh`
- `run 2-adb` -> `scripts/run_bot2_adb.sh`
- `run farm` -> `scripts/run_farm.sh`
- `run stop` -> `scripts/stop_bot.sh`
- `stop` alias -> `scripts/stop_bot.sh`

Usage text matches supported subcommands.

## Findings (ordered by severity)

### 1. [High] `stop_bot.bat` does not stop `bot2.py` / `bot2_adb.py`
- File: `scripts/stop_bot.bat`
- Current WMIC/taskkill filters only include:
  - `telegram_control_aiogram.py`
  - `telegram_control.py`
  - `bot.py`
- Result on Windows: `run 2` and `run 2-adb` can remain alive after `run stop` / `stop`.

### 2. [Medium] `run_bot2_adb.sh` has no preflight checks
- File: `scripts/run_bot2_adb.sh`
- It directly `exec python3 bot2_adb.py` without verifying:
  - `python3` existence
  - project dir existence
  - `bot2_adb.py` existence
- Risk: poorer failure diagnostics compared to other launch scripts.

### 3. [Medium] macOS stop uses broad `pgrep -f` patterns
- File: `scripts/stop_bot.sh`
- It matches by command-line substring of script path.
- Usually fine, but can overmatch if unrelated processes contain same path segments.

### 4. [Low] `run_bot.sh` hardcodes macOS defaults
- File: `scripts/run_bot.sh`
- Defaults assume macOS app paths and `open` command.
- This is acceptable for current environment but not portable by default.

## What is consistent and good
- Shell scripts are syntactically valid.
- `run` function install/update flow in `~/.zshrc` is deterministic and idempotent (marker-based replace).
- `run bot` supports `-test/--test` and passes UI mode via env.
- `run tg` starts Telegram control only (no emulator startup), as intended.
- `stop_bot.sh` handles graceful TERM then KILL fallback with wait window.

## PID/process behavior assessment
- macOS/Linux path (`stop_bot.sh`):
  - Stops all main Python entrypoints used in this repo (`telegram_control*`, `bot.py`, `bot2.py`, `bot2_adb.py`).
  - Graceful then forced stop logic is correct.
- Windows path (`stop_bot.bat`):
  - Missing `bot2.py` and `bot2_adb.py` process patterns.
  - Not equivalent to macOS stop behavior.

## Environment assumptions
- `run_bot.sh` assumes:
  - macOS (`open`, BlueStacks app bundle path)
  - executable ADB path.
- `run_tg.sh` is environment-light (only `python3`, project files).
- `.bat` scripts assume:
  - Windows + BlueStacks default install paths.

## Recommended minimal fixes (for next agent)
1. Update `scripts/stop_bot.bat` WMIC filters to include `bot2.py` and `bot2_adb.py`.
2. Add preflight checks to `scripts/run_bot2_adb.sh` (same style as `run_bot2.sh`).
3. Optional hardening: make `stop_bot.sh` deduplicate PID list before kill calls.

## Overall status
- Launch command topology is coherent and usable.
- Primary cross-platform gap is Windows stop coverage for secondary bots.
