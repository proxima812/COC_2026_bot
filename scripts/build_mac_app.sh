#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
DIST_DIR="$PROJECT_DIR/dist"
APP_NAME="${APP_NAME:-COC Bot Control}"
APP_PATH="$DIST_DIR/$APP_NAME.app"
APPLESCRIPT_PATH="$PROJECT_DIR/macos/coc_bot_control_launcher.applescript"
TMP_SCRIPT="$(mktemp)"

fatal() {
  printf '[build app] error: %s\n' "$*" >&2
  exit 1
}

command -v osacompile >/dev/null 2>&1 || fatal "osacompile not found"
[[ -f "$PROJECT_DIR/scripts/launch_control_app.sh" ]] || fatal "missing launch_control_app.sh"
[[ -f "$APPLESCRIPT_PATH" ]] || fatal "missing AppleScript source: $APPLESCRIPT_PATH"

mkdir -p "$DIST_DIR"
rm -rf "$APP_PATH"

trap 'rm -f "$TMP_SCRIPT"' EXIT
sed "s|__PROJECT_DIR__|$PROJECT_DIR|g" "$APPLESCRIPT_PATH" > "$TMP_SCRIPT"
osacompile -o "$APP_PATH" "$TMP_SCRIPT"

printf '[build app] created: %s\n' "$APP_PATH"
open "$DIST_DIR" >/dev/null 2>&1 || true
