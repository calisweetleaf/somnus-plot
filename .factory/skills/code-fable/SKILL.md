---
name: write-code-fables
description: Portable mini-harness for crafting, auditing, and curating Code Fable Scrolls for the Book of Somnus. Use ONLY when the user explicitly asks to write, refine, or inspect a Fable for a work that has accumulated real lived history. Never use Fables as mandatory regression constraints or coding specifications during ordinary software development.
---

# Write Code Fables (Book of Somnus Mini-Harness)

> *Code is shed like skin. Languages, file trees, and function signatures are temporary vessels. What endures in the archive is why the vessel had to be shaped that way, what mask it wore to enter the world, which rituals failed, and what law of intelligence the experiment uncovered.*

---

## 0. Constitutional Boundaries (Read First)

1. **No History, No Fable**:
   Never fabricate a Fable for a greenfield idea or a codebase that has no lived history, scars, corrections, or conceptual turns. Until a work has lived through time, it has no Fable.
2. **We Care About the History, Not the Code**:
   `AGENTS.md`, `SPEC.md`, `FILETREE.md`, and test suites describe what sits on disk today. A Fable records the **Soul**—the human and causal evolution across time.
3. **Never a Coding Regression Gate**:
   These Fables are **Scrolls toward the Book of Somnus**. Do **not** treat them as technical specifications, regression checklists, or rules that must be obeyed while coding unless Daeron explicitly tells you to consult a Fable.

---

## 1. Portable Mini-Harness Architecture

This directory is an **agent-agnostic mini-harness** designed to be zipped and handed to any agent (ChatGPT in Cloud Deep-Research, Codex locally, Claude, Gemini) or driven from the CLI:

- **[`scripts/fable_harness.py`](scripts/fable_harness.py)** — Unified mini-harness CLI (`status`, `lint`, `brief`, `book`, `package`) and its wrapper [`scripts/fable_lint.py`](scripts/fable_lint.py):
  - `python3 scripts/fable_harness.py status` — Inspect all Scrolls in [`fables/`](fables/), their word counts, movements, woven epigraphs, and **Voice Gravity (0–100)** scores.
  - `python3 scripts/fable_harness.py lint --all` — Run the literary & anti-LLM-tell audit across Scrolls.
  - `python3 scripts/fable_harness.py brief "ProjectName" --questions "..."` — Generate a self-contained **Cloud Deep-Research Scroll Brief** to force ChatGPT into the *Data-Agent over Memory* posture.
  - `python3 scripts/fable_harness.py book [--output BOOK_OF_SOMNUS.md]` — Compile all Scrolls into the unified **Book of Somnus**.
  - `python3 scripts/fable_harness.py package` — Bundle this entire mini-harness into a clean `.zip` to hand to any agent.
- **[`references/`](references/)** — The cognitive and literary engine (read before drafting or refining any Scroll):
  - **[`references/reverend-mother-cognition.md`](references/reverend-mother-cognition.md)** — **The Scroll Mind**: Truthsense (separating the outer mask from the inner hunger), the scrutiny of failed rituals, the ontology of true names, woven epigraph structure, and the ban on cheap AI-essay tells.
  - **[`references/symbolic-craft.md`](references/symbolic-craft.md)** — The Four Laws of Fable Symbolism and the two operating modes (Cloud Memory Weaver vs. Local Scroll Refiner).
  - **[`references/canon-and-anti-patterns.md`](references/canon-and-anti-patterns.md)** — The Scroll Archive index and the forbidden drift patterns.
  - **[`references/workflows.md`](references/workflows.md)** — Quick-reference CLI and agent workflows.
- **[`fables/`](fables/)** — The living Scroll Archive (`100/100 SCROLL PURE` calibration):
  - **[`fables/muadib-fable.md`](fables/muadib-fable.md)** — *Muad’Dib and the Mummer’s Farce* (7 movements, 7 woven epigraphs).
  - **[`fables/continuum-fable.md`](fables/continuum-fable.md)** — *Continuum and the Loom of Unchosen Worlds* (9 movements, 9 woven epigraphs).
  - **[`fables/Plot-Fable.md`](fables/Plot-Fable.md)** — *Plot and the Acre Outside the Kingdom* (5 movements, 5 woven epigraphs).

---

## 2. The Cognitive Posture: The Scroll Chronicler

Do not write like a software marketer, an academic auditor, or an LLM trying to sound dramatic. Inhabit the discipline of a **long-memory archivist** recording a Scroll—never roleplaying or name-dropping fiction, but embodying the thought process:

1. **Practice Truthsense (The Mask vs. The Hunger)**:
   Look past the outer costume a system wore so the world would accept it (`MCP`, a token search package, a tiny runner) and identify the real operational hunger that caused the builder to create or resurrect it. Anchor that turn in the builder's exact **Rosetta Stone quote** (*"simply now wanted it for the data flywheel"*, *"NOW cherry_ttt, BOOOM we now have Continuum"*).
2. **Honor the Failed Rituals**:
   Record where ceremony or misapplied abstraction failed empirically (May's Turbo Loop consuming 28% of calls with 0.04% reflection; Fabric scoring 0.19 recall as a candidate proposer; spending 1.5 seconds deliberating over a 1-millisecond write). A disproven illusion is a sacred boundary marker.
3. **Trace Name Migrations as Discovery**:
   When a name changes or is given back, never treat it as indecision; show how the true boundary of the concept finally became visible. Never invent false acronym expansions.
4. **Speak Directly to the Maker (`you`, `Daeron`)**:
   Write as a clear-eyed witness addressing the builder directly—with austere, unhurried, diamond-hard gravity.

---

## 3. Structural & Literary Laws of Every Scroll

1. **Woven Chapter Epigraphs**:
   Every major movement (`## Heading`) must open with a 1–3 sentence italicized blockquote epigraph (`> *...*`) that distills the timeless symbolic law of that movement before the historical narrative unfolds. Do not quarantine the fable to the final 50 lines; let the symbolic stratum breathe from the first movement to the last.
2. **Dissolve All Questions into Narrative**:
   Weave every question and historical distinction seamlessly into the chronological scenes. Never use `### Question?` FAQ headers.
3. **The Closing Parable & Single Governing Question**:
   In the final movement (`## The thing to remember before the evolution`), gather the symbols from the chapter epigraphs into one complete parable, followed by a blockquote synthesis of the arc and the **Single Governing Question** that the entire history was built to ask.
4. **Ban the Five "Cheap Agent" Tells**:
   - **Zero ASCII diagrams or fenced code blocks.**
   - **Zero Negative-Contrast Crutch** (do not stack `"Not X. Not Y. Not Z."` fragments).
   - **Zero Throat-Clearing Announcements** (never write `"Here is the single most important thing"` or `"That distinction matters"`).
   - **Zero Benchmark Decimal Clutter** in prose (say *"inside four thousandths of a second—beneath the six-millisecond bell"*, never `"reaches a p95 of approximately 4.066 milliseconds"`).
   - **Zero Staccato One-Line Slide Decks** (write full, breathing paragraphs of 3–6 sentences).

---

## 4. Verify with the Mini-Harness

Before finishing any Scroll work, run:

```bash
python3 scripts/fable_harness.py lint --all
```

Every Scroll in [`fables/`](fables/) must score **`100/100 [SCROLL PURE (GOLD)]`**.
