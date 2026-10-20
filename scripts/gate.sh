#!/usr/bin/env bash
# Somnus Plot integrated gate.
#
# Default mode runs the real suite inside a disposable copy of the working tree,
# because the tests rewrite evidence/*.json and build.mjs rewrites main.js.
# The evidence of record is therefore never replaced by an ordinary gate run.
#
#   scripts/gate.sh             build determinism + byte ceiling + integration/resident checks + clean-package smoke
#   scripts/gate.sh --bench     the above plus both benchmark suites (still in the disposable copy)
#   scripts/gate.sh --evidence  run everything in place, sequentially, and regenerate
#                               evidence/*.json, *.log and evidence/RESULTS.md

set -euo pipefail

root_dir="$(cd "$(dirname "$0")/.." && pwd)"
mode="${1:-}"
case "$mode" in ""|--bench|--evidence) ;; *) echo "usage: scripts/gate.sh [--bench|--evidence]" >&2; exit 2;; esac

preflight() {
  local missing=0
  command -v node >/dev/null || { echo "gate: NOT RUN (node missing)" >&2; exit 3; }
  for tool in python3 cc; do command -v "$tool" >/dev/null || { echo "gate: $tool missing; optional-Python regression checks will fail" >&2; missing=1; }; done
  python3 -c 'import sysconfig,os,sys;sys.exit(0 if os.path.exists(os.path.join(sysconfig.get_paths()["include"],"Python.h")) else 1)' 2>/dev/null \
    || { echo "gate: Python.h missing; native wheel fixture will fail" >&2; missing=1; }
  echo "gate: node $(node --version), $(python3 --version 2>&1 || echo 'python3 absent'), preflight_missing=$missing"
}

step() { echo "== $1"; shift; "$@" || { echo "gate: FAIL ($*)" >&2; exit 1; }; }

preflight

if [ "$mode" = "--evidence" ]; then
  cd "$root_dir"
  step build node build.mjs
  for pair in integration:integration resident:resident-integration benchmark:benchmark \
              resident-benchmark:resident-benchmark package-smoke:package-smoke; do
    t="${pair%%:*}" log="${pair#*:}"
    step "$t" bash -o pipefail -c "node tests/$t.mjs 2>&1 | tee evidence/$log.log"
  done
  step report node tests/report.mjs
  echo "gate: PASS (evidence regenerated in place; review git diff evidence/ before committing)"
  exit 0
fi

work="$(mktemp -d "${TMPDIR:-/tmp}/plot-gate-XXXXXX")"
trap 'rm -rf "$work"' EXIT
tar -C "$root_dir" --exclude=./.git --exclude=./.grave --exclude=./data.json -cf - . | tar -C "$work" -xf -
cd "$work"

step build node build.mjs
step "committed main.js matches build of src/plot.mjs" cmp main.js "$root_dir/main.js"
step integration node tests/integration.mjs
step resident node tests/resident.mjs
step cartographer node tests/cartographer.mjs
step bootstrap node tests/bootstrap.mjs
step package-smoke sh -c 'node tests/package-smoke.mjs >/dev/null'
if [ "$mode" = "--bench" ]; then
  step benchmark node tests/benchmark.mjs
  step resident-benchmark node tests/resident-benchmark.mjs
fi

echo "gate: PASS"
