#!/usr/bin/env python3
"""Run the skill's gate states over Markdown documents and route each finding to the state that owns it.

Gate states run in order:

  S3 EVIDENCE   claims_check    paths, scripts, modules, flags, anchors
  S6 STRUCTURE  check_docs      structure, links, alt text, emoji, SPEC banner, section openings
  S7 RENDER     GitHub API      raw HTML that GitHub strips (only with --render; needs network)

Every finding prints with the state that must fix it and the reference section to open, so
a failed gate re-enters the state machine at the right place instead of starting over.

`--self` runs the package self-gate (state E3): the unit tests, then S3 and S6 over this skill.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from scripts.check_docs import Finding, collect_markdown, inspect_document, is_legacy_reference  # noqa: E402
from scripts.claims_check import inspect_claims  # noqa: E402
from scripts.render_check import dropped_features, render_github  # noqa: E402


@dataclass(frozen=True)
class Route:
    """Map a finding message pattern to the state that owns the repair."""

    pattern: re.Pattern[str]
    state: str
    action: str
    reference: str


ROUTES = (
    Route(re.compile(r"anchor `#"), "S3 EVIDENCE", "repoint the link or rename the heading", "references/design-schema.md#voice-and-evidence"),
    Route(re.compile(r"path `|command references|module `|flag `"), "S3 EVIDENCE", "correct the claim or label it as an example or output path", "references/design-schema.md#voice-and-evidence"),
    Route(re.compile(r"local (?:image |link |HTML |reference link )?target does not exist|local (?:image|link) target"), "S3 EVIDENCE", "fix or remove the dead target", "references/design-schema.md#voice-and-evidence"),
    Route(re.compile(r"SPEC must begin"), "S4 COMPOSE", "add the identity banner: title plus explicit scope", "references/design-schema.md#banners-and-openings"),
    Route(re.compile(r"H2 at line \d+ (?:opens with|has no content)"), "S4 COMPOSE", "open the section with a sentence stating its job, or cut it", "references/design-schema.md#deletion-test"),
    Route(re.compile(r"emoji"), "S4 COMPOSE", "remove emoji", "SKILL.md#design-contract"),
    Route(re.compile(r"heading level jumps|multiple H1|banner cue"), "S5 VISUAL", "repair heading cadence", "references/design-schema.md#github-safe-composition-and-review"),
    Route(re.compile(r"alt text|remote or embedded image"), "S5 VISUAL", "describe the image or confirm it is decorative and owned", "references/rendering-and-assets.md#assets"),
    Route(re.compile(r"inline CSS|dropped by GitHub"), "S5 VISUAL", "replace the stripped device with one the renderer keeps", "references/rendering-and-assets.md#html-svg-and-styling"),
    Route(re.compile(r"unclosed fenced block|not valid UTF-8|is not a Markdown file|is not a regular file|does not exist$"), "S6 STRUCTURE", "repair the file itself", "references/rendering-and-assets.md#markdown-baseline"),
)
FALLBACK = Route(re.compile(""), "S8 READER", "review in context", "references/design-schema.md#final-review")
STATE_ORDER = ("S3 EVIDENCE", "S4 COMPOSE", "S5 VISUAL", "S6 STRUCTURE", "S7 RENDER", "S8 READER")


def route_for(finding: Finding) -> Route:
    """Return the first route whose pattern matches the finding message."""
    return next((route for route in ROUTES if route.pattern.search(finding.message)), FALLBACK)


@dataclass
class GateResult:
    """Findings produced by one gate state, or the reason it was skipped."""

    state: str
    tool: str
    findings: list[Finding] = field(default_factory=list)
    skipped: str | None = None
    failed_command: str | None = None

    def errors(self) -> int:
        """Count ERROR findings."""
        return sum(finding.level == "ERROR" for finding in self.findings)

    def warnings(self) -> int:
        """Count WARNING findings."""
        return sum(finding.level == "WARNING" for finding in self.findings)

    def verdict(self, *, fail_on_warnings: bool) -> str:
        """Return PASS, FAIL, or SKIPPED for this gate."""
        if self.skipped:
            return "SKIPPED"
        if self.failed_command or self.errors() or (fail_on_warnings and self.warnings()):
            return "FAIL"
        return "PASS"


def evidence_gate(files: list[Path], root: Path, *, strict: bool, include_legacy: bool) -> GateResult:
    """S3: verify concrete claims in every document."""
    result = GateResult("S3 EVIDENCE", "claims_check")
    cache: dict[Path, set[str]] = {}
    for path in files:
        if include_legacy or not is_legacy_reference(path, root):
            result.findings.extend(inspect_claims(path, root, strict=strict, cache=cache))
    return result


def structure_gate(files: list[Path], root: Path, *, composition: bool) -> GateResult:
    """S6: check structure, links, accessibility cues, and section openings."""
    result = GateResult("S6 STRUCTURE", "check_docs")
    for path in files:
        result.findings.extend(inspect_document(path, root, check_composition=composition))
    return result


def render_gate(files: list[Path], *, enabled: bool) -> GateResult:
    """S7: report raw HTML features that GitHub's renderer strips."""
    result = GateResult("S7 RENDER", "github markdown api")
    if not enabled:
        result.skipped = "pass --render to call GitHub's Markdown API"
        return result
    for path in files:
        markdown = path.read_text(encoding="utf-8")
        try:
            rendered = render_github(markdown, context=None, token=None)
        except (URLError, TimeoutError) as error:
            result.failed_command = f"GitHub render failed for {path.name}: {error}"
            return result
        dropped = dropped_features(markdown, rendered)
        if dropped:
            summary = ", ".join(f"{name} {before}->{after}" for name, (before, after) in dropped.items())
            result.findings.append(Finding("WARNING", path, f"dropped by GitHub: {summary}"))
    return result


def unit_test_gate() -> GateResult:
    """E3: run the package unit tests."""
    result = GateResult("E3 TESTS", "unittest")
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]
    completed = subprocess.run(command, cwd=PACKAGE_ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        result.failed_command = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "unittest failed"
    return result


def report(results: list[GateResult], root: Path, *, fail_on_warnings: bool, limit: int) -> int:
    """Print gate verdicts and routed findings; return the process exit code."""
    failing_states: list[str] = []
    for result in results:
        verdict = result.verdict(fail_on_warnings=fail_on_warnings)
        detail = result.skipped or result.failed_command or f"{result.errors()} error(s), {result.warnings()} warning(s)"
        print(f"{result.state:<13} {result.tool:<20} {verdict:<8} {detail}")
        grouped: dict[Route, list[Finding]] = {}
        for finding in result.findings:
            grouped.setdefault(route_for(finding), []).append(finding)
        for route, findings in grouped.items():
            blocking = any(f.level == "ERROR" for f in findings) or (fail_on_warnings and findings)
            if blocking:
                failing_states.append(route.state)
            print(f"  -> {route.state}: {route.action}  [{route.reference}]")
            for finding in findings[:limit]:
                print(f"     {finding.render(root)}")
            if len(findings) > limit:
                print(f"     ... {len(findings) - limit} more")
        if verdict == "FAIL" and not result.findings:
            failing_states.append(result.state)
    if failing_states:
        ordered = sorted(set(failing_states), key=lambda s: STATE_ORDER.index(s) if s in STATE_ORDER else -1)
        print(f"verdict: FAIL -> re-enter at {ordered[0]}")
        return 1
    print("verdict: PASS -> continue to S8 READER, then EXIT with the gate report")
    return 0


def main() -> int:
    """Parse arguments, run the gate states, and print the routed report."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="Markdown files or directories, relative to --root when not absolute")
    parser.add_argument("--root", default=".", help="repository root used to resolve claims and links")
    parser.add_argument("--self", dest="self_gate", action="store_true", help="run the package self-gate (tests, S3, S6 over this skill)")
    parser.add_argument("--strict-claims", action="store_true", help="treat missing paths, scripts, modules, and flags as errors")
    parser.add_argument("--no-composition", action="store_true", help="skip the H2 section-opening check")
    parser.add_argument("--render", action="store_true", help="run S7 against GitHub's Markdown API")
    parser.add_argument("--include-legacy", action="store_true", help="also check claims under references/legacy")
    parser.add_argument("--fail-on-warnings", action="store_true", help="treat any routed warning as a gate failure")
    parser.add_argument("--limit", type=int, default=5, help="findings shown per route (default 5)")
    args = parser.parse_args()

    if args.self_gate:
        root, raw_paths = PACKAGE_ROOT, [str(PACKAGE_ROOT)]
    elif args.paths:
        root, raw_paths = Path(args.root).resolve(), args.paths
    else:
        parser.error("give Markdown paths or --self")

    files, input_findings = collect_markdown(raw_paths, root)
    results: list[GateResult] = []
    if args.self_gate:
        results.append(unit_test_gate())
    results.append(evidence_gate(files, root, strict=args.strict_claims, include_legacy=args.include_legacy))
    structure = structure_gate(files, root, composition=not (args.no_composition or args.self_gate))
    structure.findings[:0] = input_findings
    results.append(structure)
    results.append(render_gate(files, enabled=args.render))
    return report(results, root, fail_on_warnings=args.fail_on_warnings, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
