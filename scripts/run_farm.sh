#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v}"

fatal() {
  printf '[run farm] error: %s\n' "$*" >&2
  exit 1
}

command -v python3 >/dev/null 2>&1 || fatal "required command not found: python3"
[[ -d "$PROJECT_DIR" ]] || fatal "project directory not found: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/bot.py" ]] || fatal "bot.py not found in: $PROJECT_DIR"

printf '[run farm] starting bot.py\n'
cd "$PROJECT_DIR"
exec python3 bot.py
