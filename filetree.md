# File Tree: somnus-plot v0.6 → v0.7 (in progress)

**Refreshed:** 2026-10-20 after P07-07 (previous generation 2026-10-19 recorded the old root `LAB/Experiments/projects/somnus-plot/`)
**Root Path:** `/home/factory-user/repos/somnus-plot/`

Topology map only. Route work from `AGENTS.md`, not from this tree.

```
├── AGENTS.md                 router (control plane)
├── TASK.md                   packet board (control plane)
├── PLAN.md                   v0.7 master architecture plan
├── WHITEPAPER.md             v0.7 whitepaper (draft until P07-08)
├── README.md                 quick start
├── STAGE-1.md                v0.5 acquisition/view contract
├── PERSISTENT-NATIVE.md      v0.6 resident contract
├── filetree.md               this map
├── .gitignore                runtime state (.grave/, data.json)
├── package.json              version + script aliases, no deps
├── manifest.json             default demo plot
├── build.mjs                 compactor: src/plot.mjs -> main.js, 9,063-byte ceiling
├── main.js                   GENERATED core bundle (9,008 bytes)
├── src
│   └── plot.mjs              core source of truth
├── capabilities
│   ├── resident.mjs          resident supervisor, standby workers, environment hosts/tenants
│   ├── cartographer.mjs      npm dependency closure planner (plot.closure/1)
│   ├── assembler.mjs         offline wheel/npm layer assembler, Seed Bank, planWheels
│   └── bootstrap.mjs         host inspect/plan/acquire/verify/activate/kit
├── bootstrap
│   ├── plot.sh               Node-absent launcher (POSIX)
│   ├── plot.ps1              Node-absent launcher (Windows PowerShell)
│   ├── recipes/              pinned node/python/git/zlib recipes
│   └── hosts
│       ├── README.md         Windows/macOS/Termux runbooks (NOT RUN)
│       ├── certify.sh        POSIX host certification runner
│       └── certify.ps1       Windows host certification runner
├── tests
│   ├── helpers.mjs           fixtures (wheels, C extension, TAR, CLI)
│   ├── integration.mjs       24 checks -> evidence/integration.json
│   ├── resident.mjs          41 checks -> evidence/resident-integration.json
│   ├── resident-env.mjs      21 checks -> evidence/resident-env.json
│   ├── cartographer.mjs      cartographer suite (12 checks)
│   ├── assembler.mjs         assembler suite (15 checks)
│   ├── bootstrap.mjs         bootstrap suite (21 checks)
│   ├── e2e.mjs               12 composition + crash checks -> evidence/e2e.json
│   ├── fixtures/closure/     generated corpus + sample-plan.json
│   ├── package-smoke.mjs     clean deploy -> evidence/package-smoke.json
│   ├── benchmark.mjs         -> evidence/benchmark.json
│   ├── resident-benchmark.mjs -> evidence/resident-benchmark.json
│   └── report.mjs            -> evidence/RESULTS.md
├── scripts
│   └── gate.sh               integrated gate
├── evidence                  v0.6 evidence of record (2026-10-17)
│   ├── RESULTS.md
│   ├── integration.json / .log
│   ├── resident-integration.json / .log
│   ├── benchmark.json / .log
│   ├── resident-benchmark.json / .log
│   └── package-smoke.json / .log
├── docs
│   ├── Plot-Fable.md         constitutional narrative (operator canon)
│   ├── CONTEXT.md            current state
│   ├── NOTEPAD.md            append-only ledger
│   ├── MEMORY.md             durable law + vocabulary
│   └── V07-CONTRACTS.md      frozen v0.7 shared interfaces
└── baseline                  frozen lineage, never edit
    ├── REPORT.md             v0.4 audit (2026-10-12)
    ├── observed-results.json
    ├── plot_probe.py
    ├── somnus-plot-v0.5.zip
    ├── examples
    │   └── mixed-runtime-plot
    │       ├── README.md
    │       ├── main.js
    │       └── manifest.json
    └── v0.5-evidence
        ├── RESULTS.md
        ├── benchmark.json / .log
        ├── integration.json / .log
        └── package-smoke.json
```
