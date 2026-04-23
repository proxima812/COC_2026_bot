---
name: python-aiogram-control-bot
description: Work on the aiogram Telegram control bot for this repository, including commands, callbacks, single-message panel updates, permissions, and operator-facing control flows.
---

# Goal
Keep Telegram control reliable and understandable for the operator.

# Use This Skill When
- editing `telegram_control_aiogram.py`
- changing the control panel UI, callback routing, or command behavior
- touching message cleanup, access control, or status rendering

# Repo Conventions
- control UI is centered around one editable panel message
- runtime-side notifications also go through Telegram, but not always through the same chat context
- operator actions can trigger real bot side effects, so guard rails matter

# Rules
- preserve the single-panel interaction model unless the task explicitly changes it
- keep handler functions thin where possible
- validate allowed chat access before executing operator actions
- avoid mixing long-running bot actions directly into callback handlers unless there is no safer seam
- make control text explicit; ambiguity is operational debt

# Workflow
1. Read the affected callback or command and the presentation helper it uses.
2. Check how message IDs are stored in `runtime_state.py`.
3. Verify cleanup behavior for stop, cancel, and restart paths.
4. Keep UI rendering separate from process control decisions.
5. If notifications and control chat routing diverge, call it out.

# Output
- focused aiogram change or audit notes
- affected control flow
- operator-visible behavior change, if any
