---
name: python-recovery-watchdog
description: Work on automated recovery, watchdog logic, stale-screen detection, error-template recovery, and restart policies in this bot project.
---

# Goal
Improve recovery confidence without making the bot flap or restart too aggressively.

# Use This Skill When
- editing `recovery_watchdog.py`
- changing heartbeat stages or issue detection in `bot.py`
- reviewing black-screen, stale-screen, timeout, or error-template handling

# Rules
- preserve rate limiting for recovery attempts
- keep issue detection and recovery actions conceptually separate
- treat false positives as high-cost regressions
- prefer explicit issue codes and operator-visible telemetry
- reuse `runtime_state.py` and `telegram_reporter.py` instead of creating ad hoc tracking

# Workflow
1. Identify which issue codes can fire and from where.
2. Check sampling cadence, thresholds, and recovery rate limits.
3. Verify that the main loop updates heartbeat stages consistently.
4. Ensure Telegram notifications reflect the actual action taken.
5. Prefer small threshold or sequencing fixes over large policy rewrites.

# Output
- recovery risk or fix summary
- affected issue codes and stages
- any threshold that may need field calibration
