# Somnus Plot v0.7 — Frozen Shared Contracts (P07-00)

> Interface freeze for packets P07-01..P07-09. Derived from the v0.6 source at
> base `b72a98d` (`src/plot.mjs`, `capabilities/resident.mjs`) and `PLAN.md`.
> Version: **contracts v1**. Any amendment updates every affected consumer in
> the same landing and appends a row to §14. Local choices not listed here
> belong to the implementing lane.

## 0. Base identity and baseline (tasted 2026-10-20)

| Fact | Value | How known |
| --- | --- | --- |
| Git base | `main` @ `b72a98d` (single commit `.`). Older docs cite `896f48d`; that hash is absent from this checkout. | `git log` |
| Repo root | `/home/factory-user/repos/somnus-plot` (docs previously named `/home/daeron/...`) | `pwd` |
| Core | `main.js` 9,061 / 9,063 bytes (2 bytes headroom); `src/plot.mjs` 11,124 bytes | `node build.mjs`, `wc -c` |
| Resident | `capabilities/resident.mjs` 20,708 bytes | `wc -c` |
| Baseline gate | `scripts/gate.sh` → `gate: PASS`; 18/18 integration, 19/19 resident, package smoke PASS | `/tmp/p0700-baseline-gate.log` |
| Reference host | Linux 6.1.158+ x64, Intel Xeon @ 2.60GHz, 4 vCPU, 7.9 GiB RAM, ext4 on `/dev/root` (container/VM layer, device class not observable), Node v24.22.0, Python 3.12.3, gcc, git | `nproc`, `/proc/cpuinfo`, `free`, `df -T` |

Ceilings C-01..C-05 confirmed by source reading: C-01 `provision` checks only
`old.assets?.[k]`; C-02 `exec` omits stdout, `atom` lacks dir fsync, shallow venv
always runs ensurepip; C-03 `launchWorker` spawns after submission; C-04 submit
loop `for(... readdirSync(jobs)) await summary()`; C-05 no `PLOT_JOB_STATE`, no prune.

## 1. Durability primitives (all writers)

- `atom(path, value)`: write temp `wx` 0600 → fsync → rename → fsync parent dir (POSIX). Windows: no dir fsync, disclosed.
- `once(path, value)`: `wx` 0600 create → fsync → fsync parent dir. Used for write-once records (claims, submissions, request lookups, tombstone intents).
- Directories created 0700. Executables keep their modes.
- Logs: append, fsync on close. tmpfs runs are diagnostic only.

## 2. Global lock order

Acquire only in this order; never acquire an earlier lock while holding a later one.

| Rank | Lock | Holder | Scope |
| --- | --- | --- | --- |
| L0 | `.grave/.recovery/` (mkdir) | `recover()` | Acquisition-lock reconciliation |
| L1 | `.grave/.lock/` (mkdir + `owner.json {pid,birth?,stages}`) | seed `provision`, prune apply, assembler/bootstrap publication into this plot | Object publication, ledger, views, tombstoning |
| L2 | `.grave/resident/.lock/` | supervisor (lifetime singleton) | Admission authority |
| L3 | entity reservations: `.grave/resident/envs/<name>/reserve` (once), `.grave/requests/<rid>.json` (once), `jobs/<id>/claimed.json` (once) | supervisor / env host / worker | One entity each |

Pins (§4) are **lock-free** by the pin-then-validate protocol; they never take L1.
Shared Seed Banks are read-only to consumers; a bank's own maintenance uses the bank's own lock and is never driven by one Plot's roots.

## 3. Object publication and historical reuse (P07-01)

- Identity unchanged: `key = stable([recipe, [platform, arch], needs.map(n => assets[n].path)])`.
- An object is complete iff `<obj>/.plot.json` exists, parses, equals `{key, path, ...}` with `path` = its realpath inside `.grave/objects`, and `python` (if present) exists. Unstamped stages are never adopted.
- Lookup order inside `provision` under L1: (1) `data.json.assets[k]`; (2) historical candidates `.grave/objects/<k>-*` that are valid for `key` and **not tombstoned**; (3) acquire. Hit on (2) performs zero child spawns and rebinds `data.json.assets[k]`.
- An index (if the lane chooses one) is advisory: a miss or stale entry falls back to the directory scan; it is never authority.
- Tombstoned objects (§6) are moved out of `.grave/objects`, so a scan cannot see them.

## 4. Pins (all reference producers)

Directory `.grave/pins/`, one file per live holder, written with `once` then removed on closure.

```json
{"schema":1,"kind":"job|env|acquisition|foreground|explicit","owner":{"pid":123,"birth":"bootid:ticks|null"},
 "ref":"<job id | env name/incarnation | acquisition id | 'fg' | label>","paths":["/abs/.grave/objects/x-AbC", "..."],"created":"ISO"}
```

- File name: `<kind>-<ref-or-pid>-<random>.json`.
- `paths` is the **transitive** closure of object paths the holder may read.
- **Pin-then-validate:** holder writes the pin, then checks every path exists under `.grave/objects` and has no tombstone intent (§6). On failure it removes the pin and fails retryably.
- Release: `kind=job` on terminal status; `env` on incarnation retirement; `foreground` in `run()` `finally`; `explicit` only by explicit unpin.
- A pin whose owner is proven `absent`/`other` is released by the reconciler; `same`/`unknown` (incl. `birth:null` with a live pid) is retained.
- The seed's `run()` **must** write a `foreground` pin (P07-01) and remove it in `finally`. There is no byte-budget exception: if the pin cannot fit, P07-01 stays open and the Keeper escalates a ceiling decision to the operator per `docs/MEMORY.md` law 3. Default prune never evicts objects.

## 5. Request IDs and lookup (P07-04/05/06)

- Client may send `rid` (`[A-Za-z0-9_-]{1,64}`); CLI generates one. Existing `id` idempotency remains.
- `.grave/requests/<rid>.json` (once): `{rid, kind:"submit"|"turn", target:<job id | env/incarnation/turnId>, digest: stable(request), created}`.
- Retry with same `rid` and same digest returns the existing target's current state; different digest → `request conflict`.
- Retention: lookups for jobs live as long as the job record; prune with `includeJobs` deletes them together. A `rid` whose record was evicted returns `request expired` — never re-executes.
- Turn request records live under the incarnation (§8); same rules.

## 6. Prune and tombstones (P07-04)

Ops: `prune {apply:false, includeJobs:false, cache:{maxAgeDays?, maxBytes?}}`. Dry-run default.

Apply protocol (under L1):
1. Compute roots: latest ledger assets; every `.grave/envs/*.json`; all pins; non-terminal/uncertain jobs and their `submission.json` view snapshots; retained terminal job snapshots (unless `includeJobs` expiry selects them, which releases them first in the same transaction); all non-retired env incarnations; interrupted archives; transitive closure via each object's `.plot.json` key dependency paths. Unparseable metadata ⇒ refuse.
2. For each candidate: write intent `.grave/tombstones/<objname>.json` (once) `{path, reason, at}`.
3. Re-read pins. Any candidate now pinned: delete its intent, retain.
4. Rename candidate into `.grave/tombstones/<objname>/` (same filesystem), fsync parents.
5. Release L1. Physical delete of `.grave/tombstones/<objname>/` then its intent, outside L1.
Recovery: an intent with object still in `.grave/objects` ⇒ re-run steps 3–4 under L1 or remove the intent; an intent with tombstoned dir ⇒ finish deletion.
Audit: `.grave/resident/prune.json` (atom) `{at, apply, policy, retained:[{path,reason}], selected, deleted, failed, recovered}`. Never deletes `.grave/work/*`, interrupted evidence, or bank material.

## 7. Job lifecycle (P07-04, extended by P07-05)

```
reserved -> published(submission.json) -> claimed(claimed.json+owner+control+status running) -> running -> {succeeded|failed|cancelled|timed_out}
any non-terminal --(proof absent|other, fence ok)--> interrupted
any non-terminal --(uncertain)--> unreachable (observation only, holds capacity)
```

- Terminal: `succeeded, failed, cancelled, timed_out, interrupted`.
- `status.json` carries `{id, instance, revision, state, ...}`; `revision` is monotonic, written only by the worker for live transitions.
- Reconciler fence: may write `interrupted` only if (a) owner identity is `absent`/`other`, (b) current `status.json` is non-terminal and its `revision` equals the one observed, and (c) it writes `revision+1` with `reconciledBy`. Lost race ⇒ keep the newer record.
- Admission map: `Map<id, state>` of non-terminal + reservations. Built once at `serve` start before listening for writes; updated by submit, worker completion notification (`{op:'done', id, instance, revision}` authenticated by supervisor token from submission), and a background reconciler.
- Reconciler: interval **250 ms**, max **8** entries examined per tick, 500 ms per-entry probe, never on the submit path.
- Capacity: `maxActive` default 16 (active + reserved + uncertain ≤ limit). Rejection is structured `{error:'capacity', retryable:true}` before any durable acceptance.
- `PLOT_JOB_STATE = jobs/<id>/work/`, `PLOT_STEP_INDEX`, `PLOT_STEP_OUT = jobs/<id>/work/step.json` (P07-04).

## 8. Standby claim protocol (P07-05)

- Standby worker: `--standby <root> <supervisorInstance>`; writes `.grave/resident/standby/<slot>/standby.json {pid,birth,port,token,instance,supervisor}` via atom; idles; exits on `{op:'shutdown'}` or when supervisor `service.json` instance changes / supervisor endpoint unreachable for **5 s** (idle expiry).
- Claim RPC: `{op:'claim', id, rid, token}` → worker (synchronously, before reply): `once claimed.json {pid,birth,instance,claimedAt,rid}`; atom `owner.json`, `control.json` (rotated job token); open logs `wx`; `status.json {state:'running', revision:1}`; remove `standby.json`; reply `{claimed:true, instance, control:{port}}`.
- Supervisor replies `{id, state:'submitted', claimed:true, instance, path:'standby'|'cold'|'waited', determinate:true, t:{reserved,published,claimed,replied}}` only after `claimed:true`.
- Claim timeout/lost ACK: supervisor reads `claimed.json`; if present, adopts it (never a second worker); if absent and the standby is proven gone, retries with another worker; if uncertain, reply `{determinate:false}` and keep capacity reserved.
- Bounds: `ready` default 2, `maxStarting` default 2, `maxWaiting` default 16. Exhaustion: cold spawn only if `starting < maxStarting`, else wait (bounded) or reject retryably.

## 9. Resident environments (P07-06)

Layout (incarnation-scoped):

```
.grave/resident/envs/<name>/current.json            -> {incarnation} (atom)
.grave/resident/envs/<name>/reserve                 (once; held during activation/recreate)
.grave/resident/envs/<name>/inc/<incarnation>/{instance.json, owner.json, control.json, status.json}
.grave/resident/envs/<name>/inc/<incarnation>/turns/<turnId>.json   outcome record
```
Paths named in PLAN §3 (`envs/<name>/instance.json` etc.) resolve through `current.json`; env_inspect reports them.

- States: `starting → active → draining → stopped`; any → `interrupted` (tenant death, destructive timeout, restore failure, host death with proof); `unreachable` observation.
- Turn: `{rid, runtime:'python'|'node'|'exec', code, args, env, cwd, timeoutMs}` + `expectIncarnation` (required). Outcome `{name, incarnation, turnId, rid, state:'succeeded'|'failed'|'interrupted', stateEffect:'retained'|'partial'|'lost', stdout, stderr, result, exitCode, error, lateOutput?}`.
- Tenant control channel: dedicated fd 3 (POSIX) pipe pair or authenticated loopback; frames `u32 length + JSON {v:1, id, ...}`, max 1 MiB. Tenant stdout/stderr (fd 1/2) captured separately; per-turn cap default 1 MiB, excess drained and counted.
- Queue: 1 in-flight, `maxQueued` default 8; overflow → `{error:'busy', retryable:true}`.
- Timeout: host kills tenant (SIGTERM→SIGKILL 500 ms) ⇒ incarnation `interrupted`, `stateEffect:'lost'`.
- Pins: `kind=env`, ref `<name>/<incarnation>`, released on retirement.

## 10. Closure plan schema v1 (P07-02 producer; P07-03, P07-09 consumers)

```json
{"schema":"plot.closure/1",
 "target":{"platform":"linux","arch":"x64","libc":"glibc|musl|null","node":"24.22.0","conditions":["node","import"],
           "python":{"version":"3.12.3","soabi":"cpython-312-x86_64-linux-gnu","tags":["cp312-cp312-linux_x86_64","py3-none-any"]}|null},
 "requested":["a@^1"],
 "nodes":[{"id":"a@1.2.0","ecosystem":"npm|wheel|component","name":"a","version":"1.2.0",
           "source":{"kind":"dir|tgz|whl|bank","path":"<abs>","integrity":"sha256-...|null"},
           "placement":"node_modules/a | node_modules/b/node_modules/a",
           "deps":[{"name":"d","range":"^1","kind":"prod|optional|peer|bundled","resolved":"d@1.0.1|null"}],
           "entry":{"main":"...","exports":{"<subpath>":"<resolved file>|null"},"bin":{"x":"bin/x.js"}},
           "present":{"object":"<abs .grave/objects path>|null","key":"<canonical key>|null"}}],
 "order":["d@1.0.1","b@2.0.0","a@1.2.0"],
 "pruned":[{"id":"...","reason":"os|cpu|engines|optional-absent|optional-incompatible"}],
 "unsupported":[{"where":"a@1.2.0#exports","form":"...","reason":"..."}],
 "diagnostics":[{"code":"cycle|missing|range-unsatisfied|peer-unsatisfied","detail":"..."}],
 "ok":true}
```

- Serialization: object keys sorted except `entry.exports` and other order-significant manifest maps, which preserve source order. `order` is a deterministic topological sort (ties by `id`).
- `ok:false` whenever `diagnostics` contains a fail-closed code; consumers refuse `ok:false` plans.
- Consumers own publication and pinning; the planner writes nothing.
- Producers: `capabilities/cartographer.mjs` emits `npm` nodes; `capabilities/assembler.mjs` `planWheels({bank, target, requirements})` emits `wheel` nodes in the same schema. Every assembler acceptance check that installs a wheel consumes a plan emitted by code, never a hand-written plan.
- Supported range grammar: exact, `^`, `~`, `x`/`*`, comparators `>= <= > < =`, hyphen ranges, `||`. Others → `unsupported`.

## 11. Bootstrap entry and host matrix (P07-09)

- Entry A (Node present): `node main.js` or `node capabilities/bootstrap.mjs inspect|plan|acquire|verify|activate`.
- Entry B (Node absent): `bootstrap/plot.sh` (POSIX sh + `tar` + `gzip` + one of `curl|wget` or an offline kit dir) and `bootstrap/plot.ps1` (PowerShell 5+, `Expand-Archive`/`tar.exe`). Declares its irreducible inputs; obtains Node into `<root>/.grave/host/node-<ver>-<plat>-<arch>/`, then execs the same seed.
- Sources: online official distribution URLs with pinned sha256, or a Seed Bank/kit dir with the same identity/compat records. Source is locked per attempt.
- Install roots user-local under `<root>/.grave/` (or a declared shared bank). No sudo, no package-manager edits; a needed system prerequisite is reported before mutation.

| Host family | Status target for v0.7 run |
| --- | --- |
| Linux x64 glibc (reference) | RUN |
| Linux in fresh container | RUN if a container runtime exists, else NOT RUN |
| Windows x64 | NOT RUN (kit + PowerShell runner shipped) |
| macOS arm64/x64 | NOT RUN (kit + sh runner shipped) |
| Android/Termux aarch64 | NOT RUN (kit + sh runner shipped) |

Cross-host acceptance remains **open** while every non-Linux family is NOT RUN. Searched 2026-10-20: no qemu, wine, docker, podman, pwsh, lxc, vagrant or `/dev/kvm` on the reference host (Fletcher pass).

Provenance rules: a kit's Node archive must come from a pinned official sha256 or a bank record independent of the host binary (never repacked from the host `node`). Any suite importing Python code labels its runtime `owned` (under `.grave/objects` or `.grave/host`) or `shallow-host`; owned-runtime acceptance requires `owned`.

## 12. Benchmark workloads (frozen before tuning)

| Row | Boundary | n | Gate |
| --- | --- | --- | --- |
| `view_lookup` | validated `plot.view(name)` | 1000 | p95 < 6 ms |
| `cached_view_provision` | per persisted series | 1000 | p95 < 6 ms |
| `multi_version_switch` | v1↔v2 both acquired, child spawn count = 0 | 300 | p95 < 6 ms |
| `resident_cached_view_rpc` | authenticated provision RPC | 300 | p95 < 6 ms |
| `durable_submit_and_claim` | request start → reply; request start → control-ready | ≥300 warm | p95 < 6 ms both |
| `sustained_submit` | open-loop **Poisson arrivals, mean 10 submissions/s, 120 s (≥1,200 offered)**, interarrival seed `0x5eed07`, schedule fixed before the run and independent of completions; default pool (ready 2, maxStarting 2), empty-pool start; job = `node -e "process.stdout.write('ok')"` (≤64 B output). Evidence must record pool-empty observations; a run in which the default pool was never observed empty is invalid, not a pass | ≥1200 | successful p95 < 6 ms, acceptance ≥ 99 %, 0 correctness failures |
| `burst_submit` | bursts 2/8/16/32 | all | accounted, bounded |
| `saturation` | ramp 5→40/s step 5/s, 30 s each, then drain | all | report max stable rate |
| `warm_env_interact` python | `import plot_native; plot_native.add(2,3)` style real native call, ≤64 B output | ≥300 | p95 < 6 ms |
| `warm_env_interact` node | `globalThis.__plot_session__.n++` plus a call into an **acquired** npm-style package materialized under `.grave/objects` (not a Node built-in) | ≥300 | p95 < 6 ms |
| `cold_worker_spawn`, `complete_isolated_job`, `cold_acquisition`, `bootstrap_cold`, `replenish` | separate distributions | ≥40 | reported, no 6 ms claim |

Nominal-rate rationale: v0.6 measured worker readiness p95 103 ms; with `maxStarting=2` replenishment capacity is ≈ 19 workers/s. Mean 10/s Poisson is ≈ 52 % of that capacity, turns the 2-slot pool over 5×/s, and its bursts empty the pool, so cold/waited paths are exercised rather than hidden by a prefilled reservoir. Fixed before any tuning (amended once, pre-tuning, per Fletcher TEMPO 18); not to be reduced after results.

Percentiles: nearest-rank over all successful samples; failures/rejections/timeouts reported with counts alongside. Timer `process.hrtime.bigint()` from client request initiation.

## 13. Ownership map

| Surface | Owner packet |
| --- | --- |
| `src/plot.mjs`, `build.mjs`, `main.js`, `tests/integration.mjs` | P07-01 |
| `capabilities/cartographer.mjs`, `tests/cartographer.mjs`, `tests/fixtures/closure/` | P07-02 |
| `capabilities/assembler.mjs`, `tests/assembler.mjs` | P07-03 |
| `capabilities/bootstrap.mjs`, `bootstrap/`, `tests/bootstrap.mjs` | P07-09 |
| `capabilities/resident.mjs`, `tests/resident.mjs`, `tests/resident-env.mjs` | P07-04 → P07-05 → P07-06 (serial) |
| `scripts/gate.sh`, `tests/package-smoke.mjs`, host runners | P07-07 |
| benchmarks, `tests/report.mjs`, `evidence/` (via gate), whitepaper | P07-08 |
| `manifest.json`, `package.json`, `AGENTS.md`, `TASK.md`, `docs/*`, `filetree.md`, this file | Coordinator |

`tests/helpers.mjs`: additive helpers only; coordinator merges conflicts.

## 14. Amendments

| Date | Contract | Change | Consumers updated |
| --- | --- | --- | --- |
| 2026-10-20 | v1 | Initial freeze | — |
| 2026-10-20 | v1.7 | P07-06 landed: env ops on the supervisor socket; host status states `starting/active/draining/stopped/interrupted` (`unreachable` observation); turn outcome adds `runtime`, `stdoutBytes`, `stderrBytes`, `truncated`, `outputComplete`, `ms`, `retried`; turn rid records at `inc/<inc>/requests/<rid>.json`; `activate` returns `existing`/`heap:'new'` and refuses a different spec while active; env pin ref `<name>.<incarnation>`, owned by the host; fd-3 frames are a socketpair (bidirectional) | P07-07, P07-08 |
| 2026-10-20 | v1.6 | P07-05 landed: `claimed.json` (write-once) carries owner, rid and the rotated control endpoint `{port,token}`; `owner.json`, `control.json` and `status.json {running, revision:1}` are written by the worker immediately after the claim reply, and readers fall back to `claimed.json` (claimed without status = running). Job pins skip fsync (crash roots come from `submission.json`). `submission.json`/rid record fsync overlaps the claim RPC; the reply waits for both. Reply adds `t.durable`, `claimMs`, `adopted`. Env knobs `PLOT_RESIDENT_READY`, `PLOT_RESIDENT_MAX_STARTING`, `PLOT_RESIDENT_MAX_WAITING`. A job whose standby is proven gone three times without a claim is fenced `interrupted`. Waiters admitted past `maxWaiting` only for retries and restart orphans. Ping `pool` exposes `empty` (lease found no idle standby) for the §12 pool-empty validity rule | P07-06, P07-08 |
| 2026-10-20 | v1.5 | P07-03 landed: each npm `name@version` is a component object keyed `[{component:{ecosystem:'npm',name,version},assembler:1},sig,[]]`; layers copy components into placements and list them as key dependencies; layer `.plot.json` records `inputs:[{ref,sha256}]`, re-verified at reuse, mismatch → `BANK_CHANGED` with nothing published; all sources checked before the first write | P07-07, P07-09 |
| 2026-10-20 | v1.4 | P07-04 landed: job pins released at terminal status; only the reconciler writes `interrupted` and never expires it; evicted rid leaves an expired marker (`request expired`); worker `done` goes to the supervisor recorded in `submission.json`; `PLOT_RESIDENT_MAX_ACTIVE` overrides `maxActive`; `.grave/resident/launch.json` records the launch | P07-05, P07-06 |
| 2026-10-20 | v1.3 | P07-02 landed: npm presence = complete object whose key recipe has `component:{ecosystem:"npm",name,version}` and matching host; duplicate same-version nodes get id `name@version:<placement>`; `entry.exports` null when absent, `{}` when unusable; `entry.imports` optional; `source.member` for tgz members; pruned reason `libc`; corpus unsupported forms `duplicate|archive|symlink|depth`; fail-closed codes `cycle, missing, range-unsatisfied, peer-unsatisfied` | P07-03, P07-09 |
| 2026-10-20 | v1.2 | P07-01 landed: package-less Python recipe carries `pip:false` (one-time key change, prevents pip-less/pip-bearing confusion); foreground pins use `owner.birth:null` (retained while pid alive); seed exports `create` (write-once) semantics in §1 | P07-03, P07-04, P07-09 |
| 2026-10-20 | v1.1 | Fletcher TEMPO 14–20: foreground pin mandatory (§4); wheel-node producer `planWheels` (§10); runtime ownership labelling for assembler and kit Node provenance (§11); sustained workload Poisson 10/s with pool-empty validity (§12); Node warm row uses an acquired package (§12); P07-04 starts before P07-01 lands | P07-01, P07-03, P07-09, P07-04..P07-08 (notified at landing/dispatch) |
