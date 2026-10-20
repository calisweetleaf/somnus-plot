# Rendering and Assets

Use GitHub-flavored Markdown as the portable baseline when GitHub is a target. Preserve the richer presentation the project uses when it has a tested rendering contract.

## Markdown baseline

- Use informative headings, links, prose, lists, tables, blockquotes, code fences, and Mermaid where the target supports them.
- Give diagrams a plain-language introduction and recoverable meaning in surrounding text.
- Keep essential labels, descriptions, and content visible without custom CSS.
- Use relative paths for repository-owned docs and assets.
- Check narrow-screen readability for long headings, tables, banners, and code blocks.
- Use a contents list for navigation when the page's length or structure warrants it.

### Composition levers available in GitHub Markdown

When GitHub is the target, build hierarchy with native Markdown rather than assuming control over fonts, fixed margins, or arbitrary spacing:

| Lever | Use |
| --- | --- |
| Heading cadence | One descriptive H1, followed by informative H2/H3 sections with no skipped levels. |
| Paragraph and list rhythm | Use short paragraphs for dense material, lists for parallel items, and blank lines to separate distinct thoughts. |
| Blockquote caption | Add scope or an image caption when that sentence adds context; do not use quotes as an imitation card or callout panel. |
| Narrow table | Compare a small set of related fields or route readers through a document. Split wide matrices for phone-width reading. |
| Horizontal rule | Mark a real change in subject or document state, not a cosmetic separator between every section. |
| Owned image | Use one pre-cropped, project-owned image for identity or evidence when useful. Supply meaningful alt text and a plain caption. |
| Mermaid diagram | Explain a real flow or relationship. Confirm the labels, branches, and surrounding text communicate the same facts. |
| Code fence | Show runnable commands, inspectable source, or literal data. Leave ordinary prose examples unframed. |
| Contents and cross-links | Help readers move within a substantial page and between related records. |

GitHub Markdown does not provide a dependable image-cropping control or general CSS typography and spacing control. Crop assets before adding them and verify enhanced markup in the actual GitHub view.

## HTML, SVG, and styling

GitHub renders some embedded HTML in Markdown, but support is partial and context-dependent. Markdown change previews may show only supported elements; review source and rendered views for pages that use substantial HTML. An SVG file can be a project-owned image asset, while inline SVG or styled markup should be checked in the exact target surface.

The supplied architecture example states its own GitHub render contract. It uses inline SVG, unique prefixed IDs, Mermaid, small inline-style code headers, and evidence panels; it also rules out particular effects for that repository. Treat those details as local authored choices, not a universal GitHub or Somnus requirement. Verify the exact output when adapting them.

- Test the exact target when using inline SVG, SVG filters, HTML containers, inline CSS, badges, tables, or renderer-specific markup.
- Keep a text title and explanation available for informative visuals; use alt text or accessible labels where supported.
- Avoid layout choices that impair keyboard navigation, mobile reading, text selection, or screen readers.
- Keep essential architecture and contract information in the main reading flow.
- If enhanced markup fails in the target, use project-owned image assets, plain Markdown, tables, prose, or supported Mermaid as appropriate.

## Diagrams

Use a visual when it explains real ownership, sequence, topology, data flow, or lifecycle.

- Prefer a compact Mermaid diagram for relationships when GitHub rendering is part of the target.
- Keep diagram labels accurate and ensure the chart remains understandable in the project's supported view.
- A manually authored SVG can fit a project's identity or express a complex relationship. Check its labels, accessibility, source control, and renderer behavior.
- Do not fabricate a diagram, terminal state, graph, chart, or test output for decoration.

## Assets

- Use project-owned or user-provided assets. Do not create AI-generated documentation imagery.
- Distinguish a user-provided style reference from an asset approved for publication. Do not publish reference-only screenshots, source marks, or text unless the user asks to use them.
- Use a logo only when the user provides an approved asset or explicitly asks for one.
- Place local assets in the repository's existing asset location. If none exists, use a clear `assets/` folder unless the project defines another convention.
- Give informative images useful alt text and link them with repository-relative paths.
- Use remote badges or image services only when they belong to the project and their failure does not hide essential information.
- Record asset source, creator, rights or license, and use through the repository's existing provenance convention.

## Preflight

Before delivery, confirm that:

- The page renders in the actual target, including GitHub when required.
- A rendered grayscale copy retains its hierarchy, link/status distinction, and any chart or image labels without hue as the only signal.
- A phone-width rendering clips no heading, caption, table, or diagram; unavoidable wide code remains readable and reachable.
- At most one decorative or identity image event dominates the page. Keep additional diagrams and evidence visuals only when they explain structure, evidence, or use.
- Every banner, image, table, diagram, callout, badge, code treatment, and navigation element maps to identity, orientation, structure, evidence, use, or wayfinding.
- Local links and asset paths resolve.
- Banner and image text remains available to readers who cannot see an image.
- Commands and source excerpts are real or clearly marked as examples.
- Measurements and implementation claims have traceable evidence.
- Every file named `SPEC.md` begins with a visible title and explicit scope statement.

Treat a visual acceptance item as failed if it cannot be verified in the target rendering. Do not claim a font choice, spacing behavior, or CSS effect based on a different viewer.

Official GitHub references:
- [Creating diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
- [Working with non-code files and embedded HTML](https://docs.github.com/en/repositories/working-with-files/using-files/working-with-non-code-files)
- [Basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
