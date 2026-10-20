# **Somnus Plot v0.6 to v0.7 — The Seventh Flash: Master Execution Plan**

**Document Role:** Canonical architectural specification, surface contract, wave topology, and packet board for upgrading Somnus Plot from **v0.6.0 (Persistent Native Execution)** to **v0.7.0 (The Seventh Flash: Resident Execution Environments & Compositional Substrate)**. **Target Audience:** Multi-agent engineering swarm and lane coordinators operating under the Somnus Accelerate protocol (AGENTS.md, TASK.md, scripts/gate.sh). **Operating Rule:** This plan specifies **what** must exist, **what** contracts and invariants govern every surface, **how** work is partitioned across parallel and sequential packets, and **what** evidence proves completion. It intentionally omits implementation code so each lane engineer synthesizes minimal, idiomatic code directly from the repository's existing implementation surfaces.

**Revision:** Reconciled execution edition, 20 October 2026. Synthesizes Argon's supplied architecture, the supplied GPT critique, and additional ownership, bootstrap, and measurement contracts. Historical v0.6 sizes, timings, and source line counts below are supplied baseline claims: the executing coordinator must verify them against the actual checkout. This edit does not certify repository behavior.

**Dispatch:** Launch implementation promptly. The coordinator performs P07-00 as a bounded opening integration slice, freezes shared interfaces, and dispatches disjoint lanes as soon as their interfaces are settled. No separate design committee, operator approval round, or open-ended research phase is required. Opus 5.5 may coordinate Argon 4 subagents in the operator's Factory system; model choice does not change engineering acceptance. This document specifies work for that system; editing it does not launch those agents.

**Design freedom:** Outcomes, seed laws, identity, durability, and truthful evidence are binding. Proposed data structures and process arrangements are candidates. Agents may replace a candidate with a smaller or stronger mechanism when they record the reason, preserve public compatibility, update consumers atomically, and prove the replacement against the same failure and workload tests. Never silently lower the performance target or recast an unmet contract as a pass.

## **1\. Executive Charter: The v0.6 to v0.7 Architectural Turn**

### **1.1 Lineage and Horizon Discipline**

Somnus Plot pursues the smallest, fastest, most capable portable execution environment possible by deriving capability from composition rather than core size. Across versions, each release has changed what survives after the initiating caller exits:

| Version | Architectural Stage | What Persists Across Invocations | What Dies After Each Invocation | Core Ceiling |
| :---- | :---- | :---- | :---- | :---- |
| **v0.4** | Transient Script Runner | Bootstrap ledger (data.json) and a single shallow Python directory (.grave/py) | Every foreground execution process and environment view | 9,063 bytes |
| **v0.5** | Transactional Layer Provisioner | Acquired immutable-by-contract objects (.grave/objects/), named environment views (.grave/envs/), and per-view writable state (.grave/work/) | Every foreground step runner and child process | 9,063 bytes (9,036 actual) |
| **v0.6** | Persistent Detached Batch Jobs | An optional acquired supervisor (resident.mjs), detached per-job worker processes, and captured job logs (.grave/resident/jobs/) | The worker process and tenant runtime heap at the end of each submitted job; views remain passive JSON files on disk | 9,063 bytes (9,061 actual) |
| **v0.7** | **Resident Execution Environments & Compositional Substrate** | **Multi-version indexed objects, pre-booted single-use standby workers, and live Resident Environments holding warm tenant runtime sessions across turns** | **Only single-use isolated job workers after job completion, or explicitly deactivated environment instances** | **9,063 bytes** |
| **v0.8–v1.0** | Independently Bootable Persistent Virtual Machine *(Reserved Horizon)* | Hardware-abstracted linear memory snapshots, virtualized device/filesystem mounts, and cross-host resumable execution state | Nothing unless explicitly destroyed | Governed by future seed law |

**Horizon Guardrail for All v0.7 Agents:** v0.7 must reach a level of completeness that a systems engineer regards as a finished, self-contained portable execution environment. Do **not** prematurely build bytecode interpreters, WASI runtimes, hardware emulators, or fake kernel sandboxes in v0.7. Those belong to v0.8 through v1.0. Conversely, do **not** treat v0.7 as a mere collection of convenience utilities around v0.6's batch job spawner.

### **1.2 The Central Inversion of v0.7**

In v0.6, a **View** (.grave/envs/\<name\>.json) is a dead JSON file on disk, and a **Job** (.grave/resident/jobs/\<id\>/) is the only living entity. Every time a client interacts with an environment in v0.6, the supervisor spawns a brand-new OS process (node \--worker), which boots V8 (\~85–103 ms), binds a control socket, reads the passive View JSON, spawns a brand-new child interpreter (node or python), imports packages from cold disk, runs a command array, writes files to PLOT\_STATE, and dies.  
v0.7 executes two foundational inversions while preserving 100% backward compatibility with v0.5 and v0.6:

> 1. **Separating Execution Readiness from OS Process Birth (For Isolated Jobs):** Instead of spawning a fresh OS worker process *after* a submit request arrives—or weakening durability by acknowledging submit before an independent worker owns the job—the resident supervisor maintains a bounded pool of **pre-booted, independent, single-use standby worker processes**. When submit arrives, the supervisor transfers ownership synchronously over loopback to an already-breathing standby worker, which commits claimed.json, owner.json, and control.json *before* submit returns to the caller. The required measured outcome is durable submission and worker control readiness below the **6 ms p95 bell** while strengthening crash survival.  
> 2. **Inverting View and Job into Resident Execution Environments (For Stateful Continuity):** A named View can now be **activated** from passive metadata into a living **Resident Environment** (.grave/resident/envs/\<name\>/) backed by an independent Environment Host process and warm tenant runtime sessions (such as a persistent Python \-I \-S turn loop with the View's package layer already imported in memory, or a persistent Node execution context). Work dispatched via interact reuses an already-living environment. The sub-6 ms gate applies to the specified bounded reference workload, not arbitrary user computation. Heap continuity survives supervisor death while the Environment Host and tenant remain alive; it does not imply recovery after tenant death, host reboot, or power loss.

### **1.3 The Five Concrete v0.6 Ceilings v0.7 Must Eliminate**

The supplied plan identifies five structural bottlenecks to confirm in the v0.6 checkout. Host self-establishment is an additional first-class v0.7 outcome under §6.3:

| Ceiling ID | v0.6 Defect / Bottleneck | Affected v0.6 Surface | Required v0.7 Outcome |
| :---- | :---- | :---- | :---- |
| **C-01** | **Single-Slot Ledger Amnesia:** data.json.assets only stores the single most recent object per capability ID. Switching a view or capability from v1 to v2 and back to v1 forces a cold re-acquisition of v1 even though v1's completed object directory still sits in .grave/objects/. | src/plot.mjs (provision) | provision discovers and reuses any valid completed object in .grave/objects/\<id\>-\*/ matching the exact canonical (recipe, host, dependency\_paths) key with zero child spawns. |
| **C-02** | **Shallow Python Fragility, Diagnostic Blindness & Missing Core Dir Fsync:** src/plot.mjs runs python3 \-m venv without \--without-pip even when packages is empty (failing on Debian/Ubuntu/Termux hosts without ensurepip), drops stdout when reporting spawnSync failures, and omits POSIX parent-directory fsync in atom(). | src/plot.mjs (atom, exec, acquire) | Core atom() fsyncs parent directories on POSIX; exec() surfaces stderr or stdout on failure; shallow Python succeeds without ensurepip when pip is not invoked or when layers are assembled by an offline wheel capability. |
| **C-03** | **The 111 ms / 193 ms Process-Birth Cliff:** Cached view operations take 3.6–4.1 ms p95, but durable job submission takes 7.861 ms p95, worker readiness takes 103.325 ms p95, and a trivial native job takes 192.701 ms p95 because every job boots two cold OS processes in sequence. | capabilities/resident.mjs (serve, launchWorker, worker) | Pre-booted single-use standby workers bring synchronous durable submission \+ worker claim \+ control readiness under 6 ms p95; Resident Environment interact turns execute warm tenant work under 6 ms p95. |
| **C-04** | **O(N) Submission Stalls & 16-Slot Capacity Bricking:** Every submit scans all job directories on disk and awaits summary(), incurring a 500 ms socket timeout per unreachable job, and counts interrupted (provably dead) jobs against the 16-job active limit forever. | capabilities/resident.mjs (serve, inspect, recover) | Supervisor maintains an O(1) in-memory active admission table; jobs whose workers are provably absent or other incarnation transition atomically on disk to terminal interrupted status—preserving failure evidence while releasing active admission capacity. |
| **C-05** | **Shared-View Scratch Collisions & Unbounded .grave/ Growth:** Concurrent jobs running against the same View collide if they write intermediate step data to shared PLOT\_STATE, and there is no safe mechanism to garbage-collect unreferenced .grave/objects/ or old terminal jobs. | capabilities/resident.mjs (worker, recover) | Every job receives an isolated PLOT\_JOB\_STATE directory alongside shared PLOT\_STATE, optional structured step output conduits, and a lock-guarded reachability garbage collector (prune). |

## **2\. Constitutional Laws & Non-Negotiable Invariants**

All swarm agents must obey the ten existing durable laws in docs/MEMORY.md plus two new laws governing v0.7's execution plane:

| Law | Title | Mandatory Enforcement Rule |
| :---- | :---- | :---- |
| **Law 1** | **No Assignment in Somnus** | Plot has zero runtime dependencies on broader Somnus systems and exports no mandatory service to them. |
| **Law 2** | **Core Cannot Grow With Catalog** | All new capabilities (cartographer, wheel/archive assembler, resident environment host, standby pool) live in capabilities/ and are acquired into .grave/objects/. |
| **Law 3** | **9,063-Byte Core Ceiling** | node build.mjs must produce main.js at or under **9,063 bytes** (core\_bytes \<= 9063). Only universal seed laws belong in src/plot.mjs. |
| **Law 4** | **Derivable From Bootstrap** | Every capability Plot exercises must be constructed from local recipes, declared sources, and explicit bootstrap steps—never assumed pre-installed on the host unless explicitly declared as a shallow host dependency. |
| **Law 5** | **Obsidian is Scale Reference Only** | Never import schemas, daemons, or dependencies from external frameworks. Node standard library only (package.json dependencies must remain empty). |
| **Law 6** | **Trusted Execution, Not a Sandbox** | Never claim kernel confinement, untrusted-code isolation, or virtual machine hardware isolation in v0.7. |
| **Law 7** | **Cruel Six-Millisecond Bell** | Measure every boundary separately (view\_lookup, cached\_view\_provision, durable\_submit\_and\_claim, warm\_env\_interact, cold\_worker\_spawn, complete\_isolated\_job). Never merge cold, startup, and execution costs into one composite figure. |
| **Law 8** | **Cross-Device Grammar vs. Proof** | Never claim Windows, macOS, or Android/Termux verification from Linux test runs. Report unrun host lanes as NOT RUN or NOT VERIFIABLE. |
| **Law 9** | **No Fabricated Recovery or PID Signals** | Persisted PIDs are diagnostic only and must **never** be passed to process.kill with a termination signal. Crashed workers or crashed Resident Environments are never automatically replayed or silently restarted as if nothing happened. |
| **Law 10** | **No Content Hash as Resource Identity** | Resource identity remains the canonical serialized array \[recipe, \[platform, arch\], dependency\_paths\]. SHA-256 remains an optional archive download/integrity check only. |
| **Law 11** | **Strict Wall Between Isolated Jobs and Stateful Sessions** *(New in v0.7)* | An isolated job (submit) must **never** execute inside a previously mutated interpreter heap or leak in-memory state to another isolated job. Stateful in-memory reuse is permitted **only** inside an explicitly activated Resident Environment (activate / interact) identified by an explicit incarnation token. Warm tenants must be terminable independently of their Environment Host. |
| **Law 12** | **Synchronous Ownership Handoff Before Submit Return** *(New in v0.7)* | submit must **never** return success to a client while the job is merely written to disk waiting for the supervisor to spawn or assign a worker later. Before submit replies, an independent worker process must have durably written claimed.json, owner.json, and control.json for that job so an immediate SIGKILL of the supervisor cannot orphan the accepted submission. |

## **3\. Target Filesystem Topology & Ownership Contract (.grave/ v0.7 Layout)**

v0.7 extends the .grave/ layout without breaking v0.5/v0.6 public path contracts. Private control metadata uses 0600 files and 0700 directories on POSIX; installed executables retain required executable modes. Durable metadata replacement uses file sync, atomic rename, and supported parent-directory sync; exclusive claims require equivalent durable create semantics. Append-only output follows its explicit flush policy, rather than rename on every byte. Unsupported filesystem durability guarantees must be named and tested, never silently treated as equivalent.

| Path Pattern | Owner | Mutability & Lifecycle | Purpose & Required Contents |
| :---- | :---- | :---- | :---- |
| main.js, src/plot.mjs | Seed Core | Tracked in git; main.js generated deterministically by build.mjs | Foreground acquisition, multi-version object reuse, transactional view activation, literal step runner. |
| data.json | Seed Core | Atomically replaced under .grave/.lock | Ledger recording latest assets map per capability ID and optionally indexed history references. |
| .grave/objects/\<id\>-\<rand\>/ | Seed Core | Immutable after .plot.json commit; deleted only on failed transaction rollback or explicit prune | Acquired capability material and .plot.json completion marker (key, path, runtime identity). |
| .grave/envs/\<name\>.json | Seed Core | Atomically replaced under .grave/.lock | Named executable View (schema: 1, host, assets, python, packages, state). |
| .grave/work/\<name\>/ | View / Tenant | Persistent writable directory (PLOT\_STATE) | Long-lived writable state shared intentionally by operations targeting View \<name\>. Never deleted by prune. |
| .grave/.lock/owner.json | Seed Core | Ephemeral during provision or prune | Exclusive writer guard recording {pid, birth, stages} before each stage allocation. |
| .grave/resident/service.json | Resident Supervisor | Atomically replaced on supervisor start; removed on clean stop | Private supervisor endpoint (pid, birth, port, token, instance). |
| .grave/resident/standby/\<slot\>/ | Standby Worker | Ephemeral pre-booted worker directory prior to job claim | Holds standby.json (pid, birth, port, token, instance) for an idle, independent single-use worker waiting to claim one job. |
| .grave/resident/jobs/\<id\>/submission.json | Resident Supervisor | Write-once (wx, 0600\) | Immutable resolved job specification, frozen view snapshot, absolute executables, request, limits, and timestamp. |
| .grave/resident/jobs/\<id\>/claimed.json | Job Worker | Write-once (wx, 0600\) | Exclusive one-time worker claim (pid, birth, instance, claimedAt). Proves an independent worker accepted the job. |
| .grave/resident/jobs/\<id\>/owner.json | Job Worker | Atomically replaced on worker claim | Diagnostic owner identity (pid, birth) used by inspect and recover when control.json is unreachable. |
| .grave/resident/jobs/\<id\>/control.json | Job Worker | Atomically replaced on worker claim | Private authenticated worker control endpoint (pid, birth, port, token, instance). |
| .grave/resident/jobs/\<id\>/status.json | Job Worker / Reconciler | Atomically replaced on state transitions | Current execution state (queued, running, succeeded, failed, cancelled, timed\_out, interrupted, unreachable), step index, byte counts, and timestamps. |
| .grave/resident/jobs/\<id\>/stdout.log, stderr.log | Job Worker | Append-captured up to limits.outputBytes; fsync on close | Bounded binary/UTF-8 output streams for the job. |
| .grave/resident/jobs/\<id\>/work/ | Job Worker | Created on job start; retained with job record (PLOT\_JOB\_STATE) | Job-private writable scratch directory and inter-step conduit (step.json), preventing concurrent jobs on the same View from colliding in PLOT\_STATE. |
| .grave/resident/envs/\<name\>/instance.json | Environment Host | Atomically replaced on activate | Immutable specification of the active Resident Environment incarnation (name, incarnation, created, frozen view snapshot, limits). |
| .grave/resident/envs/\<name\>/owner.json | Environment Host | Atomically replaced on activate | Diagnostic process identity (pid, birth) of the independent Environment Host process. |
| .grave/resident/envs/\<name\>/control.json | Environment Host | Atomically replaced on activate | Private authenticated endpoint (pid, birth, port, token, incarnation) of the live Environment Host. |
| .grave/resident/envs/\<name\>/status.json | Environment Host / Reconciler | Atomically replaced on state transitions | Lifecycle state (starting, active, draining, stopped, interrupted, unreachable), incarnation, turn counter, warm tenant status, and timestamps. |
| .grave/resident/prune.json | Resident / Reconciler | Atomically replaced on prune | Audit record of the last reachability garbage-collection run (timestamp, removed object paths, removed job IDs, retained counts). |

**Additional durable ownership records:** The frozen schema must include `.grave/pins/` owner/incarnation pins, `.grave/requests/` request-to-job lookup, per-incarnation turn request/outcome records, and crash-recoverable prune tombstones. Exact layouts may consolidate records to reduce durable writes if atomicity and all externally promised paths survive. Environment records must be incarnation-scoped (for example an incarnations directory plus a current pointer): old history cannot be overwritten by activation of the same name. Define request/outcome retention and expired-request errors so retries cannot silently re-execute after history eviction. Control endpoints and tokens are private; the captured output of trusted tenant code is not an authorization channel.

## **4\. Core Seed Evolution Specification (src/plot.mjs & build.mjs)**

The foreground core (src/plot.mjs) must remain small, general, and strictly under **9,063 bytes** after compaction into main.js. The seed must expose the following universal outcomes. Agents may refactor or relocate catalog-specific mechanisms behind acquired capabilities; preserving the present source layout is not a law:

### **4.1 Multi-Version Object Discovery in .grave/objects/**

> 1. **Problem:** In v0.6, provision() checks only whether old.assets?.\[k\] in data.json is valid for the newly computed key. If a user provisions View A with capability pkg@1.0, then provisions View B with pkg@2.0, data.json.assets.pkg is overwritten to point to pkg@2.0. Re-provisioning View A (or any third view needing pkg@1.0) fails the old.assets?.\[k\] check and runs a full cold acquisition, even though .grave/objects/pkg-\<rand\>/ for 1.0 is still intact and valid on disk.  
> 2. **Required Behavior:**  
   * Inside provision(), while holding .grave/.lock, if old.assets?.\[k\] does not match key, the core must scan existing subdirectories of .grave/objects/ whose basename starts with \<k\>-.  
   * For each candidate directory, read its .plot.json metadata and test it with the existing valid(candidate, key) predicate (verifying candidate.key \=== key, realpath confinement inside .grave/objects/, .plot.json self-consistency, and candidate.python existence if present).  
   * If a matching valid object directory is found in .grave/objects/, bind assets\[k\] to that existing record and update data.json.assets\[k\] without allocating a new staging directory or running acquire().  
   * Because .grave/.lock is held during provision() and .plot.json is written atomically only *after* installation and checks succeed, any directory with a valid .plot.json is guaranteed to be a complete historical object.

### **4.2 POSIX Parent-Directory fsync Parity in Core atom()**

> 1. **Problem:** PERSISTENT-NATIVE.md and evidence/RESULTS.md note that capabilities/resident.mjs syncs parent directories on POSIX after renameSync, whereas src/plot.mjs's atom() syncs only the file descriptor before renameSync.  
> 2. **Required Behavior:**  
   * Update atom() in src/plot.mjs so that after renameSync(temp, target) succeeds on non-Windows platforms (process.platform \!== 'win32'), it opens dirname(target) read-only, calls fsyncSync, and closes the directory descriptor in a finally block.

### **4.3 Shallow Python Bootstrap & Diagnostic Hardening**

> 1. **Problem:**  
   * In src/plot.mjs, exec() throws r.error?.message || r.stderr || r.status. When programs like python3 \-m venv fail on Debian/Ubuntu because ensurepip is missing, Python writes the diagnostic explanation to stdout and leaves stderr empty, causing Plot to throw an unhelpful exec python3: 1\.  
   * Furthermore, when tenants.python specifies depth: "shallow" and packages: \[\] (as in the default manifest.json), src/plot.mjs still invokes python3 \-m venv \<stage\> without \--without-pip, failing unnecessarily on any host where ensurepip is omitted from base Python.  
> 2. **Required Behavior:**  
   * Update exec() in src/plot.mjs so failure messages fall back across r.error?.message || r.stderr || r.stdout || r.status.  
   * In acquire(), when creating a shallow Python venv, if the capability graph requires no pip invocation (for example, when packages is empty on the tenant, or if a diagnosed ensurepip absence permits the explicitly selected no-pip acquisition route), fall back to or invoke \-m venv \--without-pip \<stage\> so shallow Python environments provision cleanly on minimal Linux/Debian/Termux hosts.

### **4.4 Compactor Budget Management (build.mjs)**

> 1. Where the current compactor requires registration, any new private identifier introduced in src/plot.mjs must be registered in the names array in build.mjs so frequency-sorted single-character/two-character renaming keeps main.js at or below **9,063 bytes**.  
> 2. node build.mjs must remain 100% deterministic: running it twice on unchanged src/plot.mjs must produce byte-identical main.js.

### **4.5 Seed Responsibility and Budget Proof**

P07-01 first measures actual byte headroom and identifies redundant representations, duplicated paths, and catalog-specific work that can move out of the universal seed. Identifier shortening alone is not a capacity plan. Preserve acquisition from a clean shipped seed: moving code into an undeclared helper that must already be installed fails bootstrap derivability. Report source and generated bytes, acquired capability bytes, bootstrap bytes, and required shipped files separately. No hidden mandatory payload may be excluded to manufacture the 9,063-byte result. Preserve readable source, deterministic generation, and existing public behavior while reclaiming bytes. Historical-object discovery may use a validated index rather than a literal full directory scan if completeness and stale-index recovery are proved.

## **5\. Resident Execution Plane Specification (capabilities/resident.mjs)**

capabilities/resident.mjs remains an optional acquired capability (never bundled into main.js) with zero external npm dependencies. In v0.7, it evolves across five operational dimensions:

### **5.1 O(1) Active Admission Index & Terminal interrupted Classification**

> 1. **In-Memory Active Job Index:**  
   * On supervisor startup (serve()), scan .grave/resident/jobs/ **once** to build an in-memory map of non-terminal jobs (running, queued, unreachable).  
   * During submit, check active admission capacity (activeCount \+ pendingCount \<= 16\) in **O(1) time** against this in-memory table rather than scanning .grave/resident/jobs/ and issuing 500 ms socket inspect calls on the hot submission path.  
> 2. **Persisting Proven interrupted States & Releasing Capacity Slots:**  
   * Whenever inspect() or recover() evaluates a non-terminal job whose worker control socket is unreachable, and identity(owner) proves the worker process is definitely gone (absent) or its PID has been reused by a different process (other via Linux boot ID \+ start ticks), atomically persist state: "interrupted" into jobs/\<id\>/status.json (if not already persisted) and remove id from the supervisor's active admission count.  
   * **Terminal Classification Rule:** The terminal states for admission accounting are now succeeded, failed, cancelled, timed\_out, and interrupted.  
   * **Ambiguity Preservation Rule:** If identity(owner) returns same or unknown (for instance, on non-Linux hosts where a live PID lacks /proc incarnation evidence and its control socket does not respond), the state remains unreachable and **continues to occupy an active admission slot** conservatively, preserving v0.6's safety invariant.  
   * **Evidence Preservation Rule:** Transitioning a job to interrupted never deletes its directory, logs, or metadata, never signals any PID, and never replays the job. It remains permanently inspectable via list, inspect, and output.

### **5.1.1 Execution Authority, Admission Reservations, and Reconciliation**

The independent worker owns execution state. Durable worker records and authenticated live responses are evidence; the supervisor's admission map is a cached projection, never an independent source of execution truth.

- One supervisor incarnation holds admission authority. Reserve capacity synchronously before asynchronous submission work; pending plus active plus uncertain reservations must never exceed the configured limit. Persist enough request/reservation identity to reconcile a supervisor crash between reservation, publication, claim, and reply.
- Worker completion first commits terminal status with owner incarnation and monotonic revision, then sends an authenticated notification. Notification loss must not permanently consume capacity. Background bounded reconciliation polls live/uncertain entries, observes durable terminal records, and repairs the projection. Publish its interval and maximum scheduling budget; historical job count must not enter submit's work budget.
- Rebuild reservations and active entries at supervisor start before accepting writes. Paginate reconciliation of historical records if necessary; report readiness honestly. A full ledger scan at startup is allowed, per-submit historical scans are not.
- Only the worker writes a live job's execution transitions. A reconciler may persist interrupted only with absent/other-incarnation proof and an ownership/version fence preventing a stale observation from overwriting newer terminal evidence. Unreachable is an observation when liveness is uncertain, not proof of death. Never reclaim an uncertain slot solely because a deadline elapsed.
- A claim is exclusive and fenced to the request and worker incarnation. Use a client request ID with durable lookup: a lost reply is indeterminate, and retry must return the existing job rather than execute it twice. On claim-channel timeout, reconcile the existing claim; never assign a second worker merely because an acknowledgement was lost.
- Root publication, admission reservation, claim, terminal completion, and recovery share the P07-00 lifecycle contract. P07-05 extends that contract and reruns P07-04 race tests; it does not invent a second recovery model.

Required adversarial evidence includes missed completion notification, simultaneous last-slot submissions, terminal/inspection races, supervisor replacement during claim, and a lost submit reply followed by a client retry. Claims establish at-most-one worker execution, not general exactly-once external side effects.

### **5.2 Pre-Booted Single-Use Standby Workers (Zero-Spawn submit)**

To bring both **durable submission** (7.861 ms p95 in v0.6) and **worker control readiness** (103.325 ms p95 in v0.6) below the **6 ms p95 bell** without violating Law 11 (no state sharing across isolated jobs) or Law 12 (no returning from submit before an independent worker claims ownership):

> 1. **Standby Pool Lifecycle (.grave/resident/standby/):**  
   * While running, the supervisor maintains a small configurable reservoir (default **2**) of pre-spawned, detached Node worker processes (--standby \<root\>).  
   * Each standby worker boots V8 ahead of time, binds an authenticated loopback TCP server (127.0.0.1, port 0), writes .grave/resident/standby/\<slot\>/standby.json (pid, birth, port, token, instance), and waits for a single {op: "claim"} RPC.  
   * If the supervisor stops (stop) or is killed, idle standby workers that have not claimed a job detect inactivity or receive a shutdown RPC on stop and exit cleanly removing their standby/\<slot\>/standby.json.  
> 2. **Synchronous Ownership Handoff During submit:**  
   * When submit arrives at the supervisor:  
     1. Validate request, authority, and O(1) admission capacity; resolve the View and literal executable paths; create jobs/\<id\>/ and jobs/\<id\>/work/; write jobs/\<id\>/submission.json (wx, 0600, fsync).  
     2. Pop a healthy pre-booted standby worker from the supervisor's ready queue (if the queue is momentarily empty due to burst traffic, fall back to spawning a worker and awaiting its claim handshake).  
     3. Send {op: "claim", id, token: standby.token} over loopback to the standby worker.  
     4. Upon receiving claim, the standby worker **synchronously** removes its standby/\<slot\>/standby.json, writes jobs/\<id\>/claimed.json, jobs/\<id\>/owner.json, jobs/\<id\>/control.json (reusing its already-bound loopback control server with a newly rotated job-specific control token), opens stdout.log and stderr.log, writes initial status.json (state: "running"), and replies {claimed: true, instance, control} to the supervisor before beginning step execution.  
     5. Only after receiving {claimed: true} from the independent worker does the supervisor return {id, state: "submitted", claimed: true, instance} to the client—and immediately trigger an asynchronous background replenish of the standby slot.  
> 3. **Single-Use Isolation Guarantee:**  
   * Once a standby worker claims jobs/\<id\>, it is permanently bound to id. When the job's steps finish (or fail/cancel/time out), the worker flushes stdout.log/stderr.log, writes final status.json, closes its control server, and **exits the OS process**. It never returns to the standby pool.

### **5.2.1 Reservoir Exhaustion and Sustainable Capacity**

Default ready capacity remains two; configuration must bound ready workers, concurrently starting workers, active jobs, and waiting submissions. Pool exhaustion must never trigger an unbounded spawn storm. Each submit reports path (`standby`, `cold`, or `waited`), reservation/claim timestamps, and whether its reply is determinate. An unsuccessful capacity decision returns a structured retryable rejection before acceptance; a durable claim is never disguised as a rejection.

Replenishment is observable work: measure spawn latency, CPU, RSS, readiness rate, misses, and recovery after a burst. Ready workers remain single-use. The architecture must disclose that sustainable isolated-job admission is bounded by replacement-worker readiness and hardware capacity. Warm session turns amortize process birth across many turns; the standby reservoir shifts that cost off individual warm submissions but cannot erase it. A replacement mechanism is permitted only if it preserves fresh isolated-job execution semantics and proves the same ownership boundaries.

### **5.3 Job-Private Working Scratch (PLOT\_JOB\_STATE) & Step Conduits**

> 1. Every job worker creates .grave/resident/jobs/\<id\>/work/ (0700) before launching step 0 and injects PLOT\_JOB\_STATE into every step's environment alongside PLOT\_STATE (.grave/work/\<view\_name\>/).  
> 2. PLOT\_STATE remains the durable shared writable directory for the View; PLOT\_JOB\_STATE provides a collision-free scratch directory for concurrent jobs running against the same View.  
> 3. In addition, the worker sets PLOT\_STEP\_INDEX ("0", "1", ...) and PLOT\_STEP\_OUT (.grave/resident/jobs/\<id\>/work/step.json) in each step's environment so step i can write structured JSON that step i+1 reads without polluting PLOT\_STATE or colliding with sibling jobs.

### **5.4 First-Class Resident Environments (activate, interact, env\_inspect, deactivate)**

To support stateful, sub-6ms execution turns across client connections without conflating stateful sessions with isolated batch jobs, capabilities/resident.mjs adds four environment residency operations:

| Operation (op) | CLI / Request Parameters | Behavior & Ownership Contract |
| :---- | :---- | :---- |
| **activate** | name (View name, default "default"), optional warm (\["node"\], \["python"\]), optional limits | Verifies the named View .grave/envs/\<name\>.json is valid and execution: "trusted", permissions.spawn: true. Spawns an independent detached **Environment Host** process (--env-host \<root\> \<name\>) that claims .grave/resident/envs/\<name\>/, generates a unique incarnation UUID, writes instance.json, owner.json, control.json, and status.json (state: "active"), pre-boots requested warm tenant co-processes (such as a persistent Python \-I \-S turn server with the View's sys.path and package layer already initialized), and returns {name, state: "active", incarnation}. Calling activate on an already active View with an identical frozen View snapshot is idempotent and returns the current {name, state: "active", incarnation}. If the underlying .grave/envs/\<name\>.json has changed since activation, activate rejects unless recreate: true is passed or the prior incarnation is deactivated first. |
| **interact** | name (View name), turn ({runtime: "node" / "python" / "exec", code, args, env, cwd, timeoutMs}), expectIncarnation required for mutating turns | Connects to the live Environment Host for \<name\> (either through the supervisor or directly via envs/\<name\>/control.json). If expectIncarnation is absent or does not match the live Environment Host's incarnation (or if the Environment Host is not active), fails closed immediately with an incarnation/state error. Executes the turn sequentially inside the Environment Host's single-writer turn queue against the warm tenant runtime, captures bounded stdout/stderr and return value (result / exitCode), increments turnCount, and returns {name, incarnation, turnId, state: "succeeded" / "failed" / "interrupted", stdout, stderr, result, exitCode} synchronously when the turn completes. |
| **env\_inspect** | name (View name, optional; if omitted, lists all resident environments) | Inspects .grave/resident/envs/\<name\>/. Queries control.json (500 ms deadline). If unreachable, applies the exact same identity(owner) birth-tick proof as jobs: transitions to interrupted if absent/other, or reports unreachable if ambiguous. Returns {name, state, incarnation, turnCount, warmRuntimes, created, view}. |
| **deactivate** | name (View name), expectIncarnation, optional force | Sends an authenticated deactivate request to envs/\<name\>/control.json. The Environment Host drains any in-flight turn (or aborts it with SIGTERM→SIGKILL if force: true), terminates its owned warm tenant co-processes, records state: "stopped" in status.json, removes control.json, and exits. |

**Warm Tenant Co-Process Architecture inside an Environment Host:**

> * **Warm Python Tenant (runtime: "python"):** When a View includes a Python asset (or when the first Python interact turn arrives), the Environment Host spawns a single persistent child python \-I \-S running an internal turn-loop script over a dedicated framed control channel separate from tenant stdout/stderr (platform-supported extra descriptors or authenticated loopback), with sys.path pre-populated with the View's package layer, PLOT\_STATE set to .grave/work/\<name\>, and os.environ initialized from the View. Each interact turn sends {code, args, cwd, env} as a length-prefixed JSON frame; the persistent Python process executes the turn inside a persistent namespace (\_\_plot\_session\_\_) so imported modules (import plot\_sample, plot\_native), classes, and in-memory variables **persist across turns within that incarnation**, while capturing per-turn sys.stdout/sys.stderr and exceptions cleanly without killing the interpreter\!  
> * **Warm Node Tenant (runtime: "node"):** Executes turns in a separate persistent tenant process, or an independently terminable worker thread with proved cancellation and failure boundaries; a vm context alone in the Environment Host event loop is insufficient. The tenant preserves session state on globalThis.\_\_plot\_session\_\_ across turns within that incarnation while capturing per-turn output.  
> * **Crash Honesty Invariant:** If a warm Python/Node tenant process crashes or exits unexpectedly during a turn (e.g., os.\_exit(1) or SIGKILL), the Environment Host transitions the Resident Environment's state to interrupted and retires its incarnation. It **never** silently respawns a fresh empty interpreter under the same incarnation ID.

### **5.4.1 Stateful Turn Semantics and Failure Boundary**

P07-06 must ship an executable session contract, not merely an exec loop.

| Boundary | Required semantics |
| --- | --- |
| Persistent state | Namespace, imports, heap, and deliberate process-global mutations persist. `sys.path`, module cache, cwd, environment, signal handlers, and stream rebinding are part of session state unless an explicitly documented per-turn overlay restores a particular field. Do not promise to restore arbitrary interpreter state. |
| Turn overrides | Define cwd/env/args overlay precedence, lifetime, and restoration in `finally`. Inspect reports baseline versus mutable session settings. Restoration failure taints and interrupts the incarnation; it is never swallowed. |
| Exception | Return structured error and `stateEffect: partial`; mutations before the exception remain. No transactional heap rollback is implied. A successful turn reports `stateEffect: retained`. |
| Timeout/cancel | The independent Environment Host owns deadlines and can terminate the tenant even during native-extension blocking or an infinite loop. A destructive timeout interrupts the incarnation and explicitly reports memory loss. Optional cooperative interruption may preserve the session only after a verified quiescent protocol acknowledgement. |
| Framing/output | Length-bounded frames, request IDs, and protocol version on a control channel that arbitrary output cannot corrupt. Capture raw fd 1/2 writes as well as ordinary language output; cap retained output and drain/discard excess without deadlocking. Stream rebinding must not destroy control framing. |
| Concurrency | One in-flight turn per environment; bounded queue and explicit backpressure. Caller disconnect does not imply cancellation or replay. Require turn request IDs and retained outcomes for retry lookup. |
| Background activity | Threads, subprocesses, asynchronous tasks, and timers can outlive a turn in trusted code. Late output must be marked asynchronous/unattributed rather than assigned to the next turn. Queue serialization is not heap quiescence while background activity runs. Define tracked-child shutdown and disclose that arbitrary detached descendants are outside guaranteed cleanup. |
| Result values | Only bounded, explicitly serializable results cross the channel. A serialization error does not undo executed code. Never evaluate object representations as control messages. |
| Activation/recreation | Reserve the environment name atomically; concurrent activate calls cannot create two owners. Freeze the view and pin dependencies before publishing active state. Recreate drains/retires the old incarnation before publishing the new one. |
| Host/tenant death | Supervisor death preserves live tenants. Tenant death retires the incarnation; Environment Host death does not authorize reconstruction of the old heap. Record affected turns as interrupted or indeterminate. No automatic turn replay. |

Use separate processes for Python and Node reference tenants unless an alternative proves independent cancellation. Test `os.write(1, ...)`, replaced streams, changed cwd/sys.path, a partial mutation followed by exception, output flooding, background output, duplicate turn requests, a native blocking call, and a busy Node loop. The implementation must return a usable control response or an honest interrupted outcome in each case. Trusted execution is not kernel isolation.

### **5.5 Transactional Reference Ownership and Conservative prune**

`prune` is explicit maintenance, with dry-run by default. Actual deletion requires an explicit apply choice; `includeJobs` and object-cache eviction are separate options. Never erase view writable state or interrupted evidence implicitly.

**Ownership transaction:** P07-00 freezes one global lock order covering recovery, object publication, reference publication, and deletion. All writers participate: foreground provisioning/execution, independent acquisitions, job snapshot creation, environment activation/recreation, and shared Seed Bank assembly. Publication pins the entire transitive dependency closure before releasing the lock and before another process can consume it. A live process keeps a durable owner/incarnation pin until terminal closure or proven-dead reconciliation. Legacy foreground execution must either participate or cause prune to conservatively refuse deletion. A supervisor-local mutex is insufficient.

**Protected roots:** latest ledger assets, every named View, active/uncertain jobs and acquisitions, retained job snapshots, all active/uncertain environment incarnations, explicit pins, interrupted archives, and their transitive dependency paths. Unknown dependency metadata, unresolved owner identity, or an uncoordinated mutation source forces retention/refusal. A valid completion marker alone does not imply reclaimability.

| Classification | Meaning | Default treatment |
| --- | --- | --- |
| Reachable/pinned | Named or owned by any protected root | Never delete |
| Cached | Complete historical object with no current execution/view root | Retain for multi-version reuse; eligible only under explicit cache age/size policy |
| Reclaimable | Unpinned cached object selected by declared eviction policy, or explicitly expired terminal history | Eligible after transactional revalidation |
| Incomplete/uncertain | Unstamped stage, ambiguous owner, malformed or unresolved closure | Preserve for recovery; never infer abandonment from age alone |

Under the publication/deletion lock, recompute or validate roots, select eligible objects, and atomically tombstone/detach them so no new lookup or pin can acquire them. Physical deletion may occur later outside the lock only if the tombstone protocol makes that safe and crash-recoverable. Lock contention is measured. Shared Seed Banks have their own ownership scope and cannot be pruned based on one Plot's roots. Default prune never deletes external bank material.

Expired terminal-job deletion is explicit and audited; its pins are released in the same transaction before object eligibility is recomputed. Audit records include policies, retained reasons, selected paths, completed deletions, failures, and recovery action. Tests race prune with provision, foreground execution, claim, acquisition publication, environment recreation, and supervisor death; prove that historical v1 remains reusable after default maintenance.

## **6\. Compositional Ecosystem Capabilities (capabilities/cartographer.mjs & capabilities/assembler.mjs)**

To fulfill docs/Plot-Fable.md ("The Seventh Flash") without bloating main.js, v0.7 ships two compositional capabilities under capabilities/:

### **6.1 Dependency Cartographer (capabilities/cartographer.mjs)**

> 1. **Purpose:** Ingests a local Node package corpus (directories containing package.json and local .tgz package archives) and computes the **declared dependency closure** required to satisfy a requested capability or package set on the current host.  
> 2. **Required Capabilities:**  
   * Parses name, version, dependencies, optionalDependencies, peerDependencies, bundleDependencies/bundledDependencies, bin, engines, os, cpu, main, and conditional exports / imports.  
   * Evaluates Node conditional exports deterministically for a target condition set (e.g., \["node", "import"\] vs \["node", "require"\], plus "default"), reporting unsupported or unresolvable shapes explicitly rather than guessing.  
   * Prunes branches whose os or cpu constraints exclude the target host, or optionalDependencies that are absent or host-incompatible, recording the exact pruning reason in the output plan.  
   * Collapses shared transitive dependencies (A \-\> B, C and B, C \-\> D yields a single node D in topological order).  
   * Inspects .grave/objects/\*/.plot.json and data.json.assets to mark which closure nodes are **already present in .grave/** using Plot's canonical recipe/host/dependency identity key (never content hashes).  
   * Detects dependency cycles and missing mandatory dependencies, failing closed with a structured diagnostic reason.  
   * Pure planner: never executes package lifecycle scripts, never imports package code, never touches the network, and produces byte-identical JSON output for identical inputs.

**Planner scope:** Resolve declared dependency ranges deterministically from the available corpus; preserve multiple versions where ranges conflict and encode dependency placement. Conditional exports choose entrypoints, not all runtime imports. Do not claim globally minimal program dependencies from package metadata. Preserve manifest key-order semantics where Node resolution depends on order; only canonicalize semantically unordered data. Explicitly handle peer constraints, bundled packages, optional absence, and supported range grammar, rejecting unsupported forms. Versioned closure-plan fields, dependency ordering, target runtime identity, and transaction/pin responsibilities are frozen in P07-00 so P07-02 and P07-03 can implement independently and integrate without schema guessing.

### **6.2 Offline Compositional Layer Assembler & Seed Bank (capabilities/assembler.mjs)**

> 1. **Purpose:** Turns a local Seed Bank (a directory of component tarballs, PEP 427 .whl files, and capability recipes) into composed .grave/objects/ layers without requiring network access, npm, or pip subprocesses.  
> 2. **Required Capabilities:**  
   * **Standards-Compliant PEP 427 Offline Wheel Unpacker:**  
     * Validates wheel filename and WHEEL metadata tags (py3-none-any or matching interpreter ABI/SOABI/platform tags such as cp311-cp311-linux\_x86\_64) against the target Python runtime identity recorded in .plot.json. Rejects incompatible wheels before writing.  
     * Extracts purelib/platlib module files and .dist-info/ into the target layer stage.  
     * Relocates {distribution}-{version}.data/{purelib,platlib,scripts,data,headers}/ entries into their proper target destinations within the package layer (purelib/platlib to layer root, scripts to bin/).  
     * Verifies supplied supported digests and byte lengths in .dist-info/RECORD according to the Wheel boundary contract below, failing closed on mismatches and path traversal.  
     * Preserves POSIX executable permission bits (0755) from ZIP external attributes on extracted scripts and shared objects (.so).  
   * **Seed Bank Multi-Plot Sharing:**  
     * Given a Seed Bank directory and a manifest or Cartographer closure plan, generates or executes Plot capability recipes that materialize only the required component closure into .grave/objects/, allowing multiple distinct Plots or Views to assemble different environments from one offline Seed Bank.

**Wheel boundary:** Follow actual wheel RECORD rules: RECORD's own digest/size may be blank, allowed signature metadata is handled explicitly, and missing optional hashes are not fabricated. Verify each supplied supported digest and size; declared policy may reject unhashed payloads but must state that stricter supported subset. Integrity digests are not resource identity. Validate archive paths, symlink escapes, duplicate destinations, extraction limits, metadata identity, entrypoints, and tag compatibility before atomic publication. Do not claim all PEP 427/platform support from pure-Python plus one Linux C-extension fixture. No implicit source builds: missing compatible wheels produce a structured acquisition requirement. Build fixtures ahead of isolated tests where toolchains are needed and declare that dependency.

### **6.3 Host Acquisition and Bootstrap (capabilities/bootstrap.mjs)**

The Seventh Flash includes establishing prerequisites on an unfamiliar host. This remains an acquired capability plus a distributable launcher/seed bundle; no package catalog enters `main.js`.

**Two explicit entry conditions:** (A) Node is present: the seed runs and acquires its capability closure; (B) Node is absent: a supplied host-native launcher or prepared offline kit obtains a compatible Node runtime and starts the same seed. The launcher declares its irreducible prerequisites (shell/PowerShell, filesystem, transport/extraction tools, or operator-provided runtime archive). There is no claim of installation from literally nothing.

**Inspect → plan → acquire → verify → activate:** detect OS, arch, libc/ABI where relevant, writable roots, installed executables and versions, available transports/extractors, and online/offline mode. Produce a machine-readable plan with prerequisite DAG, provenance/source, compatibility, local destination, disk needs, network needs, and explicit unsupported reasons. Acquire Node, Python, and Git through declared recipes when absent; prefer user-local roots, reuse valid versions, and support shared Seed Bank sources. Git is a required example of acquiring a native tool and its runtime closure, not a fictional universal single-binary assumption. If a supported host requires a system prerequisite or privilege, expose that requirement before mutation; no hidden sudo or global package-manager edits.

**Self-establishment proof:** on each certified host family start from outside the repository, without npm install and without Python/Git on PATH; obtain declared prerequisites through the kit, provision conflicting versions, invoke real Python/native modules and real Git against a local repository, then activate/interact and repeat after supervisor replacement. Also test a Node-absent entry path through the launcher. A PATH-masked test on a provisioned machine must disclose remaining system libraries; it is not automatically a pristine-host proof. Capture a fresh host/container/VM run where the target permits it.

Bootstrap is resumable and transactional: interrupted downloads/extraction/publication cannot become valid completed objects. Concurrent attempts share valid acquisitions without corrupting stages; source unavailability returns actionable diagnostics and preserves prior installations. Lock source selection within an execution attempt; never substitute a materially different artifact silently. Offline and online sources use the same identity/compatibility contract. Report host acquisition cold time, disk footprint, installed closure, and rerun reuse separately from six-millisecond warm gates.

**Certification:** Linux plus at least one genuinely different OS family (Windows, macOS, or Android/Termux) must pass the relevant bootstrap, acquisition, job, session, and recovery boundary tests for cross-host v0.7 certification. A container or alternate Linux distribution alone is not that second family. Use host-native tests where shell gates are unavailable. NOT RUN remains an honest status but leaves portability acceptance open. Agents finish available lanes and supply a runnable outstanding host kit; they must not relabel Linux-only evidence as full completion.

## **7. Swarm Packet Board and Execution Topology**

P07-00 is the coordinator's opening contract slice. P07-01/02/03/09 are independent implementation lanes after that freeze. The resident lane can advance as soon as P07-01 lands; it need not wait for all acquisition work. Integration depends on all producers. Existing packet IDs remain stable; P07-09 adds bootstrap without renumbering consumers.

| Wave | Packet | Primary owned surfaces | Dependency / parallelism |
| --- | --- | --- | --- |
| Opening | P07-00: Contract freeze and baseline | PLAN.md, docs/V07-CONTRACTS.md, TASK.md | Start now; release settled interfaces immediately |
| Parallel | P07-01: Universal seed and budget | src/plot.mjs, build.mjs, main.js, tests/integration.mjs | P07-00; parallel with 02/03/09 |
| Parallel | P07-02: Dependency Cartographer | capabilities/cartographer.mjs, tests/cartographer.mjs | P07-00 closure schema; parallel with 01/03/09 |
| Parallel | P07-03: Offline assembler and Seed Bank | capabilities/assembler.mjs, tests/assembler.mjs | P07-00 schema; standalone engine parallel with 02; real producer integration follows 02 |
| Parallel | P07-09: Host bootstrap and acquisition | capabilities/bootstrap.mjs, bootstrap/, tests/bootstrap.mjs | P07-00; parallel implementation, composition follows 01/03 |
| Resident | P07-04: Admission, pins, recovery, maintenance | capabilities/resident.mjs, tests/resident.mjs | P07-01; resident file owner before 05 |
| Resident | P07-05: Standby handoff and bounded capacity | capabilities/resident.mjs, tests/resident.mjs | P07-04; same file owner before 06 |
| Resident | P07-06: Resident environments and session contract | capabilities/resident.mjs, tests/resident-env.mjs | P07-05; integrates pins/recovery |
| Integration | P07-07: Adversarial and cross-host proof | scripts/gate.sh, tests/package-smoke.mjs, integration tests, host runners | P07-01/02/03/06/09 |
| Closure | P07-08: Measurements, whitepaper, release | benchmark/report tests, metadata, docs, evidence | P07-07; measurements before final claims |

**Coordination:** One owner per shared source file. Parallel agents may develop independent helpers/tests behind frozen interfaces, but the resident owner integrates shared-file changes in order. Coordinator owns shared manifests, task routing, and continuity merges; lane agents provide explicit edits/handoffs instead of racing on them. Do not add wrappers or modules merely to occupy agents. Choose module boundaries when they improve implementation, cancellation, or ownership clarity.

**Every packet:** Read actual root AGENTS.md, active TASK.md, newest NOTEPAD entry, and the packet's coupled implementation before editing. Treat absent historical source paths or counts as a reconciliation item, not a reason to invent files. Preserve baseline/ and all valid v0.5/v0.6 public regressions. Test counts below are coverage floors, never acceptance substitutes. Run the existing integrated gate at each landing plus new lane tests directly; P07-07 makes all new suites mandatory in the final gate. An intermediate gate pass is a packet checkpoint, not v0.7 release acceptance.

### **Packet P07-00: Opening Contract Freeze**

- **Mission:** Verify branch/base and supplied baseline claims; settle only blocking shared interfaces and start implementation. Record lifecycle transitions, lock order, pin schema, request IDs, closure-plan schema, supported hosts, bootstrap entry assumptions, and benchmark workload definitions in docs/V07-CONTRACTS.md. Derive definitions from real source. Begin cross-host runners early.
- **Required Reads:** Root router and continuity, this plan, src/plot.mjs, capabilities/resident.mjs, manifests, existing tests and evidence, relevant Accelerate packet contract.
- **Invariant:** No new architecture review bureaucracy. Freeze fields needed by current producers/consumers; unresolved local choices remain with their implementer. Freeze a nominal sustained workload before tuning, with declared rationale and hardware; acceptance must not be silently reduced after seeing results.
- **Surfaces:** PLAN.md (this supplied plan's repository destination), docs/V07-CONTRACTS.md, TASK.md, coordinator continuity records.
- **Hard Bans:** No invented baseline PASS; no weakening laws; no whole-program rewrite as a prerequisite.
- **Validation:** Existing baseline gate, read-through of producer/consumer contracts, acyclic packet graph, declared host test routes. Existing failures are recorded and assigned rather than hidden.
- **Exit:** Exact base identity, measured bytes, baseline status, interface versions, nominal workload, host matrix, next dispatched lanes.
- **Handoff:** Dispatch P07-01/02/03/09 immediately against frozen contracts. Bounded discoveries may amend contracts with affected consumers updated together.

### **Packet P07-01: Universal Seed Evolution**

- **Mission:** Implement §§4.1–4.5: historical exact-key reuse, durable metadata replacement, stdout diagnostics, and deliberate no-pip shallow acquisition. Reclaim byte budget through sound responsibility changes rather than minification alone. Integrate universal publication/pinning participation required by §5.5.
- **Required Reads:** Seed/build in full; STAGE-1.md; integration tests; frozen ownership contract; actual source and generated byte measurements.
- **Invariant:** Generated seed ≤9,063 bytes; stable canonical recipe/host/dependency-path identity; completed historical objects reusable without child spawns; incomplete stages never reused. Standalone foreground execution remains safe during maintenance.
- **Surfaces:** src/plot.mjs, build.mjs, generated main.js, tests/integration.mjs; declared universal contract helpers only if derivable from shipped seed.
- **Hard Bans:** No ceiling increase, handwritten generated seed, hidden mandatory payload, catalog-dependent seed expansion, or content-hash identity.
- **Validation:** Deterministic rebuild; existing integration regressions plus v1→v2→v1 for capabilities and packages, stdout-only diagnostic, no-ensurepip acquisition, interrupted publication, and pin/deletion race. Run current integrated gate and lane tests; final new-suite gate wiring belongs to P07-07.
- **Exit:** Generated/source bytes, reclaimed mechanisms, shipped closure, exact checks and remaining headroom.
- **Handoff:** Release P07-04; give 02/03/09 actual object and publication interfaces.

### **Packet P07-02: Dependency Cartographer**

- **Mission:** Implement §6.1 with version-aware local closure planning and named unsupported forms. Export planClosure and inspectCorpus plus CLI. Emit the P07-00 schema consumed by assembler and bootstrap.
- **Required Reads:** §6.1, STAGE-1.md, seed identity/validation, real package/archive fixtures, shared closure schema.
- **Invariant:** Node standard library only; pure offline planning; deterministic semantics; no lifecycle scripts or imported package execution. Compatible versions may deduplicate; incompatible ranges retain distinct nodes/placements.
- **Surfaces:** capabilities/cartographer.mjs, tests/cartographer.mjs, versioned closure fixtures owned by this lane.
- **Hard Bans:** No npm/npx/pnpm/yarn, seed edits, source execution, or claim of dynamic-import completeness.
- **Validation:** At least 10 substantive cases including diamond, conflicting versions/ranges, peer/bundled packages, conditional key order, os/cpu/engine constraints, optional pruning, historical-object presence, cycle and missing-required diagnostics, deterministic repeated output.
- **Exit:** Capability bytes, supported grammar, complete check results, producer fixture for 03/09.
- **Handoff:** Supply actual plans to P07-03/09; integrate producer/consumer test before P07-07.

### **Packet P07-03: Offline Layer Assembler and Seed Bank**

- **Mission:** Implement §6.2 real wheel/component assembly and shared-bank reuse. Export installWheels, assembleFromBank, verifyWheel plus CLI. Develop against frozen schema; integrate live Cartographer output once P07-02 lands.
- **Required Reads:** §6.2 including wheel boundary; STAGE-1.md; real pure/C-extension fixture builders; archive confinement and publication/pin contract.
- **Invariant:** No pip/ensurepip at runtime; Node standard library and explicitly acquired target Python standard library only. All materialization is staged and atomically published; external shared-bank data remains immutable unless its own owner authorizes change.
- **Surfaces:** capabilities/assembler.mjs, tests/assembler.mjs, real offline bank fixtures.
- **Hard Bans:** No weakened supplied digest verification, incompatible tag acceptance, traversal/duplicate overwrite, implicit source builds, or seed edits.
- **Validation:** At least 8 substantive cases plus real producer integration: pure wheel, compatible C extension, .data relocation, console entrypoint, malformed RECORD, incompatible ABI, traversal/duplicate paths, bounded extraction, conflicting package subsets in independent Plots, interrupted assembly and retry. Declare fixture compiler prerequisites separately from no-pip deployment.
- **Exit:** Bytes, supported wheel subset, offline timings, fixture provenance, check results. A pip timing comparison is optional and isolated from no-pip proof.
- **Handoff:** Release bank/materialization interface to 09 and integrated layers to 06/07.

### **Packet P07-04: Admission, Recovery, Pins, and Conservative Maintenance**

- **Mission:** Implement §§5.1, 5.1.1, 5.3, 5.5. Replace historical hot-path scans with reserved O(1) admission; reconcile lost transitions; persist proven interrupted state; isolate PLOT_JOB_STATE and step conduits; implement pin-safe dry-run/apply maintenance with explicit cache eviction.
- **Required Reads:** PERSISTENT-NATIVE.md ownership/recovery; full resident source; existing resident tests; seed publication contract; frozen lifecycle and lock order.
- **Invariant:** Worker owns live execution state; uncertainty retains capacity/resources. Terminal records remain inspectable. Historical cache survives default maintenance. All reference producers coordinate with deletion.
- **Surfaces:** capabilities/resident.mjs, tests/resident.mjs and justified ownership helpers; coordinator merges affected contract documentation.
- **Hard Bans:** No signals from persisted PID authority; no automatic replay; no default history/cache erasure; no stale reconciler overwrite of worker terminal status.
- **Validation:** Existing 19 baseline checks if confirmed, plus 20 killed-worker recoveries followed by successful job 21, missed notification repair, last-slot reservation race, unreachable-job hot-path independence, scratch/step separation, transitive roots, concurrent acquisition/provision/prune, legacy foreground execution, retained historical version reuse, and interrupted tombstone recovery.
- **Exit:** Check results, resident bytes, reconciliation interval/budget, lock order, pin lifecycle, remaining failure boundaries.
- **Handoff:** Give P07-05 one authoritative lifecycle model; require its handoff tests to revalidate this packet.

### **Packet P07-05: Standby Claim and Sustainable Capacity**

- **Mission:** Implement §§5.2–5.2.1: configurable bounded single-use reservoir, exclusive durable claim, idempotent submit lookup, visible exhaustion policy, and observable replenishment. Prove supervisor-independent execution immediately after acceptance.
- **Required Reads:** Full post-04 resident source, existing benchmarks, shared lifecycle/request-ID contract, workload definitions in §8.
- **Invariant:** Before success, one independent worker durably owns the submission and its authenticated control endpoint is ready. A worker serves one isolated job only. Completion before reply is allowed and reported truthfully. Lost claim replies never create a second executing worker.
- **Surfaces:** capabilities/resident.mjs, tests/resident.mjs; benchmark hooks only through coordinator-owned schema.
- **Hard Bans:** No early success, unbounded spawning/queueing, worker reuse across jobs, hidden cold fallbacks, or stale standby endpoint adoption without authentication/incarnation proof.
- **Validation:** Existing resident regressions plus immediate supervisor SIGKILL after reply, claim-stage crash injection, lost-ACK retry, simultaneous duplicate requests, burst sizes 2/8/16/32 with explicit capacity outcomes, idle standby expiry/clean stop, bounded replenishment, restart reconciliation, and P07-04 pin/admission races. Preliminary warm-reservoir p95 <6 ms; sustained behavior measured now and gated finally in P07-08.
- **Exit:** Warm and unconditioned timings, fallback fraction, capacity/rejection/throughput, replenishment costs, exact claim state transitions.
- **Handoff:** Hand resident owner to P07-06 with recovery contract already revalidated.

### **Packet P07-06: Resident Execution Environments**

- **Mission:** Implement §5.4 and §5.4.1 across CLI/RPC: activate, interact, env_inspect, deactivate, dedicated tenant control channels, independently enforceable deadlines, request lookup, and durable dependency pins. Warm Node/Python reference tenants are real runtime sessions.
- **Required Reads:** Python runner contract; post-05 resident implementation; session semantics table; acquired runtime/layer identities; lifecycle and pin contract.
- **Invariant:** Supervisor replacement preserves exact live incarnation and heap; tenant loss is explicit interruption. Mutating turns require expectIncarnation. Submit never shares tenant heap. Tenant timeout cannot freeze the Environment Host's control plane.
- **Surfaces:** capabilities/resident.mjs, tests/resident-env.mjs; acquired tenant helpers if needed and included in shipped/acquired closure.
- **Hard Bans:** No silent empty-heap restart, vm-context-only cancellation claim, stdout control framing, automatic replay, or fabricated rollback after exception.
- **Validation:** At least 10 substantive checks and all prior resident regressions; cover Python/Node memory across separate clients, imported real native modules, conflicting package sessions, supervisor kill/restart, tenant/host death, destructive timeout, blocked native call and Node loop, stream replacement/raw bytes, overflow/late output, cwd/sys.path mutation, partial exception, duplicate turn lookup, concurrent activation, bounded queues, isolation from submit, and owned-child cleanup.
- **Exit:** Session/failure semantics, bytes, warm turn distributions, timeout outcomes, inherited pin/recovery tests.
- **Handoff:** Release complete session implementation to P07-07 without claiming crash-recoverable heaps.

### **Packet P07-09: Host Bootstrap and Acquisition**

- **Mission:** Implement §6.3 inspect/plan/acquire/verify/activate and Node-absent launchers. Acquire real Node, Python, and Git closures on declared hosts through online sources and offline bank material. Include interrupted/resumed and repeated reuse paths.
- **Required Reads:** §6.3; seed/acquisition source; closure schema; assembler/bank contract; target host ABI and executable conventions verified against actual artifacts.
- **Invariant:** Host prerequisites are explicit; user-local transactional installation; no mandatory npm dependency; no hidden reliance on developer host Python/Git/Node. Bootstrap remains optional to a host where the seed already runs.
- **Surfaces:** capabilities/bootstrap.mjs, bootstrap/ host launchers and recipes, tests/bootstrap.mjs, runnable native host test kits. Shared manifest/package changes are coordinated rather than concurrent.
- **Hard Bans:** No assumed universal native binary, silent privilege escalation, remote-script execution without declared source, fake PATH-only pristine-host claim, or system-install mutation disguised as user-local acquisition.
- **Validation:** Real Git invocation/repository operation, acquired Python/native module, acquired Node seed entry; absence/mismatch detection, offline-only install, interruption/resume, competing acquisitions, source failure, stable reuse, and Node-absent launcher proof. Run Linux plus second OS-family tests through P07-07.
- **Exit:** Host/prerequisite matrix, source provenance, acquisition closure and sizes, cold/reuse timings, successful and unsupported routes.
- **Handoff:** Integrate with 01/02/03; supply clean-host runner and evidence to P07-07.

### **Packet P07-07: Adversarial Integration and Cross-Host Proof**

- **Mission:** Wire every new suite into scripts/gate.sh and equivalent native host runners; compose real Cartographer→Assembler→seed→bootstrap→resident paths. Deliver certified-host boundary tests and crash injection across publication, claim, activation, turn completion, and prune.
- **Required Reads:** All producer tests/contracts, package smoke test, gate implementation, host kits, session and ownership tables, §8.
- **Invariant:** Default gate runs in disposable state and does not dirty tracked files. Clean-package test ships only declared runtime/launcher/capability files and declared artifact inputs, runs from a foreign cwd, and requires no npm install. Host Python/Git absence must be met through actual acquisition. Node-present and Node-absent entry tests are separate.
- **Surfaces:** scripts/gate.sh, tests/package-smoke.mjs, integration tests, native host runners; coordinator resolves shared manifest closure.
- **Hard Bans:** No skipped regressions or synthetic PASS; no substituting Linux emulation for second-family proof; no assumed Python/compiler hidden in no-prerequisite smoke tests.
- **Validation:** Default gate PASS plus all new suite coverage; Linux and second-family bootstrap/acquisition/job/session/recovery checks. Missing host access records NOT RUN and leaves cross-host acceptance incomplete while local work proceeds.
- **Exit:** Coverage map by contract and host, actual checks/counts, crash outcomes, outstanding unverified boundaries, package contents and prerequisites.
- **Handoff:** Deliver integrated candidate and reproducible host evidence to P07-08. Freeze implementation for measurement, subject to fixes and affected reruns.

### **Packet P07-08: Performance Evidence, Whitepaper, and Release Closure**

- **Mission:** Extend benchmarks/reporting for §8, produce official measurements, then finalize contracts/docs and the completed-system whitepaper. Synchronize version 0.7.0, STAGE-1.md, PERSISTENT-NATIVE.md, README.md, root router, TASK.md, CONTEXT/MEMORY/NOTEPAD, and filetree. The whitepaper is terminal engineering acceptance: actual implemented system, research formulation, validation, and comprehensive exposition, not a plan renamed as a paper.
- **Required Reads:** Final code/contracts, all host evidence, tests/benchmark.mjs, tests/resident-benchmark.mjs, tests/report.mjs, evidence/RESULTS.md, §8 and existing project whitepaper conventions.
- **Invariant:** Sequence is implementation freeze → correctness/host proof → measurements → claim reconciliation → whitepaper/docs → final gate. Documentation may draft earlier; final claims follow evidence. Any source/harness change invalidates affected measurements. All raw samples retained.
- **Surfaces:** Benchmark/report tests, package.json, manifest.json, named docs/continuity, WHITEPAPER.md or existing canonical whitepaper path, generated evidence/ only through the gate.
- **Hard Bans:** No handwritten evidence, outlier removal, warm/cold merging, baseline/ changes, post-hoc workload reduction, or full-completion claim with missing portability proof.
- **Validation:** scripts/gate.sh --bench and --evidence PASS on declared reference host; native host acceptance records; whitepaper claims trace to final source and measurements. Sentinel verifies evidence; a Fletcher review challenges benchmark gaming, hidden prerequisite assumptions, arbitrary architectural limits, and whether the actual generational advance was achieved. Review findings need concrete fixes/evidence; neither persona substitutes for gates.
- **Exit:** Source/base identity, full bytes/closure, check/host matrix, p50/p95/p99/max, saturation throughput and resource envelope, whitepaper, explicit limits, reproducible commands.
- **Handoff:** Mark fully complete only when §8 is satisfied. Otherwise deliver the implemented candidate, exact unmet gate, and imperative next action; never conceal an incomplete gate behind an overall PASS.

## **8. Verification, Performance, and Terminal Acceptance**

### **8.1 Measurement Contract**

The six-millisecond bell remains a hard reference-host objective. It applies to bounded named operations, not arbitrary Python/Node programs or every storage device. Freeze reference workloads, selected host, and measurement boundaries in P07-00; publish every environmental constraint. Do not weaken file/parent-directory syncing or change durable semantics to improve timing.

Record CPU/model/core count, RAM, OS/kernel, Node/Python versions, filesystem/mount options, physical storage class/device where observable, virtualization/container layer, power mode, timer, concurrency, pool/queue limits, source identity, and durability policy. Report missing hardware visibility explicitly. A tmpfs run may be diagnostic but cannot stand in for durable-storage certification. Process-crash testing proves process-crash behavior, not physical power-loss guarantees.

Use monotonic timing from client request initiation. Record request arrival, reservation, durable submission publication, worker claim commitment, control readiness, reply receipt, execution completion, and replenishment readiness. Preserve all samples, failures, rejections, and path labels. Percentiles specify calculation method and denominator. Client timeouts are censored observations with lower bounds/failure counts, never deleted samples. Report successful latency and availability together; rejected/failed requests cannot manufacture a fast successful subset. Warmup count, tracing overhead, interarrival schedule, random seed if used, and output size are declared. Fresh CLI startup is measured separately from persistent-client RPC.

**Required workload families:**

1. **Warm reservoir:** At least 300 eligible submissions, each ready-state assumption recorded. Report deliberate spacing/replenishment waits outside request latency and total wall time. This proves warm handoff only.
2. **Burst and sustained admission:** Bursts of 2/8/16/32 and an open-loop sustained run of at least 60 seconds and 1,000 offered submissions at the frozen nominal rate. Use reproducible short jobs and bounded runtime/output; schedule arrivals independently of completions to avoid coordinated omission. Count queue delay, cold fallback, capacity rejection, missed deadlines, and all latency strata. Include empty-pool start. Publish both default pool and any tuned configuration with RSS/CPU costs. The nominal rate must exercise multiple complete pool turnovers, not merely preserve a prefilled reservoir. At nominal sustainable load, the unconditioned successful submit p95 must remain <6 ms with ≥99% successful acceptance and no correctness failure. If unmet, optimize the system; report the cliff and keep the performance gate open.
3. **Saturation:** Increase offered rate until misses/rejections or latency rise, then measure drain/recovery. Report max stable throughput, queue/memory bounds and replenishment rate. No universal <6 ms demand beyond declared capacity, and no pretending saturation is an exceptional unmeasured path.
4. **Warm sessions:** At least 300 sequential turns per runtime executing frozen small real-package work (Python includes a supported native extension) with bounded outputs. Report control/dispatch and useful execution time, result validation, plus mixed-runtime/background-contention and queued-client measurements. Heavy user work is separately timed without a <6 ms promise.
5. **Cold/full boundaries:** Cold acquisition, bootstrap, worker/tenant start, full isolated completion, and replenishment costs remain separate. Supervisor restart/reconciliation and prune contention are measured under long histories. No freshly emptied history-only benchmark may substitute for steady-state operation.

The warm durable claim row includes parent-directory sync and independent control readiness. `accepted_to_worker_control_ready` is only an invariant check once readiness precedes success; a zero value is not a latency improvement by itself. Gate request-start→control-ready and request-start→reply, and verify claim ordering independently.

### **8.2 Acceptance Matrix**

| Category | Required proof / threshold | Boundary |
| --- | --- | --- |
| Seed | Deterministic main.js ≤9,063 bytes; byte-identical repeated build | Universal seed plus honest separately reported shipped/acquired closure |
| Compatibility | All valid v0.5/v0.6 regressions retained | Any assertion correction requires concrete defect evidence, not convenience |
| Core | Historical version reuse, safe pins/publication, fsync and diagnostics, no-ensurepip path | Zero child spawn on valid cached reuse; no incomplete-stage adoption |
| Cartographer | ≥10 substantive cases and actual assembler consumption | Version/range/peer/condition semantics and explicit unsupported forms |
| Assembler | ≥8 substantive cases, real pure/native modules and console entry | Actual compatible runtime; digest/path/metadata/transaction failures |
| Resident jobs | All confirmed 19 baseline tests plus every 04/05 adversarial contract | No fixed final count substitutes for race/ownership coverage |
| Resident environments | ≥10 substantive cases plus every §5.4.1 boundary | Real warm state, independent deadlines, honest partial mutation and interruption |
| Admission | O(1) capacity decision independent of history size; lost-notification repair bounded by declared reconciliation budget | Work may reconcile in background; uncertainty remains protected |
| Maintenance | Concurrent-root publication safety, transitive pins, explicit cache eviction, recovery after tombstone | Historical cached objects survive default prune |
| Bootstrap/package | Real Node/Python/Git acquisition, no npm install, foreign cwd, offline and Node-absent routes | Declare irreducible host inputs; no hidden development tools |
| Portability | Linux plus ≥1 other OS family passing relevant host boundaries | NOT RUN leaves acceptance open; no cross-host heap migration claim |
| View lookup | 1,000 samples, p95 <6 ms; <1 ms stretch objective | Cached validated view lookup |
| Cached provision | Each persisted cached-view series 1,000 samples, p95 <6 ms | Includes locking, validation and durable publication |
| Multi-version switch | 300 samples, p95 <6 ms, zero child spawn | v1↔v2 with both versions already acquired |
| Resident cached-view RPC | 300 samples, p95 <6 ms | Authenticated transport through authoritative provisioning and reply |
| Warm durable submit | ≥300 samples, request→reply and request→control-ready p95 <6 ms | Complete durable submission and independent claim, ready reservoir condition reported |
| Sustained nominal submit | ≥60 seconds and ≥1,000 offered requests; successful p95 <6 ms, acceptance ≥99%, zero correctness failures | Unconditioned on standby/cold path; bounded fixed nominal workload |
| Burst/saturation | All requests accounted; bounded queues/processes/RSS; stable capacity and recovery published | Default and tuned pool; fallback cannot be averaged away |
| Warm Node/Python turns | ≥300 each, p95 <6 ms for frozen bounded reference work | Dedicated control channel, real package invocation, all output/result overhead |
| Separate cold/full metrics | Raw distributions and acquisition/replenishment resource costs published | No six-millisecond cold/full-runtime claim |
| Evidence | Generated gate evidence, all samples/counts, claim-to-source mapping, actual host results | No hand-edited evidence or missing-failure denominator |
| Whitepaper | Completed-system formulation, mechanisms, evaluation, failure boundaries, lineage and reproducibility | Final paper agrees with final implementation and measured evidence |

### **8.3 Completion Status**

Use distinct statuses: packet checkpoint, integrated candidate, reference-host performance verified, cross-host verified, and v0.7 complete. Full completion requires all applicable rows, reproducible evidence and the completed-system whitepaper. If hardware/storage prevents the bell or a second host is unavailable, preserve the engineering result and report the exact open gate. Do not reduce ambition, fake a pass, or stop available implementation merely because one external proof lane is pending.

The intended result is a small seed that establishes declared prerequisites on diverse hosts, composes previously acquired material, supports honest sustained isolated execution, and maintains named live runtime sessions across supervisor replacement. The swarm may discover a better mechanism than this plan proposes; the mechanism earns adoption through stronger capability and evidence under the same laws.
