#!/usr/bin/env python3
"""Check Markdown structure, local references, assets, and SPEC banners."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit


MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx"}
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+\S")
HTML_H1 = re.compile(r"<\s*h1\b[^>]*>.*?</\s*h1\s*>", re.IGNORECASE | re.DOTALL)
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)")
HTML_TARGET = re.compile(r"\b(?:href|src)\s*=\s*([\"'])(.*?)\1", re.IGNORECASE)
IMAGE_ALT = re.compile(r"!\[([^\]]*)\]\(", re.IGNORECASE)
HTML_TAG = re.compile(r"<\s*(img|svg)\b[^>]*>", re.IGNORECASE | re.DOTALL)
REFERENCE_DEF = re.compile(r"^\s{0,3}\[(?!\^)([^\]]+)\]:\s*(<[^>]+>|\S+)")
EMPTY_ALT_IMAGE = re.compile(r"!\[\s*\]\(")
IMG_ELEMENT = re.compile(r"<\s*img\b[^>]*>", re.IGNORECASE | re.DOTALL)
IMG_ALT = re.compile(r"\balt\s*=\s*([\"'])\s*\S.*?\1", re.IGNORECASE | re.DOTALL)
# Pictographic planes plus the emoji presentation selector; text symbols such as ✓ are left alone.
EMOJI = re.compile("[\U0001F000-\U0001FAFF\uFE0F]")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".somnus-debug", ".python_doctor", "render-check"}
SPEC_TITLE_WINDOW = 20
SPEC_SCOPE_LABEL = re.compile(
    r"^\s*(?:>\s*)?(?:\*\*)?(?:scope|applies to|governs)(?:\*\*)?:|^\s*(?:>\s*)?(?:\*\*)?(?:scope|applies to|governs):\*\*",
    re.IGNORECASE,
)
SPEC_SCOPE_STATEMENT = re.compile(
    r"^\s*>\s*(?:this specification\s+)?(?:defines?|specifies?|establishes?|governs?|covers?|applies to|sets out)\b\s+\S.+$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    level: str
    path: Path
    message: str

    def render(self, root: Path) -> str:
        try:
            label = self.path.relative_to(root)
        except ValueError:
            label = self.path
        return f"{self.level}: {label}: {self.message}"


def visible_lines(text: str) -> Iterable[tuple[int, str]]:
    """Yield non-fenced lines while respecting fence character and length."""
    active_char: str | None = None
    active_length = 0
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_OPEN.match(line)
        if active_char is None:
            if match:
                marker = match.group(1)
                active_char, active_length = marker[0], len(marker)
                continue
            yield number, line
            continue
        if match:
            marker = match.group(1)
            rest = line[match.end():].strip()
            if marker[0] == active_char and len(marker) >= active_length and not rest:
                active_char, active_length = None, 0


def collect_markdown(paths: list[str], root: Path) -> tuple[list[Path], list[Finding]]:
    files: list[Path] = []
    findings: list[Finding] = []
    for raw in paths:
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        if not path.exists():
            findings.append(Finding("ERROR", path, "does not exist"))
        elif path.is_dir():
            files.extend(
                child for child in path.rglob("*")
                if child.is_file()
                and child.suffix.lower() in MARKDOWN_SUFFIXES
                and not any(part in IGNORED_DIRS for part in child.parts)
            )
        elif path.suffix.lower() not in MARKDOWN_SUFFIXES:
            findings.append(Finding("ERROR", path, "is not a Markdown file"))
        elif not path.is_file():
            findings.append(Finding("ERROR", path, "is not a regular file"))
        else:
            files.append(path)
    return sorted(set(files)), findings


def link_path(target: str, document: Path, root: Path) -> Path | None:
    target = target.strip().strip("<>")
    parsed = urlsplit(target)
    if parsed.scheme or target.startswith("//") or not parsed.path:
        return None
    decoded = unquote(parsed.path)
    candidate = Path(decoded)
    return (root / candidate.relative_to("/")) if candidate.is_absolute() else (document.parent / candidate)


def has_accessible_banner_visual(text: str) -> bool:
    """Recognize a non-empty image alt or a labeled SVG near the page opening."""
    if any(match.group(1).strip() for match in IMAGE_ALT.finditer(text)):
        return True
    for match in HTML_TAG.finditer(text):
        tag, source = match.group(1).lower(), match.group(0)
        if tag == "img" and re.search(r"\balt\s*=\s*([\"'])\s*\S.*?\1", source, re.IGNORECASE | re.DOTALL):
            return True
        if tag == "svg" and (
            re.search(r"\baria-label(?:ledby)?\s*=", source, re.IGNORECASE)
            or re.search(r"\brole\s*=\s*([\"'])img\1", source, re.IGNORECASE)
        ):
            return True
    return False


def spec_scope_cue(lines: list[str]) -> bool:
    """Require an explicit scope label or a descriptive blockquote statement."""
    for line in lines:
        if SPEC_SCOPE_LABEL.match(line):
            content = SPEC_SCOPE_LABEL.sub("", line).strip(" *:—-\t")
            if len(content) >= 8:
                return True
        if SPEC_SCOPE_STATEMENT.match(line):
            statement = re.sub(r"^\s*>\s*", "", line).strip()
            if len(statement) >= 30:
                return True
    return False


def strip_front_matter(lines: list[str]) -> list[str]:
    """Ignore YAML metadata when checking whether a visible banner opens a page."""
    if not lines or lines[0].strip() != "---":
        return lines
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() in {"---", "..."}:
            return lines[index + 1:]
    return lines


def is_legacy_reference(path: Path, root: Path) -> bool:
    """Keep historical examples readable without treating them as current style."""
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return len(relative.parts) >= 2 and relative.parts[:2] == ("references", "legacy")


def composition_findings(path: Path, text: str, visible: list[tuple[int, str]]) -> list[Finding]:
    """Warn when an H2 opens with a device instead of a sentence stating the section's job."""
    raw = text.splitlines()
    findings: list[Finding] = []
    for number, line in visible:
        match = HEADING.match(line)
        if not match or len(match.group(1)) != 2:
            continue
        following = next((candidate for candidate in raw[number:] if candidate.strip()), None)
        if following is None:
            findings.append(Finding("WARNING", path, f"H2 at line {number} has no content"))
            continue
        stripped = following.strip()
        if FENCE_OPEN.match(following):
            opener = "a code fence"
        elif HEADING.match(following):
            opener = "another heading"
        elif stripped.startswith("|"):
            opener = "a table"
        elif LIST_ITEM.match(following):
            opener = "a list"
        elif stripped.startswith(("<", "![")):
            opener = "an image or HTML block"
        else:
            continue
        findings.append(Finding(
            "WARNING", path,
            f"H2 at line {number} opens with {opener}; lead with a sentence that states the section's job",
        ))
    return findings


def inspect_document(
    path: Path,
    root: Path,
    *,
    check_external_assets: bool = False,
    check_renderer_features: bool = False,
    check_composition: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Finding("ERROR", path, "is not valid UTF-8 Markdown")]

    visible = list(visible_lines(text))
    visible_text = "\n".join(line for _, line in visible)

    active_char: str | None = None
    active_length = 0
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_OPEN.match(line)
        if active_char is None:
            if match:
                marker = match.group(1)
                active_char, active_length = marker[0], len(marker)
        elif match:
            marker = match.group(1)
            rest = line[match.end():].strip()
            if marker[0] == active_char and len(marker) >= active_length and not rest:
                active_char, active_length = None, 0
    if active_char is not None:
        findings.append(Finding("ERROR", path, "has an unclosed fenced block"))

    headings: list[tuple[int, int]] = []
    for line_number, line in visible:
        match = HEADING.match(line)
        if match:
            headings.append((line_number, len(match.group(1))))
    markdown_h1_count = sum(level == 1 for _, level in headings)
    html_h1_count = len(HTML_H1.findall(visible_text))
    title_cue = markdown_h1_count > 0 or html_h1_count > 0
    visual_banner = has_accessible_banner_visual("\n".join(line for _, line in visible[:50]))
    if not is_legacy_reference(path, root):
        if markdown_h1_count + html_h1_count > 1:
            findings.append(Finding("WARNING", path, "has multiple H1 elements; confirm the title hierarchy is deliberate"))
        elif not title_cue and not visual_banner:
            findings.append(Finding("WARNING", path, "no Markdown/HTML H1 or accessible image/SVG banner cue was recognized"))
        for (line_number, level), (_, previous_level) in zip(headings[1:], headings):
            if level > previous_level + 1:
                findings.append(Finding("WARNING", path, f"heading level jumps at line {line_number}"))

    if not is_legacy_reference(path, root):
        missing_alt = len(EMPTY_ALT_IMAGE.findall(visible_text)) + sum(
            not IMG_ALT.search(match.group(0)) for match in IMG_ELEMENT.finditer(visible_text)
        )
        if missing_alt:
            findings.append(Finding(
                "WARNING", path,
                f"has {missing_alt} image(s) with empty or missing alt text; describe informative images or confirm they are decorative",
            ))
        emoji_count = len(EMOJI.findall(visible_text))
        if emoji_count:
            findings.append(Finding("WARNING", path, f"contains {emoji_count} emoji character(s); public docs in this system do not use emoji"))
        if check_composition:
            findings.extend(composition_findings(path, text, visible))

    if path.name.casefold() == "spec.md":
        opening = strip_front_matter([line for _, line in visible])[:SPEC_TITLE_WINDOW]
        opening_title = any(HEADING.match(line) and HEADING.match(line).group(1) == "#" for line in opening)
        opening_html_title = bool(HTML_H1.search("\n".join(opening)))
        opening_has_scope = spec_scope_cue(opening)
        if not (opening_title or opening_html_title) or not opening_has_scope:
            missing = []
            if not (opening_title or opening_html_title):
                missing.append("a visible title near the opening")
            if not opening_has_scope:
                missing.append("an explicit scope statement (for example, `> Defines ...` or `**Scope:** ...`)")
            findings.append(Finding(
                "ERROR", path,
                "SPEC must begin with an identity banner containing " + " and ".join(missing),
            ))

    remote_image_count = 0
    for match in INLINE_LINK.finditer(visible_text):
        target = match.group(1)
        is_image = match.group(0).startswith("!")
        parsed = urlsplit(target.strip("<>"))
        if is_image and parsed.scheme in {"http", "https", "data"}:
            remote_image_count += 1
            continue
        target_path = link_path(target, path, root)
        if target_path is None:
            continue
        if not target_path.exists():
            findings.append(Finding("ERROR", path, f"local {'image' if is_image else 'link'} target does not exist: {target.strip('<>')}"))

    for match in HTML_TARGET.finditer(visible_text):
        target = match.group(2).strip()
        parsed = urlsplit(target)
        is_image = match.group(0).lower().lstrip().startswith("src=")
        if is_image and parsed.scheme in {"http", "https", "data"}:
            remote_image_count += 1
            continue
        target_path = link_path(target, path, root)
        if target_path is not None and not target_path.exists():
            findings.append(Finding("ERROR", path, f"local HTML target does not exist: {target}"))

    for _, line in visible:
        definition = REFERENCE_DEF.match(line)
        if not definition:
            continue
        target = definition.group(2)
        target_path = link_path(target, path, root)
        if target_path is not None and not target_path.exists():
            findings.append(Finding("ERROR", path, f"local reference link target does not exist: {target.strip('<>')}"))

    if check_external_assets and remote_image_count:
        findings.append(Finding(
            "WARNING", path,
            f"uses {remote_image_count} remote or embedded image(s); confirm ownership, stability, and a text fallback",
        ))

    if check_renderer_features and re.search(
        r"<\s*style\b|\sstyle\s*=", visible_text, flags=re.IGNORECASE
    ):
        findings.append(Finding(
            "WARNING", path,
            "contains inline CSS; verify essential content and hierarchy in the target renderer",
        ))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories, relative to --root when not absolute")
    parser.add_argument("--root", default=".", help="repository root for relative input paths")
    parser.add_argument(
        "--check-external-assets", action="store_true",
        help="warn once per document when remote or embedded images are present",
    )
    parser.add_argument(
        "--check-renderer-features", action="store_true",
        help="warn when inline CSS needs review in the target renderer",
    )
    parser.add_argument(
        "--check-composition", action="store_true",
        help="warn when an H2 opens with a table, list, fence, image, or heading instead of a sentence",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files, findings = collect_markdown(args.paths, root)
    for path in files:
        findings.extend(inspect_document(
            path,
            root,
            check_external_assets=args.check_external_assets,
            check_renderer_features=args.check_renderer_features,
            check_composition=args.check_composition,
        ))

    for finding in findings:
        print(finding.render(root))
    errors = sum(finding.level == "ERROR" for finding in findings)
    warnings = sum(finding.level == "WARNING" for finding in findings)
    print(f"Checked {len(files)} Markdown file(s): {errors} error(s), {warnings} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
