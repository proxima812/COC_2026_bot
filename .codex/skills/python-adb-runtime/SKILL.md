---
name: python-adb-runtime
description: Work on the ADB-based bot runtime in this repository, including taps, swipes, screencaps, reconnect logic, config validation, and device command reliability.
---

# Goal
Keep the ADB runtime predictable and easy to validate.

# Use This Skill When
- editing `bot2_adb_runtime/*`
- changing ADB command wrappers, screen coordinate config, or image/template checks
- reviewing startup validation, reconnect behavior, or command timeout issues

# Repo Focus
- `bot2_adb_runtime/config.py` defines most runtime geometry and timing
- `bot2_adb_runtime/adb.py`, `actions.py`, and `detector.py` should own low-level device behavior
- config validation should happen early and fail loudly

# Rules
- do not scatter new ADB command assembly across modules
- prefer config validation before runtime loops start
- keep geometry conversion logic centralized
- preserve timing knobs unless the task explicitly recalibrates them

# Workflow
1. Read config constants and the low-level ADB wrapper first.
2. Check command assembly, serial selection, and timeout handling.
3. Validate required points, swipes, templates, and image paths near startup.
4. Keep detector logic separate from gesture execution.
5. If a fix changes runtime timing, state the operational risk explicitly.

# Output
- minimal ADB/runtime change or audit note
- startup assumptions
- config items that should be validated automatically
