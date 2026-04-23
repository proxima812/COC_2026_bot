---
name: python-screen-automation-pyautogui
description: Work on screen-based automation in this repository using pyautogui, image matching, search regions, retries, and safe GUI interaction patterns.
---

# Goal
Improve reliability of desktop automation without broad behavioral rewrites.

# Use This Skill When
- editing `attack_runtime/*`, `bot_runtime/screen_state.py`, `gold_filter.py`, `storage_monitor.py`, or `account_switcher.py`
- changing image-based detection, click flows, or retry logic
- reviewing screenshot-based failures or OCR sensitivity

# Rules
- prefer narrowing regions and thresholds over adding more blind retries
- keep image paths and confidence settings configurable through existing config patterns
- preserve failsafe behavior
- separate detection from action when possible
- use saved screenshots as regression references when available

# Workflow
1. Identify the exact detection or click primitive involved.
2. Check current region, confidence, retry count, and fallback behavior.
3. Change one sensitivity axis at a time.
4. If reliability depends on undocumented screenshots, note the missing artifact.
5. Prefer small helpers over duplicated locate/click loops.

# Output
- focused automation fix or reliability notes
- config knobs involved
- screenshots or regions that should be captured later for regression checks
