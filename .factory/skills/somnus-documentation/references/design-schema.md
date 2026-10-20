# Documentation Design Schema

Use this schema to decide what a public page needs to communicate and how its visual treatment can help. It defines shared design logic, not a palette, stylesheet, or fixed outline.

## Reader-facing page logic

Work through these questions:

1. **Identity:** What system, component, or question is this page about?
2. **Orientation:** What should readers understand before the details make sense?
3. **Structure:** What are the boundaries, parts, sequence, or relationships?
4. **Evidence:** What supports the claims, and where are the limits?
5. **Use:** What can readers do, verify, decide, or change?
6. **Wayfinding:** Where should they go for more detail?

These are information jobs, not required headings. Combine or reorder them to suit the document. Design cannot make missing substance feel complete.

## Banners and openings

Every file named `SPEC.md` begins with a visible identity banner. A banner establishes the subject and scope; it can be text-led or use a project-owned visual design.

Portable baseline:

```markdown
# Component Specification

> Defines the contract for the component's externally visible behavior and its boundary.

**Status:** Draft · **Document version:** 0.1
```

Use only facts supported by the repository. Omit status or document version when unknown. A richer project banner may use an existing logo, an authored SVG, badges, a centered lockup, or another established treatment. Preserve an accessible title and a text route to essential meaning. A logo belongs only when supplied as an approved asset or explicitly requested.

A `README.md` opens with project identity and a direct account of why the project exists. A banner can establish identity; it does not replace purpose, mental model, useful entry path, or routes to deeper material.

## README as landing page and walkthrough

A README gives readers an entry point and a working map. It should answer, without making readers hunt:

- What is the project for, and what does it do?
- What is in scope, and where are its boundaries?
- How do the important parts relate?
- What is a useful first route, and what should a successful result look like?
- Where are the deeper specifications, references, and operating instructions?

A README may be a long, evidence-backed technical walkthrough. Let it guide readers through concepts and decisions, not only installation. Use the project's genuine narrative voice, including first person when it is already part of the author's style. Avoid forced storytelling and repetitive setup copy.

## Visual devices

The source libraries demonstrate identity banners, badges, terminals, architecture views, split panes, monitors, research panels, metric views, evidence blocks, diffs, and pipeline diagrams. These are options. A page can use several, or rely mostly on headings, prose, and tables.

Choose a device when it makes information easier to locate or understand:

- **Banner:** identifies a project or document contract.
- **Badge or status label:** gives a meaningful, verified state at a glance.
- **Diagram:** explains real flow, ownership, topology, or lifecycle.
- **Table:** makes exact mappings, matrices, and comparisons easier to inspect.
- **Evidence panel:** keeps a claim beside its support and its limits.
- **Code label or frame:** identifies a real source path, command, trace, or output.
- **Metric display:** presents measured values with their conditions and provenance.
- **Change or decision view:** makes a consequential change and its reason legible.

Use terminal framing where it reinforces the actual project or content. It is not required for every inline example, code block, or diagram. A standard Markdown fence can be more direct.

## Project identity and color

There is no shared palette. Follow the target codebase's visual vocabulary where it exists. If it does not, choose a restrained identity only when it helps distinguish or organize information. Preserve contrast and test the chosen rendering.

Keep a project's palette, logo, typography, metaphor, and banner local to that codebase. The plum and magenta identity in the architecture example belongs to that source; it is not a Somnus-wide theme.

## Translate image references into visual roles

Treat supplied images as evidence about visual intent. First decide what role each image plays: the governing atmosphere, a banner or section image, an asset intended for publication, or an example whose role is not yet clear. Then describe visible mechanisms such as crop and scale, color relationships, light and shadow, material and texture, negative space, density, repetition, and hierarchy. Convert those observations into document treatments without copying source-specific words, marks, characters, or symbols. Do not assign a fixed palette or publish a reference image just because it was supplied.

### Governing atmosphere: a document entrusted to a reverend mother

Use the user's “Reverend Mother” and “Bene Gesserit scroll” language as private art-direction shorthand. The design should embody that presence in the document itself: a composed record of knowledge held, tested, and passed on by a disciplined institution. Authority comes from command of the material, exactness, memory, and controlled disclosure. The page should feel considered and consequential, as if it is meant to be kept and consulted.

When composing, imagine a Reverend Mother has arranged this page for a future reader: she sees the material clearly, knows what deserves prominence, preserves lineage and consequence, and wastes no movement. Let the page communicate discernment, self-command, memory, and mastery before a reader reaches the body text. This is a direction for the judgment expressed by the composition, not an invitation to imitate the character.

This is not a request to imitate a fictional character's voice or to turn documentation into roleplay. Keep public prose direct, contemporary, and technically precise. Do not name the fictional source, quote it, wink at it, or borrow its plot, costume, symbols, invented language, or specific iconography in public documents.

The reference is not a palette. It is not a requirement for black backgrounds, monochrome pages, serif type, parchment, gold, or any fixed color. Its visual force can come from form and behavior:

| Design signal | Translate it into the page | Avoid using as a shortcut |
| --- | --- | --- |
| Authority through knowledge | A clear hierarchy, confident alignment, exact labels, supported claims, useful cross-references, and deliberate emphasis. | Oversized launch slogans, grandiose copy, invented authority, or dense decoration. |
| Controlled disclosure | A purposeful reading sequence, well-framed details, partial crops when an image supports them, and space around meaningful transitions. | Obscuring essential information, arbitrary secrecy, hidden text, or mystery without a reader purpose. |
| Institutional memory | Useful document identity, dates and status when verified, provenance, source maps, and links between related records. | Fake archival dates, invented seals, faux manuscript effects, or decorative “ancient” language. |
| Composed presence | A clear heading cadence, precise captions, balanced prose and table density, deliberate image-and-text relationships, and selective material detail. | A generic dark theme, Gothic clutter, theatrical sacred symbols, or empty minimalism. |

The supplied atmosphere references show composed figures, partial concealment, precise gestures, close framing, strong tonal contrast, and richly worked materials: layered drapery, patterned veils, beads, and worked surfaces. Let those observable qualities inform image selection and framing when suitable; a poised hand, a partly revealed face, a measured silhouette, or an intricate real material can carry more presence than a decorative emblem. Do not reproduce a recognizable character or exact costume. Texture may come from actual approved photography or a repository-owned asset; do not add synthetic grain, parchment, stone, fabric, or metal effects just to signal age or sanctity.

Let the opening act as a threshold into the document: identity, scope, and a deliberately composed image or typographic lockup when it serves the project. Let section order, heading cadence, blank-line rhythm, restrained rules, useful labels, captions, and cross-references create the feeling of a maintained record. Use the target renderer's available type treatments for clarity and long reading; choose visual density deliberately. These choices must remain legible in the target renderer and specific to the codebase.

Restraint should feel chosen and complete. It can hold substantial detail. Do not confuse mystique with obscurity: readers should still find the facts, limits, procedures, and evidence they need. Do not turn the reference into Gothic horror, occult ornament, Greek-temple styling, fantasy decoration, or roleplay. These are private design cues, not public-facing language.

The surface can be quiet while the structure beneath it is exact and deep. Let that depth appear through well-ordered sections, evidence, definitions, provenance, and cross-references—not through ornamental density. A reader should sense that detail has been deliberately held in reserve and then placed where it becomes useful.

### Banner and image role: vivid natural form

The supplied coral references are banner and image-treatment examples, not a uniform macro-texture set. One is a blurred organic field with coral-like forms near its lower edge; the other is a shallow soft-focus color band. Choose the treatment from the actual image's crop, color, and visible detail. A selected image can make an opening or section boundary distinctive without establishing the body palette, requiring more color elsewhere, or displacing the governing atmosphere.

A banner may be visually assertive while surrounding typography and content remain measured. Other moments—tables, inline examples, code, and evidence—should use the treatment their reading job needs. Do not make each element repeat the banner's image or color treatment.

### Preserve the relationship

In this reference set, the entrusted-document atmosphere governs the page; vivid natural photography is an available image event within it. Let natural color bring life, scale, and contrast where an image belongs, while the document's composition remains deliberate. Do not model these as competing themes or blend them into a generic colorful-dark style. Render a grayscale copy and confirm that hierarchy, pacing, and distinctions remain clear without hue as the only signal. Keep both image treatment and atmosphere subordinate to the target codebase's own identity and the reader's task.

Use supplied or repository-owned imagery, and record provenance for assets that will be published. Do not generate documentation imagery. Keep style references separate from publication assets unless the user identifies an image as approved for use.

### GitHub-safe composition and review

GitHub does not give Markdown authors general control over fonts, fixed page margins, or arbitrary CSS spacing. Carry composition through the controls that render reliably:

- Use one descriptive H1, then a deliberate H2/H3 cadence; keep headings informative and do not skip levels for visual size.
- Set reading pace with paragraph length, lists, and blank lines. Use blockquotes for a real scope note or image caption, not as a fake panel.
- Use narrow tables for exact mappings and comparisons. Split wide tables when phone-width readers would have to scroll across unrelated fields.
- Use horizontal rules only at meaningful changes of subject or document state.
- Use a single project-owned, pre-cropped image when it adds identity or evidence; provide useful alt text and a plain caption. GitHub Markdown does not provide a dependable image-cropping control.
- Use Mermaid or another verified diagram when it explains actual structure, sequence, ownership, or state. Introduce it in prose and state its meaning outside the diagram when that meaning is essential.
- Use code fences for runnable commands, source excerpts, or literal data. Keep ordinary examples in ordinary fences; do not frame each one as a terminal display.
- Give long documents a compact linked contents list and use direct cross-references for related records.

Apply these checks before delivery:

| Check | Pass condition |
| --- | --- |
| Information job | Every banner, image, table, diagram, callout, badge, code treatment, and navigation device maps to identity, orientation, structure, evidence, use, or wayfinding. Remove devices that serve none. |
| Assertive imagery | At most one decorative or identity image event dominates the page. Functional diagrams and evidence visuals may appear when they perform a necessary information job; they do not become additional decorative events. |
| Grayscale | Inspect a rendered grayscale copy. Heading levels, links, status, chart distinctions, and essential emphasis remain legible without relying on hue alone. |
| Narrow screen | Inspect a phone-width rendering. No heading, caption, diagram, or table is clipped; unavoidable wide code remains understandable and reachable. |
| Renderer claims | Any claim about HTML, SVG, CSS, Mermaid, or badges reflects the exact target render that was checked. Do not infer GitHub behavior from another Markdown viewer. |
| Complete disclosure | The reading sequence may defer detail, but never hides required facts, caveats, procedures, ownership, or evidence. |

These checks make the composition reviewable; they do not prescribe a shared palette or a universal number of sections.

## Voice and evidence

- Use direct language and the project's real voice. Narrative progression can clarify why an implementation or design decision matters.
- Avoid generic launch copy, hollow claims, synthetic drama, and filler headings.
- Never invent commands, terminal output, metrics, tests, screenshots, components, compatibility, or maturity claims.
- Separate observed behavior, intended behavior, inference, and history. Use labels when they improve a reader's understanding; do not copy the architecture example's label taxonomy by default.
- Keep a command in a code block when readers should run, copy, or inspect it. Include prerequisites and a recognizable result when useful.
- Give source excerpts enough context to identify the file and the point being demonstrated.

## Progressive visual treatment

The structural outline and visual design are separate layers. Preserve a requested template's role and section order, then give it a finished visual treatment through hierarchy, whitespace, navigation, project identity, diagrams, tables, code labels, and evidence panels. Add content sections when the subject requires them. Do not interpret a template as a length target, and do not shorten a useful document to fit one.

Keep essential meaning available in Markdown or accessible text. Use HTML, SVG, inline styling, Mermaid, shields, and other renderer-specific presentation only when they fit the project and the target renderer. Do not require a terminal container, a color, or a special visual device for every inline element.

## Scope boundary

This skill covers reader-facing documentation design. It does not define or integrate the Somnus metadata system. Keep agent operating files and documentation metadata workflows outside this design schema.

## Final review

- Confirm the opening identifies the subject, scope, and reader route.
- Confirm the requested structure remains intact and the subject has enough evidence-backed depth.
- Confirm readers can distinguish implementation, proposal, inference, and unknowns.
- Confirm the page retains its codebase identity instead of importing a global theme.
- Complete the six checks above against the rendered target, including GitHub when required.
- Confirm every `SPEC.md` begins with a visible title and explicit scope statement.
