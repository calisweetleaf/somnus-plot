# Somnus Plot — Cognitive Bootstrap and Execution Router

> Load this file at the start of every agent session. It routes you to the
> surface that owns the work, what that surface connects to, what proves a
> change, and where work goes next. It does not replace the source, the tests,
> the version contracts, or operator direction.

## Project identity and active posture

| Field | Current value |
| --- | --- |
| Repository | `somnus-plot`, root `/home/factory-user/repos/somnus-plot` (remote `origin` = `calisweetleaf/somnus-plot`) |
| Purpose / long outcome | A tiny seed (Node stdlib core, 9,063-byte ceiling) that constructs, persists and executes complete environments by composition rather than by carrying them. Operator horizon: a fully persistent virtual machine; v10 is the predicted completion. |
| Status in Somnus | Laboratory experiment. Plot has **no role** in broader Somnus and must not become a dependency of it. First Flash Pack. |
| Landed version | v0.6.0 "Persistent Native Execution" (`package.json`, `manifest.json`) |
| Active packet | v0.7 Wave 1 (`P07-01`, `P07-02`, `P07-03`, `P07-09`) **DISPATCHED** in `TASK.md`; architecture `PLAN.md`; frozen interfaces `docs/V07-CONTRACTS.md` |
| Completion witness | `scripts/gate.sh` → `gate: PASS` (build determinism, core ≤ 9,063 bytes, 24/24 integration, 19/19 resident, clean-package smoke) |
| Landed state | Everything listed as PASS in `evidence/RESULTS.md` (2026-10-17 run) and re-run locally 2026-10-20 (see `docs/CONTEXT.md`) |
| Deferred / unverified | Windows/macOS/Termux execution, reboot/power-loss durability, process-tree ownership, quotas, hostile-code sandboxing, worker pooling, GC, full Python CLI/venv emulation, browser host. See the "Unimplemented or unverified" table in `evidence/RESULTS.md`. |

## Session entry route

| Need | Read first | Why | Then route to |
| --- | --- | --- | --- |
| Resume active work | `TASK.md` active packet + newest entry in `docs/NOTEPAD.md` | Actual assignment and last handoff | Packet Required Reads |
| Current reality | `docs/CONTEXT.md` + newest NOTEPAD entry | State, gate posture, blockers | Active packet |
| Why Plot exists / what it must never become | `docs/Plot-Fable.md` | Constitutional narrative: no-assignment status, seed vs catalog, Flash principle, v0.7 direction | `docs/MEMORY.md` laws |
| Durable law or vocabulary | `docs/MEMORY.md` | Stable decisions separated from status | Relevant contract doc |
| Acquisition / view / Python tenant behavior | `STAGE-1.md` then `src/plot.mjs` | v0.5 contract still governs these | `tests/integration.mjs` |
| Resident / jobs / recovery behavior | `PERSISTENT-NATIVE.md` then `capabilities/resident.mjs` | v0.6 contract | `tests/resident.mjs` |
| Measured numbers | `evidence/RESULTS.md` | Only measured claims are citable | `evidence/*.json` raw samples |
| Original v0.4 audit / lineage | `baseline/REPORT.md` | Historical findings and defects | Do not edit `baseline/` |
| Add, move, delete files | Active packet + `filetree.md` | Keep topology coherent | Refresh `filetree.md` |
| State disagreement | NOTEPAD, CONTEXT, last gate output | Reconcile before new work | Reconciliation packet in `TASK.md` |

## Surface router

| Surface | Owns / does | Read when | Does not own | Neighbors / consumers | Change evidence | Next route |
| --- | --- | --- | --- | --- | --- | --- |
| `src/plot.mjs` | **Source of truth** for the foreground core: manifest/DAG, host recipe selection, acquisition into `.grave/objects`, ledger `data.json`, views `.grave/envs`, Python tenant, USTAR extractor, step runner. Exports `openPlot`. | Any core behavior change | Resident lifecycle | `build.mjs` → `main.js`; imported by `capabilities/resident.mjs` via core path; `tests/helpers.mjs` | `node tests/integration.mjs` 18/18 | Rebuild `main.js` |
| `main.js` | **Generated** compacted core. The shipped 9,061-byte bundle. | Checking shipped bytes | Behavior (never hand-edit) | `src/plot.mjs`, `build.mjs`, resident launcher, package-smoke | `node build.mjs` prints `core_bytes`; gate `cmp` | `src/plot.mjs` |
| `build.mjs` | Deterministic compactor; renames listed private identifiers; enforces 9,063-byte ceiling; `node --check` | Core bytes exceed ceiling or a new identifier needs shortening | Core semantics | `src/plot.mjs`, `main.js` | Rebuild identical bytes from unchanged source | `main.js` |
| `capabilities/resident.mjs` | Optional acquired resident capability (20,708 bytes): supervisor, detached per-job workers, socket protocol, recovery, cancellation. Exports `request`, `recover`, `start`, CLI. | Any persistence/job/supervisor change | Core byte budget (counted separately) | `manifest.json` `resident` recipe, `tests/resident*.mjs`, `tests/package-smoke.mjs` | `node tests/resident.mjs` 19/19 | `PERSISTENT-NATIVE.md` |
| `manifest.json` | Default demo plot: hosts, trusted execution, capabilities (`samples`, `analysis`, `resident`), Python tenant, steps | Changing the shipped demo or recipe grammar examples | Recipe semantics (`src/plot.mjs`) | `node main.js`, package-smoke | `node main.js` (needs host Python) | `STAGE-1.md` |
| `package.json` | Version and npm script aliases (`go`, `build`, `test`, `bench`, `resident`). No dependencies by law. | Version bump | Runtime behavior | All docs citing version | Gate | `docs/CONTEXT.md` |
| `STAGE-1.md` | v0.5 acquisition/view/Python/TAR contract (2026-10-14) | Acquisition, views, tenants, archives | Interruption recovery and resident (superseded by PERSISTENT-NATIVE) | `src/plot.mjs`, integration tests | Integration suite | Source |
| `PERSISTENT-NATIVE.md` | v0.6 resident contract: commands, `.grave/resident` ownership, recovery, limits | Resident behavior or limits | Measured results | `capabilities/resident.mjs` | Resident suite | Source |
| `README.md` | Quick start | User-facing usage changes | Contracts | Both contract docs | Review | — |
| `tests/helpers.mjs` | Fixtures: scratch dirs, manifests, real wheel + C extension build, TAR builder, CLI runner | Adding tests | Expectations | All `tests/*.mjs` | — | Test files |
| `tests/integration.mjs` | 18 v0.5 regression checks; **writes `evidence/integration.json`** | Core change | Resident | `src/plot.mjs`, `main.js` | `18/18 integration checks` | — |
| `tests/resident.mjs` | 19 resident checks with real sockets/processes/SIGKILL; **writes `evidence/resident-integration.json`** | Resident change | Core | `capabilities/resident.mjs` | `19/19 resident integration checks` | — |
| `tests/package-smoke.mjs` | Deploys only `main.js`, `manifest.json`, `package.json`, `capabilities/resident.mjs`; Node-only job; **writes `evidence/package-smoke.json`** | Deployment surface change | — | Shipped file set | Exit 0, expected output | — |
| `tests/benchmark.mjs`, `tests/resident-benchmark.mjs` | Timing series; **write `evidence/benchmark.json`, `evidence/resident-benchmark.json`** | Performance claims | Correctness | Six-millisecond gates | Gates in JSON | `tests/report.mjs` |
| `tests/report.mjs` | **Generates `evidence/RESULTS.md`** from evidence JSON (its prose is a template inside this file) | Changing the report wording | Measurements | `evidence/*.json` | Regenerate | — |
| `evidence/` | Evidence of record for v0.6 (2026-10-17, linux/x64 Xeon container, Node v24.19.0) | Citing a number or a PASS | Design intent | `tests/*`, `tests/report.mjs` | Only `scripts/gate.sh --evidence` refreshes it | — |
| `baseline/` | Frozen lineage: v0.4 audit (`REPORT.md`, `plot_probe.py`, `observed-results.json`, example plot), `somnus-plot-v0.5.zip`, `v0.5-evidence/` | Lineage questions | Current behavior | Contract docs cite it | **Never edit** | — |
| `docs/Plot-Fable.md` | Constitutional narrative and v0.7 direction ("The Seventh Flash") | Before any architectural or scope decision | Measured claims (defer to evidence) | `docs/MEMORY.md`, `TASK.md` queue | Operator-owned | MEMORY |
| `scripts/gate.sh` | Integrated gate (disposable copy by default; `--bench`; `--evidence` in place) | Before landing anything | Test semantics | All tests | `gate: PASS` | Handoff |
| `PLAN.md` | v0.7 master architecture plan (operator-supplied) | Scope, laws 11–12, acceptance matrix §8 | Behavior (source wins) | `TASK.md`, contracts | Review | `docs/V07-CONTRACTS.md` |
| `docs/V07-CONTRACTS.md` | Frozen v0.7 shared interfaces: lock order, pins, request IDs, lifecycles, closure schema, workloads, ownership | Before any v0.7 packet | Implementation | Every v0.7 lane | Amendment row + consumers updated | Packet |
| `TASK.md` | Active and queued packets | Assignment | Design semantics | NOTEPAD, CONTEXT | `validate-packet` | Packet |
| `docs/CONTEXT.md` / `docs/NOTEPAD.md` / `docs/MEMORY.md` | Current snapshot / append-only log / durable law | See session entry | — | Each other | Synchronized after state change | — |
| `filetree.md` | Whole-repo topology map | Reorientation, after structural change | Task routing, authority | All roots | Refresh after add/move/delete | This router |
| `.grave/`, `data.json` (runtime, gitignored) | Plot state created by running a plot at this root | Debugging a local run | Anything in git | `src/plot.mjs`, resident | — | Delete freely only if created by your own run |

## Local authority and contradiction route

| Boundary | Intent | Local owner | Generated / consumers | Evidence | Conflict rule |
| --- | --- | --- | --- | --- | --- |
| Core behavior | `STAGE-1.md`, `docs/Plot-Fable.md` | `src/plot.mjs` | `main.js` | `tests/integration.mjs` | Source wins over `main.js`; a stale `main.js` is a build defect, not a behavior. |
| Core byte ceiling | 9,063 bytes (original v0.4 bundle) | `build.mjs` | `main.js` | `core_bytes` in build output and integration check 1 | Exceeding it fails the gate. Raising it is an operator decision recorded in MEMORY with the reason ("did the seed learn a more general law?"). |
| Resident behavior | `PERSISTENT-NATIVE.md` | `capabilities/resident.mjs` | Acquired copies in `.grave/objects/resident-*` | `tests/resident.mjs` | Contract doc + tests win; resident code never moves into the core. |
| Measured claims | Six-millisecond objective for **cached view operations, p95** | `tests/*benchmark.mjs` | `evidence/RESULTS.md` via `tests/report.mjs` | `evidence/*.json` | Only numbers in evidence may be cited; never merge cold, startup and completion costs into one number. |
| Product scope | Operator + `docs/Plot-Fable.md` | Operator | `TASK.md` | — | Operator direction wins over the fable's recommendations; the fable wins over generic convention. |
| History | — | `baseline/`, NOTEPAD | — | — | Append or preserve; never rewrite. |

Record a real contradiction in `docs/CONTEXT.md` under "Open contradictions" and route a decision to the operator rather than guessing.

## Hard laws (all packets)

1. `main.js` stays Node standard library only, no npm dependencies, at or under the ceiling. Capability arrives by acquisition into `.grave/`, never by growing the core with the catalog.
2. Do not import a mechanism because a larger Somnus/Obsidian-scale system has it. Obsidian is a scale reference, not lineage. Do not make Plot depend on Somnus being present, and do not make Somnus depend on Plot.
3. Do not call Plot a sandbox. Native execution is trusted; `permissions.fs` is not confinement.
4. Do not solve Python by finding a complete host environment and declaring success; distinguish shallow host Python from owned runtime material.
5. Never fabricate a PASS. Missing toolchain, network or device → `NOT RUN` / `NOT VERIFIABLE`. Linux evidence does not establish other hosts.
6. Never hand-edit `main.js`, `evidence/`, or `baseline/`.
7. Do not push. Commit only when the operator asks.

## Packet route

Packets live in `TASK.md`. The active packet is named in its "Current execution state" table. Every packet has, in order: Mission, Required Reads, Invariant, Surfaces, Hard Bans, Validation, Exit, Handoff. A DRAFT packet is not executable until the operator dispatches it. Validate a packet with:

~~~
node ~/.factory/skills/somnus-accelerate/scripts/validate-packet.mjs TASK.md
~~~

## Implementation, evidence, and validation route

| Change type | Inspect / update | Required proof |
| --- | --- | --- |
| Core behavior | `src/plot.mjs` → `node build.mjs` → commit regenerated `main.js` with it | `scripts/gate.sh`; byte count reported in handoff |
| Resident behavior | `capabilities/resident.mjs`, `PERSISTENT-NATIVE.md` if contract changes | `scripts/gate.sh` |
| New capability recipe or acquired module | `capabilities/`, `manifest.json` example, package-smoke deployed set if shipped | `scripts/gate.sh`; bytes counted separately from core |
| Performance claim | Benchmark file, then `scripts/gate.sh --evidence` | New `evidence/RESULTS.md` with host stated |
| Report wording | `tests/report.mjs` (not `evidence/RESULTS.md`) | `node tests/report.mjs` |
| New/moved/deleted files | `filetree.md`, this router | Gate + topology refresh |
| Version bump | `package.json`, `manifest.json`, `README.md`, contract doc for the version, `tests/report.mjs` title | Gate |

Primary gate (does not touch tracked files):

~~~
scripts/gate.sh
~~~

Prerequisites: Node ≥ 22, `python3` with `venv`, `pip` and headers (`Python.h`), and a C compiler. Without the Python toolchain the v0.5 optional-Python checks fail; report that as NOT VERIFIABLE, not as a Plot regression. Benchmarks: `scripts/gate.sh --bench`, run with no other workload. Evidence refresh (rewrites `evidence/`, review the diff): `scripts/gate.sh --evidence`.

## Continuity and handoff

Before a state-changing packet is landed:

1. Run `scripts/gate.sh` and repair real failures.
2. Regenerate coupled outputs (`main.js`, evidence when claims change).
3. Append one entry to `docs/NOTEPAD.md` in its stated format.
4. Refresh `docs/CONTEXT.md`; add to `docs/MEMORY.md` only durable law.
5. Mark the packet landed in `TASK.md` and name the next packet.
6. Refresh `filetree.md` after structural changes.

The next agent starts here, then the newest NOTEPAD entry, then the active packet.
