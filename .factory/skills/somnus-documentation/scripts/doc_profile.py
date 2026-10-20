#!/usr/bin/env python3
"""Inventory Markdown structure and visual devices without scoring the style."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
from pathlib import Path

SUFFIXES = {".md", ".markdown", ".mdx"}
IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".somnus-debug", ".python_doctor", "render-check"}
FENCE = re.compile(r"^\s*(\x60{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
IMAGE = re.compile(r"!\[[^\]]*\]\(\s*[^)]+\)")
HTML = re.compile(r"<\s*(svg|img|div|span|table|details|summary)\b", re.I)
TABLE_RULE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
HEX_COLOR = re.compile(r"(?<![A-Za-z0-9])#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![A-Za-z0-9])")


def parse_markdown(lines):
    visible, blocks, mermaid = [], 0, 0
    active, size = None, 0
    for line in lines:
        match = FENCE.match(line)
        if active is None:
            if match:
                marker, info = match.group(1), match.group(2).strip().lower()
                active, size = marker[0], len(marker)
                blocks += 1
                if info.split(maxsplit=1)[:1] == ["mermaid"]:
                    mermaid += 1
            else:
                visible.append(line)
        elif match:
            marker = match.group(1)
            if marker[0] == active and len(marker) >= size and not line[match.end():].strip():
                active, size = None, 0
    return visible, blocks, mermaid


def inputs(paths, root):
    found = []
    for raw in paths:
        path = Path(raw)
        path = path if path.is_absolute() else root / path
        if not path.exists():
            raise FileNotFoundError(path)
        if path.is_dir():
            found.extend(
                child for child in path.rglob("*")
                if child.is_file()
                and child.suffix.lower() in SUFFIXES
                and not any(part in IGNORED for part in child.parts)
            )
        elif path.is_file() and path.suffix.lower() in SUFFIXES:
            found.append(path)
        else:
            raise ValueError("not a Markdown file or directory: {}".format(path))
    return sorted(set(found))


def inspect(path, root):
    text = path.read_text(encoding="utf-8")
    raw_lines = text.splitlines()
    visible, blocks, mermaid = parse_markdown(raw_lines)
    headings = []
    for line in visible:
        match = HEADING.match(line)
        if match:
            headings.append({"level": len(match.group(1)), "text": match.group(2).strip()})

    html = {name: 0 for name in ("svg", "img", "div", "span", "table", "details", "summary")}
    visible_text = "\n".join(visible)
    for match in HTML.finditer(visible_text):
        html[match.group(1).lower()] += 1
    try:
        display = str(path.relative_to(root))
    except ValueError:
        display = str(path)

    return {
        "path": display,
        "lines": len(raw_lines),
        "words": len(text.split()),
        "headings": headings,
        "fenced_blocks": blocks,
        "mermaid_blocks": mermaid,
        "markdown_images": len(IMAGE.findall(visible_text)),
        "html_elements": html,
        "markdown_tables": sum(bool(TABLE_RULE.match(line)) for line in visible),
        "remote_badge_refs": visible_text.count("shields.io"),
        "frequent_color_values": Counter(color.lower() for color in HEX_COLOR.findall(visible_text)).most_common(8),
    }


def render(items, all_headings):
    for item in items:
        counts = []
        for level in range(1, 7):
            count = sum(h["level"] == level for h in item["headings"])
            if count:
                counts.append("H{}={}".format(level, count))
        html = [key + "=" + str(value) for key, value in item["html_elements"].items() if value]
        print(item["path"])
        print("  {} lines · {} words · {}".format(item["lines"], item["words"], " ".join(counts) or "no Markdown headings"))
        print("  fences={} (Mermaid={}) · tables={} · Markdown images={} · remote badge refs={}".format(
            item["fenced_blocks"], item["mermaid_blocks"], item["markdown_tables"],
            item["markdown_images"], item["remote_badge_refs"]))
        print("  HTML devices: {}".format(", ".join(html) or "none"))
        colors = ["{} ({})".format(color, count) for color, count in item["frequent_color_values"]]
        print("  Frequent inline colors (reference only): {}".format(", ".join(colors) or "none"))
        shown = item["headings"] if all_headings else [h for h in item["headings"] if h["level"] <= 2]
        if shown:
            print("  Outline:")
            for h in shown:
                indent = "  " * (h["level"] - 1)
                print("    {}H{} {}".format(indent, h["level"], h["text"]))
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories")
    parser.add_argument("--root", default=".", help="base directory for relative paths")
    parser.add_argument("--all-headings", action="store_true", help="include every heading level")
    parser.add_argument("--json", action="store_true", help="write the inventory as JSON")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        items = [inspect(path, root) for path in inputs(args.paths, root)]
    except (OSError, UnicodeError, ValueError) as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(items, indent=2))
    else:
        render(items, args.all_headings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
