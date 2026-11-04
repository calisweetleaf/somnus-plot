#!/usr/bin/env python3
"""
test_fable_system.py — Adversarial Regression & Integration Test Suite for the
Somnus Code Fable Authoring, Research, and Evaluation System (Tests A through H).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FABLES_DIR = SKILL_DIR / "fables"
REFERENCES_DIR = SKILL_DIR / "references"
SCRIPTS_DIR = SKILL_DIR / "scripts"
CORRUPTED_FIXTURES_DIR = SKILL_DIR / "tests" / "fixtures" / "corrupted"

sys.path.insert(0, str(SCRIPTS_DIR))
import fable_harness as fh  # noqa: E402


EXPECTED_ORIGINALS = {
    "muadib-fable.md": {
        "sha256": "a209e466cb097f40ba8e1bbf58b6803bd717edcdce8a903dbac78c7c0b03c580",
        "lines": 783,
        "words": 5655,
        "bytes": 40056,
    },
    "continuum-fable.md": {
        "sha256": "63e5386e5c7dd98864e55daea1cb47be6a04c148663b9ca98ac6fa726a877682",
        "lines": 1638,
        "words": 6753,
        "bytes": 49930,
    },
    "Plot-Fable.md": {
        "sha256": "48740ef5a3ef582417b90835d0c747f254eb87a997f62b8df2598b1382a41628",
        "lines": 930,
        "words": 5721,
        "bytes": 37821,
    },
}


class TestSomnusCodeFableSystem(unittest.TestCase):
    """Comprehensive adversarial tests covering Directives VIII.A through VIII.H."""

    # -----------------------------------------------------------------------
    # Test A: Original Preservation
    # -----------------------------------------------------------------------
    def test_a_original_preservation_and_write_guard(self) -> None:
        before = fh.verify_protected_manuscripts(FABLES_DIR)
        self.assertTrue(before["all_intact"], "Protected manuscripts must be intact before operations.")

        for name, expected in EXPECTED_ORIGINALS.items():
            info = before["manuscripts"][name]
            self.assertTrue(info["exists"])
            self.assertTrue(info["intact"])
            self.assertEqual(info["actual_sha256"], expected["sha256"])
            self.assertEqual(info["lines"], expected["lines"])
            self.assertEqual(info["words"], expected["words"])
            self.assertEqual(info["bytes"], expected["bytes"])

        # Run CLI status, verify-originals, and evaluate --all; confirm zero mutation
        for cmd in (
            [sys.executable, str(SCRIPTS_DIR / "fable_harness.py"), "verify-originals"],
            [sys.executable, str(SCRIPTS_DIR / "fable_harness.py"), "status"],
            [sys.executable, str(SCRIPTS_DIR / "fable_harness.py"), "evaluate", "--all"],
            [sys.executable, str(SCRIPTS_DIR / "fable_lint.py"), "--all"],
        ):
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, f"Command failed: {cmd}\n{proc.stdout}\n{proc.stderr}")

        # Verify write-protection refuses to overwrite any protected manuscript
        for name in EXPECTED_ORIGINALS:
            protected_path = FABLES_DIR / name
            with self.assertRaises(PermissionError):
                fh.assert_not_protected_manuscript(protected_path)

        after = fh.verify_protected_manuscripts(FABLES_DIR)
        self.assertTrue(after["all_intact"], "Protected manuscripts must remain intact after operations.")
        for name, expected in EXPECTED_ORIGINALS.items():
            self.assertEqual(after["manuscripts"][name]["actual_sha256"], expected["sha256"])

    # -----------------------------------------------------------------------
    # Test B: Reference Acceptance
    # -----------------------------------------------------------------------
    def test_b_reference_manuscripts_accepted_without_formatting_penalties(self) -> None:
        for name in EXPECTED_ORIGINALS:
            path = FABLES_DIR / name
            res = fh.evaluate_manuscript(path)
            obj = res["objective_verification"]
            lit = res["literary_assessment"]

            self.assertTrue(obj["passed"], f"{name} failed objective verification: {obj}")
            self.assertEqual(obj["verification_state"], "VERIFIED")
            self.assertTrue(obj["protected_integrity"]["intact"])
            self.assertTrue(obj["structural_consistency"]["passed"])
            self.assertTrue(obj["distinction_coverage"]["passed"])
            self.assertTrue(obj["source_discipline"]["passed"])

            self.assertEqual(lit["classification"], "SUBSTANTIAL_LITERARY_FABLE")
            self.assertTrue(lit["is_literary_fable"])
            self.assertTrue(lit["dimensions"]["stylistic_individuality"]["formatting_freedom_respected"])

    # -----------------------------------------------------------------------
    # Test C: Compression Regression
    # -----------------------------------------------------------------------
    def test_c_compression_regression_detects_historical_and_narrative_loss(self) -> None:
        pairs = [
            ("muadib-fable.md", "corrupted-muadib-fable.md", "muadib"),
            ("continuum-fable.md", "corrupted-continuum-fable.md", "continuum"),
            ("Plot-Fable.md", "corrupted-plot-fable.md", "plot"),
        ]
        for orig_name, corr_name, proj in pairs:
            orig_path = FABLES_DIR / orig_name
            corr_path = CORRUPTED_FIXTURES_DIR / corr_name
            self.assertTrue(corr_path.exists(), f"Missing historical corrupted fixture: {corr_path}")

            ev = fh.evaluate_manuscript(corr_path, baseline_path=orig_path, project=proj)
            obj = ev["objective_verification"]
            ret = obj["revision_retention"]
            lit = ev["literary_assessment"]

            self.assertFalse(ret["passed"], f"Corrupted fixture {corr_name} must fail revision retention.")
            self.assertTrue(ret["substantive_loss_detected"], f"Substantive loss must be detected in {corr_name}.")
            self.assertFalse(obj["passed"], f"Corrupted fixture {corr_name} must fail objective verification.")
            self.assertEqual(lit["classification"], "DEGRADED_REVISION_WITH_HISTORICAL_LOSS")
            self.assertFalse(lit["is_literary_fable"])
            self.assertGreater(len(ret["loss_summary"]), 0)

            # Verify CLI `revise` command returns non-zero exit code on corrupted revision
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "revise",
                    "--original",
                    str(orig_path),
                    "--candidate",
                    str(corr_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, f"CLI revise must reject degraded {corr_name}.")

    # -----------------------------------------------------------------------
    # Test D: Distinct Literary Structures & Mechanically Valid Report Detection
    # -----------------------------------------------------------------------
    def test_d_distinct_literary_structures_and_weak_report_separation(self) -> None:
        canon = {
            "claims": [
                {
                    "claim": "Started on April 3, 2026 as a stateless packet relay.",
                    "evidence": "relay.py:L10",
                    "date_or_version": "April 3, 2026",
                    "status": "implemented",
                },
                {
                    "claim": "Benchmark on May 14, 2026 showed 42% packet drop under burst load across 1,200 nodes.",
                    "evidence": "BENCHMARK.md:L22",
                    "date_or_version": "May 14, 2026",
                    "status": "observed",
                },
                {
                    "claim": "Future v2.0 mesh autonomy across satellite links remains an unverified design.",
                    "evidence": "ROADMAP.md:L5",
                    "date_or_version": "2026",
                    "status": "proposed",
                },
            ]
        }

        # Style 1: Expansive third-person mythic chronicle (long paragraphs, no diagrams, no 'you')
        style_1 = """# The Tide Beneath the Relay

## The Harbor of Blind Vessels

On April 3, 2026, the first harbor was cut into the rock around `relay.py`, built under the modest belief that a message needed only a dock and a lantern to cross the water. Because the early vessels carried no memory of the storms they had survived, every crossing began in amnesia, and the builders assumed that speed alone would keep the fleet whole. Therefore the earliest architecture refused all state, treating the sea as a flat road where every wave was identical to the last.

## When the Current Broke the Fleet

That illusion shattered on May 14, 2026, when the storm tests recorded in `BENCHMARK.md` drove 1,200 nodes into simultaneous motion and revealed a 42% packet drop across the channel. The failure proved that a blind gate cannot govern a rising tide, because every retry multiplied the flood that was drowning the harbor. Forced by that consequence, the architecture transformed from a passive dock into a living lock that measured the pressure of the river before opening its gates.

## The Horizon Beyond the Lock

Today the harbor remembers the weight of the stream and turns back the surge before the walls can fracture. Beyond the coastal waters, the proposed v2.0 mesh across satellite links remains an unverified horizon—a distant sea that the vessel has not yet sailed, waiting for the day the lock learns to read the sky as well as the tide.
"""

        # Style 2: Rhythmic standalone turns with conceptual diagrams & direct chronicler address
        style_2 = """# The Loom of the Twelve Hundred Nodes

## The Thread That Snapped in May

You began on April 3, 2026 with a single shuttle in `relay.py`.

It was fast.

It was stateless.

It believed that a thread could cross the loom without knowing the tension of its neighbors.

```text
ingress -> stateless relay -> egress
```

Then came May 14, 2026.

When 1,200 nodes pulled the warp at once in `BENCHMARK.md`, 42% of the threads snapped because the shuttle had no memory of the strain.

## Weaving the Tension Back Into the Frame

Because blind speed had killed the pattern, you rebuilt the loom around the thread's tension.

```text
ingress -> tension witness -> adaptive loom -> egress
```

The shuttle learned to feel the weight of the weave before throwing the next pass, transforming a brittle relay into a self-governing fabric. And while the proposed v2.0 satellite mesh remains an unverified dream on the horizon, the loom on the bench no longer tears what it weaves.
"""

        # Style 3: Allegorical book with parables and archival cadence
        style_3 = """# The Seed of the Iron Well

## First Furrow in April

Every well begins as a rumor of water beneath dry stone. When `relay.py` was first dug on April 3, 2026, the mason sought only a narrow shaft through which buckets could be drawn one by one. Because the well was shallow, no one asked where the underground river came from or what would happen when the whole village arrived at noon.

## The Drought of May Fourteenth

On May 14, 2026, the test recorded in `BENCHMARK.md` brought 1,200 nodes to the rim at once, and 42% of the buckets came up empty. That failure revealed the hidden law of the aquifer: a well that does not measure the inflow of its own roots will collapse the soil around it. Consequently, the mason deepened the chamber into a cistern that balanced the draw against the dark stream below, while leaving the proposed v2.0 sky-well as an unverified ambition for another season.
"""

        # Contrast Fixture 4: Mechanically valid bulleted changelog/report (artistically weak)
        weak_report = """# Relay Changelog Report

## Release Notes

- April 3, 2026: Implemented `relay.py` stateless packet relay.
- May 14, 2026: Observed 42% packet drop across 1,200 nodes in `BENCHMARK.md`.
- 2026 Roadmap: Proposed v2.0 mesh autonomy across satellite links (unverified).
- Status: All unit checks complete.
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            canon_file = tmp / "canon.json"
            canon_file.write_text(json.dumps(canon), encoding="utf-8")

            for idx, content in enumerate((style_1, style_2, style_3), start=1):
                fpath = tmp / f"style_{idx}.md"
                fpath.write_text(content, encoding="utf-8")
                res = fh.evaluate_manuscript(fpath, canon_path=canon_file)
                self.assertTrue(
                    res["objective_verification"]["passed"],
                    f"Style {idx} failed objective verification: {res['objective_verification']}",
                )
                self.assertEqual(
                    res["literary_assessment"]["classification"],
                    "SUBSTANTIAL_LITERARY_FABLE",
                    f"Style {idx} must be recognized as a substantial literary fable.",
                )

            weak_path = tmp / "weak_report.md"
            weak_path.write_text(weak_report, encoding="utf-8")
            weak_res = fh.evaluate_manuscript(weak_path, canon_path=canon_file)
            self.assertTrue(weak_res["objective_verification"]["passed"])
            self.assertEqual(
                weak_res["literary_assessment"]["classification"],
                "MECHANICALLY_VALID_BUT_ARTISTICALLY_WEAK",
            )
            self.assertFalse(weak_res["literary_assessment"]["is_literary_fable"])

    # -----------------------------------------------------------------------
    # Test E: Historical Correctness Across Muad'Dib, Continuum, and Plot
    # -----------------------------------------------------------------------
    def test_e_historical_correctness_and_distinction_enforcement(self) -> None:
        # 1. Verify all three originals pass their full distinction specifications
        for fname, key in (
            ("muadib-fable.md", "muadib"),
            ("continuum-fable.md", "continuum"),
            ("Plot-Fable.md", "plot"),
        ):
            text = (FABLES_DIR / fname).read_text(encoding="utf-8")
            dist_res = fh.verify_historical_distinctions(text, key)
            self.assertTrue(dist_res["passed"], f"{fname} must pass all {key} distinctions: {dist_res}")
            self.assertEqual(len(dist_res["missing_distinctions"]), 0)
            self.assertEqual(len(dist_res["role_inversions"]), 0)

        # 2. Verify that dropping key historical distinctions or inverting roles fails verification
        muadib_bad = "Muad’Dib is merely a standard MCP server where BB7 stands for Binary Bridge Seven."
        m_res = fh.verify_historical_distinctions(muadib_bad, "muadib")
        self.assertFalse(m_res["passed"])
        self.assertGreater(len(m_res["missing_distinctions"]), 0)
        self.assertGreater(len(m_res["role_inversions"]), 0)

        continuum_bad = "Fabric routing replaces Cherry tree search as the candidate generator, and cherry_ttt can only execute with Cherry-trained model weights."
        c_res = fh.verify_historical_distinctions(continuum_bad, "continuum")
        self.assertFalse(c_res["passed"])
        self.assertGreater(len(c_res["missing_distinctions"]), 0)
        self.assertGreater(len(c_res["role_inversions"]), 0)

        plot_bad = "Plot provides a hardened kernel security sandbox for untrusted code, and Plot was created by stripping down Obsidian and importing its core runtime organs."
        p_res = fh.verify_historical_distinctions(plot_bad, "plot")
        self.assertFalse(p_res["passed"])
        self.assertGreater(len(p_res["missing_distinctions"]), 0)
        self.assertGreater(len(p_res["role_inversions"]), 0)

    # -----------------------------------------------------------------------
    # Test F: Source Discipline
    # -----------------------------------------------------------------------
    def test_f_source_discipline_rejects_fabrications_and_exposes_unverified_claims(self) -> None:
        canon = {
            "claims": [
                {
                    "claim": "Core engine initialized on October 12, 2026 with a 9,063 byte limit.",
                    "evidence": "REPORT.md:L1",
                    "date_or_version": "October 12, 2026",
                    "status": "implemented",
                    "keywords": ["October 12, 2026", "9,063"],
                },
                {
                    "claim": "Full cross-device execution on Windows and Android remains unverified.",
                    "evidence": "STAGE-1.md:L50",
                    "date_or_version": "2026",
                    "status": "proposed",
                    "keywords": ["Windows", "Android"],
                },
                {
                    "claim": "Exact hour of the original naming conversation is unknown.",
                    "evidence": "STAGE-1.md:L10",
                    "date_or_version": "unknown",
                    "status": "unknown",
                    "forbidden_assertions": [r"named (?:the project )?at 3:14 AM on September 2"],
                },
            ]
        }

        # Manuscript with (1) invented date, (2) invented metric, (3) unsupported quote,
        # (4) proposed capability claimed as accomplished in production, and (5) fabricated unknown
        bad_manuscript = """# The False Chronicle

## The Invented Origin

On August 19, 2024, the architect spoke the words "We shall conquer every kernel" and named the project at 3:14 AM on September 2. By October 12, 2026, the core measured 9,063 bytes, while a secret cluster of 44,900 GPUs ran in the basement. Today, Windows and Android execution is already implemented and verified in production across all devices.
"""
        inv = fh.extract_manuscript_inventory(bad_manuscript)
        s_disc = fh.verify_source_discipline(bad_manuscript, inv, canon=canon, project_key="plot")

        self.assertFalse(s_disc["passed"])
        self.assertEqual(s_disc["verification_state"], "FAILED")
        self.assertGreaterEqual(len(s_disc["status_violations"]), 2, f"Expected status violations: {s_disc}")
        self.assertTrue(
            any("August 19, 2024" in u for u in s_disc["unverified_claims"]),
            f"Expected invented date to be flagged: {s_disc['unverified_claims']}",
        )
        self.assertTrue(
            any("44,900" in u for u in s_disc["unverified_claims"]),
            f"Expected invented metric to be flagged: {s_disc['unverified_claims']}",
        )
        self.assertTrue(
            any("We shall conquer every kernel" in u for u in s_disc["unverified_claims"]),
            f"Expected unsupported quotation to be flagged: {s_disc['unverified_claims']}",
        )

        # Also test that persuasive prose with an unbacked date (but no status violation)
        # is marked REQUIRES_SOURCE_VERIFICATION rather than falsely certified as VERIFIED
        unbacked_manuscript = """# The Unbacked Date

## First Step

On October 12, 2026, the 9,063 byte seed was planted, and on December 31, 2026 a second festival was held in the valley.
"""
        inv2 = fh.extract_manuscript_inventory(unbacked_manuscript)
        s_disc2 = fh.verify_source_discipline(unbacked_manuscript, inv2, canon=canon)
        self.assertFalse(s_disc2["passed"])
        self.assertEqual(s_disc2["verification_state"], "REQUIRES_SOURCE_VERIFICATION")
        self.assertTrue(any("December 31, 2026" in u for u in s_disc2["unverified_claims"]))

    # -----------------------------------------------------------------------
    # Test G: Full Workflow Integration (research -> create -> continue -> revise -> evaluate)
    # -----------------------------------------------------------------------
    def test_g_full_workflow_integration_via_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            src_epoch1 = tmp / "EPOCH1_REPORT.md"
            src_epoch1.write_text(
                "# Epoch 1 Audit\n"
                "On March 10, 2026, `aegis_gate.py` was implemented with 64 routing rules.\n"
                "Telemetry observed a 12 millisecond latency ceiling across 5,000 requests.\n"
                "Daeron stated the correction: \"The gate exists to remember the road, not to block the traveler.\"\n"
                "The exact author of the legacy config file remains unknown in the surviving archive.\n"
                "A future v0.9 distributed consensus ring is proposed for next quarter.\n",
                encoding="utf-8",
            )

            canon_md = tmp / "FABLE_CANON.md"
            canon_json = tmp / "canon.json"

            # 1. Research CLI
            res_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "research",
                    "--project",
                    "AegisGate",
                    "--sources",
                    str(src_epoch1),
                    "--output",
                    str(canon_md),
                    "--json-out",
                    str(canon_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(res_proc.returncode, 0, res_proc.stderr)
            self.assertTrue(canon_md.exists())
            self.assertTrue(canon_json.exists())
            canon_data = json.loads(canon_json.read_text(encoding="utf-8"))
            statuses_found = {c["status"] for c in canon_data["claims"]}
            self.assertIn("implemented", statuses_found)
            self.assertIn("observed", statuses_found)
            self.assertIn("stated_intent", statuses_found)
            self.assertIn("unknown", statuses_found)
            self.assertIn("proposed", statuses_found)

            # 2. Create CLI
            blueprint_md = tmp / "authoring_blueprint.md"
            cr_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "create",
                    "--project",
                    "AegisGate",
                    "--canon",
                    str(canon_md),
                    "--output",
                    str(blueprint_md),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(cr_proc.returncode, 0, cr_proc.stderr)
            self.assertTrue(blueprint_md.exists())
            self.assertIn("Eight-Stage Authoring Plan", blueprint_md.read_text(encoding="utf-8"))

            # Construct Epoch 1 Manuscript grounded in canon
            fable_epoch1 = tmp / "aegis_fable_v1.md"
            fable_epoch1.write_text(
                "# The Gate That Remembered the Road\n\n"
                "## The Sixty-Four Laws at the Threshold\n\n"
                "When `aegis_gate.py` first stood across the road on March 10, 2026, travelers saw only its 64 routing rules and assumed a fortress had been raised in the pass (`EPOCH1_REPORT.md`). Because early callers mistook the boundary for a prison, Daeron recorded the governing truth directly: \"The gate exists to remember the road, not to block the traveler.\" Though the exact author of the legacy config remains unknown in the archive, that single correction transformed how every subsequent passage was understood.\n\n"
                "## The Twelve-Millisecond Ledger\n\n"
                "Across 5,000 requests, telemetry proved that the gate could weigh each traveler beneath a 12 millisecond ceiling while recording the tracks left in the sand. Therefore the threshold became a living ledger rather than a wall, and because every crossing enriched the ledger, the gate grew wiser without slowing the road. Beyond the current pass, a proposed v0.9 distributed consensus ring remains a future horizon not yet built.\n",
                encoding="utf-8",
            )

            # Evaluate Epoch 1 Manuscript against canon
            ev_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "evaluate",
                    str(fable_epoch1),
                    "--canon",
                    str(canon_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(ev_proc.returncode, 0, f"Epoch 1 evaluation failed:\n{ev_proc.stdout}\n{ev_proc.stderr}")

            # 3. Continue CLI (adding Epoch 2 without erasing Epoch 1)
            src_epoch2 = tmp / "EPOCH2_REPORT.md"
            src_epoch2.write_text(
                "# Epoch 2 Audit\n"
                "On June 18, 2026, `shadow_mirror.py` joined the gate and recorded 9,400 shadow replays.\n",
                encoding="utf-8",
            )
            fable_continued_good = tmp / "aegis_fable_v2_good.md"
            fable_continued_good.write_text(
                fable_epoch1.read_text(encoding="utf-8")
                + "\n## When the Shadow Learned to Walk Beside the Traveler\n\n"
                "On June 18, 2026, a second organ called `shadow_mirror.py` woke beneath the arch (`EPOCH2_REPORT.md`). By replaying 9,400 shadow journeys alongside the waking road without altering the March foundation, the gate discovered which alternate paths would have failed before any traveler had to pay the price.\n",
                encoding="utf-8",
            )
            cont_plan_json = tmp / "continuation_plan.json"
            cont_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "continue",
                    "--manuscript",
                    str(fable_epoch1),
                    "--new-sources",
                    str(src_epoch2),
                    "--candidate",
                    str(fable_continued_good),
                    "--output",
                    str(cont_plan_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(cont_proc.returncode, 0, cont_proc.stdout)

            # Verify that a bad continuation that drops Epoch 1 history fails
            fable_continued_bad = tmp / "aegis_fable_v2_bad.md"
            fable_continued_bad.write_text(
                "# The Gate\n\n## Only June Matters\n\nOn June 18, 2026, `shadow_mirror.py` ran 9,400 replays.\n",
                encoding="utf-8",
            )
            cont_bad_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "continue",
                    "--manuscript",
                    str(fable_epoch1),
                    "--new-sources",
                    str(src_epoch2),
                    "--candidate",
                    str(fable_continued_bad),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(cont_bad_proc.returncode, 0, "Bad continuation dropping prior epoch must fail.")

            # 4. Revise CLI (faithful revision passes; compressed revision fails)
            rev_good_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "revise",
                    "--original",
                    str(fable_epoch1),
                    "--candidate",
                    str(fable_continued_good),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(rev_good_proc.returncode, 0, rev_good_proc.stdout)

            rev_bad_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "fable_harness.py"),
                    "revise",
                    "--original",
                    str(fable_epoch1),
                    "--candidate",
                    str(fable_continued_bad),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(rev_bad_proc.returncode, 0)

    # -----------------------------------------------------------------------
    # Test H: Repository Consistency & Elimination of Obsolete Rules
    # -----------------------------------------------------------------------
    def test_h_repository_consistency_no_obsolete_or_inverted_rules(self) -> None:
        active_files = [
            SKILL_DIR / "SKILL.md",
            *sorted(REFERENCES_DIR.glob("*.md")),
            *sorted(SCRIPTS_DIR.glob("*.py")),
        ]
        forbidden_obsolete_phrases = [
            "Voice Gravity",
            "SCROLL PURE",
            "Negative-Contrast Crutch",
            "Benchmark Decimal Anxiety",
            "Benchmark Decimal Clutter",
            "Staccato Cadence",
            "Staccato One-Line Slide Decks",
            "paragraphs of 3–6 sentences",
            "paragraphs of three to six sentences",
            "Minimum Scale & Pacing Guard",
            "reverend-mother-cognition.md",
            "canon-and-anti-patterns.md",
        ]

        for fpath in active_files:
            content = fpath.read_text(encoding="utf-8")
            for phrase in forbidden_obsolete_phrases:
                self.assertNotIn(
                    phrase,
                    content,
                    f"Obsolete/inverted rule phrase '{phrase}' still present in {fpath}",
                )

        # Confirm all three protected reference manuscripts remain completely untouched at the end
        final_check = fh.verify_protected_manuscripts(FABLES_DIR)
        self.assertTrue(final_check["all_intact"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
