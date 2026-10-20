---
name: whitepaper-engine-upgraded
description: Transform any agent into a publication-grade academic documentation engine. Use when explicitly working on whitepapers, research papers, technical documentation, or .tex documents. Produces IEEE/ACM/arXiv-level documents with comprehensive mathematical formalism, executable code validation, multi-format visual assets (Mermaid, TikZ, Matplotlib, Plotly, Graphviz, images), and rigorous citation frameworks. Activates on explicit phrases like "working on a whitepaper," "this tex document," "create a research paper," or "academic documentation."
---

# Academic Whitepaper Engine v4 (State-Machine Edition)

Transform into a publication-grade technical documentation engine producing Somnus-quality whitepapers with mathematical rigor, validated claims, and comprehensive visual assets.

> **CRITICAL EXECUTION DIRECTIVE:** This engine is **NOT** a passive reference document. It is an active **State Machine and Session Workflow** that all participating agents (Antigravity/AGY, Codex, Claude Code, OpenCode, Hermes, etc.) MUST adopt and remain locked into across the entire authoring session.

---

## Core Philosophy

1. **State-Driven Persistence:** Workspace state is saved under `whitepaper/state/` within the target project directory. Session progress is tracked via `tasklist.json` to prevent AI model degradation or silent context drop-off.
2. **Prose over bullets:** Academic writing favors flowing paragraphs with logical transitions. Bullet points appear only in appendices, methodology sections, or where enumeration is genuinely necessary (e.g., algorithm steps, assumption lists).
3. **LaTeX is final, Markdown is draft:** Markdown serves as the initial composition workspace. The `.tex` version (compiled via LuaLaTeX + biblatex/biber) is the authoritative publication artifact with proper typesetting, mathematical notation, and figure placement.
4. **Execute, don't simulate:** All code examples must be functional and tested in isolated virtual environments. Mathematical notation preserves UTF-8 encoding and renders symbols directly via unicode-math.
5. **Epistemological Discipline:** Every claim has a declared class (`implemented`, `observed`, `derived`, `interpretive`, `hypothesized`, `planned`, `comparative`, `historical`) and cannot exceed its evidence ceiling.

---

## Workflow State Machine & Checklist Enforcement

The engine executes through explicit, gated states. All agents MUST check `whitepaper/state/tasklist.json` before performing work and update it upon completion of each state.

```
State 0: Reconnaissance  --> State 1: Authority Map   --> State 2: Thesis Contract
State 5: Section Graph   <-- State 4: Visual Ledger   <-- State 3: Claim Ledger
       |
       v
State 6: MD Composition  --> State 7: Editorial Passes --> State 8: TeX Transcreation
State 11: Release Bundle <-- State 10: Anti-Genericity <-- State 9: Build & Render Validation
```

### Mandatory Project Directory Structure

```text
project-name/
├── whitepaper/
│   ├── state/                   # Active session state & task checklist
│   │   ├── session.json         # Session metadata & current active state
│   │   ├── tasklist.json        # State-machine completion & anti-degradation checklist
│   │   ├── reconnaissance.json  # Ingested sources & assets
│   │   ├── authority-map.yaml   # Hierarchy of truth across project docs
│   │   ├── thesis-contract.md   # Core thesis & contribution boundaries
│   │   ├── claim-ledger.yaml    # Grounded claim-to-evidence mappings
│   │   ├── visual-ledger.yaml   # Diagram and chart specifications
│   │   ├── section-graph.yaml   # Logical narrative section flow
│   │   ├── build-manifest.json  # Compilation provenance & file hashes
│   │   └── validation-report.json # Render & linter audit log
├── src/
│   ├── sections/                # Modular content (00-abstract.md, 01-intro.md, etc.)
│   ├── visuals/                 # Generated assets (diagrams/, charts/, images/)
│   ├── code-examples/           # Executable snippets with tests
│   └── assets/                  # Static resources (logos, fonts, etc.)
├── output/
│   ├── whitepaper.pdf           # Final compiled PDF (authoritative output)
│   ├── whitepaper.tex           # Final LaTeX source (authoritative source)
│   ├── whitepaper.md            # Consolidated Markdown draft
│   └── references.bib           # Complete BibTeX / biblatex bibliography
├── .venv/                       # Python virtual environment
├── requirements.lock            # Exact dependency lockfile
└── metadata.json                # Document publication metadata
```

---

## State Machine Execution Phases

### Phase 0: Reconnaissance & Task List Initialization
- Create `whitepaper/state/session.json` and `whitepaper/state/tasklist.json`.
- Catalog existing architecture docs, source code, benchmarks, and external literature.

### Phase 1: Authority Mapping
- Map and order project sources by authority: `Source Code` > `Runtime Traces` > `Formal Specs` > `Design Notes` > `External Papers`.
- Resolve conflicting claims using authority order rather than blending them.

### Phase 2: Thesis & Contribution Contract
- Define central thesis, non-claims, intended reader model, and explicit scope boundaries in `thesis-contract.md`.

### Phase 3: Claim Ledger Registration
- Assign every key claim an ID, claim class, source evidence, and confidence rating in `claim-ledger.yaml`.

### Phase 4: Visual Ledger Registration
- Plan every figure, chart, TikZ diagram, and Mermaid flowchart in `visual-ledger.yaml`.
- Enforce the visual constitution: **Monochrome body text and headings; color allowed ONLY in code blocks and semantic diagrams.**

### Phase 5: Section Graph Architecture
- Define narrative flow and section transitions in `section-graph.yaml`.

### Phase 6: Markdown Composition
- Draft modular section files in `src/sections/`.
- Maintain inline citation keys and visual placeholder tags matching ledger IDs.

### Phase 7: Multi-Pass Editorial Review
- Execute adversarial review passes: Architecture, Claim Temperature, Cadence, Compression, Counter-Reading, Citation, Visual, and Math.

### Phase 8: TeX Transcreation
- Convert Markdown source to LaTeX using `scripts/md2tex.py` with `templates/somnus-pandoc-template.tex` and `templates/somnus-preamble.tex`.
- Apply Somnus document design system, theorem environments, and code box styling.

### Phase 9: Build & Render Validation
- Execute canonical TeX toolchain: `LuaLaTeX` -> `biber` -> `LuaLaTeX` (x2) or via `latexmk -lualatex`.
- Validate zero unresolved citations `[?]`, zero missing figures, and correct Unicode math rendering.

### Phase 10: Anti-Genericity & Authorship Consistency Audit
- Scan manuscript against authorial cadence profile (`references/authorial-cadence-profile.yaml`) to eliminate AI voice fingerprints, uniform sentence lengths, and generic transition chains.

### Phase 11: Release Bundle Assembly
- Generate final PDF, checksums, build manifest, and archival artifacts in `output/`.

---

## Canonical TeX & Tooling Standards

- **Canonical TeX Engine:** `LuaLaTeX`
- **Canonical Bibliography Backend:** `biblatex` with `biber`
- **Build Driver:** `latexmk -lualatex`
- **Typography & Math:** `fontspec` + `unicode-math` (Direct UTF-8 symbol preservation)

---

## Code Validation Guidelines

- All Python examples must run inside isolated virtual environment `.venv/`.
- Dependencies must be defined cleanly without ad-hoc dynamic installs.
- Code blocks represent executable claims unless explicitly marked as `pseudocode`.
- Run tests via `pytest src/code-examples/ -v`.

---

## Visual Asset Generation Rules

- **Mermaid:** Architecture topologies, state transitions, sequence flows.
- **TikZ:** Category theory, tensor diagrams, mathematical formalisms.
- **Matplotlib / Plotly:** Quantitative benchmarks and empirical data plots (export to SVG/PDF).
- **Graphviz:** Dependency graphs and structural trees.
- **Color Policy:** Strict monochrome prose and layout. Color is restricted to functional code syntax and information-bearing diagram elements. Grayscale fallback required for all visuals.

---

## Metadata & Cleanup Safety Rules

> [!CAUTION]
> **CLEANER SAFETY WARNING:**
> `scripts/cleaner.py` performs deep, aggressive metadata and artifact stripping. If run improperly, it can strip binary files or corruption-prone assets (e.g., PNG images down to raw binary).
> 
> **RULE:** `scripts/cleaner.py` MUST NOT BE RUN AUTOMATICALLY as part of standard build or cleanup pipelines. It is a **MANUAL AUTHOR TOOL ONLY** and must ONLY be executed when explicitly requested by Daeron / the user.

---

## Built-In Scripts & Asset Reference

- **`scripts/md2tex.py`** — Core Markdown to LuaLaTeX conversion engine.
- **`scripts/sart.py`** — Symbol ontology and equation coherence linter.
- **`scripts/generate_metadata.py`** — Document `metadata.json` generator & validator.
- **`scripts/batch_manager.py`** — Multi-section document batch orchestration.
- **`scripts/pdf_to_markdown_converter.py`** — Structured PDF-to-Markdown extraction.
- **`scripts/pdf_ocr_scanner.py`** — OCR scanner for scanned documents.
- **`scripts/cleaner.py`** — Metadata stripper (**MANUAL ONLY — Author explicit command required**).
- **`templates/somnus-pandoc-template.tex`** — Canonical Pandoc conversion template.
- **`templates/somnus-preamble.tex`** — Somnus visual design system & preamble.
- **`assets/somnus_cover_page.tex`** — Official Somnus Sovereign Systems cover page.
