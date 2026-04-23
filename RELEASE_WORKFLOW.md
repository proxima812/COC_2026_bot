# Release Workflow

## Pre-Release Report

Before a release-style push, generate a report from the latest tag to current `HEAD`:

```bash
scripts/pre_release.sh
```

This creates a markdown file in `release_reports/` with:
- commit list
- diff stat
- changed files
- rollback hints

If you want a rollback point, create a tag at the same time:

```bash
scripts/pre_release.sh --tag v0.1.0-pre.1
```

Then push branch and tag:

```bash
git push origin main
git push origin v0.1.0-pre.1
```

## Rollback

Safe rollback that preserves history:

```bash
scripts/rollback_to_tag.sh v0.1.0-pre.1 --mode revert
```

Fast local rollback:

```bash
scripts/rollback_to_tag.sh v0.1.0-pre.1 --mode hard
```

If you must update the remote after a hard reset:

```bash
scripts/rollback_to_tag.sh v0.1.0-pre.1 --mode hard --push
```

Use `revert` by default. Use `hard` only when you explicitly want to rewrite branch history.
