#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v}"

log() {
  printf '[run 2] %s\n' "$*"
}

fatal() {
  printf '[run 2] error: %s\n' "$*" >&2
  exit 1
}

command -v python3 >/dev/null 2>&1 || fatal 'python3 not found'
[[ -d "$PROJECT_DIR" ]] || fatal "project directory not found: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/bot2.py" ]] || fatal "missing bot2.py in: $PROJECT_DIR"

log 'starting bot2'
cd "$PROJECT_DIR"
exec python3 bot2.py
