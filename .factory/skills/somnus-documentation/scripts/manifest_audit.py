#!/usr/bin/env python3
"""Verify MANIFEST.md hashes for the portable Operator Lock-In package.

Git is preferred when available, but this package is intentionally usable when
unzipped into a provider workspace with no VCS metadata. In that case the
manifest covers the deterministic package tree while excluding generated cache,
test, and archive outputs.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path


TICK = chr(96)
ROW_RE = re.compile(
    r"\| " + re.escape(TICK) + r"([^" + TICK + r"]+)" + re.escape(TICK)
    + r" \| (\d+) \| " + re.escape(TICK) + r"([a-f0-9]{64})" + re.escape(TICK)
    + r" \|"
)
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "artifacts", "dist", ".somnus-debug", ".python_doctor", "render-check"}
EXCLUDED_NAMES = {"MANIFEST.md"}


def git_tracked_files(root: Path) -> list[str] | None:
    """Return git paths when root is a repository; otherwise return None."""

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return [
        relative
        for relative in result.stdout.splitlines()
        if relative not in EXCLUDED_NAMES and (root / relative).is_file()
    ]


def portable_files(root: Path) -> list[str]:
    """Return deterministic package files for a non-git portable checkout."""

    files: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.name in EXCLUDED_NAMES or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        files.append(relative.as_posix())
    return sorted(files)


def tracked_files(root: Path) -> list[str]:
    """Return manifest inputs from git when possible, portable tree otherwise."""

    return git_tracked_files(root) or portable_files(root)


def manifest_row(root: Path, relative_path: str) -> str:
    data = (root / relative_path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return f"| {TICK}{relative_path}{TICK} | {len(data)} | {TICK}{digest}{TICK} |"


def rewrite_manifest(root: Path) -> int:
    path = root / "MANIFEST.md"
    rows = [manifest_row(root, relative_path) for relative_path in tracked_files(root)]
    path.write_text(
        "# Package Manifest\n\n"
        "MANIFEST.md is intentionally excluded from its own digest set.\n\n"
        "| File | Bytes | SHA256 |\n"
        "|---|---:|---|\n"
        + "\n".join(rows)
        + "\n",
        encoding="utf-8",
    )
    return 0


def manifest_rows(root: Path) -> list[tuple[str, str, str]]:
    path = root / "MANIFEST.md"
    if not path.is_file():
        return []
    return ROW_RE.findall(path.read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if len(sys.argv) > 1 and sys.argv[1] in ("--write", "-w"):
        rewrite_manifest(root)

    rows = manifest_rows(root)
    expected = tracked_files(root)
    row_relative_paths = [relative_path for relative_path, _size, _digest in rows]
    errors: list[str] = []
    expected_set = set(expected)
    row_set = set(row_relative_paths)
    missing = sorted(expected_set - row_set)
    stale = sorted(row_set - expected_set)
    duplicate = sorted(
        {relative_path for relative_path in row_relative_paths if row_relative_paths.count(relative_path) > 1}
    )

    if row_relative_paths != expected:
        if missing:
            errors.append("missing manifest entries: " + ", ".join(missing))
        if stale:
            errors.append("stale manifest entries: " + ", ".join(stale))
        if duplicate:
            errors.append("duplicate manifest entries: " + ", ".join(duplicate))
        if not missing and not stale and not duplicate:
            errors.append("manifest row order differs from deterministic file order")

    for relative_path, size, expected_digest in rows:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing file: {relative_path}")
            continue
        data = path.read_bytes()
        actual_digest = hashlib.sha256(data).hexdigest()
        if len(data) != int(size) or actual_digest != expected_digest:
            errors.append(f"mismatch: {relative_path}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"manifest audit: FAIL ({len(errors)} errors, {len(rows)} entries)", file=sys.stderr)
        return 1
    print(f"manifest audit: PASS ({len(rows)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
