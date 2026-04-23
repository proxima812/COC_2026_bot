---
name: python-bot-architecture
description: Review and improve the architecture of this Python bot project with focus on loop orchestration, runtime modules, Telegram control boundaries, and state ownership.
---

# Goal
Keep the bot maintainable while preserving behavior.

# Use This Skill When
- changing `bot.py`, `attack.py`, `attack_runtime/*`, `bot2_runtime/*`, or `bot2_adb_runtime/*`
- moving logic between loop orchestration, runtime helpers, and side-effect code
- reducing coupling between Telegram control, runtime state, and bot execution
- deciding whether a refactor is worth the risk

# Repo Focus
- `bot.py` is the main orchestration loop
- `telegram_control_aiogram.py` is the control surface and has async/runtime coupling risk
- `runtime_state.py` is the shared persistence layer and should stay the single source of lightweight operator state
- `attack_runtime/*`, `bot_runtime/*`, `bot2_runtime/*`, `bot2_adb_runtime/*` are runtime slices and should own domain-specific behavior

# Rules
- preserve current observable behavior unless the task says otherwise
- prefer extracting helpers over broad rewrites
- separate orchestration from low-level actions
- avoid duplicating state in globals if `runtime_state.py` can own it
- call out hidden coupling explicitly before adding more

# Workflow
1. Read the entry module and the nearest helper modules it delegates to.
2. Mark what is orchestration, what is state, and what is side effect.
3. Keep edits inside the smallest layer that can solve the problem.
4. If a function mixes async control, subprocesses, and GUI actions, split only along those seams.
5. Prefer one source of truth for counters, flags, and current mode.

# Output
- minimal architectural change or review notes
- root cause of coupling or complexity
- follow-up refactor suggestions only if they clearly reduce operational risk
