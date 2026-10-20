from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_docs import inspect_document


class CheckDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def inspect(self, name: str, text: str, **options):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return inspect_document(path, self.root, **options)

    def test_spec_with_title_and_explicit_scope_passes_without_status(self) -> None:
        findings = self.inspect(
            "SPEC.md",
            "# Queue Contract\n\n> Defines the public behavior and failure boundary of the queue.\n\n## Terms\n",
        )
        self.assertFalse([f for f in findings if f.level == "ERROR"])

    def test_spec_scope_label_accepts_bold_colon_inside_label(self) -> None:
        findings = self.inspect(
            "SPEC.md",
            "# Queue Contract\n\n**Scope:** Covers enqueue, dequeue, and timeout behavior.\n",
        )
        self.assertFalse([f for f in findings if f.level == "ERROR"])

    def test_spec_title_and_generic_prose_do_not_count_as_banner(self) -> None:
        findings = self.inspect(
            "SPEC.md",
            "# Queue Contract\n\nThis document explains the queue.\n",
        )
        errors = [f for f in findings if f.level == "ERROR"]
        self.assertEqual(len(errors), 1)
        self.assertIn("explicit scope statement", errors[0].message)

    def test_spec_needs_a_title_near_the_opening(self) -> None:
        headings = "\n".join(f"Paragraph {number}." for number in range(25))
        findings = self.inspect(
            "SPEC.md",
            f"{headings}\n\n# Late Title\n\n**Scope:** Covers the public API.\n",
        )
        errors = [f for f in findings if f.level == "ERROR"]
        self.assertTrue(any("visible title near the opening" in f.message for f in errors))

    def test_remote_assets_are_opt_in_and_aggregated(self) -> None:
        text = (
            "# Notes\n\n"
            "![A](https://example.org/a.png)\n\n"
            "![B](https://example.org/b.png)\n"
        )
        default_findings = self.inspect("README.md", text)
        self.assertFalse([f for f in default_findings if f.level == "WARNING"])

        strict_findings = self.inspect("README.md", text, check_external_assets=True)
        warnings = [f for f in strict_findings if f.level == "WARNING"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("2 remote or embedded image(s)", warnings[0].message)

    def test_inline_css_is_opt_in_renderer_warning(self) -> None:
        text = "# Notes\n\n<style>h1 { color: navy; }</style>\n"
        default_findings = self.inspect("README.md", text)
        self.assertFalse([f for f in default_findings if f.level == "WARNING"])

        renderer_findings = self.inspect("README.md", text, check_renderer_features=True)
        self.assertTrue(any("target renderer" in f.message for f in renderer_findings))

    def test_broken_local_links_remain_errors_by_default(self) -> None:
        findings = self.inspect("README.md", "# Notes\n\n[Missing](./missing.md)\n")
        self.assertTrue(any(f.level == "ERROR" and "does not exist" in f.message for f in findings))

    def test_legacy_reference_heading_warnings_are_suppressed_but_links_are_checked(self) -> None:
        findings = self.inspect(
            "references/legacy/old.md",
            "# Old title\n\n### Jumped heading\n\n[Missing](./missing.md)\n",
        )
        self.assertFalse([f for f in findings if f.level == "WARNING"])
        self.assertTrue(any(f.level == "ERROR" and "does not exist" in f.message for f in findings))


if __name__ == "__main__":
    unittest.main()
