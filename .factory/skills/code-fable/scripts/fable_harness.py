#!/usr/bin/env python3
"""
fable_harness.py — Portable Agnostic Mini-Harness for the Book of Somnus (Code Fables).

Subcommands:
    status   — Overview of all Scrolls in fables/ with metrics and Voice Gravity scores
    lint     — Deep literary, symbolic, and anti-LLM-tell audit
    brief    — Generate a Cloud Deep-Research "Data-Agent over Memory" Scroll prompt
    book     — Compile or preview the unified Book of Somnus from fables/
    package  — Bundle this mini-harness into a clean portable .zip for any agent
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FABLES_DIR = SKILL_DIR / "fables"
REFERENCES_DIR = SKILL_DIR / "references"


def analyze_scroll(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    words = len(text.split())

    # Title
    title = path.stem
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # 1. Movements (## Headings) & Woven Scroll Epigraphs (> *...* right after ## )
    movements: list[str] = []
    epigraphs: list[str] = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            movements.append(line[3:].strip())
            # Look ahead up to 4 lines for a blockquote epigraph
            for j in range(i + 1, min(i + 6, len(lines))):
                candidate = lines[j].strip()
                if not candidate:
                    continue
                if candidate.startswith("> *") or candidate.startswith(">*"):
                    epigraphs.append(candidate.lstrip("> ").strip("*").strip())
                break

    # 2. Fenced code / ASCII diagram blocks
    code_blocks = re.findall(r"```[\s\S]*?```", text)
    ascii_diagrams = [
        b for b in code_blocks if any(tok in b for tok in ("->", "↓", "┌", "│", "└", "──"))
    ]

    # 3. FAQ-style question subheaders
    headings = [line for line in lines if re.match(r"^#{1,4}\s+", line)]
    question_headings = [h for h in headings if h.strip().endswith("?")]

    # 4. Fourth-wall / meta-methodology self-references
    meta_patterns = [
        r"code-fable methodology",
        r"supplied fable-writing method",
        r"The Stones Beneath the Fable",
        r"What the record establishes",
        r"Source notes",
    ]
    meta_hits = []
    for idx, line in enumerate(lines, start=1):
        for pat in meta_patterns:
            if re.search(pat, line, re.IGNORECASE):
                meta_hits.append((idx, line.strip()))

    # 5. Spec/roadmap backlog drift
    roadmap_hits = []
    for idx, line in enumerate(lines, start=1):
        if re.search(
            r"\bThe (first|second|third|fourth|fifth|sixth)\s+(v\d+\.\d+\s+)?(instrument|acceleration|step|milestone|priority)\b",
            line,
            re.IGNORECASE,
        ):
            roadmap_hits.append((idx, line.strip()))

    # 6. LLM-Tell #1: Negative-contrast crutch ("Not X." standalone paragraphs or runs)
    in_code = False
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line.strip():
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line.strip())
    if current:
        paragraphs.append(" ".join(current))

    body_paragraphs = [
        p for p in paragraphs if not p.startswith("#") and not p.startswith(">") and not p.startswith("-")
    ]

    not_fragments = [
        p for p in body_paragraphs
        if re.match(r"^(Not|It is not|It was not|Nor)\b", p) and len(p.split()) <= 12
    ]
    max_not_run = 0
    cur_not_run = 0
    for p in body_paragraphs:
        if re.match(r"^(Not|It is not|It was not|Nor)\b", p) and len(p.split()) <= 12:
            cur_not_run += 1
            max_not_run = max(max_not_run, cur_not_run)
        else:
            cur_not_run = 0

    # 7. LLM-Tell #2: Throat-clearing announcements
    throat_clearing_patterns = [
        r"\bHere is the single most important\b",
        r"\bThis may be the second most important\b",
        r"\bThat distinction matters enormously\b",
        r"\bRead that again\b",
        r"\bThis is where the story gets interesting\b",
    ]
    throat_hits = []
    for idx, line in enumerate(lines, start=1):
        for pat in throat_clearing_patterns:
            if re.search(pat, line, re.IGNORECASE):
                throat_hits.append((idx, line.strip()))

    # 8. LLM-Tell #3: Raw benchmark decimal anxiety in prose (e.g., "4.066 milliseconds")
    decimal_benchmark_hits = []
    for idx, line in enumerate(lines, start=1):
        if re.search(r"\b\d+\.\d{2,}\s*(milliseconds|ms)\b", line, re.IGNORECASE):
            decimal_benchmark_hits.append((idx, line.strip()))

    # 9. LLM-Tell #4: Staccato one-line paragraph cadence
    short_paras = [p for p in body_paragraphs if len(p.split()) <= 10]
    short_ratio = (len(short_paras) / len(body_paragraphs)) if body_paragraphs else 0.0
    max_short_run = 0
    cur_run = 0
    for p in body_paragraphs:
        if len(p.split()) <= 12:
            cur_run += 1
            max_short_run = max(max_short_run, cur_run)
        else:
            cur_run = 0

    # 10. Second-person chronicler intimacy
    you_count = len(re.findall(r"\b(you|your|yours)\b", text, re.IGNORECASE))

    # Extract governing question (last bold question in the scroll)
    bold_questions = re.findall(r"\*\*([^*]+\?)\*\*", text)
    governing_question = bold_questions[-1].strip() if bold_questions else "(None detected)"

    # Build warnings & Voice Gravity Score (100 base)
    score = 100
    warnings: list[str] = []

    if len(code_blocks) > 0:
        score -= 15
        warnings.append(
            f"ASCII/Code block bloat: {len(code_blocks)} fenced blocks ({len(ascii_diagrams)} ASCII diagrams). "
            "Scrolls are pure literary prose."
        )
    if question_headings:
        score -= 15
        warnings.append(
            f"FAQ subheader drift: {len(question_headings)} question heading(s) (e.g. '{question_headings[0]}')."
        )
    if meta_hits:
        score -= 20
        warnings.append(
            f"Fourth-wall meta-audit break at line {meta_hits[0][0]}: '{meta_hits[0][1][:75]}'."
        )
    if roadmap_hits:
        score -= 15
        warnings.append(
            f"Spec/roadmap backlog drift at line {roadmap_hits[0][0]}."
        )
    if len(epigraphs) < max(1, len(movements) // 2):
        score -= 10
        warnings.append(
            f"Missing Woven Scroll Epigraphs: {len(epigraphs)}/{len(movements)} movements open with a `> *...*` epigraph."
        )
    if max_not_run >= 3 or len(not_fragments) > 6:
        score -= 10
        warnings.append(
            f"LLM-Tell (Negative-Contrast Crutch): {len(not_fragments)} short 'Not X.' fragments "
            f"(max consecutive run: {max_not_run}). Weave contrasts into full sentences."
        )
    if throat_hits:
        score -= 8
        warnings.append(
            f"LLM-Tell (Throat-Clearing Announcement) at line {throat_hits[0][0]}: '{throat_hits[0][1][:70]}'."
        )
    if decimal_benchmark_hits:
        score -= 8
        warnings.append(
            f"LLM-Tell (Benchmark Decimal Anxiety) at line {decimal_benchmark_hits[0][0]}: '{decimal_benchmark_hits[0][1][:70]}'. "
            "Translate raw benchmark decimals into literary precision."
        )
    if max_short_run >= 8 or short_ratio > 0.35:
        score -= 10
        warnings.append(
            f"LLM-Tell (Staccato Cadence): {short_ratio:.0%} of paragraphs are <=10 words "
            f"(max consecutive short run: {max_short_run}). Build fuller, breathing paragraphs."
        )
    if you_count < 35:
        score -= 10
        warnings.append(
            f"Weak chronicler witness: only {you_count} second-person ('you'/'your') references."
        )

    score = max(0, score)

    return {
        "file": path.name,
        "path": path,
        "title": title,
        "lines": len(lines),
        "words": words,
        "movements": len(movements),
        "epigraphs": len(epigraphs),
        "epigraph_list": epigraphs,
        "you_count": you_count,
        "not_fragments": len(not_fragments),
        "max_not_run": max_not_run,
        "short_para_ratio": round(short_ratio, 2),
        "max_short_run": max_short_run,
        "governing_question": governing_question,
        "score": score,
        "warnings": warnings,
    }


def cmd_status(_args: argparse.Namespace) -> int:
    scrolls = sorted(FABLES_DIR.glob("*.md"))
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                   BOOK OF SOMNUS — SCROLL ARCHIVE STATUS                     ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    for p in scrolls:
        r = analyze_scroll(p)
        badge = "SCROLL PURE" if not r["warnings"] else f"{len(r['warnings'])} NOTE(S)"
        print(f"• {r['file']:<22} | Gravity: {r['score']:>3}/100 [{badge}]")
        print(f"  Title:     {r['title']}")
        print(
            f"  Metrics:   {r['words']} words | {r['movements']} movements | "
            f"{r['epigraphs']}/{r['movements']} woven epigraphs | {r['you_count']} 'you/your' refs"
        )
        print(f"  Question:  {r['governing_question'][:95]}...")
        print()
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    if args.all or not args.paths:
        targets = sorted(FABLES_DIR.glob("*.md"))
    else:
        targets = [Path(p) for p in args.paths]

    for path in targets:
        r = analyze_scroll(path)
        status = "SCROLL PURE (GOLD)" if not r["warnings"] else f"{len(r['warnings'])} DRIFT WARNING(S)"
        print(f"=== {r['file']} | Voice Gravity: {r['score']}/100 [{status}] ===")
        print(
            f"  Words: {r['words']} | Movements: {r['movements']} | Epigraphs: {r['epigraphs']}/{r['movements']} | "
            f"Second-person ('you/your'): {r['you_count']} | Short-para ratio: {r['short_para_ratio']:.0%} "
            f"(max run: {r['max_short_run']}) | 'Not X.' fragments: {r['not_fragments']} (max run: {r['max_not_run']})"
        )
        for w in r["warnings"]:
            print(f"  [!] {w}")
        print()
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    questions = [q.strip() for q in (args.questions or "").split(",") if q.strip()]
    q_block = "\n".join(f"- {q}" for q in questions) if questions else "- Trace the true births, the mask vs. the organism underneath, the failed rituals, and the approaching horizon."

    prompt = f"""# DEEP-RESEARCH SCROLL BRIEF: {args.project}
{f'> *{args.subtitle}*' if args.subtitle else ''}

You are operating as a **Data-Agent over the lived memories of {args.project}**.
Do **not** treat this as a software specification, filetree audit, or release log. Code is temporary skin; only the causal history, the human corrections, the disproven illusions, and the evolving purpose endure.

## 1. Cognitive Posture: The Scroll Chronicler
- Write directly to the maker (`Daeron`, `you`) with austere, unhurried, diamond-hard gravity.
- Practice **Truthsense**: separate the outer mask the system wore to enter the world from the real hunger that caused it to be built or resurrected.
- Hunt for the **Rosetta Stone sentences** in the memory record—the exact moments where Daeron corrected a false assumption or named what the system was truly for.
- Record **Failed Rituals** honestly: where ceremony, blind search, or a misapplied abstraction failed empirically, and what law that failure taught.

## 2. Structural & Literary Architecture
- **Woven Chapter Epigraphs**: Open every major movement (`## Heading`) with a 2–3 sentence italicized blockquote epigraph (`> *...*`) that distills the symbolic law of that movement before telling its history.
- **Dissolve All Questions into Narrative**: Answer every question below inside the chronological and symbolic turns of the scroll—never use FAQ headers (`### Question?`):
{q_block}
- **The Closing Parable & Single Governing Question**: In the final movement (`## The thing to remember before the evolution`), gather the symbols from your epigraphs into a complete parable, followed by a blockquote synthesis of the arc and the single governing question the experiment was built to answer.

## 3. Forbidden Cheapness (Strict Bans)
- **Zero ASCII diagrams or fenced code blocks.**
- **Zero negative-contrast spam** (do not stack `"Not X. Not Y. Not Z."` sentences).
- **Zero throat-clearing announcements** (never write `"Here is the single most important thing"` or `"That distinction matters"`).
- **Zero benchmark decimal clutter** in the narrator's mouth (translate `4.066ms` into `"under four thousandths of a second—inside the six-millisecond bell"`).
- **Zero staccato slide-deck paragraphs** (write full, breathing paragraphs of 3–6 sentences; save single-line turns for rare fulcrums).
"""
    if args.output:
        out_path = Path(args.output)
        out_path.write_text(prompt, encoding="utf-8")
        print(f"Wrote Deep-Research Scroll Brief to {out_path}")
    else:
        print(prompt)
    return 0


def cmd_book(args: argparse.Namespace) -> int:
    scrolls = sorted(FABLES_DIR.glob("*.md"))
    now = datetime.now().strftime("%Y-%m-%d")
    parts: list[str] = [
        "# The Book of Somnus: Scrolls of the Living Archive",
        "",
        f"> *Compiled {now}. These scrolls are not specifications, nor laws to bind the hand of the coder. They are the memory of why each work was born, what masks it wore, which rituals it outgrew, and what question it was built to ask.*",
        "",
        "## Table of Scrolls",
        "",
    ]

    analyzed = [analyze_scroll(p) for p in scrolls]
    for idx, r in enumerate(analyzed, start=1):
        parts.append(f"{idx}. **{r['title']}** (`fables/{r['file']}`) — *{r['words']} words*")
        parts.append(f"   - **Governing Question:** *{r['governing_question']}*")

    parts.append("\n---\n")
    index_text = "\n".join(parts)
    for r in analyzed:
        parts.append(r["path"].read_text(encoding="utf-8").strip())
        parts.append("\n\n---\n")

    book_text = "\n".join(parts)
    if args.output:
        out = Path(args.output)
        out.write_text(book_text, encoding="utf-8")
        print(f"Compiled Book of Somnus ({len(analyzed)} scrolls, {len(book_text.split())} words) -> {out}")
    else:
        print(index_text)
        print(f"[Index preview complete. Pass --output BOOK_OF_SOMNUS.md to compile the full {len(book_text.split())}-word volume.]")
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    out_path = Path(args.output) if args.output else SKILL_DIR / "code-fable-harness.zip"
    included = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(SKILL_DIR.rglob("*")):
            if file_path.is_dir():
                continue
            if file_path.resolve() == out_path.resolve():
                continue
            if any(part.startswith(".") or part == "__pycache__" for part in file_path.relative_to(SKILL_DIR).parts):
                continue
            arcname = Path("code-fable") / file_path.relative_to(SKILL_DIR)
            zf.write(file_path, arcname)
            included += 1
    print(f"Packaged {included} files into portable mini-harness archive: {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Code-Fable Portable Mini-Harness CLI")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="Show archive status and Voice Gravity scores for all Scrolls")

    p_lint = sub.add_parser("lint", help="Run deep literary & anti-LLM-tell linter on Scrolls")
    p_lint.add_argument("paths", nargs="*", help="Scroll files to lint")
    p_lint.add_argument("--all", action="store_true", help="Lint all Scrolls in fables/")

    p_brief = sub.add_parser("brief", help="Generate a Cloud Deep-Research Scroll prompt pack")
    p_brief.add_argument("project", help="Name of the project/system")
    p_brief.add_argument("--subtitle", default="", help="Optional subtitle or core tension")
    p_brief.add_argument("--questions", default="", help="Comma-separated list of questions to dissolve into the Scroll")
    p_brief.add_argument("--output", default="", help="Optional file path to save the brief")

    p_book = sub.add_parser("book", help="Compile or preview the Book of Somnus from fables/")
    p_book.add_argument("--output", default="", help="Output markdown path for the full compiled Book")

    p_pkg = sub.add_parser("package", help="Bundle this mini-harness into a portable .zip")
    p_pkg.add_argument("--output", default="", help="Output .zip path")

    args = parser.parse_args()
    if not args.cmd or args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "lint":
        return cmd_lint(args)
    if args.cmd == "brief":
        return cmd_brief(args)
    if args.cmd == "book":
        return cmd_book(args)
    if args.cmd == "package":
        return cmd_package(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
