---
name: python-asyncio-debug
description: Debug asyncio issues in this project, especially aiogram callbacks, background tasks, cancellation, and blocking synchronous work inside async control flows.
---

# Goal
Find and fix async control bugs without destabilizing bot operations.

# Use This Skill When
- working in `telegram_control_aiogram.py`
- investigating stuck callbacks, leaked tasks, cancellation bugs, or race conditions
- reviewing background scenarios such as fill-storages flows

# Main Risks In This Repo
- synchronous GUI or subprocess work inside async handlers
- module-global task ownership
- bot state split between in-memory task references and `runtime_state.py`
- callbacks editing the same Telegram message concurrently

# Rules
- do not convert everything to async for style reasons
- isolate blocking work behind small helpers or executors only when necessary
- make cancellation paths explicit
- persist operator-visible long-lived scenario state when restart resilience matters

# Workflow
1. Identify task owner, lifecycle, and cancellation path.
2. Check whether work inside async handlers blocks the event loop.
3. Verify whether state survives process restart when operators expect it to.
4. Fix the narrowest task/control boundary first.
5. Re-check message update and cleanup behavior after cancellation or failure.

# Output
- async bug or risk summary
- smallest safe fix
- residual risk if the flow still depends on foreground GUI automation
