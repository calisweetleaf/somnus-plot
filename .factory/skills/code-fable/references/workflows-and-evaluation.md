# Workflows & Evaluation Architecture

The Somnus Code Fable system separates its operations into four distinct authoring workflows (**Research**, **Create**, **Continue**, **Revise**) and a dual-layer evaluation architecture (**Objective Verification** vs. **Qualitative Literary Assessment**).

---

## 1. The Four Authoring Operations

### I. Researching (`research`)
```bash
python3 scripts/fable_harness.py research \
  --project "ProjectName" \
  --sources path/to/doc1.md path/to/code.py \
  --output path/to/FABLE_CANON.md
```
- **Purpose:** Inspect primary artifacts, extract dated events, metrics, quotations, component names, and architectural boundaries, and organize them into a source-linked research ledger (`FABLE_CANON.md` or JSON ledger) without prematurely generating Fable prose.
- **Epistemic Discipline:** Every entry carries an explicit status (`implemented`, `observed`, `stated_intent`, `proposed`, `inferred`, `unknown`, `conflicting`) and source locator. Claims lacking direct source verification are marked accordingly rather than certified as fact.

### II. Creating (`create`)
```bash
python3 scripts/fable_harness.py create \
  --project "ProjectName" \
  --canon path/to/FABLE_CANON.md \
  --output path/to/authoring-brief.md
```
- **Purpose:** Prepare a research-grounded authoring brief and coverage map following the eight-stage `write-code-fables` methodology so a new Fable can be written as a book for readers.
- **Literary Freedom:** Does not impose the narrative structure, pronoun choice, paragraph length, or word count of another Fable. Derives the governing question and symbolic mapping from the project's own record.

### III. Continuing (`continue`)
```bash
python3 scripts/fable_harness.py continue \
  --manuscript path/to/existing-fable.md \
  --new-sources path/to/new-epoch.md \
  --output path/to/continuation-plan.md
```
- **Purpose:** Extend an existing Fable or canon with later historical developments while locking the prior manuscript's historical claims and epoch boundaries.
- **Anti-Retroactivity:** Preserves what was true and what was known in earlier epochs so later architectures or renames are never projected backward as if they existed from day one.

### IV. Revising (`revise`)
```bash
python3 scripts/fable_harness.py revise \
  --original path/to/original-fable.md \
  --candidate path/to/revised-fable.md
```
- **Purpose:** Audit a candidate revision against its original manuscript to ensure historical events, chronology, empirical figures, quotations, named components, and causal turns were preserved rather than silently eliminated through summary compression.

---

## 2. Dual-Layer Evaluation (`evaluate` / `lint`)

```bash
python3 scripts/fable_harness.py evaluate --all
python3 scripts/fable_harness.py evaluate path/to/fable.md \
  [--baseline path/to/original.md] \
  [--canon path/to/canon.json] \
  [--project muadib|continuum|plot] \
  [--json]
```

To prevent evaluation from reducing literature to simplistic formatting heuristics, evaluation is strictly divided into two independent layers:

### Layer A: Objective Verification (`objective_verification`)
Machine-checkable, deterministic verification of factual, structural, and archival requirements:
1. **Protected Manuscript Integrity:** Confirms that the three authoritative reference manuscripts in [`../fables/`](../fables/) match their canonical SHA-256 hashes and have not been mutated.
2. **Structural Validity:** Confirms valid Markdown structure (title, coherent section hierarchy, balanced code fences if present, non-empty sections) without penalizing short paragraphs, standalone lines, repetition, diagrams, or narrative voice.
3. **Historical Distinction & Coverage Verification:** When a project coverage specification or canon is supplied (including the built-in regression specifications for `Muad’Dib`, `Continuum`, and `Plot`), verifies that required architectural distinctions, chronological turns, and epistemic boundaries (`implemented` vs. `proposed`, `unknown` acknowledgments) are substantively present.
4. **Source & Epistemic Discipline:** When evaluated against a source ledger/canon:
   - Flags **Status Violations** (e.g., presenting a `proposed` capability as an `implemented` or accomplished fact, or projecting a later rename/architecture backward into an earlier date).
   - Flags **Unverified Claims** (dates, empirical numbers, or direct quotations introduced in prose without backing in the source record), exposing the need for source verification rather than certifying persuasive prose as fact.
5. **Revision Retention Verification:** When a `--baseline` manuscript is supplied, compares the baseline's extracted historical claim inventory (dates, empirical metrics, named mechanisms, quotations, citations, and narrative movements) against the candidate revision and fails if substantive historical or narrative material was dropped.

### Layer B: Qualitative Literary Assessment (`literary_assessment`)
Structured literary analysis grounded in the manuscript itself—never collapsed into a deterministic 0–100 formatting score:
1. **Narrative Development & Causal Arc:** Evaluates whether the work moves through dramatic pressure, causal transitions, discovery, and transformation rather than reading like a static inventory, bulleted changelog, or bare outline.
2. **Symbolic Coherence:** Traces recurring motifs across movements to assess whether symbols connect technical mechanisms to deeper meaning throughout the piece.
3. **Stylistic Individuality & Cadence Profile:** Describes the work's distinctive voice and structural choices (such as third-person literary chronicle, direct chronicler address, rhythmic standalone lines, expansive meditative prose, or conceptual diagrams) as legitimate artistic instruments.
4. **Distinguishing Literature from Mechanically Valid Reports:** Explicitly identifies when a manuscript is **mechanically valid yet artistically weak** (e.g., a dry chronological report or outline that includes every required date and keyword from the canon—passing `objective_verification`—while lacking narrative development, symbolic coherence, or literary life).
