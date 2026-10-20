# PLAN.md — Academic Whitepaper Engine v4 Hardening & Execution Plan

**Target:** `academic-whitepaper-engine`  
**Goal:** Squad wipe the codebase in one pass to transform the engine into a state-machine-driven, publication-grade academic whitepaper system with unified TeX toolchains, epistemological claim ledgers, authorial cadence profiles, and anti-degradation state tracking.

---

## 1. Executive Summary & Core Rules

### 1.1 State Machine Nature
This engine is **NOT** a passive set of formatting hints. It is an **Active State Machine Workflow**.
- Global binaries and scripts live in the engine repository (`scripts/`, `templates/`, `schemas/`).
- Manuscript content, compiled PDFs, and active session states live **per codebase/project** in `whitepaper/state/`.
- Participating models (Antigravity/AGY, Codex, Claude Code, OpenCode, Hermes) MUST check and update `whitepaper/state/tasklist.json` to prevent context drop-off and silent degradation.

### 1.2 Cleaner Policy (`scripts/cleaner.py`)
- `scripts/cleaner.py` performs aggressive character, homoglyph, and metadata stripping.
- **DIRECTIVE:** `scripts/cleaner.py` is **STRICTLY MANUAL ONLY**. It MUST NEVER run automatically during routine builds, compilation, or cleanup. It is invoked ONLY when explicitly commanded by Daeron / the user.
- **v4 ENFORCEMENT:** `--force-author-command` flag is now required to run. Without it, the script prints a safety block and exits.

### 1.3 Unified TeX Toolchain Consensus
- **Source:** Markdown (`src/sections/`) -> Pandoc AST / `scripts/md2tex.py`
- **TeX Engine:** `LuaLaTeX`
- **Bibliography:** `biblatex` + `biber`
- **Build Driver:** `latexmk -lualatex`
- **Font & Math:** `fontspec` + `unicode-math` (Direct UTF-8 math rendering)

---

## 2. Squad-Wipe Execution Blueprint

```
       [PHASE 1: STATE MACHINE & TASKLIST ARCHITECTURE]
                            │
                            ▼
        [PHASE 2: CANONICAL TEMPLATES & PREAMBLE]
                            │
                            ▼
   [PHASE 3: SCRIPT REFACTORING & MD2TEX PARSER REWRITE]
                            │
                            ▼
      [PHASE 4: CLAIM LEDGER & AUTHORIAL CADENCE]
                            │
                            ▼
     [PHASE 5: DEPENDENCY LOCKING & SELF-CHECK ENGINE]
                            │
                            ▼
     [PHASE 6: VERIFICATION & GOLDEN TEST SUITE]
```

---

## Phase 1: State Machine & Tasklist Architecture Setup

- [x] **Create JSON Schemas (`schemas/`)**
  - `schemas/session.schema.json`: Session metadata & active state marker.
  - `schemas/tasklist.schema.json`: State machine phase completion & checklist tracker.
  - `schemas/authority-map.schema.json`: Source hierarchy mapping (`Code` > `Traces` > `Specs` > `Notes`).
  - `schemas/claim-ledger.schema.json`: Epistemological claim classification & evidence bounds.
  - `schemas/visual-ledger.schema.json`: Figure specifications, color policies, and fallback rules.
  - `schemas/section-graph.schema.json`: Narrative structure and transition graph.
  - `schemas/build-manifest.schema.json`: Cryptographic provenance and compilation log.

- [x] **Implement State Tracker Module (`whitepaper_engine/state.py`)**
  - Initialize project `whitepaper/state/` directory structure.
  - Generate default `tasklist.json` containing all 12 workflow states (State 0 through State 11).
  - Provide CLI subcommands: `state init`, `state status`, `state advance`, `state verify`.

---

## Phase 2: Canonical Template & TeX Preamble Unification

- [x] **Create `templates/somnus-pandoc-template.tex`**
  - Extract actual Pandoc variable placeholders (`$body$`, `$title$`, `$author$`, `$abstract$`, `$biblatex$`).
  - Replace broken `assets/whitepaper-template.tex` with valid template variables.

- [x] **Create `templates/somnus-preamble.tex`**
  - Configure single unified typography stack (`fontspec` + `unicode-math`).
  - Define custom theorem environments (`theorem`, `lemma`, `definition`, `invariant`, `non-claim`).
  - Configure code box listings with restrained functional syntax highlighting.
  - Enforce monochrome body text, headings, and hyperref links.

- [x] **Create `templates/somnus-cover.tex`**
  - Bind cover page fields to Pandoc metadata variables instead of hardcoded author strings.

---

## Phase 3: Script Suite Hardening & `md2tex.py` Rewrite

- [x] **Rewrite `scripts/md2tex.py` (Core Publication Compiler)**
  - **Math Fence Parser Fix:** Correctly handle ` ```math ` blocks without skipping or breaking formatting.
  - **Remove Unsafe Math Rewriting:** Stop converting ordinary prose containing `=` or mathematical symbols into display math `$$...$$`. Require explicit inline `$...$` or fenced blocks.
  - **Unicode Classification:** Replace generic non-ASCII rejection with domain classification (prose typography vs mathematical symbols vs forbidden characters).
  - **Deterministic Cross-Reference Registry:** Fix `CrossReferenceLinker` label generator to prevent duplicate environment labels across sections.
  - **Biblatex / Biber Integration:** Automatically invoke `biber` as part of the `latexmk` build pass graph.
  - **Remove Import-Time Dynamic Installs:** Replace inline `pip install` calls with explicit missing dependency checks and structured error reporting.

- [x] **Refactor `scripts/batch_manager.py`**
  - Remove direct module imports from sibling scripts.
  - Convert to standalone process invocation.
  - Add missing `argparse` and `logging` imports.

- [x] **Harmonize `scripts/sart.py`**
  - Align SART CLI with `scan` subcommand documented in AGENTS.md.
  - Add proper help text and error handling.

- [x] **Refactor Ingestion Scripts (`scripts/pdf_to_markdown_converter.py`, `scripts/pdf_ocr_scanner.py`, `scripts/generate_metadata.py`)**
  - Clean up CLI interfaces, remove dynamic dependency mutations, and ensure clean exit codes.
  - Add `--output` flag to `generate_metadata.py`.
  - Add `--interactive` flag requirement to prevent stdin-blocking in headless pipelines.

- [x] **Enforce Manual-Only Policy for `scripts/cleaner.py`**
  - Add explicit CLI flag `--force-author-command` to `scripts/cleaner.py` to prevent accidental execution.

---

## Phase 4: Epistemological Claim Ledger & Authorial Cadence Framework

- [x] **Implement Claim Epistemology Engine (`whitepaper_engine/claims.py`)**
  - Enforce 8 explicit claim classes: `implemented`, `observed`, `derived`, `interpretive`, `hypothesized`, `planned`, `comparative`, `historical`.
  - Validate claim temperature (e.g., flag `planned` features written in present tense as `implemented`).

- [x] **Implement Visual Constitution Engine (`whitepaper_engine/visuals.py`)**
  - Validate visual ledger entries against color policy (monochrome layout, functional diagram color only, mandatory grayscale fallback).

- [x] **Create Authorial Cadence Reference (`references/authorial-cadence-profile.md` & `authorial-cadence-profile.yaml`)**
  - Document Daeron's sentence length variance, argument movement, negative definition usage, colon/semicolon rhythm, and structural transitions.

- [x] **Implement Anti-Genericity Reviewer (`whitepaper_engine/style_review.py`)**
  - Scan Markdown text for AI voice fingerprints, uniform sentence lengths, generic transition words ("Furthermore," "Moreover," "Delving deeper"), and un-grounded claim inflation.

---

## Phase 5: Dependency Management & Repository Self-Check

- [x] **Create `pyproject.toml`**
  - Define package metadata, entry points (`whitepaper-engine`), and explicit dependency ranges.

- [x] **Create `system-requirements.md`**
  - Document required external system binaries: `lualatex`, `biber`, `latexmk`, `pandoc`, `graphviz`, `poppler-utils`.

- [x] **Implement Repository Self-Check Script (`scripts/check_engine.py`)**
  - Inspect repository integrity, verify presence of canonical templates and scripts, check system dependencies, and exit with status code 0 on clean pass.

---

## Phase 6: Automated Verification & Golden Test Suite

- [x] **Create `tests/` Test Suite**
  - `tests/test_unicode_rendering.py`: Test UTF-8 math symbols under UnicodeClassifier.
  - `tests/test_cross_references.py`: Test label collisions and reference resolution.
  - `tests/test_bibliography.py`: Test biblatex/biber compilation graph.
  - `tests/test_color_policy.py`: Test monochrome enforcement in TeX templates.
  - `tests/test_md2tex_roundtrip.py`: Golden file Markdown-to-TeX conversion test.
  - `tests/test_cli_workflow.py`: End-to-end state machine CLI test.

---

## 3. Execution Checklist — COMPLETED

| Step | Action Item | Target File | Status |
|------|-------------|-------------|--------|
| 1 | Update `SKILL.md` for v4 state machine & manual `cleaner.py` policy | `SKILL.md` | ✅ DONE |
| 2 | Update `AGENTS.md` tool registry & tasklist protocols | `AGENTS.md` | ✅ DONE |
| 3 | Create comprehensive execution blueprint | `PLAN.md` | ✅ DONE |
| 4 | Create JSON schemas for state tracking & ledgers | `schemas/*.json` | ✅ DONE |
| 5 | Refactor canonical TeX templates & preamble | `templates/*.tex` | ✅ DONE |
| 6 | Rewrite `scripts/md2tex.py` parser & build graph | `scripts/md2tex.py` | ✅ DONE |
| 7 | Refactor script suite (`sart.py`, `batch_manager.py`, etc.) | `scripts/*.py` | ✅ DONE |
| 8 | Build claim ledger & authorial cadence modules | `references/`, `whitepaper_engine/` | ✅ DONE |
| 9 | Add `pyproject.toml` & system requirements | `pyproject.toml` | ✅ DONE |
| 10 | Build self-check tool & test suite | `scripts/check_engine.py`, `tests/` | ✅ DONE |

---

*Plan completed: 2026-08-06 (Academic Whitepaper Engine v4 Hardening)*
*Execution completed: 2026-08-06 — All 6 phases delivered. 26 tests passing.*
