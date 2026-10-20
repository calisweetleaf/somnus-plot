---
name: somnus-documentation
description: Create, review, or revise public-facing Markdown documentation for human readers (README.md, SPEC.md, architecture guides, API references, research notes, release documents) through a gated state machine that verifies claims, structure, and GitHub rendering. Also installs and audits the codebase document substrate (AGENTS, CONTEXT, MEMORY, NOTEPAD, BRAINSTORM) in a target repository. Use when documentation must be evidence-grounded, visually deliberate, distinctive to its codebase, and readable in GitHub.
---

# Somnus Documentation

This skill is a state machine. Enter at **S0**, run one state at a time, and load only the file or section named by the current state. Every state ends at an exit condition or a gate; a gate either advances the machine or routes back to the state that owns the defect. The machine stops at **EXIT** with a gate report, never on a feeling of completeness.

Public documentation is part of the product's interface. It gives readers an inviting way into the subject, an exact account of how it works, and routes through the details, with visual form that carries meaning and the codebase's own identity.

## Tracks

S0 classifies the request into one track. A request can queue several tracks; finish one before entering the next.

| Track | Enter when | States |
| --- | --- | --- |
| **D: public document** | Writing, revising, or reviewing reader-facing Markdown | S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8 → EXIT |
| **R: review only** | The user wants findings, not edits | S1 → S3 gate → S6 gate → S7 gate → S8 → EXIT, with no writes |
| **T: codebase substrate** | A repository needs, or is auditing, its `AGENTS`/`CONTEXT`/`MEMORY`/`NOTEPAD`/`BRAINSTORM` roles | T1 → T2 → T3 → T4 → EXIT |
| **E: skill evolution** | The user supplies a source, image, or change for this skill itself | E1 → E2 → E3 → (E4) → EXIT |

## Invariants held in every state

### Design contract

- Match the repository's own voice and visual identity. Do not import another project's palette, logo, banner, motifs, or layout as a default.
- A supplied template describes shape, not length. Preserve its order when the user asks, then expand with evidence, diagrams, and navigation as the subject requires.
- No target word count or maximum. Do not compress useful detail; do not add filler.
- Deletion test: every section names the reader question it answers. Cut or merge a section that cannot, or that repeats an earlier answer. Bloat is the more common failure than truncation.
- Grounded, contemporary prose. First person only when it is the author's real voice. No invented persona, no launch copy, no synthetic drama.
- No emoji. No AI-generated imagery. A logo only when the user supplies an approved asset or asks for one.
- Banners, badges, diagrams, tables, code labels, evidence panels, and terminal frames are available devices, not a required kit. Ordinary fenced code is often the clearest treatment.
- Essential meaning stays in Markdown or accessible text. HTML, SVG, inline styles, and renderer-specific features are allowed only inside a tested rendering contract.

### Machine rules

- **Load on entry, not in advance.** Each state names its load. Do not read references a state does not name. Open the 1,846-line architecture example only through the [section map](references/examples/project-specific-architecture/README.md#section-map). Open [legacy libraries](references/legacy/README.md) only when the user asks for a legacy pattern.
- **Gates are not optional.** A gate that cannot run (no network, no browser) is reported as `SKIPPED` with the reason. It never counts as a pass.
- **Route failures to their owner.** Use the failure routing table below or the `->` lines that `scripts/doc_gate.py` prints. Fix the defect in the owning state, then re-run the gate that failed and every gate after it.
- **Loop bound.** If the same finding survives three repair attempts, stop, record it as a blocker with its evidence, and continue to EXIT.
- **Precedence when sources disagree:** the user's instruction for this document, then the target codebase's established style and tested renderer, then this file and `design-schema.md`, then the closest example, then legacy libraries. See [source-lineage.md](references/source-lineage.md#when-examples-differ).
- **Separate layers.** Track D documents receive the public visual layer. Track T documents are operating documents and do not, unless the user explicitly asks. The Somnus metadata system is out of scope for every track.

## Track D: public document

### S0 INTAKE

- **Do:** Identify the target files, the requested action (create, revise, review), any supplied template, images, or examples, and the target renderer (GitHub unless stated).
- **Exit:** Track chosen. If the request is review-only, switch to track R.
- **Next:** S1.

### S1 SURVEY

- **Load:** nothing new. Read the target document, nearby public docs, owned visual assets, and the source code or tests behind its claims.
- **Do:** Run `python3 scripts/doc_profile.py --root <repo> <paths...>` to inventory headings, fences, tables, images, HTML devices, and inline colors in existing public docs. Assign each supplied image a role: governing atmosphere, banner or section image, publishable asset, or unassigned. Do not take agent-context files as the style target.
- **Exit:** You can state the audience, the reader's next decision or action, the codebase's existing visual vocabulary, and the evidence sources available.
- **Next:** S2.

### S2 SHAPE

- **Load:** the one matching section of [compositions.md](references/compositions.md): [README](references/compositions.md#readme-landing-page-and-walkthrough), [SPEC](references/compositions.md#spec-identity-banner-and-contract), [architecture dossier](references/compositions.md#architecture-dossier), [field guide](references/compositions.md#field-guide), [contract atlas](references/compositions.md#contract-atlas), [evidence ledger](references/compositions.md#evidence-ledger), or [release handoff](references/compositions.md#release-handoff). For an architecture template, also load [ARCHITECTURE_template.md](references/ARCHITECTURE_template.md).
- **Do:** Draft the outline. Write the reader question each section answers beside it.
- **Exit:** Every section passes the [deletion test](references/design-schema.md#deletion-test). A supplied template's order is intact.
- **Next:** S3.

### S3 EVIDENCE

- **Load:** [design-schema.md, Voice and evidence](references/design-schema.md#voice-and-evidence).
- **Do:** Verify names, paths, commands, flags, compatibility, status, measurements, and links against source, tests, and runs. Keep observed behavior, intended behavior, inference, and history distinct. Use evidence labels only when the codebase benefits; the architecture example's labels are local to it.
- **Gate:** `python3 scripts/claims_check.py --root <repo> <paths...>` (add `--strict` when every named path must already exist). It checks backticked paths, scripts and modules in shell fences, their `--flags` against script source, and inline or reference-style `#anchor` links.
- **Pass:** S4. **Fail:** stay in S3 and fix the claim, or label it as an example or output path.

### S4 COMPOSE

- **Load:** [design-schema.md, Reader-facing page logic](references/design-schema.md#reader-facing-page-logic), [Banners and openings](references/design-schema.md#banners-and-openings), and, for a README, [README as landing page and walkthrough](references/design-schema.md#readme-as-landing-page-and-walkthrough).
- **Do:** Write to the full depth the subject needs. Meet the document requirements below. Open every H2 with a sentence that states the section's job.
- **Exit:** Draft complete, and every `SPEC.md` opens with a visible title and explicit scope.
- **Next:** S5.

### S5 VISUAL

- **Load:** [design-schema.md, Visual devices](references/design-schema.md#visual-devices) and [Project identity and color](references/design-schema.md#project-identity-and-color). Load [the governing atmosphere](references/design-schema.md#governing-atmosphere-a-kept-record) for the page's overall treatment. Load [visual-reference-roles.md](references/visual-reference-roles.md) only when assigning roles to supplied images. Load [rendering-and-assets.md, HTML, SVG, and styling](references/rendering-and-assets.md#html-svg-and-styling) before using any HTML, SVG, or inline style.
- **Do:** Describe an image's observable mechanisms before choosing treatments. Map every device to one of the six information jobs: identity, orientation, structure, evidence, use, or wayfinding. Remove any device that serves none. Allow at most one assertive decorative or identity image event per page. Never let controlled disclosure hide a fact, caveat, procedure, or evidence.
- **Exit:** Every device has an information job, and each design signal passes its [concrete test](references/design-schema.md#governing-atmosphere-a-kept-record).
- **Next:** S6.

### S6 STRUCTURE

- **Gate:** `python3 scripts/check_docs.py --root <repo> --check-composition <paths...>`. It errors on dead local links (inline and reference-style), unclosed fences, and a `SPEC.md` without title and scope. It warns on heading jumps, multiple H1s, missing alt text, emoji, and H2 sections that open with a table, list, fence, image, or heading. Add `--check-external-assets` for remote or embedded images and `--check-renderer-features` for inline CSS.
- **Pass:** S7. **Fail:** route by the failure table: content defects to S4, device defects to S5, broken files stay here.

### S7 RENDER

- **Load:** [rendering-and-assets.md, Preflight](references/rendering-and-assets.md#preflight).
- **Gate:** `python3 scripts/render_check.py --root <repo> <paths...>` renders through GitHub's Markdown API. It reports raw HTML that GitHub strips (inline SVG, `style=` attributes, and similar) and writes desktop, narrow (390 px), and grayscale views, with screenshots when Chrome or Chromium is available. Inspect all three views: no clipped heading, caption, table, or diagram at narrow width, and no hierarchy that depends on hue alone in grayscale. Mermaid renders client-side on github.com and must be confirmed there.
- **Pass:** S8. **Fail:** stripped devices go to S5 to be replaced with ones the renderer keeps. Clipping and grayscale failures go to S5. A render that cannot run is `SKIPPED`, not passed.

### S8 READER

- **Load:** [design-schema.md, Final review](references/design-schema.md#final-review).
- **Do:** Read the page as its intended reader. Confirm the opening says what the document is and where to go. Confirm that depth is navigable, that examples and claims are real, and that styling never obscures meaning.
- **Pass:** EXIT. **Fail:** return to the state that owns the defect.

### Shortcut: one-command gate

`python3 scripts/doc_gate.py --root <repo> <paths...>` runs S3 and S6 in order, and S7 with `--render`. It prints each finding with the state that owns it, the repair action, and the reference section to open. It ends with `verdict: FAIL -> re-enter at <state>` or `verdict: PASS`. Use it at the end of S5 and after every repair batch. Add `--strict-claims` or `--fail-on-warnings` to tighten the gate.

## Track R: review only

Run S1, then the S3, S6, and S7 gates (or `doc_gate.py --render`), then S8, without editing. Report findings grouped by owning state, each with its evidence and the reference section a fix would follow. State which gates were skipped and why.

## Track T: codebase substrate

Every repository carries its own operating documents. They are seeds to customize and must never regress back to template text. The roles and their templates:

| Installed file | Template | Role |
| --- | --- | --- |
| `AGENTS.md` | `templates/AGENTS.codebase.template.md` | Runtime navigation router, environment contract, and transition grammar |
| `CONTEXT.md` | `templates/CONTEXT.md` | Chronological traversal index into memory |
| `MEMORY.md` | `templates/MEMORY.md` | Deep durable store: findings, provenance, failures, verification |
| `NOTEPAD.md` | `templates/NOTEPAD.md` | Append-only live workbook; not canon until promoted |
| `BRAINSTORM.md` | `templates/BRAINSTORM.md` | Flags for tangents, future questions, and context shifts |

`AGENTS.md` also names project-authored surfaces (`SPEC.md`, `STATE.md`, `ANTITHESIS.md`, `filetree.md`). The installer does not create them. A `SPEC.md` written for readers enters track D.

- **T1 PROBE:** `python3 scripts/operator_lockin.py init --target <repo> --project-name <name> --dry-run`. Exit: the create and preserve lists are known. Existing files are never overwritten.
- **T2 INSTALL:** run the same command without `--dry-run`. Exit: all five roles exist.
- **T3 ADAPT:** Fill `AGENTS.md` from repository evidence: identity, environment, commands, generated surfaces, quirks, invariants, hard bans, and the gate command. Every value comes from the repository or the user. Unknowns stay visible as unknowns, never as invented values.
- **T4 GATE:** `python3 scripts/operator_lockin.py check --target <repo>`. It fails on a missing role or any unfilled `AGENTS.md` placeholder, and it audits structure on the five role files only. `--allow-unresolved` turns placeholders into warnings during staged adoption. Pass: EXIT, or `export` (portable pack with manifest) or `fork` (provider projection such as `CLAUDE.md`) when asked. Fail: T3.

## Track E: skill evolution

- **E1 PRESERVE:** Retain every supplied source under `references/` with its original name, and record its role in [source-lineage.md](references/source-lineage.md). Record images, with provenance and distribution limits, in [visual-reference-roles.md](references/visual-reference-roles.md). Never silently rewrite a source example. Record any repair you make.
- **E2 INTEGRATE:** Update only the reference whose semantic role changed, and keep its "Next state" footer accurate. When scripts change, run a `somnus-debug doctor` baseline first and a rescan after, if the CLI is available.
- **E3 GATE:** `python3 scripts/doc_gate.py --self` runs the unit tests, then S3 and S6 over this package. Pass: EXIT or E4. Fail: E2.
- **E4 PACKAGE (on request):** `python3 scripts/package_skill.py --output <file.zip>`. It excludes the private `references/visual-references/` images unless `--include-visual-references` is given, and writes a `MANIFEST.md` that `scripts/manifest_audit.py` verifies after unzipping.

## Failure routing table

`scripts/doc_gate.py` applies this table automatically.

| Finding contains | Owning state | Open |
| --- | --- | --- |
| `anchor`, `path`, `command references`, `module`, `flag`, `target does not exist` | S3 EVIDENCE | [Voice and evidence](references/design-schema.md#voice-and-evidence) |
| `SPEC must begin` | S4 COMPOSE | [Banners and openings](references/design-schema.md#banners-and-openings) |
| `H2 at line … opens with`, `has no content` | S4 COMPOSE | [Deletion test](references/design-schema.md#deletion-test) |
| `emoji` | S4 COMPOSE | [Design contract](#design-contract) |
| `heading level jumps`, `multiple H1`, `banner cue` | S5 VISUAL | [GitHub-safe composition](references/design-schema.md#github-safe-composition-and-review) |
| `alt text`, `remote or embedded image` | S5 VISUAL | [Assets](references/rendering-and-assets.md#assets) |
| `inline CSS`, `dropped by GitHub` | S5 VISUAL | [HTML, SVG, and styling](references/rendering-and-assets.md#html-svg-and-styling) |
| `unclosed fenced block`, `not valid UTF-8` | S6 STRUCTURE | [Markdown baseline](references/rendering-and-assets.md#markdown-baseline) |
| anything else | S8 READER | [Final review](references/design-schema.md#final-review) |

## Document requirements

- **`SPEC.md`:** Always opens with a visible identity banner: a text-led Markdown banner or an accessible, project-owned visual. It must state the subject and scope. Show status or version only when known. `python3 scripts/doc_banner.py --title <title> --scope <scope>` prints an optional portable baseline.
- **`README.md`:** The project's front door and a working map. It covers what the project is, the problem it serves, its boundaries or mental model, how the important parts fit, a verified route with a recognizable result, and where to go next. Never reduce it to a setup card.
- **Architecture documents:** Cover the governing problem, ownership, boundaries, flow, state, contracts, failure behavior, evidence, and operation as relevant. Add source maps, validation, threat views, glossaries, or registers only when they are supported and answer reader questions.
- **Specifications and references:** Make terms, contracts, constraints, examples, status, and lookup paths precise. Separate normative rules from rationale, implementation, and proposal.
- **Research, evaluation, release, and migration documents:** Preserve methods, measurements, limitations, user impact, required actions, and recovery paths. Raw data never becomes a slogan.

## Load map

| File | Loaded in | Holds |
| --- | --- | --- |
| [design-schema.md](references/design-schema.md) | S3, S4, S5, S8 | Page logic, banners, visual devices, atmosphere with concrete tests, deletion test, GitHub-safe review checks |
| [compositions.md](references/compositions.md) | S2 | Adaptable shapes per document type and motif selection |
| [rendering-and-assets.md](references/rendering-and-assets.md) | S5, S7 | GitHub levers, HTML and SVG limits, diagrams, assets, preflight |
| [visual-reference-roles.md](references/visual-reference-roles.md) | S5 (images only), E1 | Private art direction, image inventory, provenance limits |
| [source-lineage.md](references/source-lineage.md) | E1, conflicts | Source roles and precedence |
| [examples/monochrome/README.md](references/examples/monochrome/README.md) | S5, on demand | A GitHub-native finished page with no HTML or palette (fictional fixture) |
| [Architecture example scope note](references/examples/project-specific-architecture/README.md) | S2 or S5, on demand | Section map into the large example and its render warning |
| [Template-to-realization case study](references/examples/project-specific-architecture/architecture-template-and-realization.md) | S2, architecture only | How the template grows into a finished document |
| `templates/` | T1 to T3 | Codebase document substrate |

## Tools

| Script | State | Purpose |
| --- | --- | --- |
| `scripts/doc_profile.py` | S1 | Read-only inventory of structure and visual devices |
| `scripts/claims_check.py` | S3 gate | Paths, scripts, modules, flags, and anchors resolve, without executing anything |
| `scripts/check_docs.py` | S6 gate | Structure, links, alt text, emoji, SPEC banner, section openings |
| `scripts/render_check.py` | S7 gate | GitHub's real HTML, stripped features, desktop, narrow, and grayscale views |
| `scripts/doc_gate.py` | S3, S6, S7, E3 | Runs the gates in order and routes findings to owning states |
| `scripts/doc_banner.py` | S4 | Optional portable SPEC banner from verified title and scope |
| `scripts/operator_lockin.py` | T1, T2, T4 | `init`, `check`, `export`, and `fork` for the codebase substrate |
| `scripts/package_skill.py` | E4 | Shareable zip without private images, plus manifest |
| `scripts/manifest_audit.py` | E4 receiver | Verifies every byte of an unpacked package against `MANIFEST.md` |

`render_check.py` and `doc_gate.py --render` need network access. Set `GITHUB_TOKEN` to raise GitHub's anonymous limit of 60 requests per hour. Flatpak and Snap browsers can only write to folders such as `~/Downloads`; pass `--output` there when screenshots fail. Run the package tests with `python3 -m unittest discover -s tests -t .` from the skill root.

## EXIT report

End every track with:

- **Changed:** files touched, and the state that changed each one.
- **Gates:** each gate run, its verdict, and its counts. List skipped gates with the reason.
- **Routed and resolved:** findings that looped back, and where they were fixed.
- **Open:** blockers that hit the loop bound, accepted warnings with their reason, and unverifiable claims.

A clean gate does not replace content, evidence, accessibility, or rendering judgment. It proves only what that gate checks.
