#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v}"
ZSHRC_PATH="${ZSHRC_PATH:-$HOME/.zshrc}"
START_MARKER="# >>> coc-bot-run >>>"
END_MARKER="# <<< coc-bot-run <<<"

fatal() {
  printf '[install run] error: %s\n' "$*" >&2
  exit 1
}

[[ -d "$PROJECT_DIR" ]] || fatal "project directory not found: $PROJECT_DIR"
[[ -f "$PROJECT_DIR/scripts/run_bot.sh" ]] || fatal "missing script: $PROJECT_DIR/scripts/run_bot.sh"
[[ -f "$PROJECT_DIR/scripts/run_bot2.sh" ]] || fatal "missing script: $PROJECT_DIR/scripts/run_bot2.sh"
[[ -f "$PROJECT_DIR/scripts/run_bot2_adb.sh" ]] || fatal "missing script: $PROJECT_DIR/scripts/run_bot2_adb.sh"
[[ -f "$PROJECT_DIR/scripts/run_farm.sh" ]] || fatal "missing script: $PROJECT_DIR/scripts/run_farm.sh"
[[ -f "$PROJECT_DIR/scripts/run_tg.sh" ]] || fatal "missing script: $PROJECT_DIR/scripts/run_tg.sh"
[[ -f "$PROJECT_DIR/scripts/stop_bot.sh" ]] || fatal "missing script: $PROJECT_DIR/scripts/stop_bot.sh"

mkdir -p "$(dirname "$ZSHRC_PATH")"
[[ -f "$ZSHRC_PATH" ]] || : > "$ZSHRC_PATH"

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

awk -v start="$START_MARKER" -v end="$END_MARKER" '
  $0 == start {skip=1; next}
  $0 == end {skip=0; next}
  skip != 1 {print}
' "$ZSHRC_PATH" > "$TMP_FILE"

cat >> "$TMP_FILE" <<EOF2
$START_MARKER
run() {
  local project_dir="$PROJECT_DIR"

  if [ "\$#" -lt 1 ]; then
    echo "Usage: run {bot|2|2-adb|tg|farm|stop} [flags]"
    return 1
  fi

  case "\$1" in
    bot)
      shift
      "\$project_dir/scripts/run_bot.sh" "\$@"
      ;;
    2)
      shift
      "\$project_dir/scripts/run_bot2.sh" "\$@"
      ;;
    2-adb)
      shift
      "\$project_dir/scripts/run_bot2_adb.sh" "\$@"
      ;;
    tg)
      shift
      "\$project_dir/scripts/run_tg.sh" "\$@"
      ;;
    farm)
      "\$project_dir/scripts/run_farm.sh"
      ;;
    stop)
      "\$project_dir/scripts/stop_bot.sh"
      ;;
    *)
      echo "Usage: run {bot|2|2-adb|tg|farm|stop} [flags]"
      return 1
      ;;
  esac
}

stop() {
  local project_dir="$PROJECT_DIR"
  "\$project_dir/scripts/stop_bot.sh"
}
$END_MARKER
EOF2

mv "$TMP_FILE" "$ZSHRC_PATH"
trap - EXIT

printf '[install run] installed command block into %s\n' "$ZSHRC_PATH"
printf '[install run] reload shell: source %s\n' "$ZSHRC_PATH"
printf '[install run] commands: run bot | run bot -test | run 2 | run 2-adb | run tg | run tg -test | run farm | run stop | stop\n'
