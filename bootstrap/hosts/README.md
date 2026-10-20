# Bootstrap host kits: Windows, macOS, Android/Termux

Status: **NOT RUN.** On 2026-10-20 the P07-09 suite (`tests/bootstrap.mjs`) ran only on the Linux x64
glibc reference host. Nothing in this file is a result. It explains how to run the outstanding host
families so their results can be recorded honestly (contracts §11; PLAN §6.3, Certification).

## 1. Build a kit on any networked host that has Node

```sh
node capabilities/bootstrap.mjs kit /path/to/kit --hosts win32-x64,darwin-arm64,darwin-x64,linux-arm64
```

The kit directory contains these files:

| File | Purpose |
| --- | --- |
| `kit.json` | `schema: plot.kit/1`. Holds the same identity and compatibility records as `bootstrap/recipes/*.json`: tool, version, platform, arch, libc, route, sha256, size, unpacked size, publisher, checksum list, requirements, and build steps. |
| `SHA256SUMS` | `sha256  file` lines, read by `plot.sh` and `plot.ps1`, which cannot parse JSON. |
| archives | The pinned upstream files, byte-identical to the online sources. |

A kit file is accepted only when its sha256 equals the recipe pin. A kit record for a host that the
recipes do not cover is reported as `provenance: kit-declared` and is never treated as pinned. To copy
already-downloaded archives instead of fetching them again, pass `--from <dir>`.

## 2. Windows x64 (PowerShell 5.0+ or 7)

Prerequisites: Windows PowerShell 5.0+ with .NET Framework 4.5+, and the kit or HTTPS access to
nodejs.org. No administrator rights are needed, and no winget, choco or scoop.

```powershell
Copy-Item -Recurse <seed> C:\plot      # main.js, manifest.json, package.json, capabilities\, bootstrap\
$env:PLOT_KIT = 'D:\kit'               # omit to fetch https://nodejs.org/dist (sha256-pinned)
powershell -ExecutionPolicy Bypass -File C:\plot\bootstrap\plot.ps1 plan
powershell -ExecutionPolicy Bypass -File C:\plot\bootstrap\plot.ps1 bootstrap acquire python git --kit D:\kit
powershell -ExecutionPolicy Bypass -File C:\plot\bootstrap\plot.ps1 bootstrap verify
```

Expected layout: `C:\plot\.grave\host\node-24.22.0-win32-x64-XXXXXX\node.exe`, Python from the
python-build-standalone `x86_64-pc-windows-msvc` archive, and Git from MinGit
(`cmd\git.exe`, a binary route with no build). The Node test suite runs on Windows via
`node tests\bootstrap.mjs`. Its POSIX launcher checks need `sh` and fail there. Record such a failure
as NOT RUN, not as a PASS.

Known gaps to check on that host:

- No parent-directory fsync on Windows (contracts §1).
- Lock staleness is pid-only (`birth: null`).
- The zip extractor rejects zip64 and symlink entries.

## 3. macOS arm64 or x64

Prerequisites: `/bin/sh`, `tar`, `gzip`, `shasum`, `curl` (all in the base system), and the kit or
network access. Building Git from source also needs the Xcode Command Line Tools (`cc`, `make`).
Bootstrap never installs them; `plan` reports them as missing before any change is made.

```sh
PLOT_KIT=/Volumes/kit sh <seed>/bootstrap/plot.sh plan
PLOT_KIT=/Volumes/kit sh <seed>/bootstrap/plot.sh bootstrap acquire python git --kit /Volumes/kit
sh <seed>/bootstrap/plot.sh bootstrap verify
node tests/bootstrap.mjs   # with the acquired node on PATH; record the output verbatim
```

The kit glibc and `ldd` assertions do not apply to macOS. The suite asserts libc only on Linux.

## 4. Android / Termux aarch64

Neither Node.js nor python-build-standalone publishes an Android build. `plan` reports `node` and
`python` as `unsupported` with that reason, and `plot.sh` refuses the host. Supported route:

1. Install Node yourself (for example with `pkg install nodejs`; the launcher never runs `pkg` itself).
2. Run `PLOT_NODE=$(command -v node) sh bootstrap/plot.sh plan`.
3. For Git, the source-build route applies when `cc` and `make` are on PATH (`pkg install clang make`,
   which you also install yourself). Then run `sh bootstrap/plot.sh bootstrap acquire git --kit <kit>`.

## 5. What a certifying run must record

For each host family, record the following:

- OS and version, CPU, Node version.
- The full stdout of `node tests/bootstrap.mjs` and `scripts/gate.sh` where a shell gate exists.
- `plan` JSON.
- Acquired closure sizes from `.plot-host.json` (`tree`).
- Cold and reuse timings.
- The system libraries that the acquired tools still load (`otool -L` on macOS, `dumpbin /dependents`
  or Dependencies on Windows).

A PATH-masked run on a provisioned machine is not a pristine-host proof. Name the libraries that
remain.
