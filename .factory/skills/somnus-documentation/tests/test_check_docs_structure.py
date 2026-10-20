from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_docs import inspect_document


class StructureEdgeCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inspect(self, text: str, name: str = "README.md", **options):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return inspect_document(path, self.root, **options)

    def messages(self, findings, level):
        return [f.message for f in findings if f.level == level]

    def test_unclosed_fence_is_an_error(self) -> None:
        findings = self.inspect("# Notes\n\n```bash\necho hi\n")
        self.assertIn("has an unclosed fenced block", self.messages(findings, "ERROR"))

    def test_shorter_closing_fence_does_not_close(self) -> None:
        findings = self.inspect("# Notes\n\n````\n```\n````\n")
        self.assertFalse(self.messages(findings, "ERROR"))

    def test_heading_jump_warns(self) -> None:
        findings = self.inspect("# Notes\n\n### Jumped\n")
        self.assertTrue(any("heading level jumps at line 3" in m for m in self.messages(findings, "WARNING")))

    def test_html_image_banner_counts_as_title_cue(self) -> None:
        findings = self.inspect('<p align="center"><img src="logo.png" alt="Queue logo"></p>\n')
        warnings = self.messages(findings, "WARNING")
        self.assertFalse(any("banner cue" in m for m in warnings))

    def test_broken_reference_definition_is_an_error(self) -> None:
        findings = self.inspect("# Notes\n\nSee [the guide][g].\n\n[g]: ./missing.md\n[^1]: footnote text\n")
        errors = self.messages(findings, "ERROR")
        self.assertEqual(errors, ["local reference link target does not exist: ./missing.md"])

    def test_resolving_reference_definition_passes(self) -> None:
        (self.root / "guide.md").write_text("# Guide\n", encoding="utf-8")
        findings = self.inspect("# Notes\n\n[g]: <guide.md>\n[remote]: https://example.org\n")
        self.assertFalse(self.messages(findings, "ERROR"))

    def test_missing_alt_text_warns_once_with_count(self) -> None:
        (self.root / "a.png").write_bytes(b"")
        findings = self.inspect('# Notes\n\n![](a.png)\n\n<img src="a.png">\n\n<img src="a.png" alt="Diagram">\n')
        warnings = [m for m in self.messages(findings, "WARNING") if "alt text" in m]
        self.assertEqual(len(warnings), 1)
        self.assertIn("2 image(s)", warnings[0])

    def test_emoji_warns_but_text_symbols_do_not(self) -> None:
        self.assertTrue(any("emoji" in m for m in self.messages(self.inspect("# Notes \U0001F680\n"), "WARNING")))
        self.assertFalse(any("emoji" in m for m in self.messages(self.inspect("# Notes\n\n✓ done\n"), "WARNING")))

    def test_emoji_inside_code_fence_is_ignored(self) -> None:
        findings = self.inspect("# Notes\n\n```\n\U0001F680\n```\n")
        self.assertFalse(any("emoji" in m for m in self.messages(findings, "WARNING")))

    def test_composition_check_is_opt_in(self) -> None:
        text = "# Notes\n\n## Table first\n\n| a | b |\n| --- | --- |\n\n## Prose first\n\nThis section explains b.\n"
        self.assertFalse(any("H2 at line" in m for m in self.messages(self.inspect(text), "WARNING")))
        warnings = [m for m in self.messages(self.inspect(text, check_composition=True), "WARNING") if "H2 at line" in m]
        self.assertEqual(len(warnings), 1)
        self.assertIn("line 3 opens with a table", warnings[0])

    def test_composition_flags_fence_list_and_heading_openers(self) -> None:
        text = "# N\n\n## A\n\n```\nx\n```\n\n## B\n\n- item\n\n## C\n\n### D\n\nText.\n"
        warnings = [m for m in self.messages(self.inspect(text, check_composition=True), "WARNING") if "H2 at line" in m]
        self.assertEqual(len(warnings), 3)


if __name__ == "__main__":
    unittest.main()
