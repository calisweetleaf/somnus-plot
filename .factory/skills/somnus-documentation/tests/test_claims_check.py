from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.claims_check import github_slug, inspect_claims


class ClaimsCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
        (self.root / "tools").mkdir()
        (self.root / "tools" / "run.py").write_text("parser.add_argument('--fast')\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inspect(self, text: str, **options):
        path = self.root / "README.md"
        path.write_text(text, encoding="utf-8")
        return inspect_claims(path, self.root, **options)

    def test_existing_path_passes_and_missing_path_warns(self) -> None:
        findings = self.inspect("# R\n\nSee `src/app.py` and `src/gone.py`.\n")
        self.assertEqual([f.message for f in findings], ["line 3: path `src/gone.py` does not exist"])
        self.assertEqual(findings[0].level, "WARNING")

    def test_strict_promotes_missing_path_to_error(self) -> None:
        findings = self.inspect("# R\n\n`src/gone.py`\n", strict=True)
        self.assertEqual(findings[0].level, "ERROR")

    def test_prose_with_slash_is_not_a_path(self) -> None:
        self.assertFalse(self.inspect("# R\n\nUse `read/write` or `client/server` mode.\n"))

    def test_flag_missing_from_script_source_warns(self) -> None:
        text = "# R\n\n```bash\npython3 tools/run.py --fast --slow\n```\n"
        messages = [f.message for f in self.inspect(text)]
        self.assertEqual(messages, ["line 4: flag `--slow` does not appear in the source of `tools/run.py`"])

    def test_missing_script_and_module(self) -> None:
        text = "# R\n\n```sh\n$ ./tools/missing.sh && python -m src.nothing\n```\n"
        messages = " ".join(f.message for f in self.inspect(text))
        self.assertIn("`./tools/missing.sh`, which does not exist", messages)
        self.assertIn("module `src.nothing` is not in the repository", messages)

    def test_external_module_is_ignored(self) -> None:
        self.assertFalse(self.inspect("# R\n\n```bash\npython3 -m pip install x\n```\n"))

    def test_anchor_resolution_inline_reference_and_duplicates(self) -> None:
        text = (
            "# R\n\n## Setup\n\n## Setup\n\n"
            "[a](#setup) [b](#setup-1) [c](#missing)\n\n[ref]: #also-missing\n"
        )
        errors = [f.message for f in self.inspect(text) if f.level == "ERROR"]
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("#missing" in m for m in errors))
        self.assertTrue(any("#also-missing" in m for m in errors))

    def test_cross_file_anchor(self) -> None:
        (self.root / "GUIDE.md").write_text("# Guide\n\n## Install `tool`\n", encoding="utf-8")
        errors = [f for f in self.inspect("# R\n\n[x](GUIDE.md#install-tool) [y](GUIDE.md#nope)\n") if f.level == "ERROR"]
        self.assertEqual(len(errors), 1)
        self.assertIn("#nope", errors[0].message)

    def test_github_slug(self) -> None:
        self.assertEqual(github_slug("1. EXECUTIVE SUMMARY"), "1-executive-summary")
        self.assertEqual(github_slug("Use `check_docs.py` [here](x)"), "use-check_docspy-here")


if __name__ == "__main__":
    unittest.main()
