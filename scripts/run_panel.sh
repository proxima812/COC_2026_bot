#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PANEL_HOST="${PANEL_HOST:-127.0.0.1}"
PANEL_PORT="${PANEL_PORT:-8765}"

fatal() {
  printf '[run panel] error: %s\n' "$*" >&2
  exit 1
}

command -v python3 >/dev/null 2>&1 || fatal "required command not found: python3"
[[ -d "$PROJECT_DIR" ]] || fatal "project directory not found: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/control_panel.py" ]] || fatal "control_panel.py not found in: $PROJECT_DIR"

printf '[run panel] starting local control panel at http://%s:%s\n' "$PANEL_HOST" "$PANEL_PORT"
cd "$PROJECT_DIR"
export PANEL_HOST PANEL_PORT
python3 control_panel.py &
panel_pid=$!

sleep 1
if command -v open >/dev/null 2>&1; then
  open "http://$PANEL_HOST:$PANEL_PORT" >/dev/null 2>&1 || true
fi

wait "$panel_pid"
