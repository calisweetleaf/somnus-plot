#!/bin/sh
# Somnus Plot Node-absent launcher (entry B, docs/V07-CONTRACTS.md section 11).
#
# Irreducible host inputs, declared rather than assumed:
#   - a POSIX sh plus mkdir rmdir mv rm cat uname dirname ls sleep date mktemp cut sed grep tr wc sync
#     (coreutils, BSD userland or busybox)
#   - tar and gzip
#   - one sha256 tool: sha256sum, shasum or openssl
#   - either curl or wget with HTTPS reachability, or PLOT_KIT naming an offline kit directory
#     (kit.json + SHA256SUMS + archives, built by `node capabilities/bootstrap.mjs kit <dir>`)
# Node is obtained into <root>/.grave/host/node-<ver>-<plat>-<arch>-XXXXXX, completion marker
# written last, and the same main.js is exec'd. No sudo, no package manager, no remote script.
#
# Environment: PLOT_ROOT (plot root, default: directory holding main.js), PLOT_KIT, PLOT_OFFLINE=1,
# PLOT_NODE (operator-supplied node binary; skips acquisition), PLOT_NODE_MIRROR (base URL with the
# same layout as https://nodejs.org/dist; artifacts stay sha256-pinned), PLOT_LOCK_WAIT (seconds).
# `plot.sh bootstrap <args>` runs capabilities/bootstrap.mjs on the acquired Node instead of main.js;
# `plot.sh --node-path` prints the Node binary and exits.
set -eu
NODE_VERSION=24.22.0
say() { printf '[plot.sh] %s\n' "$*" >&2; }
die() { say "$*"; exit 1; }
here=$(cd "$(dirname "$0")" && pwd -P)
seed=$(dirname "$here")
[ -f "$seed/main.js" ] || die "main.js not found at $seed/main.js"
root=$(cd "${PLOT_ROOT:-$seed}" 2>/dev/null && pwd -P) || die "PLOT_ROOT does not exist: ${PLOT_ROOT:-}"
case $root in *'"'*|*'\'*) die "root path must not contain a double quote or backslash: $root";; esac

launch() {
  node=$1; shift
  PATH="$(dirname "$node"):$PATH"; PLOT_ROOT=$root; export PATH PLOT_ROOT
  if [ "${1:-}" = --node-path ]; then printf '%s\n' "$node"; exit 0; fi
  if [ "${1:-}" = bootstrap ]; then shift; exec "$node" "$seed/capabilities/bootstrap.mjs" "$@"; fi
  exec "$node" "$seed/main.js" --root "$root" "$@"
}

if [ -n "${PLOT_NODE:-}" ]; then
  [ -x "$PLOT_NODE" ] || die "PLOT_NODE is not an executable: $PLOT_NODE"
  say "using operator-supplied Node $PLOT_NODE (no acquisition)"
  launch "$PLOT_NODE" "$@"
fi

case $(uname -m) in x86_64|amd64) arch=x64;; aarch64|arm64) arch=arm64;; *) arch=$(uname -m);; esac
libc=null
case $(uname -s) in
  Linux)
    if [ "$(uname -o 2>/dev/null || true)" = Android ] || [ -n "${TERMUX_VERSION:-}" ]; then plat=android
    elif ls /lib/ld-musl-* >/dev/null 2>&1; then plat=linux_musl; libc='"musl"'
    else plat=linux; libc='"glibc"'; fi;;
  Darwin) plat=darwin;;
  *) plat=$(uname -s);;
esac

# Pins mirror bootstrap/recipes/node.json (tests/bootstrap.mjs asserts they agree).
official=${PLOT_NODE_MIRROR:-https://nodejs.org/dist}
unofficial=${PLOT_NODE_MIRROR:-https://unofficial-builds.nodejs.org/download/release}
case $plat-$arch in
  linux-x64) file=node-v$NODE_VERSION-linux-x64.tar.gz sha=28ea0a438de9a13bd7891fd758eee6c7819ee8af5442dfd8d45bd65e56d4228c size=58256361 base=$official pub='Node.js project (official release)';;
  linux-arm64) file=node-v$NODE_VERSION-linux-arm64.tar.gz sha=b7e7991d5407815adfa74a2a9cd4db683552c8ce32ff4a295c22e972849c3f5d size=57997377 base=$official pub='Node.js project (official release)';;
  darwin-x64) file=node-v$NODE_VERSION-darwin-x64.tar.gz sha=495e3f273c645f3c4677d438304cdfc701729ea5dec5728f5c8e76a2dece4b91 size=54356645 base=$official pub='Node.js project (official release)';;
  darwin-arm64) file=node-v$NODE_VERSION-darwin-arm64.tar.gz sha=6a9724d9b50a5f22b4816cded441b5a8d9ddae546191a5e5b7efa5a5e2ee26d5 size=53049576 base=$official pub='Node.js project (official release)';;
  linux_musl-x64) file=node-v$NODE_VERSION-linux-x64-musl.tar.gz sha=72cd253fbe0c2539d52208ed098d47b78ff2c32ba76295d8e6b5b0ce067dcba5 size=60222855 base=$unofficial pub='Node.js unofficial-builds project (project-hosted, not an official release)';;
  linux_musl-arm64) file=node-v$NODE_VERSION-linux-arm64-musl.tar.gz sha=6812a53e5b37fbc32476d6c3511038d2bc3bbd1b3bb348d6c04dd2c70a1c8f4a size=60105814 base=$unofficial pub='Node.js unofficial-builds project (project-hosted, not an official release)';;
  android-*) die "unsupported host android-$arch: Node.js publishes no Android/Termux build. Install Node yourself and rerun with PLOT_NODE=<path to node>; this launcher never runs pkg or sudo.";;
  *) die "unsupported host $plat-$arch: no pinned Node archive (see bootstrap/recipes/node.json)";;
esac
url=$base/v$NODE_VERSION/$file
case ${PLOT_KIT:-}$url in *'"'*|*'\'*) die "PLOT_KIT and PLOT_NODE_MIRROR must not contain a double quote or backslash";; esac
platform=${plat%_musl}
id=node-$NODE_VERSION-$plat-$arch
host=$root/.grave/host
lockd=$host/.locks/$id

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  elif command -v openssl >/dev/null 2>&1; then openssl dgst -sha256 "$1" | sed 's/^.*= *//'
  else die "no sha256 tool on PATH (need sha256sum, shasum or openssl)"; fi
}
birth() { [ -r "/proc/$1/stat" ] && [ -r /proc/sys/kernel/random/boot_id ] || { echo null; return; }; printf '"%s:%s"' "$(cat /proc/sys/kernel/random/boot_id)" "$(sed 's/^.*) //' "/proc/$1/stat" | cut -d' ' -f20)"; }
valid() {
  m=$1/.plot-host.json
  [ -f "$m" ] && [ -x "$1/bin/node" ] && grep -q "\"id\":\"$id\"" "$m" && grep -q "\"sha256\":\"$sha\"" "$m" && grep -q "\"path\":\"$1\"" "$m"
}
installed() { for d in "$host/$id"-??????; do [ -d "$d" ] && valid "$d" && { printf '%s\n' "$d"; return 0; }; done; return 1; }

if d=$(installed); then launch "$d/bin/node" "$@"; fi

mkdir -p "$host/.locks" "$host/.stage" "$host/.dl" "$host/.attempts"
chmod 700 "$root/.grave" "$host" 2>/dev/null || true
attempt=$(date -u +%Y%m%d%H%M%S)-$$-sh
locked=0 stage='' final=''
cleanup() {
  [ -n "$stage" ] && rm -rf "$stage"
  [ -n "$final" ] && [ ! -f "$final/.plot-host.json" ] && rm -rf "$final"
  if [ "$locked" = 1 ]; then rm -f "$lockd/owner.json"; rmdir "$lockd" 2>/dev/null || true; locked=0; fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

waited=0 polls=0 limit=$(( ${PLOT_LOCK_WAIT:-1800} * 5 ))
until mkdir "$lockd" 2>/dev/null; do
  own=$(cat "$lockd/owner.json" 2>/dev/null || true)
  pid=$(printf '%s' "$own" | sed -n 's/.*"pid":\([0-9][0-9]*\).*/\1/p')
  stale=0
  if [ -n "$pid" ]; then
    if ! kill -0 "$pid" 2>/dev/null; then stale=1
    else b=$(printf '%s' "$own" | sed -n 's/.*"birth":\("[^"]*"\).*/\1/p'); [ -n "$b" ] && [ "$(birth "$pid")" != "$b" ] && [ "$(birth "$pid")" != null ] && stale=1; fi
  elif [ "$polls" -ge 50 ]; then stale=1
  fi
  if [ "$stale" = 1 ] && mkdir "$lockd.break" 2>/dev/null; then
    if [ "$(cat "$lockd/owner.json" 2>/dev/null || true)" = "$own" ]; then
      dead=$host/.locks/.dead-$id-$$; mv "$lockd" "$dead" 2>/dev/null && rm -rf "$dead" && say "broke stale lock of pid ${pid:-unrecorded}"
    fi
    rmdir "$lockd.break"; continue
  fi
  [ "$waited" = 1 ] || say "waiting for concurrent acquisition of $id (pid ${pid:-?})"
  waited=1; polls=$((polls + 1)); [ "$polls" -lt "$limit" ] || die "lock on $id held beyond ${PLOT_LOCK_WAIT:-1800}s by pid ${pid:-?}"
  sleep 0.2 2>/dev/null || sleep 1
done
locked=1
printf '{"pid":%s,"birth":%s,"attempt":"%s","writer":"plot.sh"}' "$$" "$(birth $$)" "$attempt" > "$lockd/owner.json"
if d=$(installed); then cleanup; say "shared concurrent acquisition $d"; launch "$d/bin/node" "$@"; fi
for d in "$host/$id"-?????? "$host/.stage/$id"-*; do [ -d "$d" ] && [ ! -f "$d/.plot-host.json" ] && { rm -rf "$d"; say "removed interrupted stage $d"; }; done

if [ -n "${PLOT_KIT:-}" ] && [ -f "$PLOT_KIT/$file" ]; then
  [ -f "$PLOT_KIT/SHA256SUMS" ] && ! grep -q "^$sha  $file\$" "$PLOT_KIT/SHA256SUMS" && die "kit $PLOT_KIT: SHA256SUMS does not record the pinned sha256 for $file; refusing a different artifact"
  archive=$PLOT_KIT/$file kind=kit
  [ "$(sha256 "$archive")" = "$sha" ] || die "kit file $archive does not match pinned sha256 $sha; rebuild the kit"
  srcjson="\"kind\":\"kit\",\"file\":\"$file\",\"url\":null,\"path\":\"$archive\""
else
  [ -z "${PLOT_OFFLINE:-}" ] || die "offline and no kit carries $file (set PLOT_KIT to a kit directory)"
  archive=$host/.dl/$sha part=$host/.dl/$sha.part kind=online
  if [ ! -f "$archive" ]; then
    have=0; [ -f "$part" ] && have=$(wc -c < "$part" | tr -d ' ')
    [ "$have" -le "$size" ] || { rm -f "$part"; have=0; }
    if [ "$have" -lt "$size" ]; then
      [ "$have" -gt 0 ] && say "resuming $file at byte $have"
      if command -v curl >/dev/null 2>&1; then
        curl -fL --retry 3 --retry-delay 2 --connect-timeout 30 -sS -C - -o "$part" "$url" || die "download failed: $url (rerun to resume from $part, or set PLOT_KIT)"
      elif command -v wget >/dev/null 2>&1; then
        wget -q -c -T 60 -t 3 -O "$part" "$url" || die "download failed: $url (rerun to resume from $part, or set PLOT_KIT)"
      else die "no transport: need curl or wget on PATH, or PLOT_KIT"; fi
    fi
    got=$(sha256 "$part")
    [ "$got" = "$sha" ] || { rm -f "$part"; die "sha256 mismatch for $url: got $got, pinned $sha; discarded, nothing installed"; }
    mv "$part" "$archive"
  fi
  srcjson="\"kind\":\"online\",\"file\":\"$file\",\"url\":\"$url\",\"path\":null"
fi

stage=$(mktemp -d "$host/.stage/$id-XXXXXX")
gzip -dc "$archive" | tar -xf - -C "$stage"
top=$stage/${file%.tar.gz}
[ -x "$top/bin/node" ] || die "archive $file did not contain ${file%.tar.gz}/bin/node"
final=$host/$id-${stage##*-}
mv "$top" "$final"; rmdir "$stage"; stage=
out=$("$final/bin/node" --version) || die "acquired node failed to start (missing system library? see bootstrap/recipes/node.json requires)"
[ "$out" = "v$NODE_VERSION" ] || die "acquired node reports $out, expected v$NODE_VERSION"
printf '{"schema":"plot.host/1","id":"%s","tool":"node","version":"%s","platform":"%s","arch":"%s","libc":%s,"route":"binary","provenance":"pinned-recipe","source":{%s,"sha256":"%s","size":%s,"publisher":"%s"},"inputs":null,"path":"%s","exe":"bin/node","bin":"bin","probe":{"args":["--version"],"output":"%s"},"tree":null,"writer":"plot.sh","attempt":"%s","at":"%s"}\n' \
  "$id" "$NODE_VERSION" "$platform" "$arch" "$libc" "$srcjson" "$sha" "$size" "$pub" "$final" "$out" "$attempt" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$final/.plot-host.json.tmp"
mv "$final/.plot-host.json.tmp" "$final/.plot-host.json"
sync
[ "$kind" = online ] && rm -f "$archive"
say "acquired $id from $kind into $final"
node=$final/bin/node final=
cleanup
launch "$node" "$@"
