#!/usr/bin/env python3
"""Install and project the Operator Lock-In document substrate safely.

The script copies only missing template roles. It deliberately does not infer
architecture, modify existing documents, or claim a target is ready before its
evidence placeholders are replaced and the document audit passes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PACKAGE_ROOT / "templates"
AUDIT_TOOL = PACKAGE_ROOT / "scripts" / "check_docs.py"

DOCUMENT_TEMPLATES = {
    "AGENTS.md": "AGENTS.codebase.template.md",
    "BRAINSTORM.md": "BRAINSTORM.md",
    "CONTEXT.md": "CONTEXT.md",
    "MEMORY.md": "MEMORY.md",
    "NOTEPAD.md": "NOTEPAD.md",
}
EXPORT_DOCUMENTS = (
    "AGENTS.md",
    "BRAINSTORM.md",
    "CONTEXT.md",
    "MEMORY.md",
    "NOTEPAD.md",
)
# Matches fill-in slots such as <RUNTIME>, <GATE_COMMAND>, <BAN_1>, <directory-loc>
# without matching ordinary HTML tags such as <br> or <details>.
PLACEHOLDER = re.compile(r"<(?:[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*|[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+)>")
PLACEHOLDER_SCAN = ("AGENTS.md",)
PROJECTION_NAMES = {
    "claude": "CLAUDE.md",
    "chatgpt": "CHATGPT_PROJECT.md",
    "gemini": "GEMINI_PROJECT.md",
    "cursor": "CURSOR.md",
    "generic": "OPERATOR_PROJECTION.md",
}


class LockInError(RuntimeError):
    """Raised for an explicit, non-destructive command failure."""


def utc_date() -> str:
    return datetime.now(UTC).date().isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_directory(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise LockInError(f"target directory does not exist: {resolved}")
    return resolved


def render_template(template_path: Path, *, target: Path, project_name: str, kind: str) -> str:
    if not template_path.is_file():
        raise LockInError(f"missing package template: {template_path}")
    replacements = {
        "%%PROJECT_NAME%%": project_name,
        "%%PROJECT_ROOT%%": str(target),
        "%%PROJECT_KIND%%": kind,
        "%%CREATED_DATE%%": utc_date(),
    }
    text = template_path.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def install_documents(
    target: Path, *, project_name: str, kind: str, dry_run: bool
) -> tuple[list[str], list[str]]:
    """Install missing document roles and preserve every pre-existing file."""

    created: list[str] = []
    preserved: list[str] = []
    for destination_name, template_name in DOCUMENT_TEMPLATES.items():
        destination = target / destination_name
        if destination.exists():
            preserved.append(destination_name)
            continue
        if not dry_run:
            destination.write_text(
                render_template(
                    TEMPLATE_ROOT / template_name,
                    target=target,
                    project_name=project_name,
                    kind=kind,
                ),
                encoding="utf-8",
            )
        created.append(destination_name)
    return created, preserved


def unresolved_placeholders(target: Path) -> dict[str, list[str]]:
    """Return fill-in slots still present in documents that must be adapted per repository."""
    found: dict[str, list[str]] = {}
    for name in PLACEHOLDER_SCAN:
        path = target / name
        if path.is_file():
            slots = sorted(set(PLACEHOLDER.findall(path.read_text(encoding="utf-8"))))
            if slots:
                found[name] = slots
    return found


def run_audit(target: Path, *, allow_unresolved: bool) -> int:
    missing = [name for name in DOCUMENT_TEMPLATES if not (target / name).is_file()]
    for name in missing:
        print(f"ERROR: {name}: required codebase document role is missing; run init", file=sys.stderr)

    unresolved = unresolved_placeholders(target)
    level = "WARNING" if allow_unresolved else "ERROR"
    for name, slots in unresolved.items():
        print(f"{level}: {name}: {len(slots)} unresolved placeholder(s): {', '.join(slots)}", file=sys.stderr)

    present = [str(target / name) for name in DOCUMENT_TEMPLATES if (target / name).is_file()]
    structure = subprocess.run([sys.executable, str(AUDIT_TOOL), "--root", str(target), *present], text=True).returncode if present else 0
    failed = bool(missing) or (bool(unresolved) and not allow_unresolved) or structure != 0
    print(f"operator-lockin check: {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


def command_init(args: argparse.Namespace) -> int:
    target = require_directory(args.target)
    project_name = args.project_name.strip()
    if not project_name:
        raise LockInError("project name must not be empty")
    created, preserved = install_documents(
        target, project_name=project_name, kind=args.kind, dry_run=args.dry_run
    )
    action = "would create" if args.dry_run else "created"
    print(f"operator-lockin init: {action}: {', '.join(created) or 'none'}")
    print(f"operator-lockin init: preserved existing: {', '.join(preserved) or 'none'}")
    if not args.dry_run:
        print(
            "operator-lockin init: target-specific evidence remains unresolved; "
            "run the audit after adapting AGENTS.md and the state documents."
        )
    return 0


def command_check(args: argparse.Namespace) -> int:
    target = require_directory(args.target)
    return run_audit(target, allow_unresolved=args.allow_unresolved)


def manifest_for(directory: Path, files: list[Path], provider: str) -> dict[str, object]:
    return {
        "format": "operator-lockin-cloud-pack-v1",
        "provider_target": provider,
        "generated_at": datetime.now(UTC).isoformat(),
        "files": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
        "capability_boundary": (
            "This package is portable documentation. The receiving provider's "
            "filesystem, execution, network, memory, and tool capabilities must "
            "be verified at runtime."
        ),
    }


def command_export(args: argparse.Namespace) -> int:
    target = require_directory(args.target)
    output = args.output.expanduser().resolve()
    if output.exists():
        raise LockInError(f"output must not already exist: {output}")

    selected = [target / name for name in EXPORT_DOCUMENTS if (target / name).is_file()]
    missing = [name for name in EXPORT_DOCUMENTS if not (target / name).is_file()]
    if missing:
        raise LockInError("cannot export incomplete substrate; missing: " + ", ".join(missing))

    output.mkdir(parents=True)
    copied: list[Path] = []
    for source in selected:
        destination = output / source.name
        shutil.copy2(source, destination)
        copied.append(destination)

    upload_order = output / "UPLOAD_ORDER.md"
    upload_order.write_text(
        "# Operator Lock-In cloud project upload order\n\n"
        "1. AGENTS.md — runtime navigation router and authority map.\n"
        "2. CONTEXT.md — chronological index into memory; read newest relevant entries.\n"
        "3. NOTEPAD.md — newest relevant entries only; live working state, not canon.\n"
        "4. MEMORY.md — deep durable store; traverse by CONTEXT keys when the task needs it.\n"
        "5. BRAINSTORM.md — deferred ideas and open questions; consult at session boundaries.\n\n"
        "Project-authored surfaces named by AGENTS.md (SPEC.md, STATE.md, ANTITHESIS.md, "
        "filetree.md) are not part of this pack; upload them separately when they exist.\n\n"
        "The package does not prove the host has a local filesystem, terminal, "
        "git, web, memory, or Sovereign/BB7 access. Verify before relying on "
        "those capabilities.\n",
        encoding="utf-8",
    )
    copied.append(upload_order)

    manifest = manifest_for(output, copied, args.provider)
    manifest_path = output / "PACKAGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    copied.append(manifest_path)

    archive = output.parent / f"{output.name}-{args.provider}.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in copied:
            bundle.write(path, path.name)
    print(f"operator-lockin export: package={output}")
    print(f"operator-lockin export: archive={archive}")
    return 0


def command_fork(args: argparse.Namespace) -> int:
    target = require_directory(args.target)
    source = target / "AGENTS.md"
    if not source.is_file():
        raise LockInError(f"cannot project without canonical AGENTS.md: {source}")
    projection_name = args.output or PROJECTION_NAMES[args.provider]
    projection_path = Path(projection_name)
    if projection_path.is_absolute() or projection_path.name != projection_name:
        raise LockInError("projection output must be a filename relative to the target")
    destination = target / projection_path
    if destination.exists():
        raise LockInError(f"refusing to overwrite provider projection: {destination}")

    source_hash = sha256_file(source)
    header = (
        f"# {args.provider.title()} operator projection\n\n"
        f"**Canonical source:** AGENTS.md\n"
        f"**Canonical source SHA256:** {source_hash}\n"
        f"**Generated:** {datetime.now(UTC).isoformat()}\n\n"
        "## Projection boundary\n\n"
        "This is a derived view of the canonical codebase router. It does not "
        "supersede AGENTS.md or assert that this provider has the same tools, "
        "filesystem, shell, memory, network, git, or Sovereign surfaces as "
        "another operator. Verify runtime capability before execution. Preserve "
        "the source workspace's authority, navigation, verification, and OPSEC "
        "constraints; report projection drift back to canonical documents.\n\n"
        "---\n\n"
    )
    destination.write_text(header + source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"operator-lockin fork: wrote {destination}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely install, audit, export, or project an Operator Lock-In document substrate."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="install only missing document roles")
    init.add_argument("--target", type=Path, required=True)
    init.add_argument("--project-name", required=True)
    init.add_argument("--kind", default="repository")
    init.add_argument("--dry-run", action="store_true")
    init.set_defaults(handler=command_init)

    check = subparsers.add_parser("check", help="audit an installed document substrate")
    check.add_argument("--target", type=Path, required=True)
    check.add_argument(
        "--allow-unresolved", action="store_true",
        help="report unfilled AGENTS.md placeholders as warnings instead of errors",
    )
    check.set_defaults(handler=command_check)

    export = subparsers.add_parser("export", help="create a portable cloud-project package")
    export.add_argument("--target", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--provider", default="generic")
    export.set_defaults(handler=command_export)

    fork = subparsers.add_parser("fork", help="create a non-destructive provider projection")
    fork.add_argument("--target", type=Path, required=True)
    fork.add_argument("--provider", choices=sorted(PROJECTION_NAMES), default="claude")
    fork.add_argument("--output", help="projection filename relative to target")
    fork.set_defaults(handler=command_fork)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        return args.handler(args)
    except LockInError as error:
        print(f"operator-lockin: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"operator-lockin: filesystem failure: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
