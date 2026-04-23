# Project Memory

## Stable Rules
- Keep changes minimal and behavior-preserving unless the task explicitly changes behavior.
- Prefer editing the smallest relevant module instead of broad rewrites.
- Use `runtime_state.py` as the shared lightweight persistent state layer for operator-facing bot state.
- Keep Telegram UI concerns separated from low-level runtime side effects where possible.

## Stack And Runtime
- Primary stack: Python, aiogram, pyautogui, ADB, image-based automation.
- Main entry points: `bot.py`, `telegram_control_aiogram.py`.
- Preferred operator interface: local web control panel via `control_panel.py`.
- Main bot loop lives in `bot.py`.
- Telegram control panel lives in `telegram_control_aiogram.py`.
- Runtime modules are split across `attack_runtime/*` and `bot_runtime/*`.

## Important Business Logic
- The main farming loop waits for home, searches for a target, validates battle-ready state, filters loot, deploys, surrenders, returns home, increments attack count, and periodically checks storages.
- Recovery behavior is handled through `recovery_watchdog.py` with issue detection, staged heartbeats, and Telegram notifications.
- Storage monitoring and loot OCR are operationally important but sensitive to screenshot quality and OCR noise.

## Recurring Pitfalls
- `telegram_control_aiogram.py` is a complexity hotspot because it mixes async callbacks, runtime process control, and GUI-side effects.
- Operator-visible long-running scenarios should not rely only on in-memory task globals if restart resilience matters.
- Telegram notifications can diverge from the active control chat because `telegram_reporter.py` uses configured chat routing.
- `storage_monitor.py` currently depends on private helpers from `gold_filter.py`, which is hidden coupling.
- OCR-related behavior is sensitive to image region quality, scaling, and noise, so threshold tweaks should be narrow and validated carefully.

## Useful Docs
- `DOCUMENTATION.md` for the current high-level project overview
- `SPECIFICATION.md` for deeper functional expectations
- `audit_docs/MASTER_AUDIT_SUMMARY.md` for previously identified risks and work order
