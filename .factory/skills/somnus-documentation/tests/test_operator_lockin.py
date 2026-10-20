from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.operator_lockin import DOCUMENT_TEMPLATES, PLACEHOLDER, TEMPLATE_ROOT

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "operator_lockin.py"


def lockin(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


class OperatorLockInTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.target = Path(self.temporary.name) / "repo"
        self.target.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_every_role_has_a_package_template(self) -> None:
        for template in DOCUMENT_TEMPLATES.values():
            self.assertTrue((TEMPLATE_ROOT / template).is_file(), template)

    def test_init_creates_missing_roles_and_preserves_existing(self) -> None:
        (self.target / "MEMORY.md").write_text("# Custom memory\n", encoding="utf-8")
        result = lockin("init", "--target", str(self.target), "--project-name", "Repo")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("preserved existing: MEMORY.md", result.stdout)
        self.assertEqual((self.target / "MEMORY.md").read_text(encoding="utf-8"), "# Custom memory\n")
        for name in DOCUMENT_TEMPLATES:
            self.assertTrue((self.target / name).is_file(), name)

    def test_dry_run_writes_nothing(self) -> None:
        result = lockin("init", "--target", str(self.target), "--project-name", "Repo", "--dry-run")
        self.assertIn("would create", result.stdout)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_check_fails_on_missing_roles(self) -> None:
        result = lockin("check", "--target", str(self.target))
        self.assertEqual(result.returncode, 1)
        self.assertIn("required codebase document role is missing", result.stderr)

    def test_check_enforces_placeholders_unless_allowed(self) -> None:
        lockin("init", "--target", str(self.target), "--project-name", "Repo")
        strict = lockin("check", "--target", str(self.target))
        self.assertEqual(strict.returncode, 1)
        self.assertIn("ERROR: AGENTS.md:", strict.stderr)
        self.assertEqual(lockin("check", "--target", str(self.target), "--allow-unresolved").returncode, 0)

        agents = self.target / "AGENTS.md"
        agents.write_text(PLACEHOLDER.sub("filled", agents.read_text(encoding="utf-8")), encoding="utf-8")
        self.assertEqual(lockin("check", "--target", str(self.target)).returncode, 0)

    def test_check_scopes_audit_to_role_files(self) -> None:
        lockin("init", "--target", str(self.target), "--project-name", "Repo")
        (self.target / "docs").mkdir()
        (self.target / "docs" / "broken.md").write_text("[x](./missing.md)\n", encoding="utf-8")
        self.assertEqual(lockin("check", "--target", str(self.target), "--allow-unresolved").returncode, 0)

    def test_placeholder_pattern_ignores_html_tags(self) -> None:
        self.assertEqual(PLACEHOLDER.findall("<br> <details> <RUNTIME> <BAN_1> <directory-loc>"), ["<RUNTIME>", "<BAN_1>", "<directory-loc>"])

    def test_export_requires_full_substrate_then_packages_it(self) -> None:
        output = Path(self.temporary.name) / "pack"
        self.assertEqual(lockin("export", "--target", str(self.target), "--output", str(output)).returncode, 2)
        lockin("init", "--target", str(self.target), "--project-name", "Repo")
        result = lockin("export", "--target", str(self.target), "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((output / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(entry["path"] for entry in manifest["files"]),
            sorted([*DOCUMENT_TEMPLATES, "UPLOAD_ORDER.md"]),
        )
        self.assertNotIn("TASK.md", (output / "UPLOAD_ORDER.md").read_text(encoding="utf-8"))
        self.assertTrue((Path(self.temporary.name) / "pack-generic.zip").is_file())

    def test_fork_refuses_overwrite_and_path_escape(self) -> None:
        lockin("init", "--target", str(self.target), "--project-name", "Repo")
        self.assertEqual(lockin("fork", "--target", str(self.target)).returncode, 0)
        self.assertIn("Canonical source SHA256", (self.target / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertEqual(lockin("fork", "--target", str(self.target)).returncode, 2)
        self.assertEqual(lockin("fork", "--target", str(self.target), "--output", "../escape.md").returncode, 2)


if __name__ == "__main__":
    unittest.main()
