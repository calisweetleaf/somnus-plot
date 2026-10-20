# Somnus Plot — Execution Ledger

Append-only. Newest entry at the bottom. Never rewrite an earlier entry; correct it with a new one.

Format:

~~~
### YYYY-MM-DD HH:MM TZ — <executor> — <lane>
- Base:
- Did:
- Validation:
- Proof facts:
- Surfaces synchronized:
- Next agent:
- Hazards:
~~~

### 2026-10-20 00:55 CDT — Droid — control plane (P06-CP)
- Base: `main` @ `896f48d` (v0.6.0), clean tracked tree; untracked `docs/Plot-Fable.md` supplied by operator. Repo moved from `LAB/Experiments/projects/somnus-plot` to `Repositories/somnus-plot` on 2026-10-19.
- Did: Installed Accelerate control plane: `AGENTS.md` (router), `TASK.md` (P07-01 DRAFT + v0.7 queue), `docs/CONTEXT.md`, `docs/MEMORY.md`, this ledger, `scripts/gate.sh` (disposable-copy gate; `--bench`; `--evidence`), `.gitignore` (`/.grave/`, `/data.json`). Refreshed `filetree.md`. No source, test, evidence or baseline file changed.
- Validation: `scripts/gate.sh` → `gate: PASS` (65 s). `validate-packet.mjs TASK.md` → PASS. Benchmarks NOT RUN.
- Proof facts: `core_bytes` 9,061 ≤ 9,063; rebuilt `main.js` byte-identical to committed; 18/18 integration; 19/19 resident; package smoke PASS. Host: Linux 7.0.0-38, Node v24.14.0, Python 3.14.4, gcc. `git status` shows no tracked modifications after the gate.
- Surfaces synchronized: `AGENTS.md`, `TASK.md`, `docs/CONTEXT.md`, `docs/MEMORY.md`, `docs/NOTEPAD.md`, `filetree.md`.
- Next agent: Ask the operator to dispatch or reorder P07-01 in `TASK.md`; do not start implementation while it is DRAFT.
- Hazards: Core has 2 bytes of headroom; any `src/plot.mjs` change will likely need `build.mjs` identifier additions or an operator ceiling decision.

### 2026-10-20 12:10 UTC — Droid (Opus 5.5, Keeper/coordinator) — P07-00 contract freeze
- Base: `main` @ `b72a98d` (single commit `.`); docs previously cited `896f48d` and root `/home/daeron/...`, both reconciled. Untracked operator files `.colony/`, `.factory/`, `SWARM.md`, `attachments/` left untouched.
- Did: Placed operator-supplied v0.7 master plan as `PLAN.md` (§7 packet detail moved to `TASK.md`). Wrote `docs/V07-CONTRACTS.md` (contracts v1: durability primitives, global lock order, historical reuse, pins with pin-then-validate, request IDs, prune tombstones, job/standby/env lifecycles, closure schema `plot.closure/1`, bootstrap entry + host matrix, frozen workloads incl. nominal 5 submit/s × 200 s, ownership map). Rewrote `TASK.md` with P07-00..P07-09. Refreshed `AGENTS.md`, `docs/CONTEXT.md`, `filetree.md`.
- Validation: `scripts/gate.sh` → `gate: PASS` (18/18 integration, 19/19 resident, package smoke). Packet validator NOT RUN (`~/.factory/skills/somnus-accelerate` absent on this host).
- Proof facts: core 9,061/9,063; resident 20,708; host Linux 6.1.158+ x64 Xeon 2.60GHz 4 vCPU 7.9 GiB ext4, Node v24.22.0, Python 3.12.3, gcc, git. No Windows/macOS/Termux host available.
- Surfaces synchronized: `PLAN.md`, `docs/V07-CONTRACTS.md`, `TASK.md`, `AGENTS.md`, `docs/CONTEXT.md`, `docs/NOTEPAD.md`, `filetree.md`.
- Next agent: Wave 1 foragers on P07-01, P07-02, P07-03, P07-09 per `TASK.md`.
- Hazards: 2 bytes of core headroom; sustained-submit bell bounded by worker replenishment; second OS family NOT RUN keeps cross-host acceptance open.

### 2026-10-20 13:05 UTC — Droid (Keeper; wore Sentinel; counted the beat with Fletcher's lexicon) — P07-01 landed
- Base: `fc683f8`.
- Did: Landed forager-1's P07-01: historical exact-key reuse (scan `.grave/objects/<k>-*` under L1, zero spawn), `atom` parent-dir fsync + `create` write-once primitive, `exec` stdout fallback, `pip:false` + `venv --without-pip` for package-less tenants, mandatory foreground pin in `run()`. Compactor strengthened (collision-free alphabet, `;}` drop, `let` joining, numeric folding) and repeated forms removed from src.
- Validation: Keeper `scripts/gate.sh` → `gate: PASS` (build 9,008/9,063, rebuild identical, 24/24 integration, 19/19 resident, smoke). Keeper Sentinel tastes in scratch copy: rebuild deterministic; `a` vs `a-b` prefix collision cannot cross-adopt (keys differ) and v1 reuse spawned nothing. Second independent Sentinel NOT RUN (operator redirected reviewer use).
- Proof facts: `main.js` 9,008 bytes (55 headroom), `src/plot.mjs` 12,017, `build.mjs` 4,586.
- Decision: accepted `pip:false` one-time key change for package-less Python tenants (contracts v1.2).
- Minor: if two valid objects share a key, selection follows `readdirSync` order (harmless; identical identity).
- Next agent: P07-04 (forager-5, running) may now close its seed-coupled checks.
- Hazards: historical scan is O(objects with prefix) on ledger miss; no index.

### 2026-10-20 13:20 UTC — Droid (Keeper; wore Sentinel) — P07-02 landed
- Base: `2b9b384`.
- Did: Landed forager-2's `capabilities/cartographer.mjs` (31,126 B; `planClosure`, `inspectCorpus`, CLI) + `tests/cartographer.mjs` + generated `tests/fixtures/closure/` (sample plan, 11 nodes, ok:true). Wired `node tests/cartographer.mjs` into `scripts/gate.sh`. Contracts v1.3 records presence rule (`recipe.component={ecosystem,name,version}` + host match), placement-qualified duplicate ids, new fields, fail-closed codes.
- Validation: lane `scripts/gate.sh` PASS; Keeper Sentinel in scratch: 12/12, fixture regeneration byte-stable, CLI byte-identical across runs, no `child_process`/eval/fetch/dynamic import in the module. Lane mutation testing: 7/8 mutants killed (peer-lookup start at own node_modules survived; SALT).
- Proof facts: supported range grammar per contracts §10; unsupported forms reported (tags, git+, npm:, file:, workspace:, URLs, 4-part, `~>`).
- Next agent: P07-03 must stamp `recipe.component` for npm presence and add `planWheels` (Fletcher TEMPO 15).
- Hazards: placement is deterministic hoisting, not npm arborist parity; optional-subtree deep failure fails the plan (stricter than npm).

### 2026-10-20 13:45 UTC — Droid (Keeper; wore Sentinel) — P07-04 landed
- Base: `eef36b8`.
- Did: Landed forager-5's resident work (`capabilities/resident.mjs` 20,708→39,085 B, `tests/resident.mjs` 41,206 B): O(1) reserved admission map built at `serve` start, revisioned `status.json` with fenced reconciler (250 ms / 8 entries / 500 ms probe, off the submit path), worker `done` notification authenticated by supervisor token, `rid` lookup records (`request conflict`, `request expired`), `PLOT_JOB_STATE`/`PLOT_STEP_INDEX`/`PLOT_STEP_OUT`, transitive job pins, pin-safe dry-run/apply prune with tombstone intents and crash recovery, `PLOT_RESIDENT_MAX_ACTIVE`, `launch.json`.
- Validation: Keeper `PLOT_REQUIRE_SEED_COUPLED=1 scripts/gate.sh` → `gate: PASS` (24/24 integration, 32/32 resident, 12/12 cartographer, smoke). Keeper Sentinel: `.kill(` uses only `process.kill(pid,0)` liveness probe and SIGTERM/SIGKILL of the worker's own direct child; no signal is sent to a PID read from a record.
- Decisions (contracts v1.4): job pins released at terminal status; `interrupted` written only by the reconciler and never expired by it; evicted rid leaves an expired marker; completion notify goes to the supervisor recorded in the submission.
- Next agent: P07-05 standby claim (Keeper, per operator 2026-10-20: Keeper implements directly).
- Hazards: ALARM 51 open: seed `run()` does not re-check `.grave/tombstones/<obj>.json` after writing its foreground pin (pin-then-validate gap on the seed side; 55 bytes headroom). PERSISTENT-NATIVE.md not yet updated for v0.7 resident ops (P07-08).
