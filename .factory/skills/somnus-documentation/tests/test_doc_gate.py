"""Tests for the gate runner's routing and verdicts."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.check_docs import Finding
from scripts.doc_gate import FALLBACK, GateResult, route_for

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "doc_gate.py"


def finding(message: str, level: str = "ERROR") -> Finding:
    """Build a finding with a throwaway path."""
    return Finding(level, Path("x.md"), message)


class RouteTests(unittest.TestCase):
    """Each checker message reaches the state that owns its repair."""

    def test_messages_route_to_owning_states(self) -> None:
        cases = {
            "line 3: anchor `#a` not found in x.md": "S3 EVIDENCE",
            "line 3: path `src/a.py` does not exist": "S3 EVIDENCE",
            "line 4: flag `--x` does not appear in the source of `a.py`": "S3 EVIDENCE",
            "local link target does not exist: ./m.md": "S3 EVIDENCE",
            "local reference link target does not exist: ./m.md": "S3 EVIDENCE",
            "SPEC must begin with an identity banner containing a visible title": "S4 COMPOSE",
            "H2 at line 3 opens with a table; lead with a sentence": "S4 COMPOSE",
            "contains 1 emoji character(s)": "S4 COMPOSE",
            "heading level jumps at line 9": "S5 VISUAL",
            "has 2 image(s) with empty or missing alt text": "S5 VISUAL",
            "dropped by GitHub: svg 9->0": "S5 VISUAL",
            "has an unclosed fenced block": "S6 STRUCTURE",
            "does not exist": "S6 STRUCTURE",
        }
        for message, state in cases.items():
            with self.subTest(message=message):
                self.assertEqual(route_for(finding(message)).state, state)

    def test_unknown_message_falls_back_to_reader_review(self) -> None:
        self.assertIs(route_for(finding("something new")), FALLBACK)

    def test_verdicts(self) -> None:
        self.assertEqual(GateResult("S3", "t").verdict(fail_on_warnings=False), "PASS")
        warned = GateResult("S3", "t", [finding("w", "WARNING")])
        self.assertEqual(warned.verdict(fail_on_warnings=False), "PASS")
        self.assertEqual(warned.verdict(fail_on_warnings=True), "FAIL")
        self.assertEqual(GateResult("S7", "t", skipped="no network").verdict(fail_on_warnings=True), "SKIPPED")
        self.assertEqual(GateResult("E3", "t", failed_command="boom").verdict(fail_on_warnings=False), "FAIL")


class GateCommandTests(unittest.TestCase):
    """The CLI re-enters the machine at the earliest failing state."""

    def run_gate(self, text: str, *args: str) -> subprocess.CompletedProcess[str]:
        """Write one document and gate it."""
        directory = Path(self.temporary.name)
        (directory / "README.md").write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(directory), "README.md", *args],
            capture_output=True, text=True, check=False,
        )

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_clean_document_passes_with_render_skipped(self) -> None:
        result = self.run_gate("# Queue\n\n## Use\n\nThis section shows the route.\n")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("S7 RENDER", result.stdout)
        self.assertIn("SKIPPED", result.stdout)
        self.assertIn("verdict: PASS", result.stdout)

    def test_earliest_failing_state_wins(self) -> None:
        result = self.run_gate("# Q\n\n[x](#nope)\n\n[y](./missing.md)\n\n```\nopen\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("verdict: FAIL -> re-enter at S3 EVIDENCE", result.stdout)

    def test_warning_only_fails_when_requested(self) -> None:
        text = "# Q\n\n## Table\n\n| a |\n| --- |\n"
        self.assertEqual(self.run_gate(text).returncode, 0)
        strict = self.run_gate(text, "--fail-on-warnings")
        self.assertEqual(strict.returncode, 1)
        self.assertIn("re-enter at S4 COMPOSE", strict.stdout)

    def test_paths_or_self_required(self) -> None:
        result = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
