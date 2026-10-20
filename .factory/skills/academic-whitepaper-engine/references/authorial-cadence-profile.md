# Authorial Cadence Profile — Daeron / Somnus Sovereign Systems

This document captures the measurable and semantic features of Daeron's writing style for use by the anti-genericity reviewer and editorial pass engines.

---

## 1. Argument Movement

Daeron's papers follow a specific intellectual sequence that differs from the standard model-generated pattern:

### Canonical Sequence
1. **Establish the exact object** under investigation — not a broad field survey.
2. **Identify the regime** under which existing terminology becomes insufficient.
3. **Define the new object** without inflating the claim — what it is, then what it is not.
4. **Expose mechanism or architecture** before celebrating implications.
5. **Formalize selectively** — only the parts that benefit from formalization.
6. **Separate behavioral categories:** implemented behavior, measured behavior, architectural intention, and future extension.
7. **Return to the opening problem** with a narrower but stronger conclusion.

### Anti-Pattern (Generic Model Output)
```
broad historical introduction
→ generic gap statement
→ list of contributions
→ architecture description
→ optimistic conclusion
```

---

## 2. Sentence Cadence

### Length Distribution
- **Mean sentence length:** 18–26 words (varies by section type)
- **Standard deviation:** ≥ 8 words (high variance is a signature)
- **Short terminal sentences:** Frequently used after complex compound sentences to create punctuation rhythm
- **Maximum sentence length:** Up to 50–60 words in mechanism-describing passages
- **Minimum sentence length:** 3–8 word declarative anchors

### Structural Patterns
- **Ratio of simple to compound sentences:** approximately 1:2
- **Recursively qualified sentences:** common — subordinate clauses that refine the main assertion
- **Thesis reversals:** appear within paragraphs, not just between sections
- **Colon usage:** introduces elaboration or specification (not mere listing)
- **Semicolon usage:** joins related independent clauses that share conceptual weight
- **Parenthetical asides:** used for scope-narrowing or qualification, not decoration
- **Short terminal anchors:** "This is the constraint." / "That distinction matters." / "The mechanism is recursive."

---

## 3. Paragraph Architecture

- **Mean paragraph length:** 4–7 sentences
- **First sentence function:** typically states the paragraph's thesis or introduces the object
- **Last sentence function:** either a short anchor, a transition hook, or a qualification
- **Internal structure:** claim → mechanism → evidence → scope boundary
- **No uniform paragraph lengths:** variation signals intentional pacing

---

## 4. Transition Vocabulary

### Permitted Transitions
- Structural markers: "The question then becomes," "This leads to," "What remains is"
- Contrastive: "However," "But this assumes," "The distinction is"
- Consequential: "The result is," "This means," "Therefore" (used sparingly)
- Temporal/procedural: "First," "Then," "Before that,"

### Forbidden Transitions (AI Fingerprints)
- "Furthermore," "Moreover," "Additionally," "Delving deeper"
- "It is worth noting," "Notably," "Importantly,"
- "In this context," "This highlights," "This underscores"
- "plays a crucial role," "a testament to," "the intricacies of"
- "a comprehensive," "a nuanced," "a holistic"
- "groundbreaking," "cutting-edge," "game-changing," "paradigm shift"
- "at the heart of," "at its core," "This is not merely"
- "multifaceted," "leverage," "synergy," "tapestry"

---

## 5. Negative-Definition Discipline

Daeron frequently establishes an object by defining **what it is not** before specifying what it is. This technique is used when:

- The new architecture is adjacent to familiar categories and likely to be flattened into them
- An existing term carries connotations that would mislead the reader
- The object's boundary is more informative than its center

### Rules
- Bounded: negative-definition passages should not exceed 3–4 negations
- Non-repetitive: once a distinction is established, do not re-negate it
- Followed by positive definition: the "what it is" must follow promptly

---

## 6. Formalism Placement

> Introduce formal objects at the earliest point where they remove ambiguity from a mechanism, contract, invariant, or claim.

- Equations are **not** decorative and should not precede their motivating mechanism
- Each equation must be followed by an interpretation sentence
- Notation is introduced inline before being used in display math
- Symbolic names carry compressed architecture (e.g., Ψ for state transformation)

---

## 7. Claim Temperature

| Claim Class | Permitted Temperature | Permitted Tense |
|-------------|----------------------|-----------------|
| implemented | cold, measured | present |
| observed | cold, measured | past, present |
| derived | measured | present (logical) |
| interpretive | measured, warm | present |
| hypothesized | warm | conditional, subjunctive |
| planned | measured | future, conditional |
| comparative | measured | present, past |
| historical | cold, measured | past |

### Temperature Violations to Flag
- Planned features described in present tense as if implemented
- Hypothesized mechanisms stated with certainty
- Comparative claims without explicit baseline
- Historical claims without citation

---

## 8. Design Metaphor

The prose should feel like an advanced research artifact — precise, mechanistic, restrained. Not academic-generic, not conversational, not promotional.

The guiding aesthetic: *an alternate 1980s DARPA technical report, reconstructed with modern typography and DeepMind-level information design.*

---

*Profile version: 1.0 — Pending calibration against Daeron-authored whitepaper comparison.*
*Last updated: 2026-08-06*
