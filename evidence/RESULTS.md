# Somnus Plot v0.6 — evidence report

Generated from completed runs on 2026-10-17.
**37/37 integration checks pass** (18/18 v0.5 regressions;
19/19 resident checks). Clean-package Node-only smoke status:
**PASS**.

The complete required foreground bundle is **9,061 bytes**,
within the unchanged **9,063-byte ceiling**. The optional acquired resident module
is **20,708 bytes**, counted separately,
with no external runtime packages. Total deployed executable JS for resident use is
**29,769 bytes**;
resident code is not hidden inside the core byte figure. Each active job additionally
uses its own Node worker and native child; process/memory overhead is not claimed away.

## Verified persistence

- **optional capability acquisition and native-only clean CLI startup:** {"pythonRequired":false,"acquiredResident":true}
- **concurrent start clients converge on one authenticated supervisor:** {"clients":3,"supervisors":1}
- **job outlives submitting CLI; a distinct CLI discovers identity, status and output:** {"id":"d3c44385-c55a-4682-84fb-32e3f5aba7a2","submittingClientExited":true,"reconnectedClient":true,"status":"succeeded","output":"before disconnect\nafter disconnect\n"}
- **abrupt transport disconnect after submission does not cancel accepted work:** {"id":"drop-ad0b98ae-0eee-4ca0-b431-57373560a692","transportClosedBeforeResponse":true}
- **concurrent clients, stable identities and exactly one job for retried submission:** {"clients":8,"retries":2,"singleExecution":true}
- **supervisor SIGKILL/restart reconnects to an already running independent worker:** {"id":"5be27d2f-1673-4a19-9b35-258f3181a491","workerInstance":"32508e70-05ed-401c-82f4-1598681c3285","state":"succeeded"}
- **exact frozen view, executable, environment, literal commands and dependencies survive changes:** {"oldObjectRetained":true,"snapshotExecuted":true}
- **persistent Python jobs retain conflicting package views while reusing one runtime:** {"sharedRuntime":true,"isolatedVersions":["1.0","2.0"]}
- **stale records never authorize signalling an unrelated live process:** {"state":"unreachable","unrelatedProcessUntouched":true}
- **worker crash becomes interrupted/unreachable; no success fabricated or step replayed:** {"id":"9e26f941-b3c2-4298-af36-9db63e5e2ccf","state":"interrupted","executions":1}
- **acquisition crash reconciliation retains incomplete objects, committed views and owned state:** {"reconciliation":"reconciled","incompleteRetained":true,"viewRetained":true,"noSignals":true}
- **cancellation owns the direct child and bounds inherited-pipe waiting:** {"directChildCancelled":true,"descendantNotSignalled":true}
- **failed resident acquisition rolls back; disconnected provisioning client does not cancel writer:** {"clientKilled":true,"viewCommitted":true}
- **cold acquisition continues through supervisor death and restart:** {"supervisorKilled":true,"acquisitionCommitted":true}

These are actual CLI/process/socket/file experiments. Submission returns without
waiting for execution. Separate CLI processes discover and read an earlier job;
other tests disconnect the socket before the response, kill the supervisor while
the worker is running, stop/restart it, and interrupt acquisitions. Job identities,
outputs, frozen views, private metadata and completion markers are checked.

## Measurements

Host: linux/x64, v24.19.0,
INTEL(R) XEON(R) PLATINUM 8573C; kernel 6.18.55. Container scratch filesystem,
warm local caches. Integration completed before the final sequential benchmark runs.
Every raw sample is retained; no outliers are removed.

| Operation | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| Mixed-runtime cached view creation | 1000 | 2.036 | 3.059 | 3.888 | 6.497 |
| Mixed-runtime cached reprovision | 300 | 1.994 | 3.134 | 4.718 | 14.182 |
| Validated view lookup | 1000 | 0.077 | 0.253 | 0.500 | 0.859 |
| Fresh CLI + cached provisioning | 60 | 84.430 | 131.101 | 201.584 | 201.584 |
| Fresh CLI + Python/package execution | 60 | 99.431 | 151.477 | 340.286 | 340.286 |
| Raw Python child startup | 60 | 12.885 | 18.288 | 27.869 | 27.869 |
| Empty venv without pip (runtime-only reference) | 20 | 56.585 | 78.597 | 90.356 | 90.356 |
| Native cached view creation (direct API) | 1000 | 1.922 | 4.066 | 5.964 | 50.551 |
| Resident authenticated ping (fresh socket) | 300 | 0.163 | 0.664 | 1.415 | 2.149 |
| Resident request through persisted cached view | 300 | 2.177 | 3.614 | 4.532 | 24.068 |
| Raw Node child startup through exit | 40 | 78.999 | 113.272 | 130.852 | 130.852 |
| Durable resident submission through response | 40 | 5.636 | 7.861 | 9.545 | 9.545 |
| Accepted submission to worker control readiness | 40 | 84.813 | 103.325 | 151.039 | 151.039 |
| Complete native job submission through child exit | 40 | 176.814 | 192.701 | 251.898 | 251.898 |
| Resident terminal job inspection | 40 | 1.003 | 2.369 | 3.055 | 3.055 |

Cold acquisitions are separate, single offline observations:

| Cold operation | ms | Scope |
|---|---:|---|
| Mixed runtime + two real wheels + dataset/analysis DAG | 3065.752 | Actual CPython venv, pip target resolution/install and native fixture acquisition |
| Native dataset | 95.584 | Actual native installer child and committed owned resource |
| Optional resident capability | 90.747 | Actual native copy recipe and resource/ledger/view commits |
| Resident startup with cached capability | 113.615 | Cached activation, detached service process and authenticated ready endpoint |

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
| Host reboot / power-loss recovery | Not tested; metadata survives tested process interruptions. No automatic boot service is installed. Core parent-directory fsync/full transaction durability remains unimplemented. |
| Worker death with a surviving tenant | Conservatively reported; safe control adoption, tenant termination and automatic replay are not implemented. |
| Hostile native sandbox | Not implemented. Native steps are trusted OS processes; fs declarations are not kernel confinement. |
| Process-tree termination and quotas | Not implemented. Cancellation covers direct children; descendants, CPU/RAM/network enforcement need explicit acquired OS adapters. |
| Physical PID reuse and Linux /proc incarnation branch | Not forced in this environment. Authentication and conservative live-PID fallback are verified; unavailable incarnation data leaves identity unknown. |
| Immutable host executable contents | Not promised. Absolute resolution preserves command selection, while trusted host files/libraries and symlinks can still change. |
| Worker pooling | Not implemented. Per-job worker and tenant startup are measured separately. |
| Resource/job garbage collection | Not implemented. Historical objects, output and uncertain jobs remain owned and inspectable. Unknown jobs conservatively consume admission capacity. |
| Legacy unstamped/incomplete writer or recovery locks | Retained for inspection; no blind lock theft. A recovery guard interrupted before release requires operator inspection. |
| Windows/macOS/Termux native execution | Unverified. Portable Node/path/identity fallbacks are implemented; Linux execution is the evidence here. |
| Public standalone Python downloads / broader TAR formats | Not newly validated. v0.5 real local CPython extraction and conservative archive tests pass; no new network-distribution claim. |
| Full Python CLI / editable installs / browser host | Outside this change; v0.5 limits remain in STAGE-1.md. |

## Executed checks

### Original regression suite

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
- PASS: real pip target acquisition, shared interpreter and version conflicts
- PASS: Python module, script, argv, metadata resources and console entrypoint
- PASS: subprocess package inheritance, host PYTHONPATH exclusion and writable isolation
- PASS: package installation failure and requested depth/version drift fail without stale reuse
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

## Clean package and reproduction

The smoke test deploys only `main.js`, `manifest.json`, `package.json`, `capabilities/resident.mjs`,
launches from a different cwd, acquires only resident code, submits a Node-only
job, lets its submitting client exit and reconnects through new CLI processes.
No npm install, Python or container engine is required. Captured output:

```text
clean package started
clean package survived
```

Run sequentially from the distribution root:

```sh
node build.mjs
node tests/integration.mjs
node tests/resident.mjs
node tests/benchmark.mjs
node tests/resident-benchmark.mjs
node tests/package-smoke.mjs
node tests/report.mjs
```

The full historical Python regression/benchmark fixtures require host Python,
pip/venv support, headers and a C compiler. Native resident operation is Node-only.

Evidence files: integration.json/log, resident-integration.json/log,
benchmark.json/log, resident-benchmark.json/log and package-smoke.json/log.
Original v0.5 evidence is preserved in baseline/v0.5-evidence; the unchanged
source ZIP is preserved in baseline/somnus-plot-v0.5.zip.
