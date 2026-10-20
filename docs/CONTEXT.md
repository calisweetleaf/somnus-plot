# Somnus Plot — Current Context

Snapshot of what is true now. History lives in `NOTEPAD.md`; durable law in `MEMORY.md`.

_Last refreshed: 2026-10-20 after P07-08._

## State

| Field | Value |
| --- | --- |
| Version | v0.7.0 "The Seventh Flash": integrated candidate, reference-host measured, open gates below |
| Git | `main`; v0.7 packets committed locally from `d97981f` to the P07-08 commit; base `b72a98d`; nothing pushed. Untracked operator files: `.colony/`, `.factory/`, `SWARM.md`, `attachments/`. |
| Location | `/home/factory-user/repos/somnus-plot` (earlier: `/home/daeron/Repositories/somnus-plot`) |
| Active packet | None. P07-00..P07-09 landed. See `TASK.md`, `docs/V07-CONTRACTS.md` (v1.9), `WHITEPAPER.md` (v1.0 candidate) |
| Core bytes | `main.js` 9,008 / 9,063 ceiling (55 bytes headroom) |
| Capability bytes | resident 70,243; assembler 51,459; cartographer 31,126; bootstrap 37,922 (each counted separately) |
| Host matrix | Linux x64 glibc reference: RUN. Windows, macOS, Android/Termux, fresh container: NOT RUN (no host or container runtime available) |

## Gate posture (evidence of record, 2026-10-20, Linux 6.1.158+ x64, Xeon @ 2.60GHz × 4, KVM guest, ext4, Node v24.22.0, Python 3.12.3)

| Check | Result |
| --- | --- |
| `node build.mjs` | 9,008 bytes; rebuild byte-identical |
| Suites | 146/146: integration 24, resident 41, resident-env 21, e2e 12, cartographer 12, assembler 15, bootstrap 21 |
| `tests/package-smoke.mjs` | PASS |
| `scripts/gate.sh --bench` / `--evidence` | PASS (the evidence run regenerated `evidence/`) |
| Frozen §12 rows | valid run; 8 of 9 p95 < 6 ms boundaries PASS; `sustained_submit` successful p95 FAIL |

## Headline measured numbers (v0.7, p95)

- Validated view lookup 0.131 ms; mixed cached view 3.612 ms; resident cached-view RPC 4.293 ms
- multi_version_switch 4.701 ms with 0 child spawns
- Warm durable submit-and-claim: reply 5.933 ms, claim record 5.990 ms (thin margins); endpoint first answer 16.805 ms (no gate)
- Warm turns: Python 3.829 ms (shallow host), Node 3.620 ms
- sustained_submit (Poisson 10/s, 1,200 offered): 100 % accepted, 0 failures, successful p95 40.536 ms → **FAIL**; saturation max stable 25/s
- Cold/full (no 6 ms claim): cold worker 76.9, complete job 72.9, cold acquisition 33.4, replenish 105.0, bootstrap_cold 3,176.6 ms

## Open gates and items

- `sustained_submit` p95 40.536 ms against 6 ms (frozen workload; not reduced).
- Non-Linux host families and fresh container NOT RUN; cross-host acceptance open.
- Power-loss / reboot durability untested.
- Durable submit-and-claim margins under 0.1 ms; load average 1.59 at benchmark start.
- ALARM 51: seed `run()` does not check tombstone intents after the foreground pin (55 bytes headroom).
- `evidence/benchmark.json` `limits[2]` carries pre-v0.7 fsync wording; source fixed, evidence changes at the next `--evidence` run.

## Open contradictions

- Horizon wording: `PLAN.md` §1.1 places the persistent VM at v0.8–v1.0; `AGENTS.md`/`docs/MEMORY.md` say "v10". Operator to confirm (`WHITEPAPER.md` O-4).
- Law 12 wording (PLAN §2: `claimed.json`, `owner.json`, `control.json` before reply) vs implementation (one durable `claimed.json` carrying owner and control endpoint before reply; the others follow; contracts v1.6). Operator to accept or reject (`WHITEPAPER.md` O-10).
- `docs/Plot-Fable.md` contains leftover citation markers (`citeturn…`) from its export. Operator-owned; not edited.

## Environment notes

- Gate prerequisites present on this host: node, python3 + venv + pip + `Python.h`, cc. Offline kit at `/tmp/plot-bootstrap-kit` (built by `tests/bootstrap.mjs`).
- No npm install is ever required.
