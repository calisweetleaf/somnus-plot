# Somnus Plot v0.4.0: hands-on capability and boundary audit

**Date:** 2026-10-12  
**Subject:** the original `somnus-plot-v0.4.zip` uploaded by the operator.  
**Environment:** Debian Linux, Node.js v22.16.0, Python 3.13.5.  
**Method:** inspect actual TS/JS/HTML; run only isolated copies and disposable fixtures. No network downloads or pip installations. Original archive not modified.

## What it is

A small **portable plot-rooted execution substrate**, with its own manifest, bundled Node.js ES-module entrypoint (`main.js`), optional embedded Python tenant (`.grave/py`), bootstrap ledger (`data.json`), and declarative child-process step sequence. A second webview host (`host.html`) executes a selected pack's JS in a browser Worker inside an opaque-origin sandbox iframe and exposes manifest-authorized messages for logs, local key-value storage, and HTTPS fetch. The two hosts are *not* feature-equivalent.

The bundled main.js is approximately 9 KiB and requires a Node.js runtime but not the package.json development dependencies; package.json identifies `tsx` as a dev dependency for TypeScript scripts. `main.js` is generated from `sandbox.ts` and `untar.ts`. The `harness.ts` file is a simpler legacy runner not launched by `node main.js`.

## Capabilities actually reproduced

1. **Shallow bootstrapping:** `node main.js` creates a tenant virtual environment under `.grave/py` using host Python, then runs its commands.
2. **Idempotence:** second boot skips installation when ledger, Python path and version check appear healthy.
3. **Host gating:** manifest `hosts: ["webview"]` is rejected by Node entrypoint.
4. **Relative plot root:** the main entrypoint changes cwd to its own directory; execution remains plot-relative even if launched elsewhere.
5. **Step sequence and stop:** child processes run in order with literal args and nonzero exit halts subsequent steps.
6. **Offline deep-bootstrap mechanism:** a local tar.gz shaped like a standalone Python install, pinned by SHA256, was unpacked using bundled untar, flattened, and recognized through a stub Python executable. **This does not test a real standalone Python distribution or actual binary compatibility.**
7. **Digest verification:** a wrong pin aborts the install.
8. **Direct path traversal:** tar archive entry `../escape.txt` was rejected.
9. **Mixed runtime experiment:** a separate demonstration pack successfully created `samples.json` in Node, computed an aggregate inside buried Python, and read `result.json` in Node. Result: count 4, sum 114, average 28.5.

## Confirmed defects and risks

### Critical for untrusted packs: Node permissions are not enforced

The `permissions` object in manifest.json is only read to type/check metadata, not enforced in `sandbox.ts` or bundled `main.js` for steps. With `permissions: {"spawn": false, "fs": []}`, the executable still launched a child process. With `fs: []`, a child process read a harmless sentinel file outside the plot. Child processes receive inherited OS privileges and environment by default. The entries are **policy declarations, not a sandbox**. See `sandbox.ts` lines 13–33 and 65–68, 132–138, and bundled main.js lines 109–117 and 204–215.

### Critical for untrusted archives: chained symlink escape

`untar.ts` checks symlink targets using lexical `path.resolve()` on the archive path but not the **actual filesystem resolution of a chain of previously created symlinks**. A disposable tar with links `a -> .` and `a/up -> ..` followed by the ordinary file `a/up/sentinel.txt` wrote `.grave/sentinel.txt`, outside the `.grave/py` extraction root, while every individual lexical check passed. The test never accessed a path outside its own disposable plot. The deep bootstrap subsequently failed only because the fixture deliberately supplied no Python binary. **A pinned archive does not make the extractor safe against a malicious or compromised pinned source.** See `untar.ts` lines 16–60.

Recommended remediation: do not install untrusted archives with this extractor. Use a thoroughly validated extraction strategy that guarantees confinement under actual filesystem resolution; favor extract-to-new-temp-root, reject dangerous link relationships, detect duplicate/path collisions, enforce limits, and atomically promote only after full validation. A simple string prefix check is not sufficient.

### Medium: tenant identity is underchecked

After a shallow install, change manifest tenant depth to `deep` and supply an intentionally invalid SHA256. The existing `.grave/py` was reused and `data.json` still reported `shallow`, because health checks only examine ledger tenant kind and whether `.grave/py/bin/python3 --version` begins with `Python`. Requested depth, URL, version, and archive pin are not compared. See `sandbox.ts` lines 70–87.

### Other limitations found by inspection

- **Webview not verified:** attempted headless Chromium and Playwright; this environment blocked both HTTP localhost and `file://` navigation with `ERR_BLOCKED_BY_ADMINISTRATOR`. No pass/fail claim about Chrome CSP/Worker behavior or the raw-fetch isolation probe.
- **Webview capabilities:** `log`, `kv.get`, `kv.set`, `net.fetch` only. No native Node process, filesystem or Python interface. The main JS pack inside Worker requires the browser host; there is no generic Node equivalent in the core.
- **Webview network policy:** HTTPS host matching is implemented at the URL request point, but redirects and final destination are not explicitly reauthorized (`host.html` lines 26–30, 62). Browser CORS may additionally restrict actual fetches.
- **Windows native deep installation:** absent; unsupported platform throws in `resolveStandaloneUrl` (`sandbox.ts` lines 53–62).
- **Termux native deep installation:** unresolved because standalone Python target is not compatible with Android Bionic as shipped (README confirms open).
- **Archive inflation:** full decompressed tar buffered into RAM before extraction (`untar.ts` lines 22–27), so large archives or expansion bombs can exhaust memory.
- **Network deep bootstrap:** actual public download/retry/curl fallback not exercised (offline lab).
- **Automatic latest download:** when `url` is omitted, release selection occurs dynamically, and when `sha256` is omitted the digest is printed but not pinned; current lock policy is warning-only (`sandbox.ts` lines 91–105).
- **Step runner:** plain sequential steps, no built-in branching, DAG, looping, deterministic resume, structured step output, concurrency, resource quota, or environment isolation. Individual invoked programs can, of course, implement these themselves.
- **Python packages:** `packages` invoked via pip on every launch after health check; no package lock validation in the current manifest.
- **README npm script mismatch:** `npm run go` invokes `tsx harness.ts` (legacy `steps.json` runner), not the plot bootstrap (`node main.js`). The README's statement that `npm run go` operates the full plot may mislead unless clarified.

## Capability matrix

| Feature | Status |
|---|---|
| Bundled zero-NPM-runtime JavaScript core (Node required) | Verified |
| Declarative step execution | Verified |
| Shallow Python tenant | Verified |
| Offline deep installer pathway | Stub fixture verified, real CPython unverified |
| Digest mismatch rejection | Verified |
| Direct tar parent traversal rejection | Verified |
| Host metadata gating | Verified |
| Manifest fs/spawn enforcement on Node | Not implemented; bypass reproduced |
| Symlink-safe extraction | Failed; breakout reproduced |
| Manifest/ledger drift detection | Failed; stale reuse reproduced |
| Real webview isolation | Unverified (browser environment blocked) |
| Windows/Termux deep support | Not implemented |
| Bare-metal/full OS isolation | Not provided |

## Experiments worth doing next

1. Complete real browser-origin test on phone/desktop. Serve `host.html` over HTTP, run bundled `pack-demo` and verify both capability denial and the message `raw fetch blocked (expected)`; **stop** if `RAW FETCH SUCCEEDED` appears.
2. Run a genuine pinned Python standalone tarball offline on Linux and validate interpreter/library support and filesystem confinement.
3. Add an enforcement boundary for Node steps and test hostile manifests before treating the plot as a general third-party pack host.
4. Correct link-confinement and replay the included adversarial archive test plus additional hardlink, PAX and decompression-limit cases.
5. Align `data.json` tenant state to manifest semantics and test requests to switch depth, runtime version, package specification, and archive identity.

## Files included in this audit kit

- `plot_probe.py` is an **offline** behavior test tool which takes a path to the ORIGINAL zip, writes only to disposable temporary directories, and prints expected behaviors and reproducible defects. It requires Node and host Python venv support. It writes a short JSON result in the invocation directory.
- `observed-results.json` is the result of running the portable 12-check probe against the uploaded v0.4 zip here.
- `examples/mixed-runtime-plot/` is a separate, trusted demonstration plot using the unchanged bundled `main.js`. Run `node main.js` inside it.

**Interpretation:** the implementation is a real small execution substrate, not just conceptual scaffolding. It is suitable for **trusted** personal plots and controlled local experiments now. It is not yet an isolation boundary for untrusted code or download artifacts. Passing the probe's vulnerability-reproduction assertions means the defect was confirmed, not that the subsystem is safe.
