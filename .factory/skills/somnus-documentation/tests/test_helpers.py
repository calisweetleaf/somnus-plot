from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.doc_profile import inspect as profile
from scripts.package_skill import PACKAGE_ROOT, selected_files
from scripts.render_check import dropped_features, wrap_page

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, text=True)


class DocBannerTests(unittest.TestCase):
    def test_banner_with_status_and_version(self) -> None:
        result = run("doc_banner.py", "--title", "Queue  Contract", "--scope", "Defines a|b.", "--status", "Draft", "--version", "0.1")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "# Queue Contract\n\n> Defines a\\|b.\n\n**Status:** Draft · **Document version:** 0.1\n")

    def test_banner_omits_unknown_fields_and_rejects_blank_title(self) -> None:
        self.assertNotIn("Status", run("doc_banner.py", "--title", "T", "--scope", "S").stdout)
        self.assertEqual(run("doc_banner.py", "--title", "  ", "--scope", "S").returncode, 2)


class DocProfileTests(unittest.TestCase):
    def test_counts_devices_outside_fences(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "README.md"
            path.write_text(
                "# T\n\n## A\n\n| a | b |\n| --- | --- |\n\n```mermaid\ngraph TD\n```\n\n"
                "```\n<svg></svg> #ffffff\n```\n\n<svg></svg>\n\n![x](y.png)\n<span style=\"color:#AA00ff\">s</span>\n",
                encoding="utf-8",
            )
            item = profile(path, root)
        self.assertEqual(item["fenced_blocks"], 2)
        self.assertEqual(item["mermaid_blocks"], 1)
        self.assertEqual(item["markdown_tables"], 1)
        self.assertEqual(item["markdown_images"], 1)
        self.assertEqual(item["html_elements"]["svg"], 1)
        self.assertEqual(item["frequent_color_values"], [("#aa00ff", 1)])


class RenderCheckTests(unittest.TestCase):
    def test_dropped_features_ignore_code_spans_and_fences(self) -> None:
        source = "Use `<details>` sparingly.\n\n```html\n<svg></svg>\n```\n\n<svg></svg>\n<div style=\"x\">a</div>\n"
        dropped = dropped_features(source, "<div>a</div>")
        self.assertEqual(dropped, {"svg": (1, 0), "style=": (1, 0)})

    def test_wrap_page_sets_view_width_and_filter(self) -> None:
        page = wrap_page("<h1>T</h1>", title="R.md", base=Path("/tmp"), view="grayscale")
        self.assertIn("filter: grayscale(1)", page)
        self.assertIn("max-width: 1012px", page)
        self.assertIn('<base href="file:///tmp/">', page)
        self.assertIn("max-width: 390px", wrap_page("", title="R", base=Path("/tmp"), view="narrow"))


class PackageSkillTests(unittest.TestCase):
    def test_private_references_excluded_by_default(self) -> None:
        default = {path.as_posix() for path in selected_files(PACKAGE_ROOT, include_private=False)}
        self.assertIn("SKILL.md", default)
        self.assertFalse(any(path.startswith("references/visual-references/") for path in default))
        self.assertFalse(any("__pycache__" in path or path.endswith(".directory") for path in default))

    def test_export_round_trips_through_manifest_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "skill.zip"
            self.assertEqual(run("package_skill.py", "--output", str(archive)).returncode, 0)
            self.assertNotEqual(run("package_skill.py", "--output", str(archive)).returncode, 0)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                bundle.extractall(temporary)
            self.assertIn("somnus-documentation/MANIFEST.md", names)
            unpacked = Path(temporary) / "somnus-documentation"
            audit = subprocess.run([sys.executable, str(unpacked / "scripts" / "manifest_audit.py")], capture_output=True, text=True)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            (unpacked / "SKILL.md").write_text("tampered\n", encoding="utf-8")
            tampered = subprocess.run([sys.executable, str(unpacked / "scripts" / "manifest_audit.py")], capture_output=True, text=True)
            self.assertEqual(tampered.returncode, 1)
            self.assertIn("mismatch: SKILL.md", tampered.stderr)


if __name__ == "__main__":
    unittest.main()
