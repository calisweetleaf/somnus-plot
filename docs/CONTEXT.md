# Somnus Plot — Current Context

Snapshot of what is true now. History lives in `NOTEPAD.md`; durable law in `MEMORY.md`.

_Last refreshed: 2026-10-20 00:47 CDT._

## State

| Field | Value |
| --- | --- |
| Version | v0.6.0 Persistent Native Execution |
| Git | `main` @ `b72a98d` base (older entries cite `896f48d`, absent from this checkout). Coordinator commits each landed v0.7 packet locally; nothing pushed. Untracked operator files: `.colony/`, `.factory/`, `SWARM.md`, `attachments/`. |
| Location | `/home/factory-user/repos/somnus-plot` (earlier: `/home/daeron/Repositories/somnus-plot`) |
| Active packet | Landed P07-00/01/02/03/04/05/09. P07-06 landed; P07-07 active (Keeper); then P07-08. See `TASK.md`, `docs/V07-CONTRACTS.md` |
| Core bytes | `main.js` 9,008 / 9,063 ceiling (55 bytes headroom) after P07-01 |
| Resident bytes | `capabilities/resident.mjs` 69,478 after P07-06 (counted separately); 41/41 resident, 21/21 resident-env |

## Gate posture

| Check | Evidence of record (2026-10-17, linux/x64 Xeon container, Node v24.19.0) | Local re-run (2026-10-20, this laptop, Node v24.14.0, Python 3.14.4, gcc) |
| --- | --- | --- |
| `node build.mjs` | 9,061 bytes | 9,061 bytes; rebuilt `main.js` byte-identical to committed |
| `tests/integration.mjs` | 18/18 | 18/18 PASS |
| `tests/resident.mjs` | 19/19 | 19/19 PASS |
| `tests/package-smoke.mjs` | PASS | PASS |
| Benchmarks | See `evidence/RESULTS.md` | NOT RUN locally |
| `scripts/gate.sh` | — | PASS 2026-10-20 on reference host (Linux 6.1 x64 Xeon 4 vCPU, Node v24.22.0, Python 3.12.3) |

Local re-runs were executed in a disposable copy; `evidence/` was not modified.

## Headline measured numbers (evidence of record, p95)

- Validated view lookup 0.253 ms; resident ping 0.664 ms
- Native cached view creation 4.066 ms; resident request through persisted view 3.614 ms (both PASS the 6 ms gate)
- Durable resident submission 7.861 ms (not under 6 ms)
- Fresh CLI + cached provisioning 131.1 ms; complete native job 192.7 ms

The operator's shorthand "140 ms full, sub-1 ms" matches the fresh-CLI series
(p95 131 ms, p99 202 ms) and the lookup/ping series respectively.

## Open contradictions

- None material. `filetree.md` previously recorded the old `LAB/` root; refreshed 2026-10-20.
- Horizon wording: `PLAN.md` §1.1 places the persistent VM at v0.8–v1.0; `AGENTS.md`/`docs/MEMORY.md` say "v10". Likely the same milestone (v1.0) written two ways; operator to confirm. `WHITEPAPER.md` carries it as LEAP #23.
- `docs/Plot-Fable.md` contains leftover citation markers (`citeturn…`) from its export. Operator-owned; not edited.

## Environment notes

- Gate prerequisites present on this host: node, python3 + venv + pip + `Python.h`, cc.
- No npm install is ever required.
