# Code-Fable Mini-Harness Workflows

This directory (`/home/daeron/.codex/skills/custom/code-fable`) is an **agent-agnostic, portable mini-harness**. It can be zipped and handed to any agent environment (ChatGPT, Claude, Gemini, Codex, or local CLI) to craft, inspect, refine, and curate Scrolls for the **Book of Somnus**.

> [!IMPORTANT]
> **When to Use (and When NOT to Use):**
> - **Only for Systems with Lived History**: Never generate a Fable for a brand-new codebase that has no history, scars, or evolution.
> - **Never as a Coding Regression Gate**: Do not load or enforce Fables during ordinary coding/testing tasks unless Daeron explicitly requests it.

---

## Workflow 1: Cloud Deep-Research Scroll Brief (`brief`)

When you want ChatGPT (with Deep Research enabled and web/code search restricted so it acts purely as a **Data-Agent over the memories of the work**) to write a new Scroll:

```bash
python3 scripts/fable_harness.py brief "ProjectName" \
  --subtitle "The hidden question or subtitle" \
  --questions "Why did it start?,What changed in month X?,Why was Y renamed?"
```

What this does:
- Generates a self-contained **Deep-Research Scroll Prompt** infused with the **Scroll Mind** rules ([`reverend-mother-cognition.md`](reverend-mother-cognition.md)), woven epigraph requirements, and anti-LLM-tell guards.
- Forces the cloud model to mine conversational memory for dates, corrections, Rosetta Stone quotes, and failed rituals, while forbidding ASCII diagrams, FAQ headers, negative-contrast spam, and spec-sheet prose.

---

## Workflow 2: Voice & Literary Gravity Audit (`lint`)

Whenever a Scroll is drafted in the cloud or refined locally, run the harness linter before accepting it into [`../fables/`](../fables/):

```bash
python3 scripts/fable_harness.py lint --all
# or on a single scroll:
python3 scripts/fable_harness.py lint fables/muadib-fable.md
```

What the linter checks:
1. **Woven Scroll Epigraphs**: Verifies that movements open with italicized scroll epigraphs (`> *...*`) so the symbolic stratum breathes throughout the piece rather than only at the end.
2. **Chronicler Intimacy**: Ensures direct second-person witness (`you` / `your`, speaking to `Daeron`).
3. **LLM-Tell Detection**:
   - Flags **Negative-Contrast Crutch** clusters (`Not X. Not Y. Not Z.`).
   - Flags **Throat-Clearing Meta-Phrases** (`Here is the single most important`, `That distinction matters`, `Read that again`).
   - Flags **Benchmark Decimal Clutter** in prose (`4.066 milliseconds`).
   - Flags **Staccato One-Line Paragraph Runs**.
4. **Structural Purity**: Zero ASCII diagrams/code blocks, zero FAQ question headings (`### ...?`), zero fourth-wall methodology disclaimers, and zero vNext roadmap checklists.
5. **Voice Gravity Score (0–100)**: Computes an overall literary integrity score.

---

## Workflow 3: Inspect the Archive & Compile the Book of Somnus (`status` / `book`)

To inspect all Scrolls currently preserved in [`../fables/`](../fables/):

```bash
python3 scripts/fable_harness.py status
```

To compile all Scrolls into a single unified **Book of Somnus** volume (with an automatic Table of Scrolls, opening epigraph index, and Governing Questions ledger):

```bash
python3 scripts/fable_harness.py book --output BOOK_OF_SOMNUS.md
```

---

## Workflow 4: Package Portable Mini-Harness (`package`)

To bundle this entire mini-harness (`SKILL.md`, `references/`, `scripts/`, and `fables/`) into a clean `.zip` archive ready to upload to any cloud agent or move across machines:

```bash
python3 scripts/fable_harness.py package
```
