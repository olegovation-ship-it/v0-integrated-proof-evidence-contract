#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
if [[ "$MODE" != "baseline" && "$MODE" != "final" ]]; then
  echo "Usage: $0 baseline|final" >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: working tree must be clean." >&2
  exit 1
fi

git fetch origin --prune

MAIN_REF="refs/remotes/origin/main"
DEV_REF="refs/remotes/origin/gate2-development"
BASELINE="820947103d24153e00b215ced53ee8b33ef0c7bf"

MAIN_SHA="$(git rev-parse "$MAIN_REF")"
if ! git merge-base --is-ancestor "$BASELINE" "$MAIN_SHA"; then
  echo "ERROR: origin/main does not contain the Gate 2 merge baseline." >&2
  exit 1
fi

if git show-ref --verify --quiet "$DEV_REF"; then
  git switch gate2-development
else
  git switch -c gate2-development --track origin/gate2-development
fi

git merge --ff-only origin/main
git push origin gate2-development

git switch main
git pull --ff-only origin main

git fetch origin --prune
MAIN_SHA="$(git rev-parse refs/remotes/origin/main)"
DEV_SHA="$(git rev-parse refs/remotes/origin/gate2-development)"

echo "mode=$MODE"
echo "origin/main=$MAIN_SHA"
echo "origin/gate2-development=$DEV_SHA"

if [[ "$DEV_SHA" != "$MAIN_SHA" ]]; then
  echo "ERROR: branch synchronization did not produce ref equality." >&2
  exit 1
fi

echo "DEVELOPMENT_BRANCH_SYNCHRONIZATION_PASS"
