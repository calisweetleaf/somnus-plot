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

### 2026-10-20 13:55 UTC — Droid (Keeper) — P07-09 landed
- Base: `9f6f548`.
- Did: Landed forager-4's host bootstrap: `capabilities/bootstrap.mjs` (37,922 B; inspect/plan/acquire/verify/activate/kit), `bootstrap/plot.sh`, `bootstrap/plot.ps1`, `bootstrap/recipes/{node,python,git,zlib}.json` (official sha256 pins; musl Node from unofficial-builds, labelled), `bootstrap/hosts/README.md` (Windows/macOS/Termux runbooks, NOT RUN). Wired `step bootstrap` into `scripts/gate.sh`.
- Validation: `node tests/bootstrap.mjs` → 21/21 on the reference host, including online official-source checks (network available) and a Node-absent launcher with PATH masked. The suite reports offline checks as NOT RUN when no network and no cache exist.
- Proof facts: kit Node archives are the pinned upstream files (never repacked from the host `node`), which closes Fletcher call 17. Android has no upstream Node/Python build, so the route is operator-supplied `PLOT_NODE`.
- Next agent: P07-05 (Keeper).
- Hazards: the suite downloads about 60 MB into `$TMPDIR/plot-bootstrap-cache` on first run. Windows/macOS/Termux remain NOT RUN.

### 2026-10-20 14:05 UTC — Droid (Keeper) — P07-03 landed
- Base: `7e13d89`.
- Did: Landed forager-3's `capabilities/assembler.mjs` (51,459 B; `verifyWheel`, `installWheels`, `assembleFromBank`, `planWheels`, CLI incl. `plan-wheels`) and `tests/assembler.mjs`. Wired `step assembler` into `scripts/gate.sh`. Contracts v1.5 records the npm component object, the layer `.plot.json` `inputs[]`, and `BANK_CHANGED`.
- Validation: lane `node tests/assembler.mjs` 15/15 (in place and in a disposable copy); lane `scripts/gate.sh` PASS. Every installing check consumes a code-emitted plan; runtime labels `{"shallow-host":8}`; owned-runtime check NOT RUN (`PLOT_TEST_OWNED_PYTHON` unset).
- Next agent: P07-05 (Keeper, in progress); P07-07 composes assembler with bootstrap-acquired Python for the `owned` label.
- Hazards: markers in `Requires-Dist` are recorded unsupported, not evaluated; glibc Linux wheel tags only; case-only path collisions not detected; an acquisition pin from a killed writer awaits reconciler release.

### 2026-10-20 14:50 UTC — Droid (Keeper implemented; wore Sentinel after code) — P07-05 landed
- Base: `c323f7d`.
- Did: Standby claim and sustainable capacity in `capabilities/resident.mjs` (39,085→~47,900 B). Single-use standby workers (`--standby <root> <slot>`) record `standby/<slot>/standby.json`, warm their claim path on scratch files, announce `ready`, and retire on `shutdown`, supervisor instance change, or 5 s unreachable. The claim RPC writes one write-once `claimed.json` (owner, rid, rotated control endpoint) before replying. Supervisor pool: ready 2 / maxStarting 2 / maxWaiting 16 (`PLOT_RESIDENT_READY`, `PLOT_RESIDENT_MAX_STARTING`, `PLOT_RESIDENT_MAX_WAITING`); lease decided synchronously before durable acceptance; reply `{claimed, determinate, instance, path:standby|cold|waited, t:{reserved,published,durable,claimed,replied}}`. Lost ACK adopts `claimed.json`; a second worker is tried only when the first is proven gone without a claim; three proven-gone attempts fence the job `interrupted`; a live, silent standby gives `determinate:false` and keeps capacity. Restart reconciliation removes dead standby records and dispatches published, never-claimed jobs. `submission.json` and the rid record fsync on the libuv pool, overlapping the claim RPC; the reply waits for them.
- Validation: `PLOT_REQUIRE_SEED_COUPLED=1 scripts/gate.sh` → `gate: PASS` (24/24, 41/41 resident, 12/12, 15/15 assembler, 21/21 bootstrap (online checks ran), smoke). Nine new resident checks: durable claim before reply; supervisor SIGKILL right after reply; crash injection before-claimed (retried 1, succeeded) / after-claimed and after-status (adopted, interrupted, no second worker); lost ACK adopted; duplicate simultaneous rid → 1 job; bursts 2/8/16/32 (32 → 16 accepted, 16 retryable capacity; peakStarting 2); idle expiry 5.0 s after supervisor SIGKILL and clean stop; orphan dispatch after restart; preliminary warm submit-and-claim p50 3.87 / p95 5.04 / p99 7.54 ms (n=120, all `standby`).
- Sentinel (after code): only new signal is the test-only self-SIGKILL hook (`PLOT_TEST_CLAIM_CRASH`, requires a fresh marker file); standby adoption requires the spawned pid, this supervisor's instance and a live identity.
- Decisions (contracts v1.6): see §14.
- Next agent: P07-06 resident environments.
- Hazards: preliminary p95 margin ~1 ms on this host; p99 above 6 ms. The sustained Poisson row (P07-08) is not yet measured. A power loss between the overlapped fsyncs and the reply is not tested (no device).

### 2026-10-20 15:40 UTC — Droid (Keeper implemented; Sentinel after code) — P07-06 landed
- Base: `89f924e`. Correction to the P07-05 entry: resident was 49,563 B after P07-05, not ~47,900.
- Did: Resident execution environments inside `capabilities/resident.mjs` (now 69,478 B): supervisor ops `activate`, `interact`, `env_inspect`, `deactivate`; one detached Environment Host per incarnation (`--env-host`) that owns the env pin and its tenants; Python tenant (view interpreter, `-I -S -u`, persistent globals, last-expression result) and Node tenant (`--tenant-node`, `vm.runInThisContext`, `__plot_session__`, `__plot_assets__`, `require`) as direct children with u32+JSON frames on fd 3; fd 1/2 captured per turn up to 1 MiB with raw end-of-turn markers so `os.write(1)`, replaced `sys.stdout` and late output are attributed correctly; 1 in flight + 8 queued, overflow `busy`; turn rid records and outcome records under the incarnation; `exec` turns; deadlines kill the tenant and retire the incarnation `interrupted`/`lost`; host death proven by identity and fenced; tenants exit on fd-3 EOF. New `tests/resident-env.mjs` (21 checks), wired into `scripts/gate.sh` and its `--evidence` list.
- Validation: `PLOT_REQUIRE_SEED_COUPLED=1 scripts/gate.sh` → `gate: PASS` (24/24, 41/41 resident, 21/21 resident-env, 12/12, 15/15, 21/21, smoke).
- Proof facts: preliminary warm turns (n=200, quiet run): Python native call p50 2.64 / p95 3.44 ms; Node session + acquired package p50 2.54 / p95 3.23 ms.
- Decision: the resident suite's warm submit-and-claim check measured p95 11.6 ms under full-gate load vs 5.0–6.6 ms quiet; it now reports always and asserts only with `PLOT_ASSERT_LATENCY=1`. The frozen 6 ms rows are asserted by the quiet-host benchmark (P07-08).
- Next agent: P07-07 integration.
- Hazards: Node turns share one event loop, so a turn's timers outlive it (by design: the heap persists). Python `SystemExit` inside a turn is reported `failed`, not exit. Env pin ref uses `<name>.<incarnation>` (file-name safe) instead of `<name>/<incarnation>`.
