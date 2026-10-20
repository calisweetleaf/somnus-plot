---
name: somnus-documentation
description: Create, review, or revise public-facing Markdown documentation for human readers, including README.md, SPEC.md, architecture guides, API references, research notes, and release documents. Use when the content must be evidence-grounded, visually deliberate, distinctive to its codebase, and readable in GitHub.
---

# Somnus Documentation

Treat public documentation as part of the product's interface. Give readers an inviting way into the subject, a clear account of how it works, and useful routes through the details. Let the visual form carry meaning and project identity.

## Scope

Use this skill for reader-facing documentation: project landing pages, specifications, architecture whitepapers, API guides, field guides, research and evaluation records, release notes, migration guides, and related Markdown.

Do not use it to design agent operating context such as `AGENTS.md`, `MEMORY.md`, agent skills, system prompts, or private handoff files. The Somnus metadata system is separate and outside this skill; do not inspect, define, or modify its schema as part of a documentation styling task.

## Design contract

- Match the repository's own voice and visual identity. Each codebase keeps its distinct atmosphere; do not import another project's palette, logo, banner, motifs, or layout as a default.
- Treat supplied templates as structural guidance when the user says to. A template describes the document's shape, not a final length or limit. Apply the visual layer to that shape and expand explanations, diagrams, evidence, and navigation when the subject calls for them.
- There is no target word count or maximum length. Let the source material and reader's needs determine depth. Do not compress useful detail to make a document shorter; do not add filler to make it longer.
- Prefer grounded, contemporary writing over generic launch copy or synthetic drama. Use first-person technical narrative only when it matches the author's real voice. Do not invent a persona.
- Do not add emoji or AI-generated imagery. Use a logo only when the user supplies an approved asset or explicitly asks for one.
- Treat banners, badges, diagrams, tables, code labels, evidence panels, and terminal frames as available devices, not a mandatory style kit. A terminal frame is optional; ordinary fenced code can be the clearest treatment.
- Keep essential meaning available in Markdown or accessible text. Use HTML, SVG, inline styles, and renderer-specific features when they fit the project's tested rendering contract.

## Work sequence

1. **Read the reader-facing surface.** Inspect the target document, nearby public docs, owned visual assets, user-supplied image references, and source code or tests behind claims. Decide whether each supplied image sets the governing atmosphere, serves a banner or other image role, is an asset to place, or remains unassigned. When evolving this skill, preserve supplied source documents under `references/` and record their role in [source-lineage.md](references/source-lineage.md). For images, record their role and provenance in [visual-reference-roles.md](references/visual-reference-roles.md); do not package unrelated or unapproved third-party imagery as an asset. Use `python3 scripts/doc_profile.py <paths...>` to inventory existing public-doc patterns when it helps. Do not make agent-context files the style target.
2. **Establish the document's job and shape.** Identify the audience, the reader's next decision or action, and the required content. Preserve a supplied template's structure when requested. Use [compositions.md](references/compositions.md) for adaptable structures, not fixed outlines.
3. **Verify every claim.** Check names, paths, commands, compatibility, status, measurements, and links against available evidence. Keep current behavior distinct from proposals, assumptions, and history. Use evidence labels only when the codebase benefits from them; the labels in the architecture example are local to that document.
4. **Apply the visual layer.** Follow [design-schema.md](references/design-schema.md) and the repository's established style. When translating an image or mood, describe its observable visual mechanisms before choosing document treatments. Map every visual device to at least one of the six information jobs: identity, orientation, structure, evidence, use, or wayfinding. Limit assertive decorative or identity imagery to one event per page; functional diagrams and evidence visuals may appear as needed. Never let controlled disclosure hide a fact, caveat, procedure, or evidence the reader needs.
5. **Write to the full depth the subject needs.** A README can be a substantial guided technical walkthrough, not only an installation note. An architecture document may grow far beyond its template when source-backed detail is useful.
6. **Check the actual renderer.** Read [rendering-and-assets.md](references/rendering-and-assets.md) when using HTML, SVG, Mermaid, images, or other enhanced markup. Use GitHub's actual Markdown levers when it is a target; do not claim control over fonts, fixed margins, or CSS spacing unless the chosen renderer supports and verifies them. Inspect a desktop and narrow-width render, then inspect a grayscale copy to confirm that hierarchy and meaning survive without color.
7. **Run the helpers.** Use `python3 scripts/check_docs.py --root <repository-root> <paths...>` for structural and local-reference checks. `SPEC.md` banner failures are errors. Add `--check-external-assets` to review remote or embedded images, and `--check-renderer-features` to surface inline CSS for renderer review. Use `python3 scripts/doc_profile.py <paths...>` to compare the result with existing public docs. Review findings in context; neither script replaces editorial or renderer review.
8. **Read the page as its intended reader.** Confirm the opening explains what the document is, the depth is navigable, examples and claims are real, links and commands work, and styling does not obscure meaning.

## Document-specific requirements

- **`SPEC.md`:** Always begin with a visible identity banner. It may be a text-led Markdown banner or an accessible, project-owned visual treatment. Include the specification's subject and scope; show status or document version only when known. The portable pattern from `scripts/doc_banner.py` is optional, not the required final design.
- **`README.md`:** Make it the project's front door and a working map. Explain what the project is, the problem or purpose it serves, its boundaries or mental model, how its important parts fit, a useful verified route, and where readers can go next. Give the page the depth and narrative progression the project deserves; do not reduce it to a setup card.
- **Architecture documents:** Explain the governing problem, ownership, boundaries, flow, state, contracts, failure behavior, evidence, and operation as relevant. Expand a template with diagrams, source maps, validation, threat views, glossaries, or registers only when supported and useful.
- **Specifications and references:** Make terms, contracts, constraints, examples, status, and lookup paths precise. Distinguish normative rules from rationale, implementation, and proposal.
- **Research, evaluation, release, and migration documents:** Preserve methods, measurements, limitations, user impact, required actions, and recovery paths as appropriate. Do not turn raw data into slogans.

## References

| Need | Read |
| --- | --- |
| Core visual and editorial grammar | [design-schema.md](references/design-schema.md) |
| Adaptable document shapes | [compositions.md](references/compositions.md) |
| GitHub, HTML, SVG, Mermaid, and assets | [rendering-and-assets.md](references/rendering-and-assets.md) |
| How the design sources relate | [source-lineage.md](references/source-lineage.md) |
| GitHub-native monochrome README example and its fixture assumptions | [examples/monochrome/README.md](references/examples/monochrome/README.md) and [fixture-source.md](references/examples/monochrome/fixture-source.md) |
| Architecture template versus project-specific finished treatment | [examples/project-specific-architecture/architecture-template-and-realization.md](references/examples/project-specific-architecture/architecture-template-and-realization.md) |
| User-supplied visual references and their roles | [visual-reference-roles.md](references/visual-reference-roles.md) |
| Superseded pattern libraries | [legacy/README.md](references/legacy/README.md), [Somnus_Documentation_Design_System.md](references/legacy/Somnus_Documentation_Design_System.md), and [README_MdFormat_Rolling_Snippet_Library.md](references/legacy/README_MdFormat_Rolling_Snippet_Library.md) |
| Architecture template and project-specific example | [ARCHITECTURE_template.md](references/ARCHITECTURE_template.md), [examples/project-specific-architecture/ARCHITECTURE.md](references/examples/project-specific-architecture/ARCHITECTURE.md), and its [scope note](references/examples/project-specific-architecture/README.md) |

When the user supplies another document while evolving this skill, preserve it under `references/` and record its role in [source-lineage.md](references/source-lineage.md). For image sets, update [visual-reference-roles.md](references/visual-reference-roles.md), including provenance and distribution limits. Do not silently rewrite source examples.

## Tools

- `scripts/check_docs.py` checks Markdown structure and local references; it errors when a `SPEC.md` lacks an opening title and explicit scope statement. Optional flags surface remote or embedded images and inline CSS for review.
- `scripts/doc_profile.py` prints a read-only inventory of a document's structure and visual devices to help agents match the codebase's established style.
- `scripts/doc_banner.py` prints an optional portable banner when supplied with the real title and scope, and any known status or version. Review or adapt it before use.

A clean script result does not replace a content, evidence, accessibility, or rendering review.
