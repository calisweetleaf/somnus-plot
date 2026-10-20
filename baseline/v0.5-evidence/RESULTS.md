# Flashback Stage 1 — measured results

Date: 2026-10-14. **18/18 integration checks pass**.
Complete shipped core: **9,036 bytes**, within
the original 9,063-byte bundle ceiling. No mandatory external adapter or npm dependency.

This stage delivers dependency/host-aware acquisition, reuse of owned resources,
atomic environment-view activation, version-specific package layers and separate
writable state. It establishes a tested alternative to creating one Python venv
per environment for the covered execution modes.

## Timing

Host: linux/x64, v24.19.0,
Python 3.12.14, AMD EPYC 9V74 80-Core Processor. Container scratch filesystem;
warm local assets and filesystem cache. The result is host-specific.

| Operation | Samples | p50 ms | p95 ms | p99 ms | Maximum ms |
|---|---:|---:|---:|---:|---:|
| New persisted view, acquired assets | 1000 | 0.490 | 1.080 | 1.675 | 2.773 |
| Reprovision an existing view | 300 | 0.463 | 1.136 | 1.785 | 2.642 |
| Load and check an existing view | 1000 | 0.021 | 0.120 | 0.305 | 1.813 |
| Fresh Node CLI + cached-assets provisioning | 60 | 95.630 | 121.837 | 170.779 | 170.779 |
| Fresh CLI + Python/package execution | 60 | 110.992 | 160.683 | 180.053 | 180.053 |
| Raw Python startup, no view/package imports | 60 | 12.964 | 18.209 | 23.328 | 23.328 |
| Empty venv creation, no pip or package set | 20 | 53.481 | 64.691 | 65.700 | 65.700 |

Cold first acquisition of the runtime, two real wheels, dependency data and
analysis capability took **4162.648 ms** in one run.
This is one observation, not a percentile. No download was involved.

The new-view series creates **1,000 distinct persisted views**, each with its own
writable directory, referencing the same four acquired assets. Descriptors were
1956–1961 bytes.
The measured API operation includes manifest read, selected DAG/host planning,
resource availability checks, exclusive writer lock, state-directory creation,
descriptor serialization, **file fsync and atomic rename**. It excludes acquisition,
resolver work and child-process launch. Seed and measured views 0/499/999 then
execute Python imports, an actual compiled extension, package metadata and the
dependency dataset, writing their own verified output.

**The persisted cached-view p95 gate is below 6 ms. The full fresh-process
provisioning/execution target remains open.** The difference is recorded rather
than relabeled as a completed installation. Fresh Node startup, interpreter startup,
cold resolution and disk acquisition need their own subsequent work.

The empty-venv measurement is a runtime-only reference with no pip and none of the
view workload's packages or other capabilities. It is not an equivalent end-to-end
environment comparison. No speedup claim against uv or another installer is made.

Parent-directory fsync/power-loss durability is not implemented. Artifact integrity
is not rescanned during warm provisioning. Windows, macOS, Termux and browser
execution are not validated by these Linux results.

## Executed integration checks

- shipped core stays at or below original 9063 bytes: PASS
- real mixed Node/Python demo and module import parity: PASS
- default CLI is plot-relative when launched elsewhere: PASS
- literal arguments, step cwd/env, and stop on child exit: PASS
- spawn:false and missing trusted declaration fail before acquisition: PASS
- host mismatch, invalid IDs, missing dependencies, cycles fail closed: PASS
- host recipe precedence, wildcard fallback and optional unsupported DLC: PASS
- DAG order, reuse, dependency invalidation and frozen older views: PASS
- failed installer/check preserve active view, ledger, writable data: PASS
- cross-process acquisition lock rejects racing writer: PASS
- missing asset and cross-device view require reprovision: PASS
- real pip target acquisition, shared interpreter and version conflicts: PASS
- Python module, script, argv, metadata resources and console entrypoint: PASS
- subprocess package inheritance, host PYTHONPATH exclusion and writable isolation: PASS
- package installation failure and requested depth/version drift fail without stale reuse: PASS
- archive traversal, symlink pivots, hardlinks, PAX, duplicate paths, truncation rejected: PASS
- bounded decompression aborts oversized archive without activation: PASS
- real locally reconstructed CPython archive and legacy integrity check: PASS

Archive testing includes real local CPython extraction and adversarial fixtures.
The CPython archive was reconstructed from the host's actual interpreter and
standard library; dynamic OS libraries remain host dependencies. This does not
establish compatibility with a downloaded standalone distribution.

## Included evidence

- integration.json, integration.log: actual checks and output.
- benchmark.json: environment, sample counts, percentiles, every raw timing,
  workload and explicitly scoped performance gates.
- benchmark.log: concise output from the same run.
- package-smoke.json: runnable clean-package smoke check, added when packaging.

Reproduce with node build.mjs, node tests/integration.mjs,
node tests/benchmark.mjs, and node tests/report.mjs.
The source, contract and supplied audit baseline accompany this evidence.
