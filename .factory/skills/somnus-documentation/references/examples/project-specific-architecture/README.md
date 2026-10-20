# Scope Note — Project-Specific Architecture Example

This completed architecture document is retained as an example of one codebase's evidence structure and rendered presentation. Its plum and magenta palette, SVG treatment, badges, and other visual decisions belong to Sacred Timeline Substrate; they are not the governing style for this documentation skill.

Use the current design schema and visual-reference guidance for the shared art direction. Use this example only when its structure or technical presentation answers the task at hand. The separate structural source remains at [`references/ARCHITECTURE_template.md`](../../ARCHITECTURE_template.md).

The numbered sections are now in order, and the sequence/state diagrams sit beneath the GitHub rendering section that explains them. The paired interpretation document maps the template to this example without treating the example as a default visual recipe.

## Section map

Open the example by section rather than whole. Models imitate the largest example in context, so read only the range that answers the current question.

| Lines | Section | Read it for |
| --- | --- | --- |
| 1–119 | Banner, badges, contents | An authored identity opening and a long contents list |
| 120–295 | 1–2. Executive summary, system flow | Claim boundaries and a Mermaid lifecycle with prose walkthrough |
| 296–574 | 3–4. Innovations, component catalog | Mechanisms tied to tests and source excerpts |
| 575–722 | 5–7. Schemas, integration, hazards | Concrete schema tables and failure handling |
| 723–928 | 8–10. Threats, validation, roadmap | Threat mapping, validation matrices, and non-goals |
| 929–1067 | 11–12. Glossary, GitHub render contract | A glossary and an example-local render contract (see the warning below) |
| 1068–1765 | 13–22. Trust zones through change log | Registries, contracts, evidence, and change history |
| 1766–1846 | 23. Field geometry, second pass | A supplemental section placed after the core |

## Render warning

GitHub does not render this example the way its own render contract describes. `scripts/render_check.py` (run 2026-10-20 against GitHub's Markdown API) reported that all 9 inline SVGs and 42 of 49 `style=` attributes were stripped. Treat the SVG identity banner, axis views, and styled panels as patterns for renderers that keep them, or as candidates for committed `.svg` image files, not as proof of GitHub support.

## Next state

Read the range you need, then return to the state that sent you here (S2 for structure, S5 for a visual device). Before adopting any of the example's SVG or styled devices, enter S7 and confirm the target renderer keeps them.
