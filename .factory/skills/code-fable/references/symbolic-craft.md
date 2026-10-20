# Symbolic Craft & Narrative Architecture for Code Fables

## 1. Why `AGENTS.md`, `SPEC.md`, `FILETREE.md`, and Test Results Lose the Soul

A codebase can have exhaustive specifications, passing test suites, clean file trees, and agent handoff docs—and still be **meaningless** to the next intelligence (or human) that enters it.

Technical artifacts record *what currently sits on disk*. They erase:
- **The Unwritten Story**: Why this repository had to exist when five other systems already existed.
- **The False Mask**: What the system pretends to be on its surface (`mcp_server.py`, a webview runner, a token search loop) versus the creature it is quietly becoming underneath.
- **The Expensive Lesson**: The ritual that failed (like May's "Turbo Loop" burning 28% of calls on ceremony with 0.04% reflection, or Fabric scoring 0.19 recall when misapplied as a candidate generator).
- **The Maker's Corrections**: The moments where Daeron intervened—often in all-caps or mid-session pivots—because agents kept reducing a living evolutionary experiment into a generic software pattern.
- **The Trajectory of Becoming**: Where the organism is heading once its scaffolding falls away.

A Code Fable recovers the **Soul**: the causal, symbolic, and human memory that makes the technical architecture inevitable.

---

## 2. The Two Modes of Fable Creation

### Mode 1: The Memory Weaver (Deep-Research / Data-Agent Over Memories)
When operating in Cloud / Deep-Research mode (with external web search and shallow code-grep turned off or subordinated), you are a **Data-Agent over the memories of the code**:
1. **Mine the Lived Record**: Traverse conversation memories, historical notes, corrections, abandoned names, design debates, and explicit user statements.
2. **Hunt for the "Rosetta Stone" Quotes**: Look for the raw, unpolished sentences where the maker states the real motive (*"simply now wanted it for the data flywheel"*, *"store the fish"*, *"our absolute most deadly sniper yet"*, *"NOW cherry_ttt, BOOOM we now have Continuum"*).
3. **Trace Name Migrations as Architectural Revelations**: When a name changes—or gets given back—never treat it as indecision. Treat it as the moment the maker discovered what the word actually belonged to.
4. **Recover the Ten-Month Arc**: Treat the work as part of a living, continuous experiment between a human architect and agent collaborators—where the constant danger is agents getting lost in *"verify, verify, verify"* and forgetting why the machine exists.

### Mode 2: The Codebase Strengthener (Local / Codex Mode)
When strengthening an existing fable in [`../fables/`](../fables/) or writing a new fable directly from a local repository:
1. **Never Flatten a Fable into a Spec**: Code verification is your **silent foundation**, never your prose style. Do not dump `p95` benchmark tables, filetree lists, or vNext feature tickets into the fable.
2. **Use Code to Sharpen the Symbol**: When you inspect `mcp_server.py`, `.grave/`, `FabricCommitSink`, or `data/`, look for the *structural behavior* in the code that proves and deepens the symbol (e.g., seeing that raw output is captured before display projection in `mcp_server.py` gives birth to the law: *"the user may receive the story; the learner must receive the evidence"*).
3. **Store and Maintain in `fables/`**: Every major codebase gets one canonical Fable preserved in [`../fables/`](../fables/). When strengthening a fable, preserve its mythic voice and symbolic spine at all costs.

---

## 3. The Four Laws of Fable Symbolism

### Law I: Every Symbol Must Do Causal Work
Do not decorate technical nouns with random fantasy words. A symbol belongs in a fable only when it **explains a relationship that technical jargon obscures**:
- **The Mask vs. The Creature Underneath** (`muadib-fable.md`): Explains why standardizing an external protocol (MCP) actually *frees* the internal architecture to become non-standard.
- **The Mill Built Before the River** (`muadib-fable.md`): Explains why code written in one era only becomes meaningful when a continuous stream of lived experience flows through it later.
- **The School vs. The Graduate** (`muadib-fable.md`): Explains why a model trained on a specific tool dialect (`bb7_`) is meant to outgrow the dialect it learned in.
- **Dreams vs. Memory** (`muadib-fable.md`): Explains why synthetic self-play and real-world trajectories must share an ontology without polluting the same historical ledger.

### Law II: Let Symbols Evolve Across Chapters
A static metaphor is just a label. A living symbol transforms as the codebase matures:
- In Chapter 1, the system is a **gate** built for a new road.
- In Chapter 2, the gate becomes a **mummer's mask**.
- In Chapter 3, the router inside the gate is revealed as a **larval form**.
- In Chapter 5, when the surrounding harness takes over the city's bureaucracy, the creature sheds its shell and becomes **the sniper**.

### Law III: Never Audit or Decode Your Own Symbols
Never add a section at the end saying *"In this fable, the river represents `data/` and the gate represents `mcp_server.py`."* (The fatal mistake of `Plot-Fable.md`). Make the connection unmistakable inside the narrative moment when the symbol is introduced, and then trust the symbol to carry the weight.

### Law IV: Crystallize into Parable at the Threshold
Follow the structural climax of [`muadib-fable.md`](../fables/muadib-fable.md#L682-L784) (`## The thing to remember before the evolution`):
- After walking through the real dates, corrections, failures, and architectural turns, gather the entire history into a short, timeless parable (*"A man built a gate because a new road appeared..."*) where every component appears in its true symbolic role.
- Follow the parable with the **Single Governing Question**—the one proposition that the entire multi-month experiment is trying to prove.

---

## 4. Cadence, Voice, and Prose Craft

1. **Address the Maker Directly (`you`, `Daeron`)**:
   Write as an intimate, clear-eyed chronicler speaking directly to the builder—reminding him of what he built, what he corrected, and what he discovered. Avoid cold third-person academic prose (`Plot-Fable.md`), and avoid cheesy fictional roleplay (`continuum-fable.md`).
2. **Breathe in Real Paragraphs, Not Staccato One-Liners**:
   Vary your rhythm. Use short, punchy lines *only* for a sudden turn or revelation—after building pressure through full, textured paragraphs. Never stack thirty one-sentence lines in a row.
3. **Prose Over ASCII Diagrams**:
   Never use fenced `text` blocks full of ASCII boxes and arrows (`--->`, `┌───┐`). If a flow matters (*intent → state → choice → tool → arguments → observation → failure → recovery → consequence*), write it as a rhythmic sentence inside the prose.
4. **Weave Questions into Scenes, Never FAQs**:
   If the prompt includes ten technical or philosophical questions, dissolve them into the chapters where they naturally arise. Never write `### Can X do Y?` followed by `**Yes. Absolutely.**`
5. **End on the Threshold, Not a Ticket Backlog**:
   Close on the philosophical and architectural threshold that the system has now earned the right to approach—never a numbered vNext engineering todo list.
