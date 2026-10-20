#!/bin/sh
# Somnus Plot host certification runner (POSIX: Linux, macOS, Android/Termux). P07-07, contracts section 11.
#
#   sh bootstrap/hosts/certify.sh <out-dir> [--quick]
#
# Copies the seed (no .git, no .grave) into a disposable directory, obtains Node through bootstrap/plot.sh,
# runs bootstrap plan/acquire/verify, then the Node suites and the shell gate on that Node, and records
# every command's stdout, stderr and exit code under <out-dir>/<family>-<UTC stamp>/. It never prints or
# writes PASS for the host: summary.json lists exit codes, and a reviewer records the result in
# bootstrap/hosts/README.md. --quick skips scripts/gate.sh. PLOT_KIT, PLOT_OFFLINE and PLOT_NODE are passed
# through to plot.sh unchanged. Nothing outside the disposable copy and <out-dir> is written.
set -u
[ $# -ge 1 ] || { echo "usage: sh bootstrap/hosts/certify.sh <out-dir> [--quick]" >&2; exit 2; }
out_base=$1; quick=${2:-}
seed=$(cd "$(dirname "$0")/../.." && pwd -P)
case $(uname -s) in
  Linux) if [ "$(uname -o 2>/dev/null || true)" = Android ] || [ -n "${TERMUX_VERSION:-}" ]; then family=android; else family=linux; fi;;
  Darwin) family=darwin;; *) family=$(uname -s | tr 'A-Z' 'a-z');;
esac
family=$family-$(uname -m)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$out_base" && out=$(cd "$out_base" && pwd -P)/$family-$stamp && mkdir "$out" || exit 1
work=$(mktemp -d "${TMPDIR:-/tmp}/plot-certify-XXXXXX") || exit 1
trap 'rm -rf "$work"' EXIT
(cd "$seed" && tar --exclude=./.git --exclude=./.grave --exclude=./data.json -cf - .) | (cd "$work" && tar -xf -) || exit 1
steps=''
record() { # record <name> <command...>: stdout/stderr to files, exit code to summary
  name=$1; shift
  ( cd "$work" && "$@" ) >"$out/$name.out" 2>"$out/$name.err"; code=$?
  printf '%s exit=%s\n' "$name" "$code" | tee -a "$out/steps.txt" >&2
  steps="$steps${steps:+,}{\"step\":\"$name\",\"exit\":$code}"
  return 0
}
{
  echo "uname: $(uname -a)"
  [ -r /etc/os-release ] && cat /etc/os-release
  command -v sw_vers >/dev/null 2>&1 && sw_vers
  [ -n "${TERMUX_VERSION:-}" ] && echo "termux: $TERMUX_VERSION"
  echo "seed: $seed"; echo "work: $work"; echo "PLOT_KIT=${PLOT_KIT:-} PLOT_OFFLINE=${PLOT_OFFLINE:-} PLOT_NODE=${PLOT_NODE:-}"
} >"$out/host.txt" 2>&1
kit_args=''; [ -n "${PLOT_KIT:-}" ] && kit_args="--kit $PLOT_KIT"
off_args=''; [ "${PLOT_OFFLINE:-}" = 1 ] && off_args=--offline
record node-path sh bootstrap/plot.sh --node-path
node=$(tail -n 1 "$out/node-path.out" 2>/dev/null)
if [ -z "$node" ] || [ ! -x "$node" ]; then
  echo "certify: no Node obtained; see $out/node-path.err" >&2
else
  record node-version "$node" --version
  # shellcheck disable=SC2086
  record plan "$node" capabilities/bootstrap.mjs plan --root "$work" $kit_args $off_args --quiet
  # shellcheck disable=SC2086
  record acquire "$node" capabilities/bootstrap.mjs acquire python git --root "$work" $kit_args $off_args --quiet
  record verify "$node" capabilities/bootstrap.mjs verify --root "$work" --quiet
  for suite in integration resident resident-env cartographer assembler bootstrap e2e package-smoke; do
    record "suite-$suite" env PATH="$(dirname "$node"):$PATH" "$node" "tests/$suite.mjs"
  done
  if [ "$quick" != --quick ] && command -v bash >/dev/null 2>&1; then record gate env PATH="$(dirname "$node"):$PATH" bash scripts/gate.sh; fi
  for exe in "$node" "$work"/.grave/host/python-*/bin/python3 "$work"/.grave/host/git-*/bin/git; do
    [ -e "$exe" ] || continue
    if command -v otool >/dev/null 2>&1; then otool -L "$exe"; elif command -v ldd >/dev/null 2>&1; then ldd "$exe"; else echo "no ldd/otool for $exe"; fi
  done >"$out/libraries.txt" 2>&1
  cp "$work"/.grave/host/*/.plot-host.json "$out/" 2>/dev/null || true
fi
printf '{"schema":"plot.certify/1","family":"%s","at":"%s","quick":%s,"status":"RECORDED (review required; not a PASS)","steps":[%s]}\n' \
  "$family" "$stamp" "$([ "$quick" = --quick ] && echo true || echo false)" "$steps" >"$out/summary.json"
echo "certify: recorded $out" >&2
