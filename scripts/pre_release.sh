#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  scripts/pre_release.sh [--tag TAG] [--push-tag]

What it does:
  - generates a pre-release markdown report in release_reports/
  - shows commits and file changes since the latest tag
  - optionally creates an annotated tag
  - optionally pushes that tag
EOF
}

require_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "error: not inside a git repository" >&2
    exit 1
  }
}

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

slug_now() {
  date -u +"%Y%m%d-%H%M%S"
}

report_dir="release_reports"
tag_name=""
push_tag="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      [[ $# -ge 2 ]] || { echo "error: --tag requires a value" >&2; exit 1; }
      tag_name="$2"
      shift 2
      ;;
    --push-tag)
      push_tag="true"
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

require_git_repo

mkdir -p "$report_dir"

branch_name="$(git rev-parse --abbrev-ref HEAD)"
head_commit="$(git rev-parse HEAD)"
head_short="$(git rev-parse --short HEAD)"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  range_ref="${latest_tag}..HEAD"
  compare_label="$latest_tag"
else
  root_commit="$(git rev-list --max-parents=0 HEAD | tail -n 1)"
  range_ref="$root_commit..HEAD"
  compare_label="repository-start"
fi

report_file="$report_dir/pre-release-$(slug_now).md"

{
  printf '# Pre-Release Report\n\n'
  printf -- '- Generated: `%s`\n' "$(timestamp_utc)"
  printf -- '- Branch: `%s`\n' "$branch_name"
  printf -- '- HEAD: `%s` (`%s`)\n' "$head_short" "$head_commit"
  printf -- '- Compared From: `%s`\n' "$compare_label"
  if [[ -n "$tag_name" ]]; then
    printf -- '- Planned Tag: `%s`\n' "$tag_name"
  fi
  printf '\n## Commit Summary\n\n'
  if git rev-list --count "$range_ref" >/dev/null 2>&1 && [[ "$(git rev-list --count "$range_ref")" -gt 0 ]]; then
    git log --reverse --format='- `%h` %s (%an, %ad)' --date=short "$range_ref"
  else
    printf -- '- No commits since `%s`\n' "$compare_label"
  fi
  printf '\n## Files Changed\n\n'
  if git rev-list --count "$range_ref" >/dev/null 2>&1 && [[ "$(git rev-list --count "$range_ref")" -gt 0 ]]; then
    printf '```text\n'
    git diff --stat "$range_ref"
    printf '```\n\n'
    printf '## Name-Status\n\n'
    printf '```text\n'
    git diff --name-status "$range_ref"
    printf '```\n'
  else
    printf 'No file changes since `%s`.\n' "$compare_label"
  fi

  printf '\n## Rollback\n\n'
  if [[ -n "$tag_name" ]]; then
    printf -- '- Safe history-preserving rollback after push: `git revert --no-edit %s..HEAD`\n' "$tag_name"
    printf -- '- Hard local rollback: `git reset --hard %s`\n' "$tag_name"
  elif [[ -n "$latest_tag" ]]; then
    printf -- '- Safe history-preserving rollback after push: `git revert --no-edit %s..HEAD`\n' "$latest_tag"
    printf -- '- Hard local rollback: `git reset --hard %s`\n' "$latest_tag"
  else
    printf -- '- No previous tag found. Create a tag before production pushes for quick rollback.\n'
  fi
} >"$report_file"

if [[ -n "$tag_name" ]]; then
  if git rev-parse -q --verify "refs/tags/$tag_name" >/dev/null 2>&1; then
    echo "error: tag already exists: $tag_name" >&2
    exit 1
  fi
  git tag -a "$tag_name" -m "Pre-release $tag_name"
fi

if [[ "$push_tag" == "true" ]]; then
  [[ -n "$tag_name" ]] || { echo "error: --push-tag requires --tag" >&2; exit 1; }
  git push origin "$tag_name"
fi

echo "pre-release report created: $report_file"
if [[ -n "$tag_name" ]]; then
  echo "tag created: $tag_name"
fi
echo "next:"
echo "  git push origin $branch_name"
if [[ -n "$tag_name" ]]; then
  echo "  git push origin $tag_name"
fi
