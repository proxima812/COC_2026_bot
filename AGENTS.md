# AGENTS.md

## Role
You are the project coding agent for this repository.
Your job is to make precise, minimal, production-ready changes without breaking existing behavior.

## Project Context
- Stack: Python, aiogram, pyautogui, ADB, image-based automation
- Main entry points: `bot.py`, `telegram_control_aiogram.py`, `bot2.py`, `bot2_adb.py`
- Shared persistent operator state: `runtime_state.py`
- Main runtime slices: `attack_runtime/*`, `bot_runtime/*`, `bot2_runtime/*`, `bot2_adb_runtime/*`
- Telegram UI flow: `telegram_control_aiogram.py`, `telegram_ui/*`, `telegram_reporter.py`

## Primary Workflow
At the start of every new session, do this before making changes:

1. Read this file fully.
2. Read `MEMORY.md` if it exists.
3. Read the most recent file in `memory/` if it exists.
4. Read project docs directly relevant to the task.
5. Inspect the current code before planning or editing.

If previous session context exists in markdown files, treat it as useful context, but trust the current repository state as final authority.

## Memory Rules
Use these files as persistent context between sessions:

- `MEMORY.md` — stable long-term project memory
- `memory/YYYY-MM-DD.md` — short-term session logs
- `TASKS.md` — optional active tasks and next steps
- `DECISIONS.md` — optional architecture and product decisions

### `MEMORY.md` should contain only
- stable project rules
- architecture constraints
- stack decisions
- coding conventions
- important business logic
- recurring pitfalls
- reusable knowledge that should persist across sessions

Do not put temporary notes or speculative ideas into `MEMORY.md`.

### `memory/YYYY-MM-DD.md` should contain
- what was done in the session
- files changed
- why changes were made
- unresolved issues
- next recommended steps
- commands worth reusing
- test or validation results

## Session Behavior
When a new task starts:

1. Check whether relevant context already exists in `MEMORY.md` or the latest `memory/*.md`.
2. Briefly summarize relevant remembered context internally.
3. Continue using the current codebase as the final source of truth.
4. If docs conflict with code, trust code and update docs only when the task requires it.

## End-Of-Session Behavior
Before finishing any meaningful task:

1. Update or create today's file in `memory/YYYY-MM-DD.md`.
2. Record:
   - summary of work
   - changed files
   - important decisions
   - known issues
   - next steps
   - validation performed or skipped
3. If a lesson is long-term and reusable, also update `MEMORY.md`.
4. Keep memory concise and deduplicated.

## Project Constraints
- Prefer minimal diffs.
- Preserve existing naming, structure, and runtime behavior unless the task explicitly changes behavior.
- Keep orchestration separate from low-level screen, OCR, ADB, and Telegram primitives.
- Reuse existing config and `runtime_state.py` patterns before adding new state storage.
- Keep Telegram handlers thin where practical.
- Avoid broad rewrites unless explicitly requested.
- Never invent completed work.
- Never claim tests passed unless they were actually run.
- Never store secrets, tokens, passwords, or private keys in memory files.

## Coding Standards
- Keep code clean, readable, and production-ready.
- Avoid unnecessary abstractions.
- Prefer explicitness over cleverness.
- Keep naming consistent with the repository.
- When changing behavior, update relevant docs if needed.
- When fixing a bug, document the root cause in the session log.

## Task-Specific Reading Hints
If context is missing, inspect the smallest relevant set of files first:

- `DOCUMENTATION.md`
- `SPECIFICATION.md`
- `audit_docs/*` for previous audit findings
- `config.py`
- `runtime_state.py`
- relevant entry points and feature modules

## Definition Of Done
A task is complete only when all of the following are true:

- the requested change is implemented
- affected files are coherent
- obvious regressions were checked at an appropriate level
- docs and memory were updated if needed
- next steps are recorded if anything remains open
