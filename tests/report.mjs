// Evidence is generated only from completed runs; no benchmark prose is hard-coded as a pass.
import * as fs from 'node:fs';
import path from 'node:path';
const base=path.resolve(new URL('..',import.meta.url).pathname),read=n=>JSON.parse(fs.readFileSync(path.join(base,'evidence',n)));
const original=read('integration.json'),resident=read('resident-integration.json'),renv=read('resident-env.json'),e2e=read('e2e.json'),bench=read('benchmark.json'),rb=read('resident-benchmark.json'),v7=read('v07-benchmark.json'),smoke=read('package-smoke.json'),fmt=n=>n==null?'—':n.toFixed(3);
// Suites that write no JSON report their count on the last summary line of their gate log.
const logged=n=>{try{const m=[...fs.readFileSync(path.join(base,'evidence',n+'.log'),'utf8').matchAll(/^(\d+)\/(\d+) [a-z -]*checks/gm)].at(-1);return m?{passed:+m[1],total:+m[2]}:null}catch{return null}};
const logs=Object.fromEntries(['cartographer','assembler','bootstrap'].map(n=>[n,logged(n)]));
const pf=b=>b?'PASS':'FAIL';
const labels={new_persisted_cached_asset_view:'Mixed-runtime cached view creation',cached_reprovision:'Mixed-runtime cached reprovision',view_lookup:'Validated view lookup',cli_warm_provision:'Fresh CLI + cached provisioning',cli_python_package_execution:'Fresh CLI + Python/package execution',raw_python_startup:'Raw Python child startup',empty_venv_without_pip:'Empty venv without pip (runtime-only reference)',direct_persisted_cached_view:'Native cached view creation (direct API)',resident_ping:'Resident authenticated ping (fresh socket)',resident_persisted_cached_view:'Resident request through persisted cached view',raw_node_child_startup:'Raw Node child startup through exit',resident_durable_submit:'Durable resident submission through response',accepted_to_worker_control_ready:'Accepted submission to worker control readiness',complete_submit_through_verified_child_exit:'Complete native job submission through child exit',resident_terminal_inspect:'Resident terminal job inspection'};
const suites=[['core integration',original],['resident',resident],['resident environments',renv],['end-to-end composition',e2e],...Object.entries(logs).filter(([,v])=>v)];
const passed=suites.reduce((a,[,r])=>a+r.passed,0),total=suites.reduce((a,[,r])=>a+r.total,0);
let text=`# Somnus Plot v0.7 — evidence report

Generated from completed runs on ${v7.finished_at.slice(0,10)}.
**${passed}/${total} checks pass** (${suites.map(([n,r])=>`${r.passed}/${r.total} ${n}`).join('; ')}).
Suites without a JSON report are read from their gate logs${Object.entries(logs).filter(([,v])=>!v).map(([n])=>`; ${n} log absent`).join('')}.
Clean-package smoke status: **${smoke.status===0?'PASS':'FAIL'}**. Host matrix: Linux x64 glibc only;
Windows, macOS and Android/Termux are **NOT RUN** (kits and runners in \`bootstrap/hosts/\`).

The complete required foreground bundle is **${original.core_bytes.toLocaleString('en-US')} bytes**,
within the unchanged **9,063-byte ceiling**. The optional acquired resident module
is **${rb.environment.optional_resident_bytes.toLocaleString('en-US')} bytes**, counted separately,
with no external runtime packages. Other acquired capabilities, also counted separately:
${Object.entries(smoke.capability_bytes||{}).filter(([k])=>k!=='resident.mjs').map(([k,v])=>`\`${k}\` ${v.toLocaleString('en-US')} B`).join(', ')}. Total deployed executable JS for resident use is
**${(original.core_bytes+rb.environment.optional_resident_bytes).toLocaleString('en-US')} bytes**;
resident code is not hidden inside the core byte figure. Each active job additionally
uses its own single-use Node worker (claimed from a standby pool) and native child;
process/memory overhead is not claimed away.

## Verified persistence

`+[...resident.checks,...renv.checks,...e2e.checks].filter(c=>c.evidence).map(c=>`- **${c.name}:** ${JSON.stringify(c.evidence)}`).join('\n')+`

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
## v0.7 frozen workloads (docs/V07-CONTRACTS.md §12)

Host: ${v7.environment.platform}/${v7.environment.arch}, ${v7.environment.node}, ${v7.environment.cpu} × ${v7.environment.cpu_count};
kernel ${v7.environment.release}; load average at start ${v7.environment.loadavg_at_start.map(x=>x.toFixed(2)).join(' / ')}.
Run valid: **${v7.valid?'yes':'NO'}**${v7.failures.length?' — failures: '+v7.failures.join('; '):''}. ${v7.percentiles}.

| Row | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
`;
const m7=v7.metrics,row=(l,x)=>x?`| ${l} | ${x.n} | ${fmt(x.p50_ms)} | ${fmt(x.p95_ms)} | ${fmt(x.p99_ms)} | ${fmt(x.max_ms)} |\n`:'';
text+=row('multi_version_switch (child spawns '+m7.multi_version_switch?.child_spawns+')',m7.multi_version_switch?.summary)+row('durable_submit_and_claim: reply',m7.durable_submit_and_claim?.reply.summary)+row('durable_submit_and_claim: control ready (endpoint record)',m7.durable_submit_and_claim?.control_ready.summary)+row('control endpoint first answer (no gate)',m7.durable_submit_and_claim?.control_answer.summary)
 +row('sustained_submit successful (Poisson 10/s)',m7.sustained_submit?.successful.summary)+row('warm_env_interact python ('+m7.warm_env_interact_python?.runtime+')',m7.warm_env_interact_python?.summary)+row('warm_env_interact node',m7.warm_env_interact_node?.summary)
 +row('cold_worker_spawn',m7.cold_worker_spawn?.summary)+row('complete_isolated_job',m7.complete_isolated_job?.summary)+row('cold_acquisition',m7.cold_acquisition?.summary)+row('bootstrap_cold (Node from kit)',m7.bootstrap_cold?.summary)+row('replenish',m7.replenish?.summary);
const sus=m7.sustained_submit,g7=v7.gates;
text+=`
Sustained: ${sus?`${sus.offered} offered over ${sus.schedule.duration_s} s (seed ${sus.schedule.seed}), ${sus.accepted} accepted (${(sus.acceptance*100).toFixed(2)} %), ${sus.correctness_failures} correctness failures, paths ${JSON.stringify(sus.paths)}; pool empty at start ${sus.pool_empty.at_start}, leases that found no idle standby ${sus.pool_empty.lease_found_no_idle}`:'NOT RUN'}.
Bursts (offered → accepted / rejected, peak starting): ${Object.entries(m7.burst_submit||{}).map(([b,x])=>`${b} → ${x.accepted}/${x.rejected}, ${x.peakStarting}`).join('; ')}.
Saturation: max stable rate **${m7.saturation?.max_stable_rate_per_s??'—'}/s** (${m7.saturation?.stable_rule}); steps ${(m7.saturation?.steps||[]).map(x=>`${x.rate_per_s}/s ${(x.acceptance*100).toFixed(1)} % p95 ${fmt(x.successful.p95_ms)}`).join(', ')}.
${v7.not_run.length?'NOT RUN: '+v7.not_run.map(x=>x.row+' ('+x.why+')').join('; ')+'\n':''}
| Frozen gate | Result |
|---|---|
| multi_version_switch p95 < 6 ms with 0 spawns | ${pf(g7.multi_version_switch_p95_under_6_ms)} |
| durable_submit_and_claim p95 < 6 ms (reply and control ready) | ${pf(g7.durable_submit_and_claim_p95_under_6_ms)} |
| sustained_submit successful p95 < 6 ms | ${pf(g7.sustained_submit?.successful_p95_under_6_ms)} |
| sustained_submit acceptance ≥ 99 % | ${pf(g7.sustained_submit?.acceptance_at_least_99_pct)} |
| sustained_submit 0 correctness failures | ${pf(g7.sustained_submit?.zero_correctness_failures)} |
| sustained_submit pool observed empty (validity) | ${pf(g7.sustained_submit?.valid)} |
| burst_submit accounted and bounded | ${pf(g7.burst_submit_accounted_bounded)} |
| warm_env_interact python p95 < 6 ms | ${pf(g7.warm_env_interact_python_p95_under_6_ms)} |
| warm_env_interact node p95 < 6 ms | ${pf(g7.warm_env_interact_node_p95_under_6_ms)} |

A FAIL here is an open gate, reported as measured; the workload was frozen before tuning and is not reduced.

Cold acquisitions (v0.6 series) are separate, single offline observations:

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
| Host reboot / power-loss recovery | Not tested; metadata survives tested process interruptions. No automatic boot service is installed. Core \`atom\` fsyncs the file and, on POSIX, the parent directory; durability across power loss is not tested. |
| Worker death with a surviving tenant | Conservatively reported; tenant termination and automatic replay are not implemented. Lost claim ACKs are adopted from the durable claim (P07-05). |
| Hostile native sandbox | Not implemented. Native steps are trusted OS processes; fs declarations are not kernel confinement. |
| Process-tree termination and quotas | Not implemented. Cancellation covers direct children; descendants, CPU/RAM/network enforcement need explicit acquired OS adapters. |
| Physical PID reuse and Linux /proc incarnation branch | Not forced in this environment. Authentication and conservative live-PID fallback are verified; unavailable incarnation data leaves identity unknown. |
| Immutable host executable contents | Not promised. Absolute resolution preserves command selection, while trusted host files/libraries and symlinks can still change. |
| Worker pooling | Single-use standby workers (claimed once, never reused). Worker reuse across jobs is not implemented by design. |
| Resource/job garbage collection | Pin-safe prune, dry-run by default, tombstone intents with crash recovery. No automatic schedule; historical cache and uncertain jobs are kept unless policy selects them. |
| Resident environment heaps | Survive supervisor replacement; tenant or host death retires the incarnation (\`interrupted\`, heap lost). No checkpoint/restore. |
| Legacy unstamped/incomplete writer or recovery locks | Retained for inspection; no blind lock theft. A recovery guard interrupted before release requires operator inspection. |
| Windows/macOS/Termux native execution | NOT RUN. Kits, launchers and certification runners ship in \`bootstrap/\`; Linux execution is the only evidence here. Cross-host acceptance is open. |
| Pinned upstream Python/Node/Git | Acquired and verified on Linux x64 glibc from the pinned python-build-standalone/nodejs.org/git archives (bootstrap suite) and used as the owned runtime by the end-to-end suite. |
| p99 latency | Not gated. Several p99 values exceed 6 ms; only p95 is the objective. |
| Full Python CLI / editable installs / browser host | Outside this change; v0.5 limits remain in STAGE-1.md. |

## Executed checks

`;
for(const [label,report] of [['Core integration suite',original],['Resident integration suite',resident],['Resident environment suite',renv],['End-to-end composition suite (runtime '+e2e.runtime+')',e2e]]){text+=`### ${label}\n\n`;for(const c of report.checks)text+=`- ${c.passed?'PASS':'FAIL'}: ${c.name}\n`;text+='\n'}
text+=`## Clean package and reproduction

The smoke test deploys only ${smoke.deployed_files.map(x=>'`'+x+'`').join(', ')}${smoke.deployed_dirs?' and '+smoke.deployed_dirs.map(x=>'`'+x+'/`').join(', '):''},
launches from a different cwd, acquires only resident code, submits a Node-only
job, lets its submitting client exit and reconnects through new CLI processes.
${smoke.capabilities?`From the same foreign cwd it runs bootstrap inspect (\`${smoke.capabilities.bootstrap_inspect}\`), a cartographer plan and an assembler publish.`:''}
No npm install, Python or container engine is required. Captured output:

\`\`\`text
${smoke.output}\`\`\`

Run sequentially from the distribution root:

\`\`\`sh
node build.mjs
scripts/gate.sh --evidence   # build, every suite, every benchmark, then this report
\`\`\`

The full historical Python regression/benchmark fixtures require host Python,
pip/venv support, headers and a C compiler. Native resident operation is Node-only.
The end-to-end suite and bootstrap_cold need the offline kit (built by tests/bootstrap.mjs).
`+`\nEvidence files: integration, resident-integration, resident-env, e2e, benchmark,
resident-benchmark, v07-benchmark and package-smoke (.json/.log), plus cartographer,
assembler and bootstrap logs.
Original v0.5 evidence is preserved in baseline/v0.5-evidence; the unchanged
source ZIP is preserved in baseline/somnus-plot-v0.5.zip.\n`;
fs.writeFileSync(path.join(base,'evidence/RESULTS.md'),text);
console.log(JSON.stringify({checks:[passed,total],core_bytes:original.core_bytes,resident_bytes:rb.environment.optional_resident_bytes,cached_view_p95_ms:bench.metrics.new_persisted_cached_asset_view.summary.p95_ms,resident_view_p95_ms:rb.metrics.resident_persisted_cached_view.summary.p95_ms,complete_job_p95_ms:rb.metrics.complete_submit_through_verified_child_exit.summary.p95_ms,package_smoke:smoke.status,v07_valid:v7.valid,v07_gates:v7.gates}));
if(passed!==total||smoke.status!==0||!v7.valid||![...Object.values(bench.gates),...Object.values(rb.gates)].every(Boolean))process.exitCode=1;
