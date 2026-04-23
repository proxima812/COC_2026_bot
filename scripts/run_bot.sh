#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v}"
TELEGRAM_CONTROL_BACKEND="${TELEGRAM_CONTROL_BACKEND:-aiogram}"
TELEGRAM_UI_MODE="${TELEGRAM_UI_MODE:-default}"
BLUESTACKS_APP_NAME="${BLUESTACKS_APP_NAME:-BlueStacks}"
BLUESTACKS_PROCESS_NAME="${BLUESTACKS_PROCESS_NAME:-BlueStacks}"
ADB_BIN="${ADB_BIN:-/Applications/BlueStacks.app/Contents/MacOS/hd-adb}"
COC_PACKAGE="${COC_PACKAGE:-com.supercell.clashofclans}"
EMULATOR_BOOT_TIMEOUT="${EMULATOR_BOOT_TIMEOUT:-240}"
APP_LAUNCH_WAIT="${APP_LAUNCH_WAIT:-8}"
ADB_CONNECT_PORTS="${ADB_CONNECT_PORTS:-5555 5556 5565 5575 5585}"
CLASH_LAUNCH_TIMEOUT="${CLASH_LAUNCH_TIMEOUT:-120}"

log() {
  printf '[run bot] %s\n' "$*"
}

warn() {
  printf '[run bot] warning: %s\n' "$*" >&2
}

fatal() {
  printf '[run bot] error: %s\n' "$*" >&2
  exit 1
}

while [[ "${1:-}" == -* ]]; do
  case "$1" in
    -test|--test)
      TELEGRAM_UI_MODE="test"
      shift
      ;;
    *)
      fatal "unknown flag: $1"
      ;;
  esac
done

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fatal "required command not found: $1"
}

has_adb_device() {
  "$ADB_BIN" devices 2>/dev/null | awk 'NR>1 && $2=="device" {found=1} END {exit(found?0:1)}'
}

try_prepare_adb() {
  "$ADB_BIN" start-server >/dev/null 2>&1 || true
  local port
  for port in $ADB_CONNECT_PORTS; do
    "$ADB_BIN" connect "127.0.0.1:${port}" >/dev/null 2>&1 || true
  done
}

is_clash_running() {
  local pid_output
  pid_output="$($ADB_BIN shell pidof "$COC_PACKAGE" 2>/dev/null | tr -d '\r' || true)"
  [[ "$pid_output" =~ [0-9] ]]
}

wait_for_adb_device() {
  local timeout="$1"
  local deadline=$(( $(date +%s) + timeout ))

  while (( $(date +%s) < deadline )); do
    if has_adb_device; then
      return 0
    fi
    sleep 2
  done

  return 1
}

launch_clash() {
  local launched=0
  local deadline=$(( $(date +%s) + CLASH_LAUNCH_TIMEOUT ))

  while (( $(date +%s) < deadline )); do
    if is_clash_running; then
      log "Clash of Clans is already running, skip app launch"
      return 0
    fi

    try_prepare_adb

    if "$ADB_BIN" shell monkey -p "$COC_PACKAGE" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1; then
      log "Clash of Clans launch request sent via adb: $COC_PACKAGE"
      launched=1
    fi

    open -a "$BLUESTACKS_APP_NAME" "bluestacksgp://runapp?package=$COC_PACKAGE" >/dev/null 2>&1 || true
    open -a "$BLUESTACKS_APP_NAME" "bluestacksgp://$COC_PACKAGE" >/dev/null 2>&1 || true

    sleep 3
    if is_clash_running; then
      log "Clash of Clans is running"
      return 0
    fi

    if (( launched == 1 )); then
      sleep 2
    fi
  done

  warn "failed to launch package '$COC_PACKAGE' within ${CLASH_LAUNCH_TIMEOUT}s (adb/url). continuing with telegram control backend"
  return 1
}

require_cmd python3
require_cmd open
require_cmd pgrep

[[ -x "$ADB_BIN" ]] || fatal "ADB binary not found or not executable: $ADB_BIN"
[[ -d "$PROJECT_DIR" ]] || fatal "project directory not found: $PROJECT_DIR"
if [[ "$TELEGRAM_CONTROL_BACKEND" == "aiogram" ]]; then
  [[ -f "$PROJECT_DIR/telegram_control_aiogram.py" ]] || fatal "telegram_control_aiogram.py not found in: $PROJECT_DIR"
else
  [[ -f "$PROJECT_DIR/telegram_control.py" ]] || fatal "telegram_control.py not found in: $PROJECT_DIR"
fi

if ! pgrep -x "$BLUESTACKS_PROCESS_NAME" >/dev/null 2>&1; then
  log "starting $BLUESTACKS_APP_NAME..."
  open -a "$BLUESTACKS_APP_NAME" || fatal "failed to open app: $BLUESTACKS_APP_NAME"
else
  log "$BLUESTACKS_APP_NAME is already running"
fi

log "waiting for emulator adb device (timeout ${EMULATOR_BOOT_TIMEOUT}s)..."
try_prepare_adb
if wait_for_adb_device "$EMULATOR_BOOT_TIMEOUT"; then
  log "adb device is ready"
else
  warn "adb device did not appear within ${EMULATOR_BOOT_TIMEOUT}s; continue without strict adb readiness"
fi

launch_clash || true
sleep "$APP_LAUNCH_WAIT"

log "starting telegram control bot"
cd "$PROJECT_DIR"
export TELEGRAM_UI_MODE
if [[ "$TELEGRAM_CONTROL_BACKEND" == "aiogram" ]]; then
  exec python3 telegram_control_aiogram.py
fi
exec python3 telegram_control.py
