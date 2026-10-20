# Source Lineage

Keep the sources' roles distinct as the public-documentation design skill evolves.

| Source | Role in this package | How to use it |
| --- | --- | --- |
| `legacy/README_MdFormat_Rolling_Snippet_Library.md` | Original Markdown and README-format experiments; superseded | Read only for historical lineage or a user-requested legacy pattern. Its layout and presentation choices are not current defaults. |
| `legacy/Somnus_Documentation_Design_System.md` | Evolution of the snippet library into a named design system; superseded | Read only for historical lineage or a user-requested legacy pattern. Its palette, terminal frames, identity blocks, evidence panels, and visual language are not current defaults. |
| `ARCHITECTURE_template.md` | Structural starting point for an architecture specification | Treat its section sequence as the architecture spine when the user selects this template. It is not a length target. |
| `examples/monochrome/README.md` and `examples/monochrome/fixture-source.md` | Finished GitHub-native example using a non-Somnus fictional fixture | Use to see how heading cadence, restrained navigation, a text-led opening, tables, diagrams, and ordinary code fences can carry a composed atmosphere without custom CSS or color. The fixture is illustrative, not a source of reusable technical facts. |
| `examples/project-specific-architecture/ARCHITECTURE.md` | Completed public architecture whitepaper and project-specific visual realization | Consult when the project needs its deep evidence organization or a proven example-local visual device. Its plum/magenta palette, badges, source labels, SVGs, and technical claims belong to Sacred Timeline Substrate, not the shared style. |
| `examples/project-specific-architecture/architecture-template-and-realization.md` | Interpretation of the paired architecture example | Use to map the structural baseline to a finished, project-specific treatment. It does not define the governing atmosphere. |
| `examples/project-specific-architecture/README.md` | Scope note for the architecture example | Read before opening the example to distinguish its repo-specific style from current defaults. |
| `visual-reference-roles.md` and `visual-references/` | First user-supplied visual reference set and private art direction | Preserve retained reference images and read the provenance note before use. The mostly monochrome images inform a composed, knowledge-bearing presence; the coral photographs show banner roles. The user's fictional shorthand is internal skill guidance only and must not appear in public documentation. |
| `design-schema.md` | Current operational interpretation | Follow the current user request, target repository identity, evidence, and renderer. It states the atmosphere in observable, testable terms; the private shorthand stays in `visual-reference-roles.md`. |
| `../templates/` | Codebase document substrate (`AGENTS`, `BRAINSTORM`, `CONTEXT`, `MEMORY`, `NOTEPAD`) | Install with `scripts/operator_lockin.py`. These are operating documents, not public docs, and do not take the public visual layer. |

Source documents and retained supplied images are kept under `references/`. The two legacy libraries carry a superseded notice; the moved architecture companion's link and the whitepaper's section order were repaired without changing its technical claims. The architecture template's contents list originally pointed at Google Docs bookmark IDs; those links were repointed to the template's own heading anchors without changing its sections. The MTV graphic is intentionally excluded from this private package. When the user supplies more examples while evolving this skill, retain each original file there under its original name and add a short note about what it changes or confirms.

## When examples differ

Apply guidance in this order:

1. The user's instruction for the current document.
2. The target codebase's established reader-facing style and tested renderer.
3. The current rules in `SKILL.md` and `design-schema.md`.
4. The closest supplied example.
5. Older pattern libraries.

Examples show design choices, not reusable proof. Their sample projects, statuses, metrics, external assets, CSS, and technical claims do not become facts or requirements for another repository.

This package designs reader-facing public documentation. It also ships the codebase document substrate under `templates/` as a separate, installable layer; it does not define or integrate the Somnus metadata system.

## Next state

- From a precedence conflict in any state: apply the order above, then return to the state that raised the conflict.
- From E1: after recording the source, enter E2 and update only the reference whose role changed, then run E3: `python3 scripts/doc_gate.py --self`.
