# Authoritative Reference Manuscripts

The three existing works in [`../fables/`](../fables/) are the authoritative literary reference manuscripts of the Somnus Code Fable system. They are protected reference artifacts and must never be overwritten, compressed, or mutated by authoring or evaluation tools.

---

## 1. Forensic Reference Table

| Work | Path | Title | Lines (`wc -l`) | Words (`wc -w`) | Bytes (`wc -c`) | SHA-256 |
|---|---|---|---|---|---|---|
| **Muad’Dib** | [`fables/muadib-fable.md`](../fables/muadib-fable.md) | *Muad’Dib and the Mummer’s Farce: The History of the Server That Was Never Really an MCP Server* | `783` | `5,655` | `40,056` | `a209e466cb097f40ba8e1bbf58b6803bd717edcdce8a903dbac78c7c0b03c580` |
| **Continuum** | [`fables/continuum-fable.md`](../fables/continuum-fable.md) | *The Cherry Tree at Midnight* | `1,638` | `6,753` | `49,930` | `63e5386e5c7dd98864e55daea1cb47be6a04c148663b9ca98ac6fa726a877682` |
| **Plot** | [`fables/Plot-Fable.md`](../fables/Plot-Fable.md) | *The Acre That Refused the Kingdom* | `930` | `5,721` | `37,821` | `48740ef5a3ef582417b90835d0c747f254eb87a997f62b8df2598b1382a41628` |

> [!IMPORTANT]
> The line, word, and byte figures above document these three specific manuscripts for forensic integrity checking. They are **not** universal output quotas for new Fables.

---

## 2. Distinct Literary Structures & Historical Distinctions

Each of the three reference works demonstrates a distinct narrative architecture suited to its creation, while preserving strict historical and architectural distinctions:

### I. Muad’Dib: *Muad’Dib and the Mummer’s Farce*
- **Narrative Architecture:** Moves from the paradox of two births, through the central metaphor of the protocol mask, across an eight-month chronological metamorphosis (`January` through `August`), into the river of `data/`, the school of Codex trajectories, the emergence of the neural animal, and a closing parable (*The gate, the ledger, and the sand*).
- **Essential Historical & Architectural Distinctions:**
  1. **The Two Births:** First built starting **November 25, 2024** (the day Anthropic released MCP, completing `tools/` and `mcp_server.py` by **March 2025**) as a universal tool plane; resurrected on **January 1, 2026** specifically for the **data flywheel** (`intent → state → choice → tool → arguments → observation → failure → recovery → consequence → next choice → eventual outcome`).
  2. **MCP Transport vs. Underlying Organism:** MCP (`tools/list`, `tools/call`, JSON-RPC) is the outer mask/transport; underneath lives a continuously training neural-symbolic system (`Lisan`/exoskeleton control reasoning, `Muad’Dib` 512-dimensional neural manifold and scoring substrate, effectors, and `data/`).
  3. **`BB7` Provenance & Semantics:** No surviving source expands `BB7` as an English acronym; it sits in the `aa6_` / `bb7_` / `cc8_` hierarchy as a compiled callable surface rather than a thin 1-to-1 execution wrapper (`bb7_exo_execute_step` records a step rather than mutating state). Tool counts (`115`, `110`, `120`, `119`, `147`, `265`) are historical snapshots, not fixed definitions.
  4. **Data & Learning Lineage:** `data/` (`SOVEREIGN_DATA_DIR`) is a durable cognition data-plane capturing raw substrate evidence before display projection; May telemetry (`3,421` plans, `28%` ceremony vs. `0.04%` reflection) killed the rigid Turbo Loop in favor of Golden Path; Codex sessions are distilled for operational/tool reasoning (with `bb7_` as an initial seed to be outgrown), while synthetic **self-play** and real-world **RFT/distillation** remain separate streams inhabiting the same learning world; and the surrounding harness (`ASPS`, `Omnibus`, `Golden Path`, `Cherry`) frees Muad’Dib's successor to become a specialized neural execution "sniper."

### II. Continuum: *The Cherry Tree at Midnight*
- **Narrative Architecture:** Opens in a late-night study examining the lineage of `Cherry`, traces the July 5 generalization from token strings to world states (`cherry_ttt`), follows the discovery and subsequent surrender of the name `Continuum` once the resident `Fabric` and `Symbolic Fault Equalizer` arrived, illustrates the compiler-like lowering of tools and the runtime-to-training loop, and closes as dawn breaks over the unified regime.
- **Essential Historical & Architectural Distinctions:**
  1. **Cherry vs. `cherry_ttt`:** `Cherry` is the older, broader training-and-inference methodology (joining MCTS, A*, Best-of-N, verifiers, PRMs, `TreeRolloutCollector`, and `GRPOTrainer`); `cherry_ttt` (*Cherry Test-Time Tooling*, integrated **July 5, 2026**) generalized `LexicalMDP` from token strings to typed environment actions and observations across **speculative**, **transactional** (reversible), and **real** substrates.
  2. **The `Fabric` and the `Equalizer`:** The resident reactive attention `Fabric` (`observe(stream_event)`, eight attention kernels) and the GPT-4o-descended `Symbolic Fault Equalizer` (*Dyson sphere around the sun*) translate heterogeneous subsystem events through domain intakes (`FabricCommitSink` -> `EqualizedTransition` -> `StreamEvent`) into resident, witnessed state. Meanwhile, the empirical `0.19` recall failure proved that Fabric routing must not replace Cherry search as a candidate generator.
  3. **Evolution of the Name `Continuum`:** In September, `cherry_ttt` was conceptually called `Continuum` because it preserved counterfactual branch continuity across tool boundaries; in October (*"NOW cherry_ttt, BOOOM we now have Continuum"*), `cherry_ttt` reclaimed its package name because true **Continuum** is the composite regime of **`Fabric` (substrate continuity) + `cherry_ttt` (counterfactual continuity)**.
  4. **Model-Agnostic Runtime & Breathing Internalization:** Core `cherry_ttt` is model-independent (`use_value_model=False`, optional PyTorch, zero-parameter drafter); models can be trained separately or natively on full branch trees, and as Cherry internalizes search discoveries into policy weights, external search shrinks on familiar tasks and expands when reality becomes novel or uncertain (avoiding the `1.5s` search vs. `1ms` write trap).

### III. Plot: *The Acre That Refused the Kingdom*
- **Narrative Architecture:** Written as a third-person architectural chronicle and laboratory parable—moving from the unassigned acre outside Somnus and the distant mountain of Obsidian, through the distinction between the webview window and the house, into `.grave/` learning to grow persistent roots across `v0.4`, `v0.5`, and `v0.6`, the emergence of the **Flash Program**, the explicit source notes (`The Stones Beneath the Fable`), and the forward horizon (`The Seventh Flash`).
- **Essential Historical & Architectural Distinctions:**
  1. **Independent Experimental Identity:** Plot has **no assignment** inside broader Somnus (not built for Companion, ARCS, or Forseti); it is a laboratory lightning rod that teaches Somnus by **downstream transfer** without ever becoming a load-bearing core pillar, and **Obsidian** is a scale reference (*the mountain in the distance*), never an implementation parent from which Plot may borrow organs.
  2. **Not a Webview Wrapper and Not a Sandbox:** Neither the v0.4 webview nor Node defines Plot's identity; and Plot is explicitly **trusted execution**, not an isolation sandbox (*studying genesis rather than confinement*).
  3. **The Seed, the Byte Ceiling, and `.grave/`:** Across **v0.4** (Oct 12, 2026; `9,063`-byte ceiling), **v0.5 / Flashback Stage 1** (Oct 14, 2026; *"The core cannot grow with the catalog"*; `9,036` bytes; `18 of 18` checks; separating capability acquisition from environment views), and **v0.6 / Persistent Native Execution** (Oct 17–19, 2026; `9,061` bytes; zero npm install), acquired runtimes, views, state, and even the optional resident supervisor live in `.grave/` so execution outlives the initiating CLI client and supervisor restarts.
  4. **Demonstrated Capability vs. Future Ambition:** Distinguishes verified Linux gates—cached native view creation (`p95 ~4.066ms`) and resident cached-view requests (`p95 ~3.614ms`) already inside the **six-millisecond bell**, versus durable resident submission (`p95 ~7.861ms`) and worker startup still outside it—from future **Flash Program** ambitions (dependency cartography over package graphs, offline seed banks, disposable ignition rungs, full compositional Python beyond shallow host Python, unverified Windows/macOS/Android targets, and the long-term horizon of a persistent virtual machine).
