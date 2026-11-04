# Somnus Plot — Current Context

Snapshot of what is true now. History lives in `NOTEPAD.md`; durable law in `MEMORY.md`.

_Last refreshed: 2026-10-22 after the v0.7 closeout._

## State

| Field | Value |
| --- | --- |
| Version | v0.7.0 "The Seventh Flash": **closed by operator acceptance with named exceptions** (2026-10-22). Canon to reuse; not to be reopened for new scope |
| Git | `main`; v0.7 packets committed locally from `d97981f` to `3613c3d`, then `b438dfe`, `995331d`, `7c266f1`; the closeout is uncommitted until the operator asks. Nothing pushed. Operator work under `.factory/skills/code-fable/`, `SWARM.md` and root `Plot-Fable.md` is untouched. |
| Location | `/home/daeron/Repositories/somnus-plot` |
| Active packet | None. P07-00..P07-09 and the closeout landed. See `TASK.md`, `docs/V07-CONTRACTS.md` (v1.10), `WHITEPAPER.md` (v1.1) |
| Core bytes | `main.js` 9,061 / 9,063 ceiling (2 bytes headroom) |
| Capability bytes | resident 70,243; assembler 51,459; cartographer 31,126; bootstrap 37,922 (each counted separately) |
| Host matrix | Linux x64 glibc: RUN on this host and in a fresh Debian 12 container with Node absent (`bootstrap/hosts/records/`). Windows, macOS, Android/Termux: NOT RUN (named exception) |

## Gate posture (evidence of record, 2026-10-22, Linux 7.0.0-38 x64, AMD Ryzen 5 5625U × 12, bare metal, ext4 on NVMe, Node v24.14.0, Python 3.14.4)

| Check | Result |
| --- | --- |
| `node build.mjs` | 9,061 bytes; rebuild byte-identical |
| Suites | 146/146: integration 24, resident 41, resident-env 21, e2e 12, cartographer 12, assembler 15, bootstrap 21 |
| `tests/package-smoke.mjs` | PASS |
| `scripts/gate.sh --evidence` | PASS (evidence regenerated in place 2026-10-22) |
| Fresh container `certify.sh` (with gate) | every step exit 0; gate PASS |
| Frozen §12 rows | valid run; 8 of 9 p95 < 6 ms boundaries PASS; `sustained_submit` successful p95 FAIL (named exception) |

## Headline measured numbers (v0.7, p95, evidence of record 2026-10-22)

- Validated view lookup 0.170 ms; mixed cached view 0.406 ms; resident cached-view RPC 0.680 ms
- multi_version_switch 0.495 ms with 0 child spawns
- Warm durable submit-and-claim: reply 3.322 ms, claim record 3.364 ms; endpoint first answer 10.918 ms (no gate)
- Warm turns: Python 1.156 ms (shallow host), Node 0.899 ms
- sustained_submit (frozen 2/2 pool, Poisson 10/s, 1,200 offered): 100 % accepted, 0 failures, successful p95 16.365 ms → **FAIL**; tuned 4/4 pool on the same schedule 6.295 ms (reported, no gate; also above the bell on this non-idle run); saturation max stable 35/s
- Supervisor peak RSS: 75,528 KiB (sustained), 102,220 KiB (after saturation), 76,156 KiB (tuned)
- Cold/full (no 6 ms claim): cold worker 45.4, complete job 28.8, cold acquisition 20.7, replenish 46.1, bootstrap_cold 1,877.6 ms
- Benchmark run 2026-10-22T08:13–08:23Z; load average at start 2.51

These are not comparable to the 2026-10-20 run as a speedup: the host changed (Xeon 4-vCPU KVM guest → 12-thread bare metal).

## Named exceptions (operator acceptance, 2026-10-22)

- O-11 `sustained_submit` frozen-row p95. Cause measured: standby birth ≈ 42 ms (Node boot + module evaluation ≈ 26 ms, setup ≈ 7 ms, claim warm-up ≈ 6 ms); with a 2-slot pool about 7 % of Poisson arrivals wait for a worker.
- O-12 non-Linux OS families NOT RUN.
- O-13 power-loss / reboot durability untested.
- O-10 Law 12 satisfied through the single durable `claimed.json` record (accepted).

## Open contradictions

- Horizon wording (`PLAN.md` v0.8–v1.0 vs `AGENTS.md`/`MEMORY.md` v10): deliberately deferred by the operator; the next stage takes a new form and reuses v0.7.
- `docs/Plot-Fable.md` contains leftover citation markers (`citeturn…`) from its export. Operator-owned; not edited.

## Environment notes

- Gate prerequisites on this host: node, python3 + venv + pip + `Python.h`, cc. Offline kit at `/tmp/plot-bootstrap-kit` (built by `tests/bootstrap.mjs`). Docker and podman are available for fresh-container runs.
- A fresh container needs these host inputs before `certify.sh`: python3, python3-venv, python3-dev, python3-pip, gcc, libc6-dev, make, wget, ca-certificates, curl, xz-utils. Without make/wget, bootstrap correctly refuses.
- `scripts/gate.sh --evidence` regenerates `tests/fixtures/closure/sample-plan.json` with this checkout's absolute paths; the assembler test rebases them, so the file is host-independent in use.
- No npm install is ever required.
