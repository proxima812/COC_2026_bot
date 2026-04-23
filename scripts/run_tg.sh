#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/Users/samgold/Desktop/Боты/Проекты/coc_bots/coc_bot_work-v}"
TELEGRAM_CONTROL_BACKEND="${TELEGRAM_CONTROL_BACKEND:-aiogram}"
TELEGRAM_UI_MODE="${TELEGRAM_UI_MODE:-default}"

fatal() {
  printf '[run tg] error: %s\n' "$*" >&2
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

command -v python3 >/dev/null 2>&1 || fatal "required command not found: python3"
[[ -d "$PROJECT_DIR" ]] || fatal "project directory not found: $PROJECT_DIR"
if [[ "$TELEGRAM_CONTROL_BACKEND" == "aiogram" ]]; then
  [[ -f "$PROJECT_DIR/telegram_control_aiogram.py" ]] || fatal "telegram_control_aiogram.py not found in: $PROJECT_DIR"
else
  [[ -f "$PROJECT_DIR/telegram_control.py" ]] || fatal "telegram_control.py not found in: $PROJECT_DIR"
fi

printf '[run tg] starting telegram bot only\n'
cd "$PROJECT_DIR"
export TELEGRAM_UI_MODE
if [[ "$TELEGRAM_CONTROL_BACKEND" == "aiogram" ]]; then
  exec python3 telegram_control_aiogram.py
fi
exec python3 telegram_control.py
