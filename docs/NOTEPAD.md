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
