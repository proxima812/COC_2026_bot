#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/Users/samgold/Desktop/Проекты/coc_bots/coc_bot_work-v}"
STOP_WAIT_SECONDS="${STOP_WAIT_SECONDS:-8}"

log() {
  printf '[stop] %s\n' "$*"
}

pid_alive() {
  local pid="$1"
  kill -0 "$pid" >/dev/null 2>&1
}

terminate_pids() {
  local signal="$1"
  shift
  local pid
  for pid in "$@"; do
    kill "-$signal" "$pid" >/dev/null 2>&1 || true
  done
}

all_pids=()
while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  all_pids+=("$pid")
done < <(pgrep -f "$PROJECT_DIR/telegram_control.py" 2>/dev/null || true)

while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  all_pids+=("$pid")
done < <(pgrep -f "$PROJECT_DIR/telegram_control_aiogram.py" 2>/dev/null || true)

while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  all_pids+=("$pid")
done < <(pgrep -f "$PROJECT_DIR/bot.py" 2>/dev/null || true)

while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  all_pids+=("$pid")
done < <(pgrep -f "$PROJECT_DIR/bot2.py" 2>/dev/null || true)

while IFS= read -r pid; do
  [[ -n "$pid" ]] || continue
  all_pids+=("$pid")
done < <(pgrep -f "$PROJECT_DIR/bot2_adb.py" 2>/dev/null || true)

if (( ${#all_pids[@]} == 0 )); then
  log "no running bot processes found"
  exit 0
fi

log "stopping processes: ${all_pids[*]}"
terminate_pids TERM "${all_pids[@]}"

deadline=$(( $(date +%s) + STOP_WAIT_SECONDS ))
while (( $(date +%s) < deadline )); do
  alive=()
  for pid in "${all_pids[@]}"; do
    if pid_alive "$pid"; then
      alive+=("$pid")
    fi
  done

  if (( ${#alive[@]} == 0 )); then
    log "all bot processes stopped"
    exit 0
  fi

  sleep 1
done

alive=()
for pid in "${all_pids[@]}"; do
  if pid_alive "$pid"; then
    alive+=("$pid")
  fi
done

if (( ${#alive[@]} > 0 )); then
  log "force stopping remaining processes: ${alive[*]}"
  terminate_pids KILL "${alive[@]}"
fi

log "bot processes stopped"
