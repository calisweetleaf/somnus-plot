# Somnus Plot v0.7 — evidence report

Generated from completed runs on 2026-10-20.
**146/146 checks pass** (24/24 core integration; 41/41 resident; 21/21 resident environments; 12/12 end-to-end composition; 12/12 cartographer; 15/15 assembler; 21/21 bootstrap).
Suites without a JSON report are read from their gate logs.
Clean-package smoke status: **PASS**. Host matrix: Linux x64 glibc only;
Windows, macOS and Android/Termux are **NOT RUN** (kits and runners in `bootstrap/hosts/`).

The complete required foreground bundle is **9,008 bytes**,
within the unchanged **9,063-byte ceiling**. The optional acquired resident module
is **70,243 bytes**, counted separately,
with no external runtime packages. Other acquired capabilities, also counted separately:
`assembler.mjs` 51,459 B, `cartographer.mjs` 31,126 B, `bootstrap.mjs` 37,922 B. Total deployed executable JS for resident use is
**79,251 bytes**;
resident code is not hidden inside the core byte figure. Each active job additionally
uses its own single-use Node worker (claimed from a standby pool) and native child;
process/memory overhead is not claimed away.

## Verified persistence

- **optional capability acquisition and native-only clean CLI startup:** {"pythonRequired":false,"acquiredResident":true}
- **concurrent start clients converge on one authenticated supervisor:** {"clients":3,"supervisors":1}
- **job outlives submitting CLI; a distinct CLI discovers identity, status and output:** {"id":"fecb4677-0591-485a-a165-1e66d0e820af","submittingClientExited":true,"reconnectedClient":true,"status":"succeeded","output":"before disconnect\nafter disconnect\n"}
- **abrupt transport disconnect after submission does not cancel accepted work:** {"id":"drop-3039696c-877a-4d22-b396-85091f829973","transportClosedBeforeResponse":true}
- **concurrent clients, stable identities and exactly one job for retried submission:** {"clients":8,"retries":2,"singleExecution":true}
- **supervisor SIGKILL/restart reconnects to an already running independent worker:** {"id":"14b7ed55-9dfb-41da-82fd-37e04dac05da","workerInstance":"a4dc4031-ba42-4d43-ba26-7dc35008433b","state":"succeeded"}
- **exact frozen view, executable, environment, literal commands and dependencies survive changes:** {"oldObjectRetained":true,"snapshotExecuted":true}
- **persistent Python jobs retain conflicting package views while reusing one runtime:** {"sharedRuntime":true,"isolatedVersions":["1.0","2.0"]}
- **stale records never authorize signalling an unrelated live process:** {"state":"interrupted","unrelatedProcessUntouched":true}
- **worker crash becomes interrupted/unreachable; no success fabricated or step replayed:** {"id":"70d5927a-fc05-495a-8d34-e06b9c17940e","state":"interrupted","executions":1}
- **acquisition crash reconciliation retains incomplete objects, committed views and owned state:** {"reconciliation":"reconciled","incompleteRetained":true,"viewRetained":true,"noSignals":true}
- **cancellation owns the direct child and bounds inherited-pipe waiting:** {"directChildCancelled":true,"descendantNotSignalled":true}
- **failed resident acquisition rolls back; disconnected provisioning client does not cancel writer:** {"clientKilled":true,"viewCommitted":true}
- **cold acquisition continues through supervisor death and restart:** {"supervisorKilled":true,"acquisitionCommitted":true}
- **two concurrent jobs on one view get private PLOT_JOB_STATE and step conduits:** {"jobs":2,"sharedPlotState":true,"privateScratch":2}
- **reconciler revision fence never overwrites a newer terminal record:** {"liveJobRecord":"worker-owned","staleRejected":true,"terminalRejected":true,"uncertainRejected":true}
- **20 killed-worker recoveries release capacity and job 21 succeeds:** {"recoveries":20,"capacityRejections":24,"limit":4,"job21":"succeeded"}
- **missed completion notification is repaired by the background reconciler:** {"repairMs":71.53478000000177,"lostNotifications":1,"deliveredNotifications":1}
- **simultaneous last-slot submissions admit exactly one before durable acceptance:** {"concurrent":8,"admitted":1,"rejected":7,"durableJobDirs":3}
- **submit latency is independent of 1,000 historical and unreachable jobs; no submit waits on a probe:** {"historicalJobs":1000,"unreachable":4,"probeConnections":4,"emptyMs":{"p50":4.865187000003061,"max":42.62146899999789},"historyMs":{"p50":4.906531000000541,"max":41.75162300000011}}
- **prune dry-run changes nothing; default apply keeps the cache; policy apply deletes only reclaimable objects:** {"dryRunUnchanged":true,"defaultDeleted":0,"policyDeleted":1,"incompleteRetained":true}
- **prune keeps the transitive dependency closure of a pinned object:** {"pinned":1,"transitiveRetained":1,"deletedAfterUnpin":2}
- **includeJobs expiry releases job snapshot roots and expires request IDs without re-execution:** {"jobExpired":"352465f7-47cb-450f-9853-d91e0a93b48d","objectFreed":true,"ridExpired":true}
- **concurrent provision and prune serialize on .grave/.lock without losing a publication:** {"waitedMs":745.6369799999993,"publicationRetained":true}
- **tombstone crash recovery withdraws unmoved intents and finishes moved deletions:** {"crashedAfterRename":true,"lockHeldAtCrash":true,"recovered":["finish-deletion","finish-deletion"]}
- **historical v1 reusable after default prune (seed-coupled: P07-01):** {"reused":"/tmp/plot-resident-7MyT7b/history-reuse/.grave/objects/data-WRRx5R"}
- **foreground pin respected by prune (seed-coupled: P07-01):** {"pinnedDuringRun":true,"releasedAfterRun":true}
- **standby claim replies only after an independent worker durably owns the job:** {"clientMs":8.51928,"t":{"reserved":0.075482,"published":2.473646,"durable":4.911043,"claimed":7.181001,"replied":7.188902}}
- **supervisor SIGKILL immediately after reply leaves the claimed job running:** {"id":"6b6618ec-1cdc-4215-a61d-1474bf23fab3"}
- **claim-stage crash: before claim retries another worker; after claim adopts, never a second worker:** {"before-claimed":{"state":"succeeded","retried":1,"adopted":0},"after-claimed":{"state":"interrupted","retried":0,"adopted":1},"after-status":{"state":"interrupted","retried":0,"adopted":1}}
- **lost claim ACK adopts the durable claim instead of creating a second worker:** {"adopted":true}
- **duplicate simultaneous rid creates exactly one job and one worker:** {"clients":6,"jobs":1}
- **bursts of 2/8/16/32 are accounted, bounded and never exceed maxStarting:** {"2":{"accepted":2,"rejected":0,"paths":{"standby":2}},"8":{"accepted":8,"rejected":0,"paths":{"standby":2,"cold":1,"waited":5}},"16":{"accepted":16,"rejected":0,"paths":{"standby":2,"cold":1,"waited":13}},"32":{"accepted":16,"rejected":16,"paths":{"standby":2,"cold":1,"waited":13}},"pool":{"ready":2,"maxStarting":2,"maxWaiting":16,"idle":2,"starting":0,"waiting":0,"spawned":44,"standby":8,"cold":3,"waited":31,"adopted":0,"retried":0,"undetermined":0,"abandoned":0,"empty":34,"peakStarting":2}}
- **idle standbys expire after supervisor SIGKILL and leave with a clean stop:** {"expiredMs":5019,"cleanStop":true}
- **restart reconciliation dispatches a published job that was never claimed; idle pool stays bounded:** {"state":"succeeded","spawned":3}
- **preliminary warm durable submit-and-claim latency (asserted < 6 ms with PLOT_ASSERT_LATENCY=1):** {"n":120,"p50":4.339388,"p95":5.499055,"p99":6.427645,"max":7.506263,"paths":{"standby":120},"asserted":false,"gate":"tests/resident-benchmark.mjs durable_submit_and_claim"}
- **activate creates one incarnation; memory persists across independent clients in Python and Node:** {"incarnation":"f5f7401e-9e05-4a3b-be09-dd903e2030e0","clients":2}
- **warm tenants import a native extension and call an acquired npm-style package under .grave/objects:** {"native":"37","npm":"5"}
- **conflicting package sessions stay isolated on one shared runtime:** {"py1":"'1.0'","py2":"'2.0'"}
- **supervisor SIGKILL and restart preserve the live incarnation and its heap:** {"incarnation":"f5f7401e-9e05-4a3b-be09-dd903e2030e0"}
- **os.write(1), print, stderr and a replaced sys.stdout are captured without framing confusion:** {"python":["raw\nprinted\n","direct\n","back\n"],"node":"node out\ntail"}
- **a flood is capped and counted; late background output is attributed to the next turn:** {"floodBytes":3145729,"kept":1048576,"late":{"stdout":5,"stderr":0}}
- **cwd and sys.path mutations persist across turns:** {"cwd":"/tmp/plot-resident-env-MQo7Mq/cwd-lk0udg"}
- **a partial exception reports failed + partial and keeps earlier mutations:** {"python":"ValueError: half","node":"failed"}
- **duplicate turn rid executes once; a different request under the same rid conflicts:** {"clients":4,"executions":1}
- **incarnation guard rejects a stale expectIncarnation:** {"guarded":true}
- **concurrent activate converges on one incarnation and one host:** {"clients":3,"incarnations":1}
- **queue bound: one turn in flight, eight queued, overflow is busy and retryable:** {"inFlight":1,"queued":8,"busy":1}
- **submit jobs never share a tenant heap:** {"jobSaw":"undefined"}
- **exec turns run a literal command in the environment and leave the heap untouched:** {"exitCode":0}
- **the Environment Host holds a transitive env pin while active; prune retains its objects:** {"pinPaths":3}
- **a busy Node loop past its deadline kills the tenant: interrupted, heap lost, no silent restart:** {"ms":503.634807,"state":"interrupted","newIncarnation":"e3e2826f-a105-4985-b113-5f1596828c0b"}
- **a blocked native call past its deadline is destructive and reported:** {"ms":503.562309}
- **tenant death during a turn is an interruption, never an empty-heap restart:** {"state":"interrupted"}
- **Environment Host death is proven from identity; tenants do not survive it:** {"proof":"absent"}
- **deactivate stops tenants and host, releases the env pin, and refuses later turns:** {"state":"stopped"}
- **warm turn latency series (preliminary; gate in P07-08):** {"python":{"n":200,"p50":3.294388,"p95":4.298043,"p99":6.305109,"max":19.666102},"node":{"n":200,"p50":3.098559,"p95":3.927978,"p99":4.76306,"max":8.833427}}
- **bootstrap acquires an owned Node and Python closure from the offline kit into <root>/.grave/host:** {"node":"/tmp/plot-e2e-xM6Azq/root/.grave/host/node-24.22.0-linux-x64-UEkl4G/bin/node","python":"/tmp/plot-e2e-xM6Azq/root/.grave/host/python-3.12.15-linux-x64-ZasX3j/bin/python3","ms":6022.8}
- **cartographer and planWheels emit the closures; the native wheel is compiled against the owned runtime:** {"wheels":["plot-native@1.0","plot-e2e@1.0"],"npm":["d@1.0.1","a@1.2.0"]}
- **seed recipes assemble the wheel and npm layers into .grave/objects over the owned venv (no pip):** {"view":{"python":"python-9A1ZWf","python-packages":"python-packages-emhFpF","wheels":"wheels-BSVIAs","npm":"npm-vuxOfr"},"ms":282.4}
- **crash at seed publication: SIGKILL mid-install leaves an unstamped stage that is archived by recovery and never adopted:** {"stage":"held-yvYLrj","archived":"acquisition-da4706e2-0692-430e-b81a-5247b6980121"}
- **owned-runtime jobs: crash after the standby claim is adopted (interrupted, no output, no second worker); the next job runs both layers:** {"adopted":"d8911bfd-50d1-45d5-9416-c463d883e598","succeeded":"561fecfd-ab4e-4518-bf79-d07e9bc1fabf","path":"standby"}
- **environment over the assembled view: Python native wheel and Node npm layer in warm tenants; heap persists across turns:** {"incarnation":"940d3e03-0143-4ba0-8b2f-8cae7a7957fa"}
- **crash during activation: supervisor SIGKILL while the host starts; restart converges on one live host and the earlier heap survives:** {"incarnations":1,"existing":true}
- **crash at turn completion after the record: the retried rid returns the recorded outcome; the effect ran once:** {"turnId":"478a6c5e-2deb-4a58-93fa-1271c3a0e458","state":"interrupted"}
- **crash at turn completion before the record: the retried rid reports interrupted/lost and never re-executes; reactivation is a new heap:** {"lost":"b304da97-477f-40a1-842b-40faf78fd72e"}
- **crash during prune (moved): recovery then prune finishes the deletion; pinned environment objects survive:** {"deleted":1,"recovered":[{"path":"/tmp/plot-e2e-xM6Azq/root/.grave/objects/junk-YmflNu","kind":"object","action":"finish-deletion"}]}
- **crash during prune (intents): recovery then prune withdraws the intent and deletes anew; pinned environment objects survive:** {"deleted":2,"recovered":[{"path":"/tmp/plot-e2e-xM6Azq/root/.grave/objects/junk-rR9Tti","kind":"object","action":"intent-withdrawn"}]}
- **teardown: deactivate stops every host and tenant; supervisor stop is clean:** {"stopped":7}

These are actual CLI/process/socket/file experiments. Submission returns without
waiting for execution. Separate CLI processes discover and read an earlier job;
other tests disconnect the socket before the response, kill the supervisor while
the worker is running, stop/restart it, and interrupt acquisitions. Job identities,
outputs, frozen views, private metadata and completion markers are checked.

## Measurements

Host: linux/x64, v24.22.0,
Intel(R) Xeon(R) Processor @ 2.60GHz; kernel 6.1.158+. Container scratch filesystem,
warm local caches. Integration completed before the final sequential benchmark runs.
Every raw sample is retained; no outliers are removed.

| Operation | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| Mixed-runtime cached view creation | 1000 | 2.707 | 3.612 | 4.180 | 11.375 |
| Mixed-runtime cached reprovision | 300 | 2.362 | 3.324 | 3.769 | 4.364 |
| Validated view lookup | 1000 | 0.069 | 0.131 | 0.313 | 0.438 |
| Fresh CLI + cached provisioning | 60 | 42.040 | 48.886 | 50.235 | 50.235 |
| Fresh CLI + Python/package execution | 60 | 57.657 | 63.679 | 67.798 | 67.798 |
| Raw Python child startup | 60 | 8.624 | 9.431 | 10.062 | 10.062 |
| Empty venv without pip (runtime-only reference) | 20 | 36.207 | 43.387 | 44.789 | 44.789 |
| Native cached view creation (direct API) | 1000 | 2.378 | 3.330 | 3.869 | 4.981 |
| Resident authenticated ping (fresh socket) | 300 | 0.253 | 0.599 | 0.924 | 1.427 |
| Resident request through persisted cached view | 300 | 3.284 | 4.293 | 5.304 | 6.776 |
| Raw Node child startup through exit | 40 | 26.966 | 32.641 | 41.282 | 41.282 |
| Durable resident submission through response | 40 | 4.351 | 6.365 | 9.312 | 9.312 |
| Accepted submission to worker control readiness | 40 | 3.555 | 4.676 | 6.042 | 6.042 |
| Complete native job submission through child exit | 40 | 41.889 | 46.170 | 47.875 | 47.875 |
| Resident terminal job inspection | 40 | 0.812 | 1.710 | 2.285 | 2.285 |

## v0.7 frozen workloads (docs/V07-CONTRACTS.md §12)

Host: linux/x64, v24.22.0, Intel(R) Xeon(R) Processor @ 2.60GHz × 4;
kernel 6.1.158+; load average at start 1.59 / 2.26 / 1.94.
Run valid: **yes**. nearest-rank over all successful samples, process.hrtime.bigint from client request initiation.

| Row | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| multi_version_switch (child spawns 0) | 300 | 3.720 | 4.701 | 5.233 | 6.606 |
| durable_submit_and_claim: reply | 300 | 4.375 | 5.933 | 7.352 | 21.943 |
| durable_submit_and_claim: control ready (endpoint record) | 300 | 4.432 | 5.990 | 7.471 | 21.997 |
| control endpoint first answer (no gate) | 300 | 13.147 | 16.805 | 20.597 | 30.856 |
| sustained_submit successful (Poisson 10/s) | 1200 | 5.350 | 40.536 | 66.256 | 99.328 |
| warm_env_interact python (shallow-host) | 300 | 2.894 | 3.829 | 4.399 | 5.852 |
| warm_env_interact node | 300 | 2.748 | 3.620 | 4.703 | 7.257 |
| cold_worker_spawn | 40 | 61.771 | 76.942 | 122.073 | 122.073 |
| complete_isolated_job | 40 | 47.603 | 72.906 | 100.521 | 100.521 |
| cold_acquisition | 40 | 29.409 | 33.356 | 40.729 | 40.729 |
| bootstrap_cold (Node from kit) | 40 | 2980.845 | 3176.589 | 3403.234 | 3403.234 |
| replenish | 40 | 58.466 | 104.958 | 292.500 | 292.500 |

Sustained: 1200 offered over 126.573 s (seed 0x5eed07), 1200 accepted (100.00 %), 0 correctness failures, paths {"standby":1035,"waited":146,"cold":19}; pool empty at start true, leases that found no idle standby 165.
Bursts (offered → accepted / rejected, peak starting): 2 → 2/0, 2; 8 → 8/0, 2; 16 → 16/0, 2; 32 → 16/16, 2.
Saturation: max stable rate **25/s** (highest step R such that every step <= R had acceptance >= 99% and zero correctness failures after drain); steps 5/s 100.0 % p95 8.676, 10/s 100.0 % p95 33.189, 15/s 100.0 % p95 58.262, 20/s 100.0 % p95 115.612, 25/s 100.0 % p95 121.270, 30/s 98.6 % p95 375.839, 35/s 93.6 % p95 422.654, 40/s 91.1 % p95 416.287.

| Frozen gate | Result |
|---|---|
| multi_version_switch p95 < 6 ms with 0 spawns | PASS |
| durable_submit_and_claim p95 < 6 ms (reply and control ready) | PASS |
| sustained_submit successful p95 < 6 ms | FAIL |
| sustained_submit acceptance ≥ 99 % | PASS |
| sustained_submit 0 correctness failures | PASS |
| sustained_submit pool observed empty (validity) | PASS |
| burst_submit accounted and bounded | PASS |
| warm_env_interact python p95 < 6 ms | PASS |
| warm_env_interact node p95 < 6 ms | PASS |

A FAIL here is an open gate, reported as measured; the workload was frozen before tuning and is not reduced.

Cold acquisitions (v0.6 series) are separate, single offline observations:

| Cold operation | ms | Scope |
|---|---:|---|
| Mixed runtime + two real wheels + dataset/analysis DAG | 2887.343 | Actual CPython venv, pip target resolution/install and native fixture acquisition |
| Native dataset | 35.062 | Actual native installer child and committed owned resource |
| Optional resident capability | 36.742 | Actual native copy recipe and resource/ledger/view commits |
| Resident startup with cached capability | 90.139 | Cached activation, detached service process and authenticated ready endpoint |

Persisted cached-view p95 gates: mixed-runtime direct API
**PASS**;
native direct API **PASS**;
resident through validated persisted view and response
**PASS**.

**The objective is p95 below 6 ms for cached view operations. Maximums exceed
6 ms in these runs. Durable job submission, cold acquisition, fresh CLI/worker/child
startup and complete execution are distinct costs and are not below-6-ms claims.**
The old v0.5 measurement used another host; no cross-host speedup claim is made.

The mixed-runtime view series creates 1,000 distinct persisted writable views over
four shared resources, then executes representative views with real Python imports,
a compiled extension, metadata and dataset checks. Native direct/resident series
also execute representative measured views. 40 complete resident jobs
perform real dataset computation, write verified state and capture expected output.
The raw Node startup series runs independent child processes. The accepted-to-worker
series observes private control-file creation with 1 ms polling; complete-job timing
includes polling overhead. An empty venv has none of the full workload's package or
capability work and is only a runtime baseline. There are no network download timings.

## Recovery and authority findings

- Writer journals identify this transaction's allocated stages before installation.
  Recovery archives stale journals and preserves all objects, committed ledger,
  historical views and writable state. It does not delete possibly active stages.
- Worker control is authenticated by job ID, private token and instance. A surviving
  PID is never accepted as proof of managed-job identity or authority to terminate it.
  Stale/forged PID fixtures leave an unrelated live process untouched.
- Missing worker control yields interrupted or unreachable/uncertain state; it does
  not fabricate success, replay steps or send a PID-based signal. Actual tenant work
  can outlive a killed worker, so blind replay would be incorrect.
- Cancellation, timeout and SIGTERM-to-SIGKILL escalation use owned direct-child
  handles. A separate test proves descendants are not broadly signalled and that
  inherited-pipe waiting is bounded and recorded.
- Capability dependencies, absolute native lookup, original commands, cwd, full
  resolved environment, exact view/interpreter/package selections and resource keys
  are persisted before worker launch. Conflicting package jobs share one runtime
  while executing their respective frozen package layers.
- Output is bounded across both streams, with overflow reporting and exact byte
  cursors/base64. Tests cover invalid requests/limits, authentication/authority denial,
  damaged records, failed acquisitions, concurrent start/submission and retry identity.

## Unimplemented or unverified

| Surface | Status and consequence |
|---|---|
| Host reboot / power-loss recovery | Not tested; metadata survives tested process interruptions. No automatic boot service is installed. Core `atom` fsyncs the file and, on POSIX, the parent directory; durability across power loss is not tested. |
| Worker death with a surviving tenant | Conservatively reported; tenant termination and automatic replay are not implemented. Lost claim ACKs are adopted from the durable claim (P07-05). |
| Hostile native sandbox | Not implemented. Native steps are trusted OS processes; fs declarations are not kernel confinement. |
| Process-tree termination and quotas | Not implemented. Cancellation covers direct children; descendants, CPU/RAM/network enforcement need explicit acquired OS adapters. |
| Physical PID reuse and Linux /proc incarnation branch | Not forced in this environment. Authentication and conservative live-PID fallback are verified; unavailable incarnation data leaves identity unknown. |
| Immutable host executable contents | Not promised. Absolute resolution preserves command selection, while trusted host files/libraries and symlinks can still change. |
| Worker pooling | Single-use standby workers (claimed once, never reused). Worker reuse across jobs is not implemented by design. |
| Resource/job garbage collection | Pin-safe prune, dry-run by default, tombstone intents with crash recovery. No automatic schedule; historical cache and uncertain jobs are kept unless policy selects them. |
| Resident environment heaps | Survive supervisor replacement; tenant or host death retires the incarnation (`interrupted`, heap lost). No checkpoint/restore. |
| Legacy unstamped/incomplete writer or recovery locks | Retained for inspection; no blind lock theft. A recovery guard interrupted before release requires operator inspection. |
| Windows/macOS/Termux native execution | NOT RUN. Kits, launchers and certification runners ship in `bootstrap/`; Linux execution is the only evidence here. Cross-host acceptance is open. |
| Pinned upstream Python/Node/Git | Acquired and verified on Linux x64 glibc from the pinned python-build-standalone/nodejs.org/git archives (bootstrap suite) and used as the owned runtime by the end-to-end suite. |
| p99 latency | Not gated. Several p99 values exceed 6 ms; only p95 is the objective. |
| Full Python CLI / editable installs / browser host | Outside this change; v0.5 limits remain in STAGE-1.md. |

## Executed checks

### Core integration suite

- PASS: shipped core stays at or below original 9063 bytes
- PASS: real mixed Node/Python demo and module import parity
- PASS: default CLI is plot-relative when launched elsewhere
- PASS: literal arguments, step cwd/env, and stop on child exit
- PASS: spawn:false and missing trusted declaration fail before acquisition
- PASS: host mismatch, invalid IDs, missing dependencies, cycles fail closed
- PASS: host recipe precedence, wildcard fallback and optional unsupported DLC
- PASS: DAG order, reuse, dependency invalidation and frozen older views
- PASS: failed installer/check preserve active view, ledger, writable data
- PASS: cross-process acquisition lock rejects racing writer
- PASS: missing asset and cross-device view require reprovision
- PASS: historical exact-key reuse: v1->v2->v1 capability switch spawns nothing
- PASS: unstamped, interrupted or forged stages are never adopted
- PASS: stdout-only child diagnostic reaches the failure message
- PASS: foreground pin names transitive objects during a run and is removed after
- PASS: real pip target acquisition, shared interpreter and version conflicts
- PASS: Python module, script, argv, metadata resources and console entrypoint
- PASS: subprocess package inheritance, host PYTHONPATH exclusion and writable isolation
- PASS: package installation failure and requested depth/version drift fail without stale reuse
- PASS: historical exact-key reuse: Python package switch v1->v2->v1 runs no pip
- PASS: package-less shallow venv provisions without ensurepip; pip-bearing tenant reports stdout diagnostic
- PASS: archive traversal, symlink pivots, hardlinks, PAX, duplicate paths, truncation rejected
- PASS: bounded decompression aborts oversized archive without activation
- PASS: real locally reconstructed CPython archive and legacy integrity check

### Resident integration suite

- PASS: optional capability acquisition and native-only clean CLI startup
- PASS: concurrent start clients converge on one authenticated supervisor
- PASS: job outlives submitting CLI; a distinct CLI discovers identity, status and output
- PASS: abrupt transport disconnect after submission does not cancel accepted work
- PASS: concurrent clients, stable identities and exactly one job for retried submission
- PASS: supervisor SIGKILL/restart reconnects to an already running independent worker
- PASS: exact frozen view, executable, environment, literal commands and dependencies survive changes
- PASS: persistent Python jobs retain conflicting package views while reusing one runtime
- PASS: bounded binary stdout/stderr, byte cursors, timeout, cancellation and step failure
- PASS: missing capability, authority denial, unauthenticated calls and invalid requests fail closed
- PASS: stale records never authorize signalling an unrelated live process
- PASS: worker crash becomes interrupted/unreachable; no success fabricated or step replayed
- PASS: acquisition crash reconciliation retains incomplete objects, committed views and owned state
- PASS: damaged job records remain visible and cannot hide healthy jobs
- PASS: cancellation owns the direct child and bounds inherited-pipe waiting
- PASS: legacy unstamped locks and ambiguous live writers remain blocked
- PASS: failed resident acquisition rolls back; disconnected provisioning client does not cancel writer
- PASS: cold acquisition continues through supervisor death and restart
- PASS: supervisor stop leaves submitted job running and status available after restart
- PASS: two concurrent jobs on one view get private PLOT_JOB_STATE and step conduits
- PASS: reconciler revision fence never overwrites a newer terminal record
- PASS: 20 killed-worker recoveries release capacity and job 21 succeeds
- PASS: missed completion notification is repaired by the background reconciler
- PASS: simultaneous last-slot submissions admit exactly one before durable acceptance
- PASS: submit latency is independent of 1,000 historical and unreachable jobs; no submit waits on a probe
- PASS: prune dry-run changes nothing; default apply keeps the cache; policy apply deletes only reclaimable objects
- PASS: prune keeps the transitive dependency closure of a pinned object
- PASS: includeJobs expiry releases job snapshot roots and expires request IDs without re-execution
- PASS: concurrent provision and prune serialize on .grave/.lock without losing a publication
- PASS: tombstone crash recovery withdraws unmoved intents and finishes moved deletions
- PASS: historical v1 reusable after default prune (seed-coupled: P07-01)
- PASS: foreground pin respected by prune (seed-coupled: P07-01)
- PASS: standby claim replies only after an independent worker durably owns the job
- PASS: supervisor SIGKILL immediately after reply leaves the claimed job running
- PASS: claim-stage crash: before claim retries another worker; after claim adopts, never a second worker
- PASS: lost claim ACK adopts the durable claim instead of creating a second worker
- PASS: duplicate simultaneous rid creates exactly one job and one worker
- PASS: bursts of 2/8/16/32 are accounted, bounded and never exceed maxStarting
- PASS: idle standbys expire after supervisor SIGKILL and leave with a clean stop
- PASS: restart reconciliation dispatches a published job that was never claimed; idle pool stays bounded
- PASS: preliminary warm durable submit-and-claim latency (asserted < 6 ms with PLOT_ASSERT_LATENCY=1)

### Resident environment suite

- PASS: activate creates one incarnation; memory persists across independent clients in Python and Node
- PASS: warm tenants import a native extension and call an acquired npm-style package under .grave/objects
- PASS: conflicting package sessions stay isolated on one shared runtime
- PASS: supervisor SIGKILL and restart preserve the live incarnation and its heap
- PASS: os.write(1), print, stderr and a replaced sys.stdout are captured without framing confusion
- PASS: a flood is capped and counted; late background output is attributed to the next turn
- PASS: cwd and sys.path mutations persist across turns
- PASS: a partial exception reports failed + partial and keeps earlier mutations
- PASS: duplicate turn rid executes once; a different request under the same rid conflicts
- PASS: incarnation guard rejects a stale expectIncarnation
- PASS: concurrent activate converges on one incarnation and one host
- PASS: queue bound: one turn in flight, eight queued, overflow is busy and retryable
- PASS: submit jobs never share a tenant heap
- PASS: exec turns run a literal command in the environment and leave the heap untouched
- PASS: the Environment Host holds a transitive env pin while active; prune retains its objects
- PASS: a busy Node loop past its deadline kills the tenant: interrupted, heap lost, no silent restart
- PASS: a blocked native call past its deadline is destructive and reported
- PASS: tenant death during a turn is an interruption, never an empty-heap restart
- PASS: Environment Host death is proven from identity; tenants do not survive it
- PASS: deactivate stops tenants and host, releases the env pin, and refuses later turns
- PASS: warm turn latency series (preliminary; gate in P07-08)

### End-to-end composition suite (runtime owned)

- PASS: bootstrap acquires an owned Node and Python closure from the offline kit into <root>/.grave/host
- PASS: cartographer and planWheels emit the closures; the native wheel is compiled against the owned runtime
- PASS: seed recipes assemble the wheel and npm layers into .grave/objects over the owned venv (no pip)
- PASS: crash at seed publication: SIGKILL mid-install leaves an unstamped stage that is archived by recovery and never adopted
- PASS: owned-runtime jobs: crash after the standby claim is adopted (interrupted, no output, no second worker); the next job runs both layers
- PASS: environment over the assembled view: Python native wheel and Node npm layer in warm tenants; heap persists across turns
- PASS: crash during activation: supervisor SIGKILL while the host starts; restart converges on one live host and the earlier heap survives
- PASS: crash at turn completion after the record: the retried rid returns the recorded outcome; the effect ran once
- PASS: crash at turn completion before the record: the retried rid reports interrupted/lost and never re-executes; reactivation is a new heap
- PASS: crash during prune (moved): recovery then prune finishes the deletion; pinned environment objects survive
- PASS: crash during prune (intents): recovery then prune withdraws the intent and deletes anew; pinned environment objects survive
- PASS: teardown: deactivate stops every host and tenant; supervisor stop is clean

## Clean package and reproduction

The smoke test deploys only `main.js`, `manifest.json`, `package.json`, `capabilities/resident.mjs`, `capabilities/assembler.mjs`, `capabilities/cartographer.mjs`, `capabilities/bootstrap.mjs` and `bootstrap/`,
launches from a different cwd, acquires only resident code, submits a Node-only
job, lets its submitting client exit and reconnects through new CLI processes.
From the same foreign cwd it runs bootstrap inspect (`plot.bootstrap-inspect/1`), a cartographer plan and an assembler publish.
No npm install, Python or container engine is required. Captured output:

```text
clean package started
clean package survived
```

Run sequentially from the distribution root:

```sh
node build.mjs
scripts/gate.sh --evidence   # build, every suite, every benchmark, then this report
```

The full historical Python regression/benchmark fixtures require host Python,
pip/venv support, headers and a C compiler. Native resident operation is Node-only.
The end-to-end suite and bootstrap_cold need the offline kit (built by tests/bootstrap.mjs).

Evidence files: integration, resident-integration, resident-env, e2e, benchmark,
resident-benchmark, v07-benchmark and package-smoke (.json/.log), plus cartographer,
assembler and bootstrap logs.
Original v0.5 evidence is preserved in baseline/v0.5-evidence; the unchanged
source ZIP is preserved in baseline/somnus-plot-v0.5.zip.
