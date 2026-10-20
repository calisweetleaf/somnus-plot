# The Fable Canon: Gold Standard Architecture & Anti-Patterns to Forbid

This skill stores its living fables in [`../fables/`](../fables/). All three fables in [`../fables/`](../fables/) now stand at `[GOLD / CLEAN]` calibration, while the lessons from repairing the original raw drafts of `continuum-fable.md` and `Plot-Fable.md` are preserved below so no agent ever has to repair a newly written fable again.

| Fable | File | Central Myth & Symbols |
|---|---|---|
| **1. Muad'Dib** | [`fables/muadib-fable.md`](../fables/muadib-fable.md) | **The Mummer's Farce & The River**: Two births (Nov 25, 2024 vs Jan 1, 2026), MCP as the costume, `/data` as the river under the house, Larval Router → Adult Animal → Sniper, the Gate and the Sand. |
| **2. Continuum** | [`fables/continuum-fable.md`](../fables/continuum-fable.md) | **The Loom of Unchosen Worlds**: Why `cherry_ttt` had to give its second name back; the Equalizer as Dyson sphere and Fabric as the sun; the `0.19` recall boundary; LLVM-for-tools; possessing futures vs. buying FLOPs; how search and internalization breathe. |
| **3. Plot** | [`fables/Plot-Fable.md`](../fables/Plot-Fable.md) | **The Acre Outside the Kingdom**: The unassigned laboratory lightning rod; Obsidian as the distant mountain; the window vs. the house; `.grave/` as the soil where summoned things outlive the dying hand; the First Flash and the 6ms bell. |

---

## 1. Why `fables/muadib-fable.md` Struck Gold

### A. The Chronicler-to-Maker Voice
Look at the opening of [`muadib-fable.md`](../fables/muadib-fable.md#L1-L29):
> *There are two dates that matter in this story, Daeron.*
> *The first is **November 25, 2024**...*
> *The second birth is **January 1, 2026**...*
> *And your June correction tells us **why you brought the old server back**:*
> *> you "simply now wanted it for the data flywheel."*
> *That sentence is the Rosetta Stone.*

Why this works:
- It speaks **directly to the maker (`you`, `Daeron`)** as a witness who has walked through the memories of the work.
- It treats the maker's frustrations—like writing an all-caps correction because agents kept getting the timeline wrong—not as metadata to hide, but as **narrative pressure**.
- It hunts for **Rosetta Stone sentences** from the maker's own mouth (*"simply now wanted it for the data flywheel"*, *"store the fish"*, *"our absolute most deadly sniper yet"*) and builds the chapters around those revelations.

### B. Load-Bearing Symbolism (Metaphors That Explain Architecture)
In `muadib-fable.md`, symbols are never decorative adjectives glued onto a spec. Every symbol resolves a deep architectural misunderstanding:
- **The Two Births / The Mill and the River**: Explains why a 2025 tool server (`mcp_server.py`) was resurrected in January 2026 without changing its outer concept: *"You had already built the mill in 2025. In January 2026, you finally found the river."*
- **The Mummer's Farce / The Mask**: Explains how the system can simultaneously widen its MCP compatibility in May while declaring *"This is NOT an MCP server"*: *"The better the mask became, the freer the creature underneath it was to evolve."*
- **Biological Metamorphosis (Larval Router → Adult Animal → Sniper)**: Traces the 10-month arc not as a changelog of features, but as the organism discovering what kind of creature it was—shedding bureaucratic city-management (absorbed by ASPS, Omnibus, Golden Path) to become a pure neural weapon.
- **The River Under the House (`data/`)**: Explains why `/data` is not a log directory and why agents are merely *"inhabitants of the river... not what makes the river exist."*
- **The School vs. The Graduate**: Explains why distilling Codex sessions is not about cloning a cheap coding model or memorizing `bb7_` tool names: *"The school begins with BB7 vocabulary. The graduate is not supposed to speak BB7."*
- **Siblings, Not Twins (Dreams vs. Memory)**: Explains why self-play and RFT share the same action universe while remaining strictly separated in `/data`: *"That separation is what prevents the organism from eventually believing its own dreams are historical facts."*

### C. Dissolving the "Bullet Storm" into Narrative
When the user asks a dozen scattered questions about tool counts (115 vs 110 vs 120 vs 147 vs 265), acronyms (`BB7`), execution boundaries, and training loops, `muadib-fable.md` **never creates an FAQ section**. It answers every question inside the dramatic turn where that question matters.

### D. The Parable Crystallization
In [`## The thing to remember before the evolution`](../fables/muadib-fable.md#L682-L784), the fable steps back into pure mythic compression:
> *A man built a gate because a new road appeared...*
> *BB7 was the language painted on the signposts.*
> *Lisan was the cartographer.*
> *The exoskeleton was the old machinery that compared paths.*
> *Muad'Dib was the part learning the shape of the desert.*
> *And `data/` was the sand remembering every footstep.*

It only delivers this parable *after* the preceding chapters have earned every single symbol in it.

---

## 2. What Went Wrong in `fables/continuum-fable.md` (The Sloppy Drift)

`continuum-fable.md` has real moments of brilliance (the heresy of changing what a state means in MCTS; Why Continuum had to be given back; the difference between thinking longer vs. possessing more futures). Yet it breaks the spell in four specific ways:

1. **Meta-Methodology Opening Disclaimer**:
   Lines 3–5 open with a meta-note explaining that the text is obeying the prompt (`That is also the rule your own code-fable methodology asks for...`). **Rule:** Never mention the skill, the methodology, or the prompt inside the fable.
2. **Contrived Cinematic Props**:
   Lines 9–13 and 1315–1318 invent stage props (`Terminal light in the glasses. A pipe or cigar going cold...`, `So, old man, put the glasses back on.`). **Rule:** Never invent fake movie-scene props when the real emotional history of the maker and his machines is already rich.
3. **ASCII Flowchart Bloat**:
   Contains 17 fenced `text` blocks drawing boxes and arrows (`state + next_token -> new_state`, `FABRIC -> cherry_ttt -> REAL EFFECT`). **Rule:** A fable is prose, not a terminal diagram. If a transition or hierarchy matters, make the reader *see* it through imagery and sentence structure, not ASCII boxes.
4. **The Literal FAQ Breakdown**:
   Lines 1047–1274 abandon narrative entirely and become an engineering FAQ with literal question headers (`### Can a model be trained separately and then combined with cherry_ttt?`, `### Can Fabric be trained separately?`, `### Must a system be trained and deployed with Continuum?`). **Rule:** Never use Q&A subheaders. Weave the answers into the story of the architecture's evolution.

---

## 3. What Went Wrong in `fables/Plot-Fable.md` (The Spec-Audit Collapse)

By the third fable, the agent surrendered completely to the "verify, verify, verify" technical reflex:

1. **Cold Third-Person Detachment**:
   Refers to the maker in the third person (`because Daeron has now stated it plainly`) as if filing an external compliance report.
2. **Staccato One-Sentence Paragraph Disease**:
   Hundreds of consecutive one-sentence paragraphs that read like bullet points with the bullets deleted:
   > *The process dies.*
   > *The material remains.*
   > *Another process comes.*
3. **Explaining the Metaphors in an Audit Section (`## The Stones Beneath the Fable`)**:
   Line 669 literally writes:
   > *The supplied fable-writing method was also respected as an architectural constraint rather than decorative style: the symbols correspond to actual mechanisms. The acre is the deliberately non-core test system. The mountain is scale without inheritance. The grave is `.grave/`...*
   **Rule:** Explaining your symbols in an audit note murders them. If the story did its job, the reader already knows what the acre, the mountain, and the grave are.
4. **Ending with a v0.7 Feature Backlog (`## The Seventh Flash`)**:
   Lines 681–905 turn into a six-part engineering spec (`The first v0.7 instrument should be...`, `The second v0.7 acceleration should be...`, `The fifth acceleration should move the six millisecond bell...`). **Rule:** A fable ends on a threshold of meaning and destiny, never a numbered backlog of vNext feature tickets.
