# Somnus Plot — Task and Packet Board

> Current and queued executable packets. Not the authority for behavior; route
> authority through `AGENTS.md`.

## Current execution state

| Field | Value |
| --- | --- |
| Product / long goal | Persistent virtual machine built by composition from a tiny seed; v10 predicted complete |
| Current base | `main` @ `896f48d` (v0.6.0) plus uncommitted control plane (`AGENTS.md`, `TASK.md`, `docs/`, `scripts/gate.sh`, `.gitignore`) |
| Active packet | `P07-01` Dependency cartographer — **DRAFT, awaiting operator dispatch** |
| Current gate | `scripts/gate.sh` |
| Expected result | `gate: PASS` |
| Handoff surface | `docs/NOTEPAD.md` |
| Current blocker | Operator has not yet confirmed v0.7 scope or P07-01 ordering |

If `AGENTS.md`, this board, `docs/CONTEXT.md`, the newest NOTEPAD entry, the
repository state, or gate evidence materially disagree, run a bounded
state-reconciliation packet before unrelated implementation.

## Active packet

### Identity

- Packet ID: P07-01
- Title: Dependency cartographer — minimum capability closure over a local Node package corpus
- Owner / lane: unassigned (operator dispatch)
- Status: DRAFT
- Depends on: v0.6.0 landed state; operator confirmation of v0.7 order

### Mission

Teach Plot to read a local Node package corpus (directories containing
`package.json`, and npm-style tarballs if a reader for them fits the acquired
capability) and answer: given a requested capability, what is the smallest
available closure of components that satisfies it on this host? The cartographer
reads `dependencies`, `optionalDependencies`, `peerDependencies`,
`bundleDependencies`/`bundledDependencies`, `bin`, `engines`, `os`/`cpu`, `main`
and conditional `exports`; builds the graph; collapses shared nodes; reports
which nodes are already present in `.grave/`; prunes optional or
host-inapplicable branches; and emits a deterministic closure plan. It reads and
plans only. It installs nothing new. It ships as an **acquired capability** under
`capabilities/`, not inside the core.

### Required Reads

- `docs/Plot-Fable.md` section "The Seventh Flash", first acceleration — the operator-endorsed intent and the `A→B,C; B,C→D; D in grave` example that must hold
- `STAGE-1.md` "Representation and ownership" and "Acquisition transaction" — resource identity rules the closure plan must respect (no content hashes as identity)
- `src/plot.mjs` — how `needs`, host recipe selection and the ledger `data.json.assets` represent what is already in `.grave/`
- `capabilities/resident.mjs` top section and `manifest.json` `resident` recipe — the pattern for an optional acquired capability
- `tests/helpers.mjs` and `tests/resident.mjs` harness style — real fixtures, no mocks

### Invariant

`main.js` remains ≤ 9,063 bytes and unchanged in behavior unless the operator
approves a core change; the existing 18 integration and 19 resident checks and
the package smoke keep passing. The cartographer never executes package code,
never writes outside its own output and scratch paths, and never touches the
network. Resource identity remains the existing recipe/host/dependency key, not
a hash. The closure result is deterministic for identical corpus input.
Conditional `exports` resolution follows Node's documented condition order for
the selected conditions; unresolved or unsupported shapes are reported, not
guessed.

### Surfaces

| Surface | Intended action | Relation |
| --- | --- | --- |
| `capabilities/cartographer.mjs` | CREATE | Owner (acquired capability) |
| `manifest.json` | EDIT only if adding an example `cartographer` recipe | Demo |
| `tests/cartographer.mjs` | CREATE (real on-disk package fixtures built in a scratch dir) | Evidence |
| `scripts/gate.sh` | EDIT to add the new test | Gate |
| `src/plot.mjs`, `main.js` | READ (EDIT only with operator approval) | Core |
| `AGENTS.md`, `filetree.md`, `docs/CONTEXT.md`, `docs/NOTEPAD.md` | REFRESH | Continuity |

### Hard Bans

- Do not add npm dependencies or call `npm`/`npx`/`pnpm` as the resolver.
- Do not reimplement npm install; no fetching, extracting into `node_modules`, or lockfile writing.
- Do not grow `main.js` to host the cartographer.
- Do not execute package lifecycle scripts or import package code.
- Do not claim Windows/macOS/Termux results from Linux runs.
- Do not hand-edit `evidence/`.

### Validation

~~~
scripts/gate.sh
node tests/cartographer.mjs
~~~

Expected: `gate: PASS`; cartographer suite all-pass including (a) shared
dependency `D` appears once and is marked present when it exists in `.grave/`,
(b) optional and `os`/`cpu`-inapplicable branches are pruned and reported,
(c) conditional `exports` selects the expected entry for `node`+`import` vs
`require`, (d) a cycle and a missing dependency fail closed with a named reason,
(e) identical input produces byte-identical plan output, (f) `main.js` size
unchanged.

### Exit

- Record: final commit or working-tree state
- Record: exact gate output and cartographer check count
- Record: `capabilities/cartographer.mjs` byte size (separate from core)
- Record: which `package.json` fields are supported and which are reported as unsupported
- Synchronize: `docs/NOTEPAD.md`, `docs/CONTEXT.md`, `filetree.md`, `AGENTS.md` surface router row

### Handoff

Next agent: wait for operator dispatch of P07-01; once dispatched, read the
Required Reads in order, build the fixture corpus first in
`tests/cartographer.mjs`, then implement `capabilities/cartographer.mjs` until
the suite passes, then run `scripts/gate.sh`.

Hazards: conditional `exports` and peer-dependency semantics have edge cases
that can tempt a bespoke resolver; report unsupported shapes rather than
inventing behavior.

## Queued v0.7 directions (from `docs/Plot-Fable.md`, not yet packetized)

Order is the fable's; the operator decides actual order.

| ID | Direction | Notes |
| --- | --- | --- |
| P07-02 | Local seed bank: offline installation as a first-class mode from component archives, recipes and adapters | Preserve component boundaries; one bank, many plots |
| P07-03 | Bootstrap ladder: alternate ignition paths so Node is not equivalent to Plot | Node SEA as one disposable rung, not the answer |
| P07-04 | Python as compositional target: interpreter, stdlib, extensions, bootstrap, layers, entrypoints | `ensurepip` where available; other recipes elsewhere |
| P07-05 | Move the six-millisecond bell: durable submission p95 (7.861 ms) below 6 ms; worker reservoir / prewarmed slots | Measure each boundary separately |
| P07-06 | Real device runs: Windows, macOS, Android/Termux | Record forks; reduce bootstrap contract from evidence |

## Landed packets

| ID | Title | Landed | Evidence |
| --- | --- | --- | --- |
| P06-CP | Accelerate control plane installed | 2026-10-20 | `docs/NOTEPAD.md` first entry |
