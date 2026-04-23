#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"

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
