#!/usr/bin/env python3
"""
check_engine.py — Repository Self-Check for Academic Whitepaper Engine v4

Inspects repository integrity, verifies presence of canonical templates and
scripts, checks system dependencies, and exits with status code 0 on clean pass.

This is a PORTABLE SCRIPT — no sibling imports, no dynamic pip installs.
"""

import sys
import shutil
import json
from pathlib import Path


# ── Required Repository Assets ──────────────────────────────────────────────

REQUIRED_FILES = {
    "SKILL.md": "Engine skill definition",
    "AGENTS.md": "Agent context & operational protocol",
    "pyproject.toml": "Package manifest & dependency declaration",
    "system-requirements.md": "External system binary requirements",
}

REQUIRED_SCHEMAS = {
    "schemas/session.schema.json": "Session metadata schema",
    "schemas/tasklist.schema.json": "Tasklist state machine schema",
    "schemas/authority-map.schema.json": "Authority map schema",
    "schemas/claim-ledger.schema.json": "Claim ledger schema",
    "schemas/visual-ledger.schema.json": "Visual ledger schema",
    "schemas/section-graph.schema.json": "Section graph schema",
    "schemas/build-manifest.schema.json": "Build manifest schema",
}

REQUIRED_TEMPLATES = {
    "templates/somnus-pandoc-template.tex": "Pandoc conversion template",
    "templates/somnus-preamble.tex": "Somnus design system preamble",
    "templates/somnus-cover.tex": "Cover page template",
}

REQUIRED_SCRIPTS = {
    "scripts/md2tex.py": "Markdown → LuaLaTeX transcreation engine",
    "scripts/sart.py": "Symbol ontology & equation coherence engine",
    "scripts/generate_metadata.py": "DOI & document metadata generator",
    "scripts/batch_manager.py": "Multi-section batch document processor",
    "scripts/pdf_to_markdown_converter.py": "PDF-to-Markdown extraction",
    "scripts/pdf_ocr_scanner.py": "Scanned PDF OCR scanner",
    "scripts/cleaner.py": "AI artifact & metadata stripper (MANUAL ONLY)",
}

REQUIRED_REFERENCES = {
    "references/authorial-cadence-profile.md": "Authorial cadence reference",
    "references/authorial-cadence-profile.yaml": "Machine-readable cadence profile",
    "references/citation-styles.md": "Citation format reference",
    "references/visual-examples.md": "Visual asset templates",
}

REQUIRED_ENGINE_MODULES = {
    "whitepaper_engine/__init__.py": "Package init",
    "whitepaper_engine/state.py": "State machine tracker",
    "whitepaper_engine/claims.py": "Claim epistemology engine",
    "whitepaper_engine/visuals.py": "Visual constitution validator",
    "whitepaper_engine/style_review.py": "Anti-genericity reviewer",
    "whitepaper_engine/unicode_classifier.py": "Unicode domain classifier",
    "whitepaper_engine/build.py": "Build orchestrator",
}


# ── Required System Binaries ────────────────────────────────────────────────

REQUIRED_BINARIES = {
    "lualatex": {"purpose": "Canonical TeX engine", "critical": True},
    "biber": {"purpose": "Bibliography backend", "critical": True},
    "latexmk": {"purpose": "Automated TeX build driver", "critical": True},
    "pandoc": {"purpose": "Markdown → TeX conversion", "critical": True},
}

OPTIONAL_BINARIES = {
    "dot": {"purpose": "Graphviz diagram rendering"},
    "pdftotext": {"purpose": "PDF text extraction (poppler-utils)"},
    "tesseract": {"purpose": "OCR engine for scanned PDFs"},
}


# ── Check Functions ─────────────────────────────────────────────────────────

def check_files(engine_root: Path, file_map: dict, category: str) -> list[str]:
    """Check that required files exist."""
    issues = []
    for rel_path, description in file_map.items():
        full_path = engine_root / rel_path
        if not full_path.exists():
            issues.append(f"  ✗ MISSING: {rel_path} — {description}")
        elif full_path.stat().st_size == 0:
            issues.append(f"  ⚠ EMPTY:   {rel_path} — {description}")
    return issues


def check_binaries(binary_map: dict, critical: bool = True) -> list[str]:
    """Check that required system binaries are available."""
    issues = []
    for binary, info in binary_map.items():
        if shutil.which(binary) is None:
            marker = "✗ MISSING" if critical else "⚠ MISSING"
            issues.append(f"  {marker}: {binary} — {info['purpose']}")
    return issues


def check_schemas_valid(engine_root: Path) -> list[str]:
    """Verify JSON schemas are syntactically valid JSON."""
    issues = []
    schemas_dir = engine_root / "schemas"
    if not schemas_dir.exists():
        return ["  ✗ schemas/ directory does not exist"]

    for schema_file in schemas_dir.glob("*.schema.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "$schema" not in data:
                issues.append(f"  ⚠ {schema_file.name}: missing $schema declaration")
        except json.JSONDecodeError as e:
            issues.append(f"  ✗ {schema_file.name}: invalid JSON — {e}")
    return issues


def check_template_variables(engine_root: Path) -> list[str]:
    """Verify Pandoc template contains required variables."""
    issues = []
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        return ["  ✗ somnus-pandoc-template.tex not found"]

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    required_vars = ["$body$", "$title$"]
    for var in required_vars:
        if var not in content:
            issues.append(f"  ✗ Template missing required variable: {var}")

    # Check for pdflatex-only packages that conflict with LuaLaTeX
    forbidden_packages = ["inputenc", "fontenc"]
    for pkg in forbidden_packages:
        # Check for \usepackage[...]{inputenc} or \usepackage{fontenc}
        if f"\\usepackage{{{pkg}}}" in content or f"\\usepackage[" in content and f"{{{pkg}}}" in content:
            issues.append(f"  ⚠ Template uses \\usepackage{{{pkg}}} — incompatible with LuaLaTeX")

    return issues


def check_engine_importable() -> list[str]:
    """Check if the whitepaper_engine package can be imported."""
    issues = []
    try:
        # Add engine root to path temporarily
        import importlib
        spec = importlib.util.find_spec("whitepaper_engine")
        if spec is None:
            issues.append("  ⚠ whitepaper_engine package not importable (not installed)")
    except Exception as e:
        issues.append(f"  ⚠ whitepaper_engine import check failed: {e}")
    return issues


# ── Main ────────────────────────────────────────────────────────────────────

def run_checks(engine_root: Path) -> bool:
    """Run all checks and return True if all critical checks pass."""
    print("=" * 64)
    print("  Academic Whitepaper Engine v4 — Repository Self-Check")
    print("=" * 64)
    print(f"\n  Engine root: {engine_root}\n")

    all_issues = []
    critical_failure = False

    # 1. Core files
    print("  [1/8] Checking core files...")
    issues = check_files(engine_root, REQUIRED_FILES, "core")
    if issues:
        all_issues.extend(issues)
        critical_failure = True
        print(f"    ✗ {len(issues)} issue(s)")
    else:
        print("    ✓ All core files present")

    # 2. Schemas
    print("  [2/8] Checking JSON schemas...")
    issues = check_files(engine_root, REQUIRED_SCHEMAS, "schemas")
    if issues:
        all_issues.extend(issues)
        critical_failure = True
        print(f"    ✗ {len(issues)} issue(s)")
    else:
        print("    ✓ All schemas present")

    # 2b. Schema validity
    issues = check_schemas_valid(engine_root)
    if issues:
        all_issues.extend(issues)
        print(f"    ✗ {len(issues)} schema validity issue(s)")
    else:
        print("    ✓ All schemas are valid JSON")

    # 3. Templates
    print("  [3/8] Checking TeX templates...")
    issues = check_files(engine_root, REQUIRED_TEMPLATES, "templates")
    if issues:
        all_issues.extend(issues)
        critical_failure = True
        print(f"    ✗ {len(issues)} issue(s)")
    else:
        print("    ✓ All templates present")

    # 3b. Template variables
    issues = check_template_variables(engine_root)
    if issues:
        all_issues.extend(issues)
        print(f"    ⚠ {len(issues)} template variable issue(s)")
    else:
        print("    ✓ Pandoc template variables verified")

    # 4. Scripts
    print("  [4/8] Checking scripts...")
    issues = check_files(engine_root, REQUIRED_SCRIPTS, "scripts")
    if issues:
        all_issues.extend(issues)
        critical_failure = True
        print(f"    ✗ {len(issues)} issue(s)")
    else:
        print("    ✓ All scripts present")

    # 5. References
    print("  [5/8] Checking reference documents...")
    issues = check_files(engine_root, REQUIRED_REFERENCES, "references")
    if issues:
        all_issues.extend(issues)
        print(f"    ⚠ {len(issues)} issue(s)")
    else:
        print("    ✓ All references present")

    # 6. Engine modules
    print("  [6/8] Checking engine package modules...")
    issues = check_files(engine_root, REQUIRED_ENGINE_MODULES, "whitepaper_engine")
    if issues:
        all_issues.extend(issues)
        critical_failure = True
        print(f"    ✗ {len(issues)} issue(s)")
    else:
        print("    ✓ All engine modules present")

    # 7. Required system binaries
    print("  [7/8] Checking required system binaries...")
    issues = check_binaries(REQUIRED_BINARIES, critical=True)
    if issues:
        all_issues.extend(issues)
        # Not marking as critical_failure since system deps may be installed later
        print(f"    ⚠ {len(issues)} missing binary(ies)")
    else:
        print("    ✓ All required binaries found")

    # 8. Optional system binaries
    print("  [8/8] Checking optional system binaries...")
    issues = check_binaries(OPTIONAL_BINARIES, critical=False)
    if issues:
        all_issues.extend(issues)
        print(f"    ⚠ {len(issues)} optional binary(ies) missing")
    else:
        print("    ✓ All optional binaries found")

    # Summary
    print("\n" + "=" * 64)
    if not all_issues:
        print("  ✓ ALL CHECKS PASSED — Engine repository is healthy")
        print("=" * 64)
        return True
    else:
        if critical_failure:
            print("  ✗ CHECKS FAILED — Critical issues found")
        else:
            print("  ⚠ CHECKS PASSED WITH WARNINGS")
        print("=" * 64)
        print("\n  Issues:")
        for issue in all_issues:
            print(issue)
        print()
        return not critical_failure


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Academic Whitepaper Engine v4 — Repository Self-Check",
    )
    parser.add_argument(
        "--engine-root",
        type=Path,
        default=None,
        help="Path to engine repository root (default: auto-detect from script location)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable text",
    )
    args = parser.parse_args()

    # Auto-detect engine root
    if args.engine_root:
        engine_root = args.engine_root.resolve()
    else:
        # Script lives in scripts/, engine root is one level up
        engine_root = Path(__file__).resolve().parent.parent

    if not engine_root.exists():
        print(f"✗ Engine root does not exist: {engine_root}", file=sys.stderr)
        sys.exit(2)

    success = run_checks(engine_root)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
