# Flashback Stage 1: acquisition/view separation

Written 2026-10-14. Baseline: the attached capability-audit ZIP, including its
9,063-byte bundled `main.js`. The original full TypeScript/webview repository
was not supplied. Supplied files are preserved under `baseline/`.

## Governing constraints

1. Increase capability density and device portability before making efficiency
   the organizing objective. The core cannot grow with the catalog.
2. Keep native operation broad: literal executable/argument arrays plus dependency
   declarations; acquired capabilities can do sophisticated work independently.
3. JavaScript owns the plot; tenant runtimes belong in `.grave/`; `data.json`
   records owned resources. Python is optional, not the universal bootstrap.
4. Keep the operator's sub-6 ms objective intact. Measure each operation honestly.
   A successful cached-view gate does not establish cold acquisition or total
   execution below 6 ms.

## Representation and ownership

| Component | Meaning |
|---|---|
| `main.js` | Entire required core; Node standard library only |
| `manifest.json` | Capability recipes, tenant policy, selected environment and native steps |
| `data.json.assets` | Current reusable resource per capability ID, its exact recipe/dependency identity, owned path and runtime identity |
| `.grave/objects/ID-*` | Acquired resources; unique owned directories; completion marker `.plot.json` |
| `.grave/envs/NAME.json` | Executable view: resource references, host identity, Python/package selection and writable-state location |
| `.grave/work/NAME/` | Persistent writable state, exposed as `PLOT_STATE` |
| `.grave/.lock/` | Exclusive provisioning writer lock |

No content hashes stand in for resource identity. The cache compares the full
canonical recipe, host platform/architecture, and dependency resource locations.
Random directory suffixes provide collision-free allocation, not provenance.
The existing optional SHA256 field is retained solely for TAR download integrity.

Objects are shared under an **application-level read-only contract**. The core
never rewrites committed resources. This is not an OS-enforced immutable store:
trusted programs can change files they own. Writes belong in `PLOT_STATE`.
Conflicting package versions get distinct layers; views with identical assets
share those assets deliberately. Reconfigure a view to change its dependencies.

The ledger keeps the latest resource for each ID. Named descriptors retain older
references. A previously superseded specification may be reacquired when requested
again; all historical objects are not indexed as a universal cache in this stage.
Automatic garbage collection is intentionally absent. Deleting a resource referenced
by an older view invalidates that view.

## Acquisition transaction

Read manifest → select host recipes → validate selected DAG → acquire writer lock
→ reuse matching completed assets or acquire into unique owned directories
→ run installation checks → write completion metadata → commit updated ledger
→ atomically replace the named view → release lock.

Pip failures, runtime/version failures and recipe/check failures remove this
transaction's new objects and preserve earlier ledger/view/state. The writer
commits no partially successful DAG. If view activation fails **after ledger
commit**, completed new resources remain available and the previous view remains;
these two independent files are not one filesystem transaction.

Each JSON commit uses a temporary file, file fsync and rename. Parent directories
are not fsynced; this is atomic activation, not a proven power-loss transaction.
Kill/crash recovery leaves the stale lock and any incomplete objects for explicit
inspection. After confirming the writer and its children are gone, remove the
stale lock. Remove incomplete unreferenced object directories only after checking
`data.json` and every named descriptor. Plot never steals a possibly live lock.

Cache validation checks recipe identity, owned path, completion-marker presence
and Python executable presence. It does not respawn Python, re-import all packages,
rescan artifact contents or verify every executable during warm provisioning.
After OS/Python changes, validate the tenant and reprovision as appropriate.
Shallow tenants remain dependent on their host Python installation and stdlib.

## Python execution contract

The shorthand `tenants.python` expands to two reserved resources:

- `python`: acquire a native runtime. Shallow depth creates one owned venv from
  a real host Python. Discovery tries `python3`, `python`, then Windows `py -3`,
  or uses a configured `command`. Deep depth extracts an explicit TAR source
  and validates it by executing Python and reading its version/SOABI/platform.
- `python-packages`: depends on that exact runtime, invokes its real pip with
  isolated configuration and `--target`, and installs the whole package set
  together. An empty set needs no pip process.

The shorthand does not create a venv per environment. Optional `version` checks
the actual Python version prefix. Runtime acquisition records `sys.executable`,
full version, SOABI and Python platform. Package-set identity depends on the
chosen runtime asset, so changing depth, source, command or version cannot silently
reuse the earlier package layer.

For per-device runtime sources, omit `tenants` and declare the built-in recipe
through `capabilities.python.on`, with each branch containing
`{"python":{"depth":"deep","url":"..."}}`. Declare
`capabilities.python-packages` with `needs:["python"]`, `packages:[...]` and
`pip:[]`. Select `python-packages` directly or through a consumer's dependencies.
The IDs are reserved only when the shorthand is also present.

Python view commands support `-c CODE [args]`, `-m MODULE [args]`, a script path,
`--entry CONSOLE_SCRIPT [args]`, and `--version`. `python` denotes the view runtime.
The original manifest spelling `.grave/py/bin/python3` is retained as a runner
alias. There is no physical executable installed at that legacy fixed path.
Commands accessing it outside Plot's step runner must migrate to the view's actual
`python` field. Other executables remain literal native commands.

The parent Python process uses `-I -S`, excluding user/host Python paths and site
startup. Its `sys.path` gains the local execution directory and exactly the view's
package layer. Normal package imports, distribution metadata, resources, compiled
extensions, scripts, modules and console entrypoints have integration coverage.
Subprocesses using the selected `sys.executable` inherit the package layer through
`PYTHONPATH` and `PYTHONNOUSERSITE`. An explicit child `-I`, `-E`, custom env, another
interpreter or scrubbed environment changes that behavior under normal Python rules.

This is a tested alternative to **per-view** venv provisioning, not complete Python
CLI/venv emulation. Not implemented: interactive Python, all interpreter flags,
`.pth` startup hooks, editable-install semantics, shell activation, transparent
rewriting of installed absolute shebangs, per-view `sys.prefix`, build-ABI repair,
automatic subprocess interception or package mutation isolation. Use `--entry`
for pip-created console entrypoints rather than executing their generated shebangs.
Resolver locks across different devices remain the responsibility of the requested
packages/artifact selection; the core does not invent a second resolver.

## Native and archive boundaries

`execution:"trusted"` and `permissions.spawn:true` are required before acquisition
or native steps. `spawn:false` prevents both. `permissions.fs` does not confine
children; inherited OS authority remains. This stage does not host untrusted
third-party native packs or claim kernel isolation.

The extractor accepts regular files, directories and relative symlinks in a
bounded USTAR TAR. It validates checksums, sizes, unique entry paths and types
before writes; prohibits parent traversal, absolute/backslash/colon paths and
any file/link beneath an archive-defined symlink. Links are written last, and
link targets containing parent traversal are rejected. TAR hardlinks, special
device/FIFO entries, PAX headers and GNU long-name records are rejected. This
conservative subset deliberately refuses some legitimate archives. Repack a trusted
distribution into that subset or supply an acquired installer recipe for its format.

Compressed HTTPS transfers and decompressed archives have 256 MiB limits;
decompressed TAR content is bounded but still buffered. The peak footprint can
exceed that limit during buffer concatenation. Streaming file-by-file extraction
and larger-distribution support are further work. Deep HTTPS transfers have a
120-second deadline; local paths and file URLs work offline. Unpinned sources
remain trusted-source choices; no checksum is invented or required by default.

## Portability evidence

| Surface | This stage |
|---|---|
| Linux/x64 Node + native CPython | Executed integration and timing checks |
| Native Windows and macOS | Host recipe selection and native path/discovery implemented; execution unverified |
| Android/Termux | Native host Python discovery possible; execution unverified; no Bionic standalone runtime bundled |
| Browser/webview | Not included or tested in this source attachment |
| Moving `.grave/` across roots/devices | Absolute references do not silently become valid; reprovision on the new host; preserve writable data |
| Genuine public standalone CPython distribution | Not downloaded or verified; offline test used a real locally reconstructed interpreter/stdlib with host dynamic-library dependencies |

## Next bounded stage

Continue Phase I with real device runs and broader acquisition catalogs while
holding the same core byte gate. Prioritize missing native formats, explicit
package locks/artifact inventories, interruption recovery, and executable behavior
that prevents this view from replacing a project's venv. Preserve the broad recipe
surface instead of adding a bespoke command for every package manager.

Phase II must measure a resident host request **through validated persisted view
creation and response**, as well as CLI creation and first useful execution.
The API already avoids process startup for provisioning. The current benchmark
shows the fresh-host boundary separately; work there should target a reusable
execution host or acquired compiled adapter, with its bytes and setup costs counted.
Each optimization must keep real acquisition/validation and conflicting-version
tests intact. Cold downloads, package resolution, disk acquisition and fresh process
launch remain separate measured costs rather than being relabeled as a 6 ms install.
