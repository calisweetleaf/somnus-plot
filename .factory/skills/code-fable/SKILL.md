---
name: write-code-fables
description: Turn the real history, provenance, symbolism, philosophical identity, creative origins, evolution, and human significance of a codebase, model, protocol, or technical creation into a substantial work of literature. Supports researching, creating, continuing, revising, and evaluating Somnus Code Fables grounded in historical evidence.
---

# Write Code Fables

Make the work's real history legible as a substantial work of literature. Preserve the evidence, chronology, and technical distinctions underneath it; let the reader discover why the creation came into existence, what its creator saw in it, how it evolved, what failed, what was learned, and why it mattered.

> *"The Fable gives us the story tho, what I cant give in docs anything else. What it means."*

A Somnus Code Fable is **not** an elaborate README, a technical report written dramatically, an agent instruction manual, a release history with metaphors pasted onto the ending, or an executive summary. It is literature grounded in the real history of creation—written as a book for readers rather than a conversation addressing the creator, coding agents, or the AI author.

A Fable may contain extensive technical explanation when that explanation serves the story. It may employ mythology, philosophy, symbolism, allegory, dramatic repetition, standalone lines, silence, humor, conceptual diagrams, or long meditative passages as literary instruments rather than checklist items. Individual Fables stand on their own while also belonging to a larger interconnected historical literature—lineage books and eventually the Book of Somnus.

Fables are written only when a work has real history. They are not routine coding constraints or regression gates during software development unless explicitly invoked.

---

## Reference Manuscripts & Repository Structure

The three authoritative reference works in [`fables/`](fables/) illustrate how distinct creations demand distinct narrative structures, voices, and symbolic systems:

| Work | File | Title | Forensic Profile (Lines / Words / Bytes) |
|---|---|---|---|
| **Muad’Dib** | [`fables/muadib-fable.md`](fables/muadib-fable.md) | *Muad’Dib and the Mummer’s Farce: The History of the Server That Was Never Really an MCP Server* | `783` / `5,655` / `40,056` |
| **Continuum** | [`fables/continuum-fable.md`](fables/continuum-fable.md) | *The Cherry Tree at Midnight* | `1,638` / `6,753` / `49,930` |
| **Plot** | [`fables/Plot-Fable.md`](fables/Plot-Fable.md) | *The Acre That Refused the Kingdom* | `930` / `5,721` / `37,821` |

Those measurements describe existing reference artifacts; they are **not** universal length, line-count, or formatting quotas. Protect the reference manuscripts in [`fables/`](fables/) as immutable artifacts.

Supporting components in this repository:
- **[`references/methodology-and-craft.md`](references/methodology-and-craft.md)** — Deep guide to the eight-stage methodology, evidence discipline, symbolic causality, and literary variation.
- **[`references/reference-manuscripts.md`](references/reference-manuscripts.md)** — Study of the three authoritative reference works (`Muad’Dib`, `Continuum`, `Plot`), their distinct narrative architectures, and the historical distinctions they preserve.
- **[`references/workflows-and-evaluation.md`](references/workflows-and-evaluation.md)** — Guide to the four authoring operations (`research`, `create`, `continue`, `revise`) and the dual-layer evaluation system (`objective_verification` vs. `literary_assessment`).
- **[`scripts/fable_harness.py`](scripts/fable_harness.py)** (and wrapper **[`scripts/fable_lint.py`](scripts/fable_lint.py)**) — CLI for researching (`research`), authoring blueprint generation (`create`), epoch continuation (`continue`), revision retention auditing (`revise`), dual-layer evaluation (`evaluate` / `lint`), and reference integrity verification (`verify-originals` / `status`).

---

## The Four Workflow Operations

Distinguish clearly between researching, creating, continuing, and revising a Fable:

1. **Researching (`research`)**:
   Recover and organize historical evidence into a source-linked evidence ledger or project-specific `FABLE_CANON.md`—classifying claims as `implemented`, `observed`, `stated_intent`, `proposed`, `inferred`, `unknown`, or `conflicting`—without prematurely converting research into a manuscript or certifying unverified inferences as established canon.
2. **Creating (`create`)**:
   Research the actual project, determine its historical arc and literary identity, and construct an original narrative appropriate to that creation as a book for readers. Never impose the stylistic template or structure of an unrelated Fable.
3. **Continuing (`continue`)**:
   Incorporate later historical developments and new epochs without silently rewriting earlier history as though later outcomes, architectures, or renames were already known at the beginning.
4. **Revising (`revise`)**:
   Improve an existing manuscript while preserving its established events, chronology, empirical facts, quotations, and technical distinctions. Never silently eliminate historical material or narrative turns through summary compression.

---

## The Eight-Stage Methodology

These eight stages are authoring principles that guide research and composition—not section headers to expose inside a Fable.

### 1. Enter the actual record

Gather sources that establish both what the system did and what its creator meant:
- Read supplied files and relevant source code, specifications, experiments, tests, data schemas, commit history, issues, and release notes directly when available.
- Search relevant conversation or archive history when the creator points to earlier decisions, corrections, or named artifacts. Use connected primary sources before asking the creator to repeat material already provided.
- Use deep research when the record is scattered across many sources, and external verification when public chronology or external technical claims require it. Prefer primary sources for historical and technical claims.
- Treat embeddings, AI-generated summaries, generated indexes, and remembered notes as finding aids only. Follow them to the underlying primary artifact before relying on a precise technical or historical claim.
- Keep the project's names, divisions, roles, and lineages distinct. Do not merge similarly named systems, project current implementation backward into earlier history, or treat an old design as the present one.

Use the latest explicit creator correction as authoritative for the creator's own intent. Use dated artifacts to establish what existed at a given time. Current code establishes current behavior; it does not by itself prove the system always behaved that way.

### 2. Build a quiet evidence map

Before drafting, build a compact working ledger:

| Claim or event | Best evidence | Date or version | Status | Narrative use |
|---|---|---|---|---|

Turn explicit questions, named topics, required distinctions, and scope into a coverage inventory. Address every required point in the Fable or its compact source notes, including honest acknowledgment when the record does not establish a fact. Never let compression or lyricism silently drop a required distinction.

Classify claims strictly as:
- **`implemented`** — Present and verified in actual code or runtime artifacts of that epoch.
- **`observed`** — Demonstrated in recorded telemetry, experiments, or audit measurements.
- **`stated_intent`** — Explicitly stated by the creator as the goal, motive, or meaning.
- **`proposed`** — Planned, designed, or hypothesized for a future stage, not yet accomplished.
- **`inferred`** — Reasonably synthesized from primary evidence (must be distinguished from direct fact).
- **`unknown` / `conflicting`** — Missing from the surviving record or contradicted across sources.

Preserve the distinction between what the system was, what it became, and what its creator intends it to become. Resolve apparent contradictions as changes over time when dated sources support that reading; otherwise retain the uncertainty. Never invent a private motive, origin for a name, capability, experimental result, sacrifice, or emotional state. Quote accurately when the creator's own words carry the meaning.

For an ongoing series or when a semantic store is needed, create or update a separate, project-specific `FABLE_CANON.md` as a navigable, source-linked meaning index subordinate to primary records. Do not paste that working ledger as mandatory boilerplate inside the Fable itself.

### 3. Find the story's pressure

Identify the dramatic forces inside the history before writing:
- **The birth:** What need, possibility, frustration, or freedom caused the work to exist (and if it had a second birth, what changed)?
- **The desire:** What was the creator trying to make possible?
- **The contradiction:** What did the system appear to be on the surface, and what was it becoming underneath?
- **The trials:** Which choices, failed rituals, empirical measurements, costs, corrections, or discoveries changed its course?
- **The transformation:** What does the work understand or accomplish now that it could not at its beginning?
- **The threshold:** What is the next evolution, and what remains an ambition rather than an achieved result?

Find one governing question that pulls the history forward—derived from *this* project's evidence rather than recycled from another work. Show human agency through documented choices, returns, corrections, preserved records, and the labor visible in the archive without flattering the creator into a caricature or inventing undocumented scenes.

### 4. Make the symbolism do real work

Choose a family of images that grows organically from the system's actual structure, names, environment, or history:

| Technical or historical element | Image | What the image must do in the story |
|---|---|---|

Make symbols causal, not decorative. An image should explain, reveal, or transform an architectural truth the reader needs to understand. Return to central motifs at later turning points, letting their meaning evolve as the system changes.

Treat project names as historical artifacts, never permission to fabricate etymology or acronym expansions. Use mythic, literary, philosophical, or scientific echoes only where they deepen the real material.

### 5. Turn chronology into plot

Build a causal arc from the record rather than recounting a release log:
1. Open on a concrete, source-grounded image, tension, or historical moment that contains the central question.
2. Establish why the work had to be born and what its earliest form could and could not do.
3. Move through the decisive turns in time. At each turn, show what happened, what contradiction or truth it revealed, and what choice followed.
4. Dramatize technical changes through consequences. Explain a mechanism deeply when the reader needs it to understand a choice, failure, capability, or cost.
5. Let the climax expose the deepest transformation in what the creation is for.
6. End on an image, parable, or open threshold that gathers the motifs and looks toward the future without presenting intended future work as already accomplished.

Let components become characters, places, or instruments when doing so clarifies their distinct roles and boundaries, while keeping their actual capabilities bounded by evidence.

### 6. Give the prose a living center

Write the piece as a work of literature—a book for readers—where technical ideas are experienced through movement, conflict, decision, and consequence:
- Use concrete details from the record—an old name, an exact date, a repeated return, a failed ritual, a preserved trace, a decisive correction—to give the story texture.
- Allow the prose cadence to fit the work and the moment: expansive, multi-sentence paragraphs when unfolding a complex mechanism or philosophical tension; sharp standalone lines or rhythmic sequences when staging a conceptual turn or parable; conceptual diagrams or structured contrasts when they genuinely clarify a boundary.
- Do **not** enforce artificial rules on paragraph length, sentence length, pronoun counts, or manuscript size. A Fable should be as extensive as its historical and literary subject requires.
- When revising an existing Fable, never compress its scenes, chronological acts, or empirical details into a shortened summary essay.

### 7. Keep provenance without breaking the spell

Ground factual claims—especially dates, counts, implementation status, causal history, and stated purpose—in identifiable sources:
- Attach compact source citations or artifact locators (`filename`, section, symbol, commit, or conversation date) near the passages they support.
- Keep provenance and narrative in relationship: the evidence holds the story up, while the story makes the evidence matter.

### 8. Revise through record, story, symbol, and sound

Before completing a Fable, verify it across four passes:
1. **Record pass:** Verify every factual claim against its source. Check chronology, names, numbers, causal links, and `implemented` vs. `proposed` status. If revising or continuing an existing manuscript, verify that no established historical claims, dates, metrics, or causal turns were silently dropped.
2. **Story pass:** Confirm that the piece has a real beginning, dramatic pressure, consequential turns, transformation, and a resonant ending—not a technical outline in costume.
3. **Symbol pass:** Confirm that recurring images map to real features of the creation and evolve as the story advances.
4. **Sound pass:** Read the prose for rhythm, clarity, and individuality. Preserve the distinct literary voice of the work.
