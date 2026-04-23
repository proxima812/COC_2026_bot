#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PANEL_HOST="${PANEL_HOST:-127.0.0.1}"
PANEL_PORT="${PANEL_PORT:-8765}"
PANEL_URL="http://$PANEL_HOST:$PANEL_PORT"
LOG_DIR="$PROJECT_DIR/.runtime"
LOG_FILE="$LOG_DIR/control_panel.log"

mkdir -p "$LOG_DIR"

panel_running() {
  pgrep -f "$PROJECT_DIR/control_panel.py" >/dev/null 2>&1
}

start_panel() {
  nohup bash "$PROJECT_DIR/scripts/run_panel.sh" >>"$LOG_FILE" 2>&1 &
}

if ! panel_running; then
  start_panel
  sleep 1
fi

if command -v open >/dev/null 2>&1; then
  open "$PANEL_URL" >/dev/null 2>&1 || true
fi
