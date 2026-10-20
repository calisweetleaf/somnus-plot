#!/usr/bin/env python3
"""Check that Markdown documentation's concrete claims resolve against a repository.

Four claim types are verified without executing anything:

1. Inline-code repository paths (`src/app.py`) exist.
2. Shell fences that invoke a local script or `python -m` module reference something real.
3. `--flags` passed to a local script literally appear in that script's source.
4. In-page and cross-file `#anchor` links, inline or reference-style, resolve to a real heading or HTML id.

Missing anchors are errors. Missing directory-qualified paths, scripts, modules, and flags are warnings
unless `--strict` is given, because documentation may legitimately describe output
paths or files that exist only after a command runs.
"""

from __future__ import annotations

import argparse
import fnmatch
import functools
import re
import shlex
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlsplit

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from scripts.check_docs import (  # noqa: E402
    FENCE_OPEN,
    HEADING,
    INLINE_LINK,
    REFERENCE_DEF,
    Finding,
    collect_markdown,
    IGNORED_DIRS,
    is_legacy_reference,
    visible_lines,
)


INLINE_CODE = re.compile(r"`([^`\n]+)`")
HTML_ID = re.compile(r"\b(?:id|name)\s*=\s*([\"'])(.+?)\1", re.IGNORECASE)
SHELL_LANGS = {"bash", "sh", "shell", "console", "zsh"}
PYTHON_LAUNCHER = re.compile(r"^python(?:3(?:\.\d+)?)?$")
FILE_EXTENSIONS = (
    "py", "md", "sh", "toml", "json", "yaml", "yml", "txt", "cfg", "ini",
    "ts", "tsx", "js", "mjs", "rs", "go", "c", "cc", "cpp", "h", "hpp",
    "png", "svg", "jpg", "jpeg",
)
BARE_FILE = re.compile(r"^[\w.\-]+\.(?:" + "|".join(FILE_EXTENSIONS) + r")$")
PLACEHOLDER_CHARS = set("*<>{}$~|&;=()[]!?,\"'\\")
FLAG = re.compile(r"^--[A-Za-z][\w\-]*")
MAX_SOURCE_BYTES = 1_000_000


@dataclass(frozen=True)
class FencedBlock:
    """One fenced code block with its language label and first content line number."""

    language: str
    start_line: int
    lines: tuple[str, ...]


def fenced_blocks(text: str) -> list[FencedBlock]:
    """Return every closed fenced block, honoring fence character and length."""
    blocks: list[FencedBlock] = []
    active_char: str | None = None
    active_length = 0
    language = ""
    start = 0
    body: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE_OPEN.match(line)
        if active_char is None:
            if match:
                marker = match.group(1)
                active_char, active_length = marker[0], len(marker)
                info = line[match.end():].strip().split()
                language = info[0].lower() if info else ""
                start, body = number + 1, []
            continue
        if match:
            marker = match.group(1)
            rest = line[match.end():].strip()
            if marker[0] == active_char and len(marker) >= active_length and not rest:
                blocks.append(FencedBlock(language, start, tuple(body)))
                active_char, active_length = None, 0
                continue
        body.append(line)
    return blocks


def github_slug(heading_text: str) -> str:
    """Approximate GitHub's heading-to-anchor transform."""
    text = re.sub(r"<[^>]+>", "", heading_text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\s#+\s*$", "", text).replace("`", "").strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def collect_anchors(text: str) -> set[str]:
    """Return heading slugs (with GitHub duplicate suffixes) and HTML id/name values."""
    anchors: set[str] = set()
    seen: Counter[str] = Counter()
    visible = list(visible_lines(text))
    for _, line in visible:
        if HEADING.match(line):
            base = github_slug(re.sub(r"^#{1,6}\s+", "", line))
            count = seen[base]
            anchors.add(base if count == 0 else f"{base}-{count}")
            seen[base] += 1
    for match in HTML_ID.finditer("\n".join(line for _, line in visible)):
        anchors.add(match.group(2).strip().lower())
    return anchors


def resolve_path(candidate: str, document: Path, root: Path) -> Path | None:
    """Find an existing path relative to the repository root or the document's folder."""
    cleaned = candidate[2:] if candidate.startswith("./") else candidate
    for base in (root, document.parent):
        target = base / cleaned
        if target.exists():
            return target
    return None


@functools.lru_cache(maxsize=8)
def basename_index(root: Path) -> frozenset[str]:
    """Return every file name present anywhere under the repository root."""
    return frozenset(
        child.name
        for child in root.rglob("*")
        if child.is_file() and not any(part in IGNORED_DIRS for part in child.parts)
    )


def path_candidate(code: str, document: Path, root: Path) -> str | None:
    """Return a checkable repository path from inline code, or None when it is not one.

    A slash-containing token counts only when its first segment is a real directory,
    which keeps prose such as `read/write` or `client/server` from being flagged.
    """
    token = re.sub(r"(?::\d+(?::\d+)?|::\w+)$", "", code.strip())
    if not token or token.startswith(("-", "/", "#", "@", "http://", "https://")):
        return None
    if any(char in PLACEHOLDER_CHARS or char.isspace() for char in token) or ".." in token.strip("./"):
        return None
    if "/" in token:
        first = token[2:].split("/", 1)[0] if token.startswith("./") else token.split("/", 1)[0]
        return token if (root / first).is_dir() or (document.parent / first).is_dir() else None
    return token if BARE_FILE.match(token) else None


def split_commands(tokens: list[str]) -> list[list[str]]:
    """Split a tokenized shell line on pipeline and list operators."""
    commands: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= set("|&;"):
            commands.append([])
        else:
            commands[-1].append(token)
    return [command for command in commands if command]


def shell_lines(block: FencedBlock) -> Iterable[tuple[int, str]]:
    """Yield logical shell lines with backslash continuations joined and prompts stripped."""
    pending = ""
    pending_number = block.start_line
    for offset, raw in enumerate(block.lines):
        number = block.start_line + offset
        line = raw.strip()
        if not pending:
            pending_number = number
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"^[$>]\s+", "", line)
        if line.endswith("\\"):
            pending += line[:-1] + " "
            continue
        yield pending_number, (pending + line).strip()
        pending = ""
    if pending:
        yield pending_number, pending.strip()


def tokenize(line: str) -> list[str] | None:
    """Tokenize one shell line, returning None when it cannot be parsed."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return None


def command_target(command: list[str]) -> tuple[str, str, list[str]] | None:
    """Classify a simple command as ('script' | 'module', target, args), or None."""
    index = 0
    while index < len(command) and (
        re.match(r"^[A-Za-z_]\w*=", command[index]) or command[index] == "sudo"
    ):
        index += 1
    rest = command[index:]
    if not rest:
        return None
    head = rest[0]
    if PYTHON_LAUNCHER.match(head) or head in {"bash", "sh"}:
        if len(rest) >= 3 and rest[1] == "-m" and PYTHON_LAUNCHER.match(head):
            return "module", rest[2], rest[3:]
        if len(rest) >= 2 and not rest[1].startswith("-"):
            return "script", rest[1], rest[2:]
        return None
    if head.startswith("./") or ("/" in head and BARE_FILE.match(head.rsplit("/", 1)[-1])):
        return "script", head, rest[1:]
    return None


def module_exists(module: str, root: Path) -> bool | None:
    """True/False when the top-level package lives in the repo; None when it is external."""
    parts = module.split(".")
    if not (root / parts[0]).exists() and not (root / f"{parts[0]}.py").exists():
        return None
    base = root.joinpath(*parts)
    return (
        base.with_suffix(".py").is_file()
        or (base / "__init__.py").is_file()
        or (base / "__main__.py").is_file()
        or base.is_dir()
    )


def read_source(path: Path) -> str | None:
    """Read a small text file, returning None when it is large or not UTF-8."""
    try:
        if not path.is_file() or path.stat().st_size > MAX_SOURCE_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_command_claims(
    path: Path, text: str, root: Path, soft: str
) -> list[Finding]:
    """Verify scripts, modules, and long flags used in shell fences."""
    findings: list[Finding] = []
    for block in fenced_blocks(text):
        if block.language not in SHELL_LANGS:
            continue
        for number, line in shell_lines(block):
            tokens = tokenize(line)
            if tokens is None:
                continue
            for command in split_commands(tokens):
                target = command_target(command)
                if target is None:
                    continue
                kind, name, args = target
                if kind == "module":
                    exists = module_exists(name, root)
                    if exists is False:
                        findings.append(Finding(soft, path, f"line {number}: module `{name}` is not in the repository"))
                    continue
                script = resolve_path(name, path, root)
                if script is None:
                    if "/" in name or name.endswith((".py", ".sh")):
                        findings.append(Finding(soft, path, f"line {number}: command references `{name}`, which does not exist"))
                    continue
                source = read_source(script)
                if source is None:
                    continue
                for arg in args:
                    flag = FLAG.match(arg)
                    if flag and flag.group(0) != "--help" and flag.group(0) not in source:
                        findings.append(Finding(
                            soft, path,
                            f"line {number}: flag `{flag.group(0)}` does not appear in the source of `{name}`",
                        ))
    return findings


def check_path_claims(
    path: Path, text: str, root: Path, soft: str, bare_names: bool
) -> list[Finding]:
    """Verify repository paths named in inline code outside fences.

    Bare file names resolve if that name exists anywhere in the repository. An
    unresolved bare name is reported only when `bare_names` is set, because
    documentation routinely mentions conventional names such as README.md generically.
    """
    findings: list[Finding] = []
    reported: set[str] = set()
    for number, line in visible_lines(text):
        for match in INLINE_CODE.finditer(line):
            candidate = path_candidate(match.group(1), path, root)
            if candidate is None or candidate in reported:
                continue
            if resolve_path(candidate, path, root) is not None:
                continue
            if "/" not in candidate and (candidate in basename_index(root) or not bare_names):
                continue
            reported.add(candidate)
            findings.append(Finding(soft, path, f"line {number}: path `{candidate}` does not exist"))
    return findings


def check_anchor_claims(
    path: Path, text: str, root: Path, cache: dict[Path, set[str]]
) -> list[Finding]:
    """Verify fragment links against headings and HTML ids in the target document."""
    findings: list[Finding] = []
    cache.setdefault(path, collect_anchors(text))
    for number, line in visible_lines(text):
        targets = [match.group(1) for match in INLINE_LINK.finditer(line)]
        definition = REFERENCE_DEF.match(line)
        if definition:
            targets.append(definition.group(2))
        for raw_target in targets:
            target = raw_target.strip().strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("//") or not parsed.fragment:
                continue
            fragment = unquote(parsed.fragment).lower()
            if re.match(r"^(l\d+(-l\d+)?$|user-content-)", fragment):
                continue
            if parsed.path:
                destination = resolve_path(unquote(parsed.path), path, root)
                if destination is None or destination.suffix.lower() not in {".md", ".markdown"}:
                    continue
            else:
                destination = path
            if destination not in cache:
                body = read_source(destination)
                if body is None:
                    continue
                cache[destination] = collect_anchors(body)
            if fragment not in cache[destination]:
                findings.append(Finding("ERROR", path, f"line {number}: anchor `#{parsed.fragment}` not found in {destination.name}"))
    return findings


def inspect_claims(
    path: Path, root: Path, *, strict: bool = False, bare_names: bool = False,
    cache: dict[Path, set[str]] | None = None,
) -> list[Finding]:
    """Run all claim checks on one Markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Finding("ERROR", path, "is not valid UTF-8 Markdown")]
    soft = "ERROR" if strict else "WARNING"
    anchors = cache if cache is not None else {}
    return (
        check_path_claims(path, text, root, soft, bare_names)
        + check_command_claims(path, text, root, soft)
        + check_anchor_claims(path, text, root, anchors)
    )


def excluded(path: Path, root: Path, patterns: list[str]) -> bool:
    """True when the path's repository-relative form matches any exclude glob."""
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        relative = path.as_posix()
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories, relative to --root when not absolute")
    parser.add_argument("--root", default=".", help="repository root used to resolve claimed paths")
    parser.add_argument("--strict", action="store_true", help="treat missing paths, scripts, modules, and flags as errors")
    parser.add_argument("--bare-names", action="store_true", help="also report bare file names (README.md) that exist nowhere in the repository")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="skip files whose root-relative path matches (repeatable)")
    parser.add_argument("--include-legacy", action="store_true", help="also check files under references/legacy")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files, findings = collect_markdown(args.paths, root)
    cache: dict[Path, set[str]] = {}
    checked = 0
    for path in files:
        if excluded(path, root, args.exclude) or (not args.include_legacy and is_legacy_reference(path, root)):
            continue
        checked += 1
        findings.extend(inspect_claims(path, root, strict=args.strict, bare_names=args.bare_names, cache=cache))

    for finding in findings:
        print(finding.render(root))
    errors = sum(finding.level == "ERROR" for finding in findings)
    warnings = sum(finding.level == "WARNING" for finding in findings)
    print(f"Checked claims in {checked} Markdown file(s): {errors} error(s), {warnings} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
