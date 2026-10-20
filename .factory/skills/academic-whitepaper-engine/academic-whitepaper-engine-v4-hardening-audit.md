# Academic Whitepaper Engine v4 Hardening Audit

**Target:** `academic-whitepaper-engine (3).zip`  
**Audit date:** 2026-08-03  
**Purpose:** Convert the current publication skill from a broad academic-content prompt into a deterministic Somnus whitepaper workflow engine with explicit authorship, evidence, visual, conversion, and validation contracts.

---

## 1. Executive Diagnosis

The current engine is materially stronger than an ordinary “write me a whitepaper” prompt. It already understands that Markdown is the composition substrate, LaTeX is the authoritative publication source, PDF is a compiled artifact, visuals must be generated rather than described, code must be executable, and the final document has a restrained Somnus visual identity.

Its primary weakness is that it specifies outputs far more precisely than it specifies authorship.

The engine tells an agent what files to produce, how many citations and figures to include, which tools may be used, and which directory names to create. It does not yet define how a Somnus paper develops an argument, distinguishes evidence from architectural interpretation, moves between prose and mathematics, controls rhetorical temperature, or preserves Daeron’s cadence without imitating conversational speech.

The result is predictable: an agent can satisfy the visible checklist while producing prose that is technically polished, rhythmically generic, structurally over-segmented, citation-heavy without being evidence-led, and recognizably machine-composed.

A second problem is more concrete. The repository presently encodes multiple contradictory TeX toolchains and several scripts do not honor the contracts described in `SKILL.md` or `AGENTS.md`. The workflow therefore needs both an authorial constitution and an executable state machine.

The recommended v4 direction is:

> Treat the whitepaper engine as a compiler pipeline with a style constitution, claim ledger, visual ledger, source ledger, and gated publication states.

The agent should not simply “write a paper.” It should transform a project’s authority surfaces into a formal manuscript, then compile and validate that manuscript under a single deterministic TeX regime.

---

## 2. What the Current Engine Gets Right

The following ideas should remain canonical:

1. **Markdown is the manuscript workspace, not the publication artifact.** The Markdown source is where architecture, prose, equations, citations, and visual placements are developed. The final PDF must be produced from the authoritative `.tex` source.

2. **LaTeX is a creative and semantic transformation, not a file-format conversion.** The `.tex` stage must refine typography, page logic, theorem environments, captions, references, code boxes, visual placement, and publication metadata.

3. **Body typography is predominantly monochrome.** Color belongs to code syntax and information-bearing visuals. It should not leak into headings, links, decorative callouts, or ordinary prose.

4. **Visuals are first-class technical objects.** Diagrams, plots, tables, and architecture maps should be planned during manuscript composition and stored with editable sources.

5. **Code examples require execution evidence.** A code fragment should be treated as an executable claim, not decorative pseudocode, unless it is explicitly labeled as pseudocode.

6. **UTF-8 and mathematical notation require render validation.** Symbol fidelity is part of correctness.

7. **The workflow is intended to remain active across the whole whitepaper session.** This is not a one-shot formatting skill.

These are the bones of the engine. The hardening work should preserve them while replacing generic academic metrics with explicit reasoning and publication contracts.

---

## 3. Critical Contract Collisions

### 3.1 Three incompatible TeX regimes

The repository currently mixes:

- `pdflatex` and BibTeX in `SKILL.md`;
- XeLaTeX/LuaLaTeX in `md2tex.py`;
- `biblatex` and biber in the generated Pandoc template;
- `inputenc`, `fontenc`, and `newtxmath` in the canonical asset template;
- `fontspec` and `unicode-math` in the generated template;
- direct Unicode-math preservation as a stated requirement.

These are not interchangeable details. An agent can obey one file and violate another.

**v4 decision:** select one canonical build regime. For the stated requirement that all UTF-8 and mathematical symbols render directly, the strongest default is:

```text
Pandoc AST or controlled Markdown parser
        -> LuaLaTeX-compatible .tex
        -> biblatex + biber
        -> LuaLaTeX passes
        -> validated PDF
```

XeLaTeX may remain a supported fallback profile. `pdflatex` should not be the canonical path for a Unicode-first manuscript.

### 3.2 The canonical template is not a valid Pandoc template

`assets/whitepaper-template.tex` is described as the foundational conversion template, but it does not contain Pandoc variables such as `$body$`, `$title$`, or bibliography conditionals. Passing it to `md2tex.py --template` can produce a document that omits the converted manuscript body.

The generated template inside `md2tex.py` does contain `$body$`, but it is stylistically and technically different from the canonical asset.

**v4 decision:** maintain two explicitly named assets:

- `somnus-pandoc-template.tex`: contains Pandoc variables and controls conversion.
- `somnus-document-class.tex` or `somnus-preamble.tex`: contains the publication design system.

Do not call a static example document a Pandoc template.

### 3.3 Unicode policy and the symbol linter disagree

`SymbolLinter` currently treats every non-ASCII character as a symbolic operator requiring registration. That includes typographic punctuation, accented characters, non-English names, smart quotes, en dashes, em dashes, and potentially invisible Unicode spacing.

This conflicts with the goal of elegant UTF-8 prose.

**v4 decision:** classify Unicode into separate domains:

- prose typography;
- mathematical symbols;
- semantic operators owned by a project ontology;
- control/invisible characters;
- disallowed or suspicious code points.

Only semantic operators require registry entries. Typography should be normalized and validated, not rejected.

### 3.4 The current math normalizer is unsafe

`MathNormalizer` uses punctuation heuristics to infer whether an entire line is mathematics. A prose line containing `=` or other indicators may be wrapped in display math. The ` ```math` conversion branch is also unreachable because the code toggles generic code-block state before checking for a math fence.

**v4 decision:** never infer display mathematics from ordinary punctuation. Require explicit `$...$`, `$$...$$`, `\(...\)`, `\[...\]`, or fenced `math` blocks. The parser may warn about likely bare equations, but it must not silently rewrite prose as mathematics.

### 3.5 Cross-reference labels can collide

`CrossReferenceLinker._create_label()` uses `len(self.labels)` for unnamed environments but never populates `self.labels`. Multiple unnamed theorem-like environments can therefore receive the same label.

**v4 decision:** labels must be assigned from a document-wide registry with deterministic collision handling and source-location provenance.

### 3.6 Bibliography compilation is incomplete

The converter compiles the TeX engine twice but does not run BibTeX or biber. Citations can remain unresolved even though the skill promises a final verified PDF.

**v4 decision:** the build driver must inspect the selected bibliography backend and execute the correct pass graph. Prefer `latexmk` with a locked profile, or explicitly run LuaLaTeX, biber, and the required subsequent passes.

### 3.7 “Standalone tools” is not true in the current implementation

`AGENTS.md` says every tool must operate independently and must not import siblings. `batch_manager.py` imports `PDFToMarkdownConverter` from a sibling file. Several scripts also install dependencies dynamically at import time.

**v4 decision:** distinguish two categories:

- **portable commands:** single-file utilities with no sibling imports;
- **engine modules:** package-managed components allowed to share internal libraries.

Pretending a growing workflow engine is only a bag of unrelated scripts now works against hardening.

### 3.8 Missing referenced assets

The skill references files that are absent from the archive:

- `cleaner.py`;
- `hash-index.ps1`;
- `requirements.txt`;
- `README.md`;
- a shipped symbol registry.

**v4 decision:** add a repository self-check that fails before activation when required assets are missing.

### 3.9 Dependency policy is backwards

The skill prohibits version pins in the name of reproducibility. Unversioned dependencies are not reproducible and can break the workflow without repository changes.

**v4 decision:** use a human-readable dependency declaration plus a generated lock or constraints file. For example:

```text
pyproject.toml             human-maintained ranges
uv.lock / requirements.lock exact environment resolution
system-requirements.md     pandoc, graphviz, latexmk, biber, poppler
```

### 3.10 Automatic `pip install` during script import must be removed

A publication tool should never mutate its Python environment merely because a module was imported. This is fragile, non-deterministic, and hostile to isolated agent runtimes.

**v4 decision:** commands must perform dependency checks, print exact missing requirements, and exit with a typed failure. Environment creation belongs to bootstrap tooling.

---

## 3.11 Empirical conversion probe

A minimal conversion probe confirmed the highest-risk failures rather than merely inferring them from source:

- A prose sentence containing `x = y` was silently wrapped in display-math delimiters.
- A fenced ` ```math` block remained unchanged instead of being normalized.
- Passing the advertised canonical `assets/whitepaper-template.tex` to Pandoc failed with a template parser error before conversion.
- Running the converter without an existing registry created `symbols.json` in the current working directory as an undocumented side effect.

The normalized intermediate produced by the current tool included:

```markdown
$$
This line contains an equality marker x = y in prose.
$$

```math
E = mc²
```
```

This confirms that `md2tex.py` should be treated as a prototype requiring a controlled parser rewrite before it becomes the canonical publication compiler.

---

## 4. Why the Current Prose Becomes “Good, But Not Daeron”

The existing prose guidance is essentially:

- prefer prose over bullets;
- use transitions;
- be academically rigorous;
- formalize mathematics;
- avoid buzzwords.

That is not an authorial model. Nearly every capable model has been trained to produce exactly this kind of generic instruction-compliant academic prose.

A Somnus paper needs a more specific rhetorical grammar.

### 4.1 Argument movement

The paper should generally move through the following intellectual sequence:

1. establish the exact object under investigation;
2. identify the regime under which existing terminology becomes insufficient;
3. define the new object without inflating the claim;
4. expose the mechanism or architecture before celebrating its implications;
5. formalize only the parts that benefit from formalization;
6. separate implemented behavior, measured behavior, architectural intention, and future extension;
7. return to the opening problem with a narrower but stronger conclusion.

This is different from the common model pattern:

```text
broad historical introduction
-> generic gap statement
-> list of contributions
-> architecture description
-> optimistic conclusion
```

### 4.2 Sentence cadence

The engine needs a learned cadence profile derived from Daeron-authored papers, not adjectives such as “elegant” or “authoritative.” The comparison stage should extract measurable and semantic features, including:

- sentence-length distribution and variance;
- paragraph-length distribution;
- ratio of simple, compound, and recursively qualified sentences;
- frequency and location of thesis reversals;
- use of colons, semicolons, parentheses, and short terminal sentences;
- transition vocabulary;
- definition placement;
- how equations are introduced and interpreted;
- how uncertainty is stated;
- how negative definitions are used;
- how symbolic names carry compressed architecture;
- how the prose changes temperature between mechanism, doctrine, and result.

The output should become a `references/authorial-cadence-profile.md` plus a machine-readable `authorial-cadence-profile.yaml`.

### 4.3 Claim temperature

The current engine needs explicit claim classes. Suggested classes:

- **Implemented:** present in inspected source or executable artifact.
- **Observed:** produced by a recorded run, benchmark, or trace.
- **Derived:** follows from stated assumptions or formal reasoning.
- **Interpretive:** architectural or theoretical reading of evidence.
- **Hypothesized:** plausible but unverified mechanism.
- **Planned:** intended future behavior.
- **Comparative:** claim relative to another system or baseline.
- **Historical:** claim about prior work, chronology, or priority.

Each class should have a permitted rhetorical temperature. For example, planned behavior cannot be narrated in the present tense as implemented capability. This single mechanism will improve both credibility and human cadence more than arbitrary citation density.

### 4.4 Negative-definition discipline

Daeron’s architecture writing often establishes an object by defining what it is not before specifying what it is. This is valuable when the new architecture is adjacent to familiar categories and likely to be flattened into them.

The engine should permit a bounded negative-definition passage when it serves taxonomy, but forbid repetitive “not X, not Y, not Z” padding after the distinction has already been established.

### 4.5 Formalism should clarify mechanism, not decorate it

The current rule that mathematical foundations should precede implementation can force equations before the reader knows why they matter.

A stronger rule is:

> Introduce formal objects at the earliest point where they remove ambiguity from a mechanism, contract, invariant, or claim.

Some papers require a mathematical substrate first. Others require an architectural object and operational boundary before notation becomes meaningful.

---

## 5. Replace Metric Quotas with Evidence Gates

The current global metrics encourage machine-like padding:

- 15,000-word minimum;
- 8 citations per 1,000 words;
- 10 figures over 20 pages;
- four or five heading levels;
- 90% code coverage for examples.

These are easy to optimize and weakly correlated with paper quality.

### Recommended replacements

#### Length

Length is determined by closure of the argument, not a minimum. The paper is complete when every declared contribution has:

- a definition;
- a mechanism;
- evidence or an explicit evidence boundary;
- a limitation;
- a connection to the paper’s central thesis.

#### Citations

Use a claim ledger. Every externally grounded claim must map to one or more sources, while original architecture claims map to source artifacts, code, logs, or author declaration. Citation density is then an outcome, not a quota.

#### Visuals

Every visual must have a declared function:

- topology;
- process;
- comparison;
- measurement;
- state transition;
- mathematical intuition;
- implementation map;
- chronology;
- failure analysis.

A visual without a unique information function should be deleted.

#### Heading depth

Use the shallowest hierarchy that preserves argument structure. Deep heading trees are often an agent’s substitute for narrative continuity.

#### Code validation

Validate the claim made by the code. Coverage is relevant only when the code artifact itself is a tested deliverable. A ten-line numerical example may need deterministic output validation, not a synthetic 90% coverage target.

---

## 6. Proposed v4 Workflow State Machine

The new skill should operate as a persistent state machine.

### State 0: Activation and repository reconnaissance

The agent records:

- project name and paper identity;
- implementation authority surfaces;
- existing docs and specifications;
- available tests, logs, benchmarks, and figures;
- current Markdown, TeX, bibliography, and visual assets;
- selected publication profile.

Output: `whitepaper/state/reconnaissance.json`.

### State 1: Authority map

Classify every source:

- source code;
- runtime evidence;
- specification;
- planning document;
- prior paper;
- external literature;
- author clarification.

Resolve contradictions by authority order rather than blending them.

Output: `whitepaper/state/authority-map.yaml`.

### State 2: Thesis and contribution contract

Before long-form drafting, create:

- one central thesis;
- problem boundary;
- object definition;
- contribution set;
- non-claims;
- evidence ceiling;
- intended reader model.

Output: `whitepaper/state/thesis-contract.md`.

### State 3: Claim ledger

Each meaningful claim receives:

- ID;
- claim text;
- claim class;
- source/evidence;
- confidence;
- target section;
- citation or artifact reference;
- unresolved dependency.

Output: `whitepaper/state/claim-ledger.yaml`.

### State 4: Visual ledger

Every proposed visual receives:

- ID;
- purpose;
- source data;
- format;
- monochrome or color permission;
- target section;
- caption thesis;
- generation command;
- validation status.

Output: `whitepaper/state/visual-ledger.yaml`.

### State 5: Manuscript architecture

Create a section graph rather than merely a table of contents. Each section must declare:

- question answered;
- incoming assumptions;
- outgoing conclusion;
- claims consumed;
- visuals consumed;
- transition into the next section.

Output: `whitepaper/state/section-graph.yaml`.

### State 6: Markdown composition

Draft section modules while maintaining:

- cadence profile;
- claim classes;
- citation bindings;
- equation introduction and interpretation;
- visual placeholders with ledger IDs;
- explicit unresolved markers.

The Markdown manuscript is allowed to remain expansive and architecturally explicit.

### State 7: Adversarial editorial passes

Run distinct passes rather than one generic “polish” command:

1. **Architecture pass:** Does the paper describe the actual system?
2. **Claim pass:** Does rhetorical temperature match evidence?
3. **Cadence pass:** Does the prose preserve the authorial profile?
4. **Compression pass:** Remove repeated explanation and outline residue.
5. **Counter-reading pass:** Identify the strongest flattening or skeptical interpretation.
6. **Citation pass:** Validate source-to-claim bindings.
7. **Visual pass:** Ensure every visual carries information.
8. **Math pass:** Validate notation, dimensions, symbols, and interpretation.

### State 8: TeX transcreation

Do not perform a blind Markdown-to-TeX substitution. Convert through a controlled intermediate representation and then apply:

- theorem environments;
- equation numbering;
- code box styling;
- figure placement;
- table redesign;
- caption system;
- page-break logic;
- bibliography backend;
- document metadata;
- Somnus black-and-white publication styling.

### State 9: Build and render validation

The build must fail on:

- unresolved references;
- missing citations;
- missing figures;
- unrendered glyphs;
- duplicate labels;
- overfull boxes beyond threshold;
- color outside approved environments;
- missing alt descriptions in source metadata;
- code examples lacking validation state.

### State 10: Human-authorship and genericity review

Run a style-risk scanner that looks for:

- uniform sentence lengths;
- repeated paragraph templates;
- generic transition chains;
- excessive contribution enumeration;
- inflated adjectives;
- conclusion restatement without new compression;
- unsupported certainty;
- citation wallpaper;
- “AI voice” phrase clusters;
- abrupt cadence changes relative to the author profile.

This should not be marketed as an oracle that proves whether text is AI-written. It is a manuscript risk and authorship-consistency review. External detectors may be queried as one noisy signal, never as the optimization target.

### State 11: Release bundle

Produce:

- authoritative `.tex`;
- compiled `.pdf`;
- preserved `.md` source;
- bibliography;
- editable visual sources;
- claim and visual ledgers;
- build manifest;
- checksums;
- validation report;
- source-to-publication provenance map.

---

## 7. Visual Constitution

The style direction is already latent in the template and should be made enforceable.

### Body

- black text on white paper;
- no colored headings;
- no colored hyperlinks;
- no decorative gradients;
- no dashboard-style cards;
- restrained rules, boxes, and section markers;
- strong whitespace and page geometry;
- modern optical spacing over imitation typewriter degradation.

### Code

Code must appear inside a dedicated code box. Color is permitted only for syntax function. The box should remain printable in grayscale and should not depend on color to distinguish semantic categories.

### Visuals

Color is permitted when it encodes information. Every colored visual should remain interpretable under grayscale conversion or provide distinct line styles, markers, labels, or textures.

### Mathematical objects

Equations remain monochrome. Color may be used only inside a deliberately declared explanatory diagram, never in ordinary displayed mathematics.

### Design metaphor

The visual system should feel like an advanced research artifact that could have existed in an alternate 1980s DARPA archive, reconstructed with modern typography and DeepMind-level information design. It should not look retro for nostalgia’s sake. The historical layer provides discipline; the modern layer provides precision.

---

## 8. Proposed Repository Structure

```text
academic-whitepaper-engine/
├── SKILL.md
├── AGENTS.md
├── pyproject.toml
├── uv.lock
├── README.md
├── profiles/
│   ├── somnus-research.yaml
│   ├── somnus-patent.yaml
│   └── technical-memo.yaml
├── references/
│   ├── authorial-cadence-profile.md
│   ├── authorial-cadence-profile.yaml
│   ├── claim-classification.md
│   ├── evidence-policy.md
│   ├── visual-constitution.md
│   ├── citation-policy.md
│   └── tex-toolchain.md
├── schemas/
│   ├── authority-map.schema.json
│   ├── claim-ledger.schema.json
│   ├── visual-ledger.schema.json
│   ├── section-graph.schema.json
│   └── build-manifest.schema.json
├── templates/
│   ├── somnus-pandoc-template.tex
│   ├── somnus-preamble.tex
│   ├── somnus-cover.tex
│   └── codebox-listings.tex
├── whitepaper_engine/
│   ├── cli.py
│   ├── manuscript.py
│   ├── claims.py
│   ├── visuals.py
│   ├── citations.py
│   ├── unicode.py
│   ├── tex.py
│   ├── build.py
│   ├── validate.py
│   └── style_review.py
├── portable_tools/
│   ├── pdf_to_markdown.py
│   ├── pdf_ocr.py
│   └── provenance_hash.py
└── tests/
    ├── fixtures/
    ├── golden/
    ├── test_unicode_rendering.py
    ├── test_cross_references.py
    ├── test_bibliography.py
    ├── test_color_policy.py
    ├── test_md_tex_roundtrip.py
    └── test_cli_workflow.py
```

This preserves truly portable utilities while allowing the core engine to become a coherent package.

---

## 9. File-Level Patch Recommendations

### `SKILL.md`

Replace generic “IEEE/ACM/arXiv-level” positioning with the actual Somnus publication contract. Standards may be output profiles, but they should not define the engine’s voice.

Remove rigid quotas. Add the state machine, claim classes, authority ordering, visual constitution, and Markdown-to-TeX transcreation rule.

Make activation sticky by requiring `whitepaper/state/session.json` and by instructing the agent to reload it before every major phase.

### `AGENTS.md`

Rewrite around two architectures: package modules and portable tools. Add modification boundaries, test expectations, and activation behavior. Remove stale paths that do not match the archive.

### `assets/whitepaper-template.tex`

Convert to LuaLaTeX and separate document design from sample content. Remove placeholder philosophical prose from the canonical template. A prolegomenon should be supported, not forced on every paper.

Add formal monochrome enforcement and code/visual color scopes.

### `assets/somnus_cover_page.tex`

Move metadata to a generated input file or Pandoc variables. Avoid hardcoding author identity and affiliation into a reusable template. Preserve the restrained cover design while improving publication metadata and long-title handling.

### `references/latex-preamble.tex`

Stop loading a “package zoo.” Use profile-based package loading. Remove conflicting or redundant math/font packages. Set one Unicode math font and one text family. Keep optional packages behind feature flags.

### `scripts/md2tex.py`

This should become the first major rewrite target.

Required repairs:

- remove unsafe line-level math inference;
- parse fenced blocks correctly;
- classify Unicode rather than rejecting all non-ASCII;
- implement deterministic label registry;
- select a single bibliography backend;
- use the actual Pandoc template;
- run a complete build graph;
- preserve intermediate normalized Markdown only when requested;
- emit a structured conversion manifest;
- validate color policy and glyph rendering;
- use typed errors and non-zero exit states;
- add golden-file tests.

### `scripts/batch_manager.py`

Either move it into the engine package or make it invoke portable tools by subprocess. It currently violates the standalone rule and installs dependencies during import.

### OCR and PDF conversion scripts

These are useful but should not dominate the authoring skill. They belong in a source-ingestion profile. Remove automatic package installation, add capability checks, and isolate OCR because native PDF text extraction should remain the first path.

### `scripts/sart.py`

Clarify whether SART is a symbol ontology tool, a repository semantic scanner, or a reasoning-trace utility. The current skill description and AGENTS table assign it different identities. It should receive one explicit contract before being integrated into the manuscript workflow.

---

## 10. Priority Patch Sequence

### P0: Make the engine truthful

1. Choose LuaLaTeX or XeLaTeX as canonical.
2. Choose biblatex/biber or BibTeX as canonical.
3. Repair the Pandoc template boundary.
4. Remove automatic dependency installation.
5. add missing required files or stop referencing them.
6. Fix duplicate labels and unsafe math normalization.
7. Add a repository self-check command.

### P1: Make the workflow deterministic

1. Add authority map, claim ledger, visual ledger, and section graph schemas.
2. Add persistent session state.
3. Split editorial passes.
4. Add structured validation reports.
5. Add build manifests and golden tests.

### P2: Make the writing Daeron’s

1. Compare a fully Daeron-authored whitepaper against a Codex-authored paper.
2. Extract cadence features and rhetorical moves.
3. Build the authorial profile.
4. Create positive and negative prose exemplars.
5. Implement an authorship-consistency reviewer.
6. Re-run the Codex paper through the new profile and compare the revision.

### P3: Intensify the publication system

1. Add a visual compiler and color-policy validator.
2. Add source-to-claim provenance reports.
3. Add deterministic TeX build containers or Nix/UV environment manifests.
4. Add PDF/A and archival validation.
5. Add optional publisher profiles without compromising the Somnus source style.

---

## 11. Whitepaper Comparison Protocol

The two-paper comparison should not ask which paper is “better.” It should identify the transformations that cause the Codex paper to cease sounding authored.

The analysis should compare:

- opening strategy;
- paragraph architecture;
- thesis placement;
- sentence-length variance;
- transitions;
- equation staging;
- negative definitions;
- claim temperature;
- evidence placement;
- citation behavior;
- use of headings;
- use of lists;
- visual narration;
- limitation language;
- conclusions;
- repeated phrase families;
- generic model fingerprints;
- points where the author’s conceptual compression is expanded into bland explanation.

Deliverables from that comparison:

1. `authorial-cadence-profile.md`;
2. `authorial-cadence-profile.yaml`;
3. `codex-drift-patterns.md`;
4. `before-after-revision-examples.md`;
5. a revised prose section from the Codex paper as a validation sample.

---

## 12. Acceptance Tests for v4

The hardened engine is ready when all of the following are true:

- A fresh agent can identify which files are plans, specifications, implementations, and evidence.
- The agent does not begin drafting before creating the thesis contract and claim ledger.
- Markdown remains the expansive manuscript source.
- The final PDF is always compiled from TeX.
- Unicode mathematics renders under the canonical engine without silent substitution.
- Citations and cross-references resolve in an automated build.
- No body text, links, headings, or ordinary equations contain color.
- Every code sample has an execution or pseudocode declaration.
- Every visual has a ledger entry and unique information function.
- Planned capabilities are not described as implemented.
- A style review can explain why a passage drifts from the authorial profile.
- The build produces a machine-readable manifest and validation report.
- The workflow can resume from persistent state after an agent context reset.

---

## 13. Bottom Line

The current skill is not weak. It is one generation behind the way modern coding agents actually behave.

It assumes that sufficient instructions about quality, rigor, citations, figures, and file output will converge toward authored scholarship. Modern agents can satisfy those instructions too easily. They need constraints around epistemology, provenance, rhetorical motion, and stateful workflow, not more adjectives about excellence.

The v4 engine should therefore become less like a giant academic prompt and more like a publication compiler with an authorial operating system.

The next indispensable input is the two-paper comparison. The existing repository already reveals the executable defects and workflow gaps. The authored paper will reveal the missing voice law.
