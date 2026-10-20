# AGENTS.md — Agent Context & Operational Protocol for Academic Whitepaper Engine v4

## Executive Overview

This repository provides an **academic whitepaper workflow engine and standalone publication toolkit**. 

> **ENGINE NATURE:** This codebase is an active **State Machine Workflow**, not a passive reference skill. When invoked for a whitepaper session, AI agents (AGY/Antigravity, Codex, Claude Code, OpenCode, Hermes, etc.) MUST adopt this workflow and remain locked into its state-machine progression (`whitepaper/state/tasklist.json`) across the entire session.

---

## Workspace & State Scoping

- **Engine Location:** The engine files (`SKILL.md`, `AGENTS.md`, `scripts/`, `templates/`, `references/`) reside in global/shared directories or the engine home repository.
- **Project Location:** Individual whitepapers, manuscript drafts, compiled PDFs, and active session states (`whitepaper/state/`) are maintained **per codebase / per project repository**.

---

## State Machine Persistence & Anti-Degradation Checklist

To prevent AI models from silently context-degrading, dropping requirements, or losing authorial cadence over long sessions, all agents MUST enforce the following state-checking protocol:

1. **Re-hydration on Turn Start:** At the beginning of every major task or turn, check `whitepaper/state/tasklist.json` and `whitepaper/state/session.json`.
2. **Sequential Gating:** Do not skip states (e.g., drafting before claim ledger, or compilation before editorial passes).
3. **Explicit Task Check-off:** Mark completed items in `tasklist.json` as work progresses.

---

## Codebase Architecture Policy

The repository operates under a **Dual Architecture**:

1. **Portable Scripts (`scripts/`):** Self-contained, single-file CLI utilities that rely only on standard library or explicitly declared pip packages. They do NOT require imports from sibling scripts.
2. **Core Engine Package (`whitepaper_engine/`):** Modular Python package components for complex manuscript compilation, claim verification, and TeX transcreation.

---

## Current Tool Registry

| Tool Path | Purpose | Execution Command | Authorization Policy |
|-----------|---------|-------------------|----------------------|
| `scripts/md2tex.py` | Markdown → LuaLaTeX Transcreation Engine | `python scripts/md2tex.py manuscript.md` | Standard pipeline step |
| `scripts/sart.py` | Symbol Ontology & Equation Coherence Engine | `python scripts/sart.py scan` | Standard pipeline step |
| `scripts/generate_metadata.py` | DOI & Document Metadata Generator | `python scripts/generate_metadata.py` | Standard pipeline step |
| `scripts/batch_manager.py` | Multi-section Batch Document Processor | `python scripts/batch_manager.py` | Standard pipeline step |
| `scripts/pdf_to_markdown_converter.py` | PDF-to-Markdown Extraction | `python scripts/pdf_to_markdown_converter.py input.pdf` | Ingestion step |
| `scripts/pdf_ocr_scanner.py` | Scanned PDF OCR Scanner | `python scripts/pdf_ocr_scanner.py input.pdf` | Ingestion step |
| `scripts/cleaner.py` | Comprehensive AI Artifact & Metadata Stripper | `python scripts/cleaner.py file.pdf` | **MANUAL AUTHOR ONLY** (Requires explicit user command) |
| `hash-index.ps1` | Cryptographic Provenance Indexer | `.\hash-index.ps1 -Path .` | Verification step |

> [!CAUTION]
> **STRICT CLEANER SAFETY RULE:**
> `scripts/cleaner.py` MUST NEVER be invoked automatically in background tasks, automated build scripts, or routine cleanup passes. Because it performs deep, aggressive character and metadata stripping, running it without explicit user targeting can mangle PNG binaries and non-text assets. **Only run `scripts/cleaner.py` when explicitly instructed by Daeron / the user.**

---

## Canonical Build Regime

All agents MUST enforce the single unified TeX build chain:

```text
Markdown Source (src/sections/) 
  ──> controlled Pandoc AST / scripts/md2tex.py 
  ──> LuaLaTeX .tex Source 
  ──> biblatex + biber 
  ──> LuaLaTeX Passes (x2) 
  ──> Validated Output PDF (output/whitepaper.pdf)
```

- **TeX Engine:** `LuaLaTeX`
- **Bibliography Engine:** `biblatex` with `biber`
- **Build Automation:** `latexmk -lualatex`
- **Math/Fonts:** `fontspec` + `unicode-math` (Direct UTF-8 math rendering)

---

## Collaboration Guidelines

When contributing to or executing work in this repository:
1. Maintain standalone execution for scripts in `scripts/`.
2. Do not insert dynamic import-time `pip install` calls.
3. Validate changes with test suites under `tests/` before committing.
4. Keep `AGENTS.md` and `SKILL.md` aligned with current tool capabilities.

---

*Last updated: 2026-08-06 (v4 Hardened State Machine Specification)*
