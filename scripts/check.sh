#!/usr/bin/env bash
# Canonical repo health check — the one command every session runs for a
# proportionate green baseline. Fast by default (no network); each rung is
# honest about pass / fail / skip. See docs/harness_design/ for the rationale.
#
#   scripts/check.sh            # backend tests + doc-consistency + web build (if deps present)
#   SKIP_WEB=1 scripts/check.sh # backend + docs only (skip the Vite build)
#
# Ladder:
#   1. Backend unit tests (deadline, CPV, qualification, preflight, auth) + app construct
#   2. Documentation-state consistency (no known false records reintroduced)
#   3. Frontend production build (skipped with a note if web/node_modules is absent)
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2
ROOT="$(pwd)"
PY="${PYTHON:-python3}"
fail=0

hr()  { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
ok()  { printf '\033[32m  ok\033[0m   %s\n' "$1"; }
bad() { printf '\033[31m  FAIL\033[0m %s\n' "$1"; fail=1; }
skip(){ printf '\033[33m  skip\033[0m %s\n' "$1"; }

# ---- 1. Backend unit tests ---------------------------------------------------
hr "1. Backend unit tests"
if "$PY" -c "import pytest" 2>/dev/null; then
  if "$PY" -m pytest; then ok "pytest suite passed"; else bad "pytest suite failed"; fi
else
  bad "pytest not installed — run: pip install -r requirements-dev.txt"
fi

# ---- 2. Documentation-state consistency -------------------------------------
# Cheap guard against the exact drift the harness review fixed: stale "preview"
# stage labels or false "Uncommitted" records creeping back into the live docs.
hr "2. Documentation-state consistency"
docs="README.md CLAUDE.md _session/handover.md _session/todo.md"
# Flag stage-is-preview labels, but not the correct "no preview screens remain".
preview_hits="$(grep -rInE "🟡 Preview|[Pp]review screen" $docs 2>/dev/null | grep -viE "no preview screens")"
if [ -n "$preview_hits" ]; then
  bad "a live doc still calls a stage a 'preview screen' (all six stages are real)"
  printf '%s\n' "$preview_hits"
else
  ok "no stale 'preview screen' labels in the live docs"
fi
if grep -rIn "Uncommitted" _session/handover.md _session/todo.md >/dev/null 2>&1; then
  bad "handover/todo still label committed work 'Uncommitted'"
else
  ok "no false 'Uncommitted' labels in the session docs"
fi
if [ -f _session/state.yaml ]; then ok "_session/state.yaml present"; else bad "_session/state.yaml missing"; fi

# ---- 3. Frontend production build -------------------------------------------
hr "3. Frontend production build"
if [ "${SKIP_WEB:-0}" = "1" ]; then
  skip "SKIP_WEB=1 set"
elif ! command -v npm >/dev/null 2>&1; then
  skip "npm not on PATH"
elif [ ! -d web/node_modules ]; then
  skip "web/node_modules absent — run: (cd web && npm install)"
else
  if npm --prefix web run build >/tmp/psbt_web_build.log 2>&1; then
    ok "vite build clean ($(grep -Eo '[0-9.]+ kB' /tmp/psbt_web_build.log | tail -1))"
  else
    bad "vite build failed — see /tmp/psbt_web_build.log"; tail -20 /tmp/psbt_web_build.log
  fi
fi

# ---- verdict -----------------------------------------------------------------
hr "verdict"
if [ "$fail" = "0" ]; then
  printf '\033[32mall checks green\033[0m\n'; exit 0
else
  printf '\033[31mcheck failed — see FAIL lines above\033[0m\n'; exit 1
fi
