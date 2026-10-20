# Document Compositions

Choose a composition from the reader's questions, the document's purpose, and available evidence. These are starting shapes, not required heading lists. Do not compress a useful explanation to fit a preset structure.

## README: landing page and walkthrough

Use for a project's main human-readable entry point.

- Establish identity, purpose, and boundary early.
- Give readers a useful mental model of the system or library.
- Walk through a verified route, when one exists, with prerequisites and a recognizable result.
- Explain the project's structure and route readers to specifications, architecture, APIs, contribution, operation, and release details.
- Use a contents list when it helps readers navigate a substantial page.

A README can combine project overview, explanation, source-backed examples, diagrams, and technical depth. It is more than a readme in the narrow sense of a short summary or installation note. Keep the author's genuine voice; do not manufacture an origin story or conversational persona.

## SPEC: identity banner and contract

Use when behavior, data, interfaces, or constraints must be precise.

- Begin with the visible banner required for every file named `SPEC.md`.
- Define scope and terms before relying on specialized vocabulary.
- Separate normative requirements from examples, rationale, implementation status, and proposals.
- Organize around contracts, invariants, inputs and outputs, state changes, errors, compatibility, and conformance as needed.
- Use exact tables and complete examples where they help readers verify a contract.
- Close with validation criteria, open decisions, or implementation links when useful.

Do not imply that an implementation conforms just because a specification describes the intended behavior.

## Architecture dossier

Use for a public architecture guide, system whitepaper, or deep technical explanation.

- State the governing problem, practical boundary, and design constraints.
- Explain ownership, vocabulary, flow, state, and failure behavior.
- Add source maps, class contracts, threat views, validation matrices, evidence registers, glossaries, and operational procedures when they answer real reader questions.
- Tie implementation claims to source or tests. Mark inference, intended work, historical evidence, and unavailable verification as the project needs.
- Preserve substantial detail when it helps readers understand the system. There is no prescribed length.

Use [the architecture example's scope note](examples/project-specific-architecture/README.md) before reading [its paired interpretation](examples/project-specific-architecture/architecture-template-and-realization.md): the template supplies the architecture spine; the completed document shows one codebase-specific visual and evidence treatment around it.

For a GitHub-native composition that carries the current restrained atmosphere without HTML or a fixed palette, read [the monochrome README example](examples/monochrome/README.md). Its Siltline fixture is fictional and its technical details are illustrative, not a pattern to copy as facts or as a required color scheme.

## Field guide

Use for tools, CLIs, libraries, and software readers should operate.

- State what the tool enables and where its boundary sits.
- Walk through a verified route from prerequisites to a useful result.
- Explain the concepts needed to understand that route.
- Put exhaustive options and less common cases in focused references when useful.

Each command block should serve a reader goal. Include a success signal or recovery clue when it is not self-explanatory.

## Contract atlas

Use for APIs, schemas, protocols, configuration formats, and library interfaces.

- Start with scope and a capability or route map.
- Organize around reader tasks and exact contracts.
- Use tables for mappings, defaults, constraints, and errors.
- Give complete examples for important routes and keep operating guidance beside the interface it affects.

## Evidence ledger

Use for experiments, benchmarks, evaluations, investigations, and research notes.

- State the question, scope, method, and stop condition.
- Separate observation, interpretation, decision, and limitation.
- Include enough conditions and measurements to challenge or reproduce results.
- Keep contradictions visible until resolved.
- Use charts or metric panels only for real, comparable values.

## Release handoff

Use for versioned changes with an upgrade surface.

- Lead with practical user impact.
- Explain required action, breaking changes, compatibility, and migration or recovery.
- Keep raw commit history secondary to what readers need to know.

## Motif selection

A document may combine visual devices. Keep them consistent enough to reinforce hierarchy; do not turn the page into a collage.

Separate the governing atmosphere from the role of an individual image. In the current user references, the document should feel like a carefully kept instrument of knowledge: composed, exact, self-possessed, and deliberate in what it reveals. Saturated natural photography is an available banner or section-image treatment within that atmosphere. Let both roles work together without turning the banner into a global palette or making every element decorative. Map every device to identity, orientation, structure, evidence, use, or wayfinding; keep at most one assertive decorative or identity image event per page. See [design-schema.md](design-schema.md#translate-image-references-into-visual-roles) and [visual-reference-roles.md](visual-reference-roles.md) for the image-reading method and current references.

| Device | Use when | Leave it out when |
| --- | --- | --- |
| Banner | Identity and scope need a clear opening; required for `SPEC.md` | It repeats the title with no scope or meaning |
| Contents | Readers need to revisit a substantial document | The page is short or naturally read top to bottom |
| Signal label | A meaningful, verified status needs a quick cue | It repeats a heading or implies unsupported certainty |
| Comparison table | Values or fields need exact side-by-side inspection | Prose or a short list is faster |
| Evidence panel | A claim needs support, limits, or provenance nearby | It restates promotional language |
| Source trace | A real path, command, run, or failure signal is useful | It is fabricated or terminal wallpaper |
| Decision record | A consequential choice needs durable rationale | It repeats history without informing a reader |

## Next state

Leave S2 with an outline in which every section names its reader question. Then enter S3 and load [design-schema.md, Voice and evidence](design-schema.md#voice-and-evidence). For an architecture dossier, the [scope note's section map](examples/project-specific-architecture/README.md#section-map) is the only sanctioned way into the large example.
