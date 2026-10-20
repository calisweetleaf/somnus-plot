# Somnus Plot v0.7 — Persistent Native Execution

The v0.5 acquisition/view architecture remains the execution authority. The bundled
Node standard-library core remains below its original 9,063-byte ceiling. The
resident supervisor is one optional native capability, acquired into `.grave/` by
an ordinary literal recipe. Python, Docker, npm packages, databases and per-project
virtual environments are not prerequisites for native jobs.

## Start and compose

Run these from this distribution's root with Node.js. No npm install is needed.

```sh
node capabilities/resident.mjs start
node capabilities/resident.mjs provision native '{"use":[]}'
node capabilities/resident.mjs submit native node -e 'console.log("started");setTimeout(()=>console.log("still here"),1000)'
node capabilities/resident.mjs list
node capabilities/resident.mjs inspect JOB_ID
node capabilities/resident.mjs output JOB_ID stdout 0 65536
node capabilities/resident.mjs cancel JOB_ID
node capabilities/resident.mjs prune                                   # dry run
node capabilities/resident.mjs prune '{"apply":true,"cache":{"maxAgeDays":30}}'
node capabilities/resident.mjs stop
```

`submit` returns a stable opaque job ID after durable submission and after a single-use
worker has durably claimed the job (`claimed.json`); see "v0.7 additions" below. It does not wait for execution to finish. A new CLI
can discover jobs through `list` and reconnect by identity. `stop` stops the
supervisor; jobs and in-progress cold acquisitions continue in independent workers.
Run `start` again to reconnect. Nothing installs a system boot service.

Use `--root /absolute/plot` before the operation to select another plot. The
launcher uses this distribution's `main.js`. Supply the optional `resident` recipe
from `manifest.json` in a separate plot; its source must be available for acquisition.
An already running supervisor can inspect and cancel accepted jobs even if the
manifest later disables new native execution. `start`, provisioning and submission
still require `execution:"trusted"` and `permissions.spawn:true`.

`node main.js`, `plan`, `provision NAME` and `run NAME COMMAND ...` retain their
v0.5 foreground behavior. The bundled default manifest's mixed Node/Python demo
still chooses Python explicitly. The native commands above acquire no Python.

For richer compositions, one JSON command surface accepts literal native steps,
existing `needs`, `cwd` and `env` declarations, limits and caller-selected IDs:

```sh
node capabilities/resident.mjs request <<'JSON'
{"op":"submit","id":"my-analysis-001","name":"native","limits":{"outputBytes":1048576,"timeoutMs":60000},"steps":[{"cmd":"node","args":["-e","console.log(process.argv[1])","$(literal argument)"],"env":{"EXPERIMENT":"one"},"cwd":"."}]}
JSON
```

The same ID and identical request returns the existing job. A different request
under that ID is rejected. This is at-most-one worker launch per immutable
submission, not exactly-once external side effects across arbitrary crashes.
The structured `request` operation also supports `list` with `offset`/`count`
(maximum 64), `inspect`, `output`, `cancel`, `provision`, `recover`, `ping` and `stop`.
Default `list` returns the first 64 identities and a next-page offset.

For JS composition, import `start(root, corePath)` and
`request(endpoint, {op, ...})` from `capabilities/resident.mjs`. They use the same
local protocol as the CLI. Do not copy endpoint tokens into prompts or shared logs.

## Execution identity and ownership

| Path | Ownership and lifetime |
|---|---|
| `main.js`, `src/plot.mjs` | Small complete foreground acquisition/view core |
| `data.json.assets` | v0.5 reusable resource ownership; resident code is an ordinary acquired resource |
| `.grave/objects/resident-*/resident.mjs` | Acquired resident implementation; services/workers execute this frozen resource |
| `.grave/envs/NAME.json`, `.grave/work/NAME/` | Existing resolved environment and persistent writable state |
| `.grave/.lock/owner.json` | Provisioning writer PID and exact newly allocated stages, recorded before each acquisition |
| `.grave/interrupted/acquisition-*/` | Archived stale acquisition journal; resources are retained |
| `.grave/resident/service.json` | Private supervisor endpoint, instance and authentication token |
| `.grave/resident/jobs/ID/submission.json` | Immutable resolved specification and original declarations |
| `.grave/resident/jobs/ID/claimed.json` | Exclusive one-time worker claim; never replayed automatically |
| `.grave/resident/jobs/ID/control.json` | Private authenticated worker endpoint and instance |
| `.grave/resident/jobs/ID/status.json` | Atomically replaced execution state |
| `.grave/resident/jobs/ID/stdout.log`, `stderr.log` | Bounded persistent captured output |
| `.grave/resident/acquisitions/ID.json` | Submitted/running/terminal cold acquisition metadata |
| `.grave/resident/reconciliation.json` | Last acquisition reconciliation report |

A submitted job stores the complete resolved view, exact resource records (including
full recipe/dependency keys), selected interpreter/package paths, original literal
step declarations, absolute executable lookup results, argument arrays, cwd, full
resolved environment and accepted authority/limits. Changing the current manifest,
PATH, named view or latest package layer does not rewrite that snapshot. Interpreter
symlink paths are preserved because their spelling can affect runtime semantics.
Absolute command resolution does not freeze host executable bytes or host libraries.
Committed resources retain v0.5's application-level read-only contract.

Submission metadata contains the inherited environment and may therefore contain
credentials present in that environment. Its directories/files are created private
(0700/0600 on POSIX); jobs' metadata is not a public export surface. Workers receive
only their submitted environment. Worker/control tokens are separate random opaque
identities. No content hashes replace resource or job identity.

The supervisor starts one detached Node worker per job. That worker owns direct
child handles, bounded output capture and execution state. It has no client socket
as a lifetime parent. The supervisor owns discovery and submission, not job lifetime.
Cold acquisitions run in separate processes too; warm provisioning calls the core's
full authoritative path in-process after checking that selected resources are cached.
Cache checks never replace acquisition, completion checks or view activation.

## Recovery and process authority

`node capabilities/resident.mjs recover` works without a live supervisor. It takes
an exclusive recovery guard and inspects the acquisition journal. It archives a
writer lock only when the owner is provably absent, or when a recorded Linux
incarnation demonstrably differs. A live PID without incarnation evidence remains
ambiguous. Legacy v0.5/partially written locks are retained for operator inspection.
All completed and incomplete objects, ledger references, historical views and
writable state are retained. An old installer may still write an incomplete stage;
recovery neither reuses nor deletes that stage. New acquisition allocates fresh
objects. There is no automatic repair or installer replay; deletion happens only through
an explicit `prune` (below).

On supervisor restart, `inspect` authenticates the independent worker using its
private endpoint and returned job/instance identity. PIDs are diagnostic only. On
Linux, boot ID plus process start ticks can distinguish reused PIDs when `/proc`
is available; elsewhere a nonresponsive live PID remains unknown. If worker control
is unavailable, state becomes `interrupted` when absence/different incarnation is
proved, or `unreachable` otherwise. A persisted success is never invented. A dead
worker is never restarted automatically; its tenant process could still be running.

Cancellation goes through the authenticated live worker, which signals only its
own direct `ChildProcess` handle. It tries SIGTERM and escalates after 500 ms if
that same owned child remains alive. Recorded PIDs are never termination targets.
Canceling a finished job returns its final state. Unavailable worker control causes
cancellation to fail; it does not authorize a PID-based fallback. SIGTERM/SIGKILL
behavior is verified on Linux only.

Descendants created by a tenant are outside that direct-child cancellation scope.
If they keep output pipes open after the direct child's exit, the worker closes
those inherited pipes after 500 ms and records `inheritedPipesClosed:true`. It does
not signal descendants. Full process-tree ownership, OS job objects, pidfds,
cgroups and hostile-code isolation belong in explicit acquired adapters; none is
silently approximated through persisted PIDs or broad group signals.

## v0.7 additions

Frozen interfaces: `docs/V07-CONTRACTS.md` §§4–9. Summary:

- **Standby claim.** The supervisor keeps a pool of single-use standby workers
  (`PLOT_RESIDENT_READY` default 2, `PLOT_RESIDENT_MAX_STARTING` 2, `PLOT_RESIDENT_MAX_WAITING` 16).
  A submission leases an idle standby, which writes the write-once `claimed.json`
  (owner, rid, rotated control endpoint) before the reply. The reply carries
  `{claimed, determinate, path:'standby'|'cold'|'waited', t:{...}}`. A lost ACK adopts the durable claim; a
  second worker is tried only when the first is proven gone without a claim. Workers are never reused.
- **Request IDs.** `rid` (`[A-Za-z0-9_-]{1,64}`) makes a retry return the existing job or turn;
  a different request under the same rid is `request conflict`. The CLI generates one per submit.
- **Pins and prune.** Foreground, job, acquisition and environment pins under `.grave/pins/`
  protect objects in use. `prune` is a dry run unless `apply:true`; `cache:{maxAgeDays,maxBytes}`
  selects unpinned, unreferenced objects and `includeJobs:{maxAgeDays}` expires terminal jobs.
  Deletion writes a tombstone intent under `.grave/tombstones/` first; a crash leaves an intent
  that the next applied prune finishes or withdraws.
- **Environments.** `activate`, `interact`, `env_inspect` and `deactivate` (through `request`)
  run one detached Environment Host per incarnation with Python and/or Node tenants whose heap
  persists across turns and across supervisor replacement:

  ```sh
  echo '{"op":"activate","name":"lab","view":"default"}' | node capabilities/resident.mjs request
  echo '{"op":"interact","name":"lab","expectIncarnation":"INC","runtime":"python","code":"x=41\nx+1"}' | node capabilities/resident.mjs request
  ```

  A turn is 1 in flight plus 8 queued (overflow `busy`, retryable), output capped at 1 MiB per
  stream, default deadline 30 s. A deadline, tenant death or host death retires the
  incarnation `interrupted` with `stateEffect:'lost'`; nothing restarts with an empty heap.
  A retried turn rid on a retired incarnation returns the recorded outcome if one was written.

| Path (v0.7) | Ownership and lifetime |
|---|---|
| `.grave/resident/standby/SLOT/standby.json` | Idle standby endpoint; removed at claim or retirement |
| `.grave/requests/RID.json` | Job rid lookup, write-once |
| `.grave/pins/*.json` | Reference pins (foreground, job, acquisition, env) |
| `.grave/tombstones/` | Prune intents and moved objects awaiting deletion |
| `.grave/resident/envs/NAME/current.json` | Current incarnation of an environment |
| `.grave/resident/envs/NAME/inc/INC/` | `instance.json`, `owner.json`, `control.json`, `status.json`, `turns/`, `requests/` |

## Limits and boundaries

- Output retains at most 1 MiB per job by default, shared across stdout/stderr;
  callers can select 0 through 16 MiB. Overflow is drained and discarded and
  `outputLimited` is reported. Output responses use byte offsets, include exact
  base64 bytes and convenient UTF-8 text, and cap a read at 256 KiB.
- A job timeout is optional (0 means no timeout), with a maximum requested value
  of 24 hours. Timeout authority covers the direct child as cancellation does.
- One supervisor admits at most 16 active or uncertain jobs (`PLOT_RESIDENT_MAX_ACTIVE`), up to 16 pending
  submissions, one cold acquisition and 64 simultaneous sockets per endpoint.
  Frames are bounded at 1 MiB, output responses at 8 MiB. Job history remains
  until an applied prune with `includeJobs` expires it; uncertain jobs consume capacity.
- If a job is interrupted and the operator has established that its processes
  are gone, archive that job directory outside `.grave/resident/jobs/` to release
  its conservative active slot. Keep its evidence; Plot does not erase it for you.
- Native code remains trusted and inherits OS authority. `permissions.fs` is
  not a kernel filesystem sandbox; CPU, RAM and network quotas are not implemented.
  Owned resource paths, marker identity, dependency presence and view selections
  are checked; this does not turn native tenants into hostile-code sandboxes.
- Metadata uses private file creation, fsync and atomic replacement. Resident
  replacements additionally sync parent directories on POSIX. Core parent-dir
  fsync and a complete power-loss transaction remain unimplemented. A successful
  ledger commit followed by failed view activation keeps completed resources and
  the prior view, as in v0.5.
- Native Windows, macOS and Termux execution are unverified. Native path lookup,
  detached worker flags, host recipe selection and conservative identity fallback
  are present. Windows shell wrappers require an explicitly acquired shell.
  No Python/Docker/systemd/daemon package is mandatory.

## Verify and reproduce

```sh
scripts/gate.sh              # every suite in a disposable copy
scripts/gate.sh --bench      # plus every benchmark, including the v0.7 frozen workloads
scripts/gate.sh --evidence   # in place: regenerates evidence/ and evidence/RESULTS.md
```

The v0.5 suite's optional-Python checks require host Python, pip/venv support,
headers and a C compiler; the native runtime itself does not. Tests build real
local wheel/extension fixtures and use real sockets/processes. The bootstrap suite
uses the network only to fill its pinned-archive cache and for its online checks.
Benchmarks retain every sample and report outliers. Run them sequentially with no
other test workload. See `evidence/RESULTS.md` for actual results and limitations;
`baseline/v0.5-evidence/` preserves the supplied prior measurements. `STAGE-1.md`
remains the historical acquisition/view contract; this document supersedes only
its interruption-recovery and future-resident sections.
