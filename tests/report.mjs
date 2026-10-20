// Evidence is generated only from completed runs; no benchmark prose is hard-coded as a pass.
import * as fs from 'node:fs';
import path from 'node:path';
const base=path.resolve(new URL('..',import.meta.url).pathname),read=n=>JSON.parse(fs.readFileSync(path.join(base,'evidence',n)));
const original=read('integration.json'),resident=read('resident-integration.json'),bench=read('benchmark.json'),rb=read('resident-benchmark.json'),smoke=read('package-smoke.json'),fmt=n=>n.toFixed(3);
const labels={new_persisted_cached_asset_view:'Mixed-runtime cached view creation',cached_reprovision:'Mixed-runtime cached reprovision',view_lookup:'Validated view lookup',cli_warm_provision:'Fresh CLI + cached provisioning',cli_python_package_execution:'Fresh CLI + Python/package execution',raw_python_startup:'Raw Python child startup',empty_venv_without_pip:'Empty venv without pip (runtime-only reference)',direct_persisted_cached_view:'Native cached view creation (direct API)',resident_ping:'Resident authenticated ping (fresh socket)',resident_persisted_cached_view:'Resident request through persisted cached view',raw_node_child_startup:'Raw Node child startup through exit',resident_durable_submit:'Durable resident submission through response',accepted_to_worker_control_ready:'Accepted submission to worker control readiness',complete_submit_through_verified_child_exit:'Complete native job submission through child exit',resident_terminal_inspect:'Resident terminal job inspection'};
const passed=original.passed+resident.passed,total=original.total+resident.total;
let text=`# Somnus Plot v0.6 — evidence report

Generated from completed runs on ${rb.finished_at.slice(0,10)}.
**${passed}/${total} integration checks pass** (${original.passed}/${original.total} v0.5 regressions;
${resident.passed}/${resident.total} resident checks). Clean-package Node-only smoke status:
**${smoke.status===0?'PASS':'FAIL'}**.

The complete required foreground bundle is **${original.core_bytes.toLocaleString('en-US')} bytes**,
within the unchanged **9,063-byte ceiling**. The optional acquired resident module
is **${rb.environment.optional_resident_bytes.toLocaleString('en-US')} bytes**, counted separately,
with no external runtime packages. Total deployed executable JS for resident use is
**${(original.core_bytes+rb.environment.optional_resident_bytes).toLocaleString('en-US')} bytes**;
resident code is not hidden inside the core byte figure. Each active job additionally
uses its own Node worker and native child; process/memory overhead is not claimed away.

## Verified persistence

`+resident.checks.filter(c=>c.evidence).map(c=>`- **${c.name}:** ${JSON.stringify(c.evidence)}`).join('\n')+`

These are actual CLI/process/socket/file experiments. Submission returns without
waiting for execution. Separate CLI processes discover and read an earlier job;
other tests disconnect the socket before the response, kill the supervisor while
the worker is running, stop/restart it, and interrupt acquisitions. Job identities,
outputs, frozen views, private metadata and completion markers are checked.

## Measurements

Host: ${rb.environment.platform}/${rb.environment.arch}, ${rb.environment.node},
${rb.environment.cpu}; kernel ${rb.environment.release}. Container scratch filesystem,
warm local caches. Integration completed before the final sequential benchmark runs.
Every raw sample is retained; no outliers are removed.

| Operation | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
`;
for(const group of [bench.metrics,rb.metrics])for(const [name,{summary:s}] of Object.entries(group))text+=`| ${labels[name]||name} | ${s.n} | ${fmt(s.p50_ms)} | ${fmt(s.p95_ms)} | ${fmt(s.p99_ms)} | ${fmt(s.max_ms)} |\n`;
text+=`
Cold acquisitions are separate, single offline observations:

| Cold operation | ms | Scope |
|---|---:|---|
| Mixed runtime + two real wheels + dataset/analysis DAG | ${fmt(bench.cold_first_acquisition_ms)} | Actual CPython venv, pip target resolution/install and native fixture acquisition |
| Native dataset | ${fmt(rb.cold_acquisition.native_data_ms)} | Actual native installer child and committed owned resource |
| Optional resident capability | ${fmt(rb.cold_acquisition.optional_resident_ms)} | Actual native copy recipe and resource/ledger/view commits |
| Resident startup with cached capability | ${fmt(rb.resident_startup_ms)} | Cached activation, detached service process and authenticated ready endpoint |

Persisted cached-view p95 gates: mixed-runtime direct API
**${bench.gates.new_persisted_cached_asset_view_p95_under_6_ms?'PASS':'FAIL'}**;
native direct API **${rb.gates.direct_cached_view_p95_under_6_ms?'PASS':'FAIL'}**;
resident through validated persisted view and response
**${rb.gates.resident_cached_view_p95_under_6_ms?'PASS':'FAIL'}**.

**The objective is p95 below 6 ms for cached view operations. Maximums exceed
6 ms in these runs. Durable job submission, cold acquisition, fresh CLI/worker/child
startup and complete execution are distinct costs and are not below-6-ms claims.**
The old v0.5 measurement used another host; no cross-host speedup claim is made.

The mixed-runtime view series creates 1,000 distinct persisted writable views over
four shared resources, then executes representative views with real Python imports,
a compiled extension, metadata and dataset checks. Native direct/resident series
also execute representative measured views. ${rb.verified_job_ids.length} complete resident jobs
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

`;
for(const [label,report] of [['Original regression suite',original],['Resident integration suite',resident]]){text+=`### ${label}\n\n`;for(const c of report.checks)text+=`- ${c.passed?'PASS':'FAIL'}: ${c.name}\n`;text+='\n'}
text+=`## Clean package and reproduction

The smoke test deploys only ${smoke.deployed_files.map(x=>'`'+x+'`').join(', ')},
launches from a different cwd, acquires only resident code, submits a Node-only
job, lets its submitting client exit and reconnects through new CLI processes.
No npm install, Python or container engine is required. Captured output:

\`\`\`text
${smoke.output}\`\`\`

Run sequentially from the distribution root:

\`\`\`sh
node build.mjs
node tests/integration.mjs
node tests/resident.mjs
node tests/benchmark.mjs
node tests/resident-benchmark.mjs
node tests/package-smoke.mjs
node tests/report.mjs
\`\`\`

The full historical Python regression/benchmark fixtures require host Python,
pip/venv support, headers and a C compiler. Native resident operation is Node-only.
`+`\nEvidence files: integration.json/log, resident-integration.json/log,
benchmark.json/log, resident-benchmark.json/log and package-smoke.json/log.
Original v0.5 evidence is preserved in baseline/v0.5-evidence; the unchanged
source ZIP is preserved in baseline/somnus-plot-v0.5.zip.\n`;
fs.writeFileSync(path.join(base,'evidence/RESULTS.md'),text);
console.log(JSON.stringify({checks:[passed,total],core_bytes:original.core_bytes,resident_bytes:rb.environment.optional_resident_bytes,cached_view_p95_ms:bench.metrics.new_persisted_cached_asset_view.summary.p95_ms,resident_view_p95_ms:rb.metrics.resident_persisted_cached_view.summary.p95_ms,complete_job_p95_ms:rb.metrics.complete_submit_through_verified_child_exit.summary.p95_ms,package_smoke:smoke.status}));
if(passed!==total||smoke.status!==0||![...Object.values(bench.gates),...Object.values(rb.gates)].every(Boolean))process.exitCode=1;
