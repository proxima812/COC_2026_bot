#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/rollback_to_tag.sh <tag> [--mode revert|hard] [--push]

Modes:
  revert  create a history-preserving revert commit from <tag>..HEAD
  hard    hard-reset the current branch to <tag>
EOF
}

[[ $# -ge 1 ]] || { usage >&2; exit 1; }

tag_name="$1"
shift
mode="revert"
push_after="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      [[ $# -ge 2 ]] || { echo "error: --mode requires a value" >&2; exit 1; }
      mode="$2"
      shift 2
      ;;
    --push)
      push_after="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

git rev-parse --verify "$tag_name" >/dev/null 2>&1 || {
  echo "error: tag not found: $tag_name" >&2
  exit 1
}

branch_name="$(git rev-parse --abbrev-ref HEAD)"

case "$mode" in
  revert)
    git revert --no-edit "${tag_name}..HEAD"
    ;;
  hard)
    git reset --hard "$tag_name"
    ;;
  *)
    echo "error: unsupported mode: $mode" >&2
    exit 1
    ;;
esac

if [[ "$push_after" == "true" ]]; then
  if [[ "$mode" == "hard" ]]; then
    git push --force-with-lease origin "$branch_name"
  else
    git push origin "$branch_name"
  fi
fi

echo "rollback complete: mode=$mode tag=$tag_name branch=$branch_name"
