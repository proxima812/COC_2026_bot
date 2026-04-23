# AI Helper For Create Recovery Mod

## Goal
Create a separate recovery module for the main Clash of Clans bot that can detect game launch issues, bad connection states, black screens, and frozen states without mixing recovery logic into the main attack flow.

## Recommended structure

### 1. Dedicated recovery module
- Keep all error detection and recovery logic in a separate module.
- The main loop should only do:
  - detect issue
  - handle issue
  - continue loop

### 2. Detect these issue types
- Error templates on screen:
  - connection lost
  - reload screen
  - restart required
- Black screen:
  - low average brightness
  - high dark-pixel coverage
  - no expected UI found
- Stuck state:
  - no progress for too long on one stage
  - repeated loop without reaching home, battle, or go-home
- Unknown empty state:
  - multiple cycles where the bot cannot identify any expected screen

### 3. Recovery policy should be layered
Use escalation instead of one hard restart:

1. Soft recovery
- press `-`
- press `esc`
- short wait
- check if normal UI returns

2. Restart game only
- close Clash of Clans
- launch Clash again

3. Restart emulator
- only if several recovery attempts fail

### 4. Black screen logic
Recommended rule:
- capture screenshot
- measure average brightness
- measure percentage of very dark pixels
- confirm no normal UI templates are visible

Only classify as black screen when all those conditions align.

### 5. Template-based error detection
Use template folders such as:
- `images/errors/restart_game/*.png`
- `images/errors/restart_emulator/*.png`

This lets the module choose the recovery action directly.

### 6. Track loop stages
Maintain heartbeat stages such as:
- `home_ready`
- `searching`
- `battle_ready`
- `deploying`
- `post_battle`
- `recovering`

If the bot stays too long in one stage, classify that as stale / stuck.

### 7. Rate-limit recovery attempts
Prevent infinite recovery loops:
- maximum N attempts per time window
- example: max 6 attempts per hour

If the limit is exceeded:
- stop the bot
- notify in Telegram

### 8. Logging
Every recovery event should store:
- issue type
- issue details
- selected action
- timestamp

Also store:
- last issue
- last action
- count of recent attempts

### 9. Telegram debugging
Add a debug panel or command that shows:
- last recovery issue
- last recovery action
- attempts in the current rate window

### 10. Recommended implementation order
1. error-template detection
2. black-screen detection
3. stale-loop detection
4. restart-game action
5. restart-emulator action
6. Telegram status/debug

## Practical summary
The clean design is:
- separate recovery watchdog module
- clear issue classes
- layered recovery actions
- heartbeat-based stale detection
- Telegram logging and debugging

Do not spread this logic directly across `bot.py`.
