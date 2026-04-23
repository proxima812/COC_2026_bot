---
name: python-tests-pytest
description: Create and improve focused pytest coverage for Python bot logic that can be tested without a real emulator, ADB device, or desktop GUI.
---

# Goal
Add useful tests without forcing end-to-end automation into unit tests.

# Use This Skill When
- fixing pure logic in `runtime_state.py`, config parsing, formatting helpers, or controller logic
- adding regression coverage for OCR parsing, state transitions, or small runtime helpers
- validating bug fixes that do not require real `pyautogui` or live Telegram network calls

# Rules
- use pytest
- test behavior, not implementation details
- mock `pyautogui`, subprocess, and Telegram I/O at the boundary
- prefer fixture data from saved screenshots or payloads when useful
- do not invent a large test harness if a small monkeypatch is enough

# Workflow
1. Identify the narrowest testable unit.
2. Keep emulator, GUI, and network side effects mocked.
3. Cover success path, failure path, and one edge case.
4. Run only the relevant tests first.
5. If the code is hard to test, suggest a small seam instead of over-mocking.

# Good Targets In This Repo
- `runtime_state.py`
- `bot_config_schema.py`
- parsing or formatting helpers in Telegram UI modules
- detector/config helpers in `bot2_runtime/*` and `bot2_adb_runtime/*`

# Output
- test file changes
- what behavior is covered
- any remaining untestable seam worth isolating later
