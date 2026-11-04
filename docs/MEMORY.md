# Somnus Plot — Durable Memory

Stable law and vocabulary. Add only what is likely to stay true across versions.
Source for each law is cited; `docs/Plot-Fable.md` is operator canon.

## Laws

1. **No assignment.** Plot has no role in broader Somnus. It is a laboratory lightning rod, not a pillar. Somnus may learn from Plot (downstream transfer); it must not depend on Plot (core adoption). — Fable, "Before the First Furrow", "What Plot Gives Back"
2. **The core cannot grow with the catalog.** Capability arrives by acquisition into `.grave/`, not by enlarging the seed. — `STAGE-1.md` constraint 1
3. **Byte ceiling pressure.** 9,063 bytes, from the original v0.4 bundle. The number may someday move; the pressure may not. Any increase must answer: did the seed learn a more general law, or was an organ stuffed in? — Fable, "The Seventh Flash"
4. **Derivable from bootstrap.** What Plot can do must be derivable from what Plot can bootstrap. No borrowing capability from a larger Somnus system or a pre-provisioned host. — Fable, "The First Flash"
5. **Obsidian is the mountain, not the father.** Scale reference only, never implementation lineage. — Fable
6. **Not a sandbox.** Execution is trusted; permission fields are declarations, not confinement. — `baseline/REPORT.md`, `STAGE-1.md`, `PERSISTENT-NATIVE.md`
7. **Six-millisecond bell is cruel by design.** Objective is p95 < 6 ms per measured boundary. Never merge cold acquisition, process birth, execution and completion into one flattering number. — `STAGE-1.md` constraint 4, Fable
8. **Cross-device in grammar before proof.** Linux is the only demonstrated execution lane until a device run says otherwise. — `STAGE-1.md`, `evidence/RESULTS.md`
9. **No fabricated recovery.** PIDs are never signal targets; uncertain jobs are reported, never replayed or marked successful. — `PERSISTENT-NATIVE.md`
10. **No content hash as identity.** Resource identity = canonical recipe + host + dependency locations. — `STAGE-1.md`
11. **Acceptance with named exceptions is not a pass.** A version may close by operator acceptance; each unmet gate stays named, measured and open in the paper, and is never reworded as satisfied. — Operator, 2026-10-22 (v0.7 closeout)

## Vocabulary

| Term | Meaning |
| --- | --- |
| Plot | The seed environment: `main.js` + `manifest.json` + its root |
| `.grave/` | Where acquired things persist after the process that summoned them dies: objects, envs, work, resident |
| View | Named environment `.grave/envs/NAME.json` over shared acquired resources plus own writable state |
| Tenant | A runtime living in `.grave/` (Python today) |
| Shallow / deep Python | Shallow: venv from real host Python. Deep: owned runtime extracted from an explicit TAR source |
| Resident | Optional acquired supervisor capability (v0.6) |
| Flash / Flash Pack | A tiny ignition that makes a much larger capable world constructible without carrying it. Plot is the first. "Flashback Stage 1" = `STAGE-1.md` |
| Minimum sufficient ignition | The engineering target for portability; not magical universality |

## Version lineage

| Version | Date | Turn |
| --- | --- | --- |
| v0.4 | ≤ 2026-10-12 | Tiny runner; webview + Node hosts; audited in `baseline/REPORT.md` |
| v0.5 | 2026-10-14 | Acquisition separated from view; DAG; 9,036 bytes; 18/18 |
| v0.6 | 2026-10-17 | Persistent native execution; optional resident; 9,061 bytes; 37/37 |
| v0.7 | 2026-10-22 | "Seventh Flash": composition from small pieces (cartographer, assembler, bootstrap, resident jobs/environments, pins/prune); 9,061 bytes; 146/146. Closed by operator acceptance with named exceptions (`WHITEPAPER.md` App C) |
| v10 | operator prediction | Total completion: persistent VM deployable on any device. Numbering after v0.7 (v0.8–v1.0 vs v8–v10) deliberately deferred by the operator, 2026-10-22: the next stage takes a new form with more code and reuses v0.7 as canon |
