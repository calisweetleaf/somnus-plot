# Somnus Code Fable Methodology & Literary Craft

## 1. Purpose of a Somnus Code Fable

A Somnus Code Fable is a substantial work of literature that reveals the history, meaning, symbolism, philosophical identity, creative origins, evolution, and human significance of a real technical creation.

> *"The Fable gives us the story tho, what I cant give in docs anything else. What it means."*

Code, specifications, file trees, and test suites record *what exists on disk at a moment in time*. They do not preserve why a creation had to be born, what false assumptions surrounded its birth, what contradictions its evolution exposed, which experiments failed and taught a deeper law, or how its creator's understanding transformed over time.

A Fable is written as **a book for readers**—never as a conversational chat message to the user, an instruction prompt for coding agents, an elaborate README, a release log with decorative metaphors, or an executive summary. Individual Fables also participate in a larger interconnected historical literature—lineage books and the eventual Book of Somnus—which demands rigorous historical fidelity and respect for each creation's distinct identity.

---

## 2. Historical & Evidentiary Discipline

Literature grounded in real creation draws its authority from the historical record.

### Primary vs. Secondary Evidence
- **Primary Evidence:** Source files, specifications, commits, dated architecture audits, experimental results (`RESULTS.md`), telemetry logs, issue trackers, and explicit dated statements or corrections by the creator.
- **Finding Aids (Subordinate):** Embeddings, AI-generated summaries, generated indexes, and retrospective paraphrases. Always trace a finding aid back to the underlying artifact before asserting a technical or historical claim.

### The Six Evidence Statuses
Every historical or technical claim in a research ledger (`FABLE_CANON.md` or JSON canon) and in the authoring workflow belongs to one of six epistemic categories:

| Status | Definition | How It Must Be Represented in Prose |
|---|---|---|
| **`implemented`** | Verified in actual code or runtime artifacts of the relevant epoch. | May be narrated as established historical or present capability of that epoch. |
| **`observed`** | Demonstrated in recorded experiments, telemetry, or forensic audits. | Narrated as empirical findings, bounded to the conditions and epoch measured. |
| **`stated_intent`** | Explicitly declared by the creator as the motive, design law, or goal. | Attributed accurately to the creator's vision, doctrine, or correction. |
| **`proposed`** | Designed or planned for a future version or threshold, not yet achieved. | Framed clearly as an approaching horizon, design direction, or unfulfilled ambition—**never** as an accomplished experiment. |
| **`inferred`** | Reasonably synthesized across primary sources where no single document states it verbatim. | Presented transparently as synthesis or architectural interpretation rather than direct quotation. |
| **`unknown` / `conflicting`** | Absent from surviving records or contradicted across dated artifacts. | Acknowledged honestly as an evidentiary boundary or unresolved tension—**never** papered over with fabricated dates, motives, or acronym expansions. |

### Four Temporal & Provenance Laws
1. **Never Project Present Code Backward:** Current implementation proves what the system does today; it does not prove the system behaved that way at its birth.
2. **Never Present Proposals as Accomplished Results:** Future designs, unverified cross-platform targets, or next-stage architectures must remain clearly distinguished from demonstrated behavior.
3. **Keep Evolving Names & Boundaries Distinct:** When a name moves across components or epochs (such as `cherry_ttt` and `Continuum`, or `Somnus-MCP`, `BB7`, and `Muad’Dib`), trace the historical reason for the shift rather than collapsing the names into synonyms.
4. **Preserve `FABLE_CANON.md` as a Subordinate Research Index:** When maintaining a project-specific `FABLE_CANON.md`, keep it source-linked and separate from other projects' canons. Never force the working ledger table itself into the prose of the Fable.

---

## 3. Literary Instruments & Narrative Freedom

A Fable succeeds when historical accuracy and literary art reinforce one another:
- **Causal Plot Over Chronological List:** Do not merely list events in order (`v0.4`, `v0.5`, `v0.6` or `Jan`, `Feb`, `Mar`). Show what expectation existed, what pressure or failure broke that expectation, what choice followed, and how that choice transformed the nature of the work.
- **Load-Bearing Symbolism:** Symbols must grow from the creation's actual names, mechanisms, constraints, and history (such as a protocol acting as a mummer's mask, `.grave/` acting as soil where summoned capabilities outlive a dying CLI process, or a resident Fabric acting as a loom beneath a branching explorer). A symbol must clarify a real architectural relationship and evolve as the system matures.
- **Technical Depth When It Serves the Story:** A Fable may include deep technical explanations, empirical measurements, architectural contrasts, or conceptual flow illustrations whenever they illuminate the stakes of a decision or transformation.
- **Stylistic Individuality:** Different creations call for different literary forms, rhythms, and voices. A Fable may use expansive meditative paragraphs, sharp standalone sentences, rhythmic repetition, rhetorical reversals, dramatic irony, quiet restraint, or structural diagrams when appropriate to its subject.
- **No Arbitrary Formatting Quotas:** Never judge or constrain a Fable by universal word counts, line counts, byte sizes, paragraph sentence-count rules, pronoun quotas, or punctuation heuristics. A Fable should be as extensive as its historical and literary subject requires—and during revision, substantive historical content, scenes, and causal links must never be eliminated through summary compression.
