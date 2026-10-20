# Architecture Template and Realization

This pair defines the current architecture-doc example for the skill. The template provides the requested structure. The completed document demonstrates how a real project can give that structure a more elaborate visual and evidentiary treatment.

## The two roles

- [`ARCHITECTURE_template.md`](../../ARCHITECTURE_template.md) provides an architecture outline: executive summary, system flow, technical innovations, component breakdown, data structures, integration challenges, operational hazards, and roadmap. It is a starting shape, not a word-count target or final size.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) is a long-form architecture whitepaper for Sacred Timeline Substrate. At 1,846 lines, it preserves the template's core sections and adds detail needed by its codebase. Length is a consequence of the subject and evidence, not a requirement for other docs.

## How the realization grows from the outline

| Template section | Realization | What the added layer does |
| --- | --- | --- |
| Executive summary | Section 1, with intent, governing logic, and claim boundary | Opens with a strong project voice while limiting what the sign-off claims. |
| System flow | Section 2, with Mermaid flow, phases, accept/reject behavior, and source references | Makes the data lifecycle navigable and then explains each phase in prose. |
| Core innovations | Section 3, with six technical mechanisms | Connects design decisions to measurements, tests, source excerpts, and current boundaries. |
| Component breakdown | Section 4 component catalog | Pairs named modules with a custom axis-identity SVG and codebase-specific ownership. |
| Data structures and schemas | Section 5, with ontology, on-disk schemas, relationships, and examples | Moves from a broad category to concrete definitions. |
| Integration challenges | Section 6 | Preserves the template's concern while using project-specific facts. |
| Operational hazards | Section 7 | Describes real failure patterns and handling. |
| Roadmap | Section 10, with immediate work and explicit non-goals | Keeps future state distinct from implemented behavior. |

The realization adds security and threat considerations, validation, a glossary, a GitHub render contract, trust zones, class and state contracts, source contracts, packet-local evidence, lift-out and operation guidance, hard bans, open questions, registries, and a change log. Those additions answer questions raised by the specific implementation; they are not required headings for every architecture document.

The supplemental “Field Geometry — Second Pass” section follows the numbered core sections and change log, as section 23. Keep supplemental placement and numbering tied to the source document's actual revision history. Do not make it a template rule.

## Visual grammar in the completed document

The completed architecture uses a codebase-specific visual system:

- A large, authored SVG identity banner with project title, scope cues, version, and a repository-specific plum/magenta atmosphere.
- Meaningful plane and status badges, followed by a narrow SVG sign-off strip.
- A long contents list that exposes both the main architecture and supplemental sections.
- A project-local evidence vocabulary: `CONFIRMED`, `TARGET`, `INFERRED`, `HISTORY`, and `NOT VERIFIABLE`.
- Mermaid for lifecycle, state, and dependency relationships.
- Tables for status definitions, ownership, schemas, source positions, threat mapping, runner results, measurements, invariants, and error registries.
- Code excerpts that retain ordinary fenced blocks, sometimes preceded by a small inline-styled source-path and language label.
- Authored SVGs for project-specific conceptual views and inline HTML panels for actual test-log excerpts.
- Prose with a clear authorial point of view, placed beside code and evidence rather than replaced by them.
- A closing assessment that restates scope and limits.

The document does not wrap every inline example or diagram in a terminal frame. Prose, Mermaid, SVG, Markdown tables, and occasional styled panels share the page. Use a visual device where it fits the content.

## Transferable rules

1. Preserve the user-selected template's core order and purpose.
2. Add visual hierarchy without flattening the technical depth or trimming to an arbitrary length.
3. Expand sections with evidence and source-backed detail when they answer reader questions.
4. Keep repository-specific status labels, palette, logos, metaphors, and rendering choices local.
5. Distinguish current implementation from target design, inference, history, and unknowns.
6. Use enhanced HTML or SVG only within the target repository's rendering contract; retain accessible text and review the exact output.
7. Treat the document's own “GitHub render contract” as an example-specific claim to verify in that repository, not as a universal compatibility guarantee.

For future examples such as the user's Full Reinforcement Learning Pipeline README, add the original file to `references/` and extend this case study only after the example is supplied.

## Next state

Return to S2 with the template's section order fixed and a list of additions justified by the target codebase's evidence. Use the [scope note's section map](README.md#section-map) for any excerpt you still need.
