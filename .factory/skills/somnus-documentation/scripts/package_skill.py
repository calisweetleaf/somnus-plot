#!/usr/bin/env python3
"""Export this skill as a shareable zip with a verifiable MANIFEST.md.

Private art-direction images under references/visual-references/ are excluded by
default because their source and publication rights are unverified. The staged copy
receives a MANIFEST.md written by scripts/manifest_audit.py, so a recipient can unzip
the archive and run `python3 scripts/manifest_audit.py` to confirm every byte.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DIRS = ("references/visual-references",)
EXCLUDED_PARTS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", "render-check", "dist", "artifacts",
    ".somnus-debug", ".python_doctor",
}
EXCLUDED_NAMES = {".directory", ".DS_Store", "MANIFEST.md"}


def skill_name(root: Path) -> str:
    match = re.search(r"^name:\s*(\S+)\s*$", (root / "SKILL.md").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise SystemExit("package-skill: SKILL.md front matter has no name field")
    return match.group(1)


def selected_files(root: Path, *, include_private: bool) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.name in EXCLUDED_NAMES or path.suffix == ".pyc":
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if not include_private and any(relative.as_posix().startswith(prefix + "/") for prefix in PRIVATE_DIRS):
            continue
        files.append(relative)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="zip path to create; must not already exist")
    parser.add_argument("--include-visual-references", action="store_true", help="also ship the private reference images")
    args = parser.parse_args()

    output = args.output.expanduser().resolve()
    if output.exists():
        print(f"package-skill: output must not already exist: {output}", file=sys.stderr)
        return 2
    name = skill_name(PACKAGE_ROOT)
    files = selected_files(PACKAGE_ROOT, include_private=args.include_visual_references)

    with tempfile.TemporaryDirectory() as temporary:
        staged = Path(temporary) / name
        for relative in files:
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PACKAGE_ROOT / relative, destination)
        audit = subprocess.run(
            [sys.executable, str(staged / "scripts" / "manifest_audit.py"), "--write"],
            capture_output=True, text=True,
        )
        if audit.returncode != 0:
            print(audit.stdout + audit.stderr, file=sys.stderr)
            return 1
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(staged.rglob("*")):
                if path.is_file():
                    bundle.write(path, (Path(name) / path.relative_to(staged)).as_posix())

    private = "included" if args.include_visual_references else "excluded"
    print(f"package-skill: {output} ({len(files) + 1} files, visual references {private})")
    print(f"package-skill: {audit.stdout.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
