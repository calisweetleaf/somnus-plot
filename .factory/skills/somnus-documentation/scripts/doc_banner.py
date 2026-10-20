#!/usr/bin/env python3
"""Print an optional portable identity banner for a SPEC.md file."""

from __future__ import annotations

import argparse


def one_line(value: str) -> str:
    """Keep supplied values on one Markdown line and protect table separators."""
    return " ".join(value.split()).replace("|", r"\|")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="verified document title")
    parser.add_argument("--scope", required=True, help="one sentence describing what the specification governs")
    parser.add_argument("--status", help="known reader-facing status; omit when unknown")
    parser.add_argument("--version", help="known document version; omit when unknown")
    args = parser.parse_args()

    title = one_line(args.title)
    scope = one_line(args.scope)
    status = one_line(args.status) if args.status is not None else ""
    version = one_line(args.version) if args.version is not None else ""
    if not title or not scope or (args.status is not None and not status) or (args.version is not None and not version):
        parser.error("title and scope must be visible; optional status and version must be visible when supplied")

    print(f"# {title}")
    print()
    print(f"> {scope}")
    if status or version:
        print()
        fields = []
        if status:
            fields.append(f"**Status:** {status}")
        if version:
            fields.append(f"**Document version:** {version}")
        print(" · ".join(fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
