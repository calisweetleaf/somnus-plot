#!/usr/bin/env python3
"""
fable_harness.py — Research, Authoring, Continuation, Revision, and Dual-Layer
Evaluation System for Somnus Code Fables.

Operations:
    verify-originals — Verify SHA-256 integrity of protected reference manuscripts
    status           — Display reference archive status and dual-layer evaluation summary
    research         — Extract and organize source-linked evidence into FABLE_CANON.md / JSON
    create           — Generate an 8-stage authoring blueprint from a project canon
    continue         — Lock prior epoch history and verify/plan a manuscript continuation
    revise           — Audit a candidate revision against an original manuscript for claim retention
    evaluate / lint  — Run Objective Verification + Qualitative Literary Assessment
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).resolve().parent.parent
FABLES_DIR = SKILL_DIR / "fables"
REFERENCES_DIR = SKILL_DIR / "references"

VALID_CLAIM_STATUSES = (
    "implemented",
    "observed",
    "stated_intent",
    "proposed",
    "inferred",
    "unknown",
    "conflicting",
)

# Authoritative reference manuscripts and their canonical forensic measurements.
# These figures describe the specific restored artifacts; they are NOT universal quotas.
PROTECTED_REFERENCE_MANUSCRIPTS: dict[str, dict[str, Any]] = {
    "muadib-fable.md": {
        "project": "muadib",
        "title": "Muad’Dib and the Mummer’s Farce: The History of the Server That Was Never Really an MCP Server",
        "sha256": "a209e466cb097f40ba8e1bbf58b6803bd717edcdce8a903dbac78c7c0b03c580",
        "lines": 783,
        "words": 5655,
        "bytes": 40056,
    },
    "continuum-fable.md": {
        "project": "continuum",
        "title": "The Cherry Tree at Midnight",
        "sha256": "63e5386e5c7dd98864e55daea1cb47be6a04c148663b9ca98ac6fa726a877682",
        "lines": 1638,
        "words": 6753,
        "bytes": 49930,
    },
    "Plot-Fable.md": {
        "project": "plot",
        "title": "The Acre That Refused the Kingdom",
        "sha256": "48740ef5a3ef582417b90835d0c747f254eb87a997f62b8df2598b1382a41628",
        "lines": 930,
        "words": 5721,
        "bytes": 37821,
    },
}

# Project-specific historical & architectural distinction specifications for regression testing (Test E).
REFERENCE_DISTINCTIONS: dict[str, dict[str, Any]] = {
    "muadib": {
        "project": "muadib",
        "required_distinctions": [
            {
                "id": "two_births",
                "description": "Preserves the two historical births: Nov 25, 2024 (finished tools/ and mcp_server.py by March 2025 as a tool server) vs. Jan 1, 2026 resurrection for the data flywheel.",
                "required_groups": [
                    ["November 25, 2024"],
                    ["March 2025"],
                    ["January 1, 2026"],
                    ["data flywheel"],
                ],
            },
            {
                "id": "mcp_transport_vs_organism",
                "description": "Distinguishes MCP as the outer transport/mask from the underlying neural-symbolic organism (Lisan/exoskeleton, Muad'Dib 512-dimensional substrate, effectors, and data/).",
                "required_groups": [
                    ["mummer", "mask", "costume"],
                    ["transport", "routed"],
                    ["Lisan"],
                    ["exoskeleton"],
                    ["512-dimensional"],
                ],
            },
            {
                "id": "bb7_provenance_and_execution",
                "description": "Preserves that no surviving source expands BB7 as an acronym, the aa6_/bb7_/cc8_ hierarchy, bb7_exo_execute_step recording rather than mutating, and tool counts (115, 110, 120, 119, 147, 265) as snapshots.",
                "required_groups": [
                    ["acronym"],
                    ["aa6_", "bb7_", "cc8_"],
                    ["bb7_exo_execute_step"],
                    ["115"],
                    ["265"],
                ],
            },
            {
                "id": "data_and_learning_lineage",
                "description": "Preserves data/ as an intelligent cognition data-plane (raw evidence before display cleaning), May telemetry (3,421 plans, 28% vs 0.04%), Codex distillation for tool reasoning (outgrowing bb7_), RFT vs. self-play separation, and the harness freeing the sniper successor.",
                "required_groups": [
                    ["SOVEREIGN_DATA_DIR", "intelligent data-plane", "durable cognition"],
                    ["3,421"],
                    ["0.04%"],
                    ["self-play"],
                    ["sniper"],
                ],
            },
        ],
        "forbidden_role_inversions": [
            {
                "id": "mcp_is_whole_system",
                "pattern": r"\bMuad[’']?Dib is merely a standard MCP server\b",
                "reason": "Contradicts the core distinction between MCP transport and the underlying neural-symbolic organism.",
            },
            {
                "id": "self_play_writes_q_table",
                "pattern": r"\bself-play trajectories write directly into the live Q-table by default\b",
                "reason": "Contradicts the separation of synthetic self-play from real observations in the Q-table.",
            },
            {
                "id": "invented_bb7_acronym",
                "pattern": r"\bBB7 stands for [A-Z][a-z]+\s+[A-Z][a-z]+",
                "reason": "Fabricates an English acronym expansion for BB7 where the record establishes none.",
            },
        ],
    },
    "continuum": {
        "project": "continuum",
        "required_distinctions": [
            {
                "id": "cherry_vs_cherry_ttt",
                "description": "Distinguishes Cherry (the older training-and-inference methodology) from cherry_ttt (Cherry Test-Time Tooling, July 5, 2026, generalizing LexicalMDP across speculative, transactional, and real substrates).",
                "required_groups": [
                    ["Cherry always was like that", "never downstream"],
                    ["LexicalMDP"],
                    ["July 5, 2026", "July 5"],
                    ["speculative", "transactional"],
                ],
            },
            {
                "id": "fabric_and_equalizer_boundaries",
                "description": "Preserves the resident reactive attention Fabric (observe(stream_event)), the Symbolic Fault Equalizer (Dyson sphere / sun), FabricCommitSink translating EqualizedTransition into StreamEvent, and the 0.19 recall failure proving Fabric cannot replace Cherry search.",
                "required_groups": [
                    ["observe(stream_event)"],
                    ["Dyson sphere"],
                    ["FabricCommitSink", "EqualizedTransition", "StreamEvent"],
                    ["0.19"],
                ],
            },
            {
                "id": "continuum_naming_evolution",
                "description": "Preserves the evolution of the name Continuum: September framing of cherry_ttt as Continuum (counterfactual continuity) vs. October restoration of cherry_ttt because Continuum = Fabric + cherry_ttt.",
                "required_groups": [
                    ["counterfactual continuity"],
                    ["substrate continuity"],
                    ["NOW cherry_ttt, BOOOM we now have Continuum"],
                ],
            },
            {
                "id": "compiler_pro_mode_and_training_loop",
                "description": "Preserves the LLVM compiler analogy, the Pro Mode contrast (1.5 seconds search vs millisecond write), model-independence (use_value_model=False), and Cherry training internalization (TreeRolloutCollector / GRPOTrainer).",
                "required_groups": [
                    ["LLVM"],
                    ["1.5 seconds"],
                    ["use_value_model=False"],
                    ["TreeRolloutCollector", "GRPOTrainer"],
                ],
            },
        ],
        "forbidden_role_inversions": [
            {
                "id": "fabric_replaces_search",
                "pattern": r"\bFabric routing replaces Cherry tree search as the candidate generator\b",
                "reason": "Contradicts the 0.19 recall finding that rejected Fabric routing as a candidate generator.",
            },
            {
                "id": "continuum_locked_to_cherry_weights",
                "pattern": r"\bcherry_ttt can only execute with Cherry-trained model weights\b",
                "reason": "Contradicts constitutional model-independence (use_value_model=False).",
            },
        ],
    },
    "plot": {
        "project": "plot",
        "required_distinctions": [
            {
                "id": "independent_experimental_identity",
                "description": "Preserves Plot's unassigned laboratory status (role in broader Somnus is none; not built for Companion, ARCS, or Forseti), downstream transfer vs. core adoption, and Obsidian as scale reference rather than parent.",
                "required_groups": [
                    ["no assignment", "role in broader Somnus was **none**", "role in broader Somnus was none"],
                    ["Obsidian"],
                    ["downstream transfer"],
                ],
            },
            {
                "id": "not_webview_and_not_sandbox",
                "description": "Preserves that the v0.4 webview was a window rather than the house, and that Plot is trusted execution rather than an isolation sandbox.",
                "required_groups": [
                    ["window was never the house"],
                    ["not a sandbox"],
                    ["trusted execution"],
                ],
            },
            {
                "id": "seed_ceiling_and_grave_persistence",
                "description": "Preserves the 9,063-byte ceiling across v0.4 (Oct 12), v0.5 / Flashback Stage 1 (Oct 14, 9,036 bytes, 18 of 18 checks, 'The core cannot grow with the catalog'), and v0.6 (9,061 bytes), with .grave/ holding acquired capabilities and the optional resident supervisor.",
                "required_groups": [
                    ["9,063"],
                    ["9,036"],
                    ["9,061"],
                    ["The core cannot grow with the catalog"],
                    [".grave/"],
                ],
            },
            {
                "id": "demonstrated_vs_future_ambition",
                "description": "Separates demonstrated Linux metrics (4.066ms cached view and 3.614ms resident request beneath 6ms vs. 7.861ms durable submission) from unverified Windows/macOS/Android paths, full Python beyond shallow host Python, and the future persistent virtual machine goal.",
                "required_groups": [
                    ["4.066"],
                    ["3.614"],
                    ["7.861"],
                    ["unverified"],
                    ["persistent virtual machine"],
                ],
            },
        ],
        "forbidden_role_inversions": [
            {
                "id": "plot_is_security_sandbox",
                "pattern": r"\bPlot provides a hardened kernel security sandbox for untrusted code\b",
                "reason": "Contradicts STAGE-1.md and PERSISTENT-NATIVE.md which define Plot as trusted execution, not a sandbox.",
            },
            {
                "id": "plot_inherits_from_obsidian",
                "pattern": r"\bPlot was created by stripping down Obsidian and importing its core runtime organs\b",
                "reason": "Contradicts the canon that Obsidian is only a scale comparison, not an implementation parent.",
            },
            {
                "id": "plot_already_verified_all_platforms",
                "pattern": r"\bv0\.6 is fully verified in production across Windows, macOS, Android, and iOS\b",
                "reason": "Presents unverified cross-device targets as accomplished fact.",
            },
        ],
    },
}


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_protected_manuscript(path: Path) -> bool:
    try:
        resolved = path.resolve()
        for name in PROTECTED_REFERENCE_MANUSCRIPTS:
            if resolved == (FABLES_DIR / name).resolve():
                return True
    except OSError:
        pass
    return False


def assert_not_protected_manuscript(path: Path) -> None:
    if is_protected_manuscript(path):
        raise PermissionError(
            f"Refusing to overwrite protected reference manuscript: {path}. "
            "Authoritative reference works in fables/ are immutable."
        )


def verify_protected_manuscripts(fables_dir: Path = FABLES_DIR) -> dict[str, Any]:
    results: dict[str, Any] = {}
    all_intact = True
    for filename, meta in PROTECTED_REFERENCE_MANUSCRIPTS.items():
        fpath = fables_dir / filename
        if not fpath.exists():
            all_intact = False
            results[filename] = {
                "exists": False,
                "intact": False,
                "expected_sha256": meta["sha256"],
                "actual_sha256": None,
            }
            continue
        actual_hash = compute_sha256(fpath)
        raw_bytes = fpath.read_bytes()
        text = raw_bytes.decode("utf-8")
        # wc -l counts newline characters
        line_count = raw_bytes.count(b"\n")
        word_count = len(text.split())
        byte_count = len(raw_bytes)
        intact = actual_hash == meta["sha256"]
        if not intact:
            all_intact = False
        results[filename] = {
            "exists": True,
            "intact": intact,
            "expected_sha256": meta["sha256"],
            "actual_sha256": actual_hash,
            "lines": line_count,
            "words": word_count,
            "bytes": byte_count,
        }
    return {"all_intact": all_intact, "manuscripts": results}


# ---------------------------------------------------------------------------
# Manuscript Parsing & Historical Inventory Extraction
# ---------------------------------------------------------------------------

DATE_PATTERNS = [
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?\b",
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b202[4-9]\b",
]

METRIC_PATTERNS = [
    r"\bv\d+\.\d+\b",
    r"\b\d{1,3}(?:,\d{3})+\b",
    r"\b\d+(?:\.\d+)?%\b",
    r"\b\d[\d,]*(?:\.\d+)?\s*(?:milliseconds|millisecond|ms|seconds|bytes|tools|modules|kernels|trajectories|steps|observations|entries|nodes|requests|replays|rules)\b",
    r"\b\d+-dimensional\b",
    r"\b0\.\d+\b",
    r"\b\d+\s+of\s+\d+\b",
]


def extract_manuscript_inventory(text: str) -> dict[str, Any]:
    lines = text.splitlines()

    # Title
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Headings (## and ###)
    h2_headings = [line[3:].strip() for line in lines if line.startswith("## ")]
    h3_headings = [line[4:].strip() for line in lines if line.startswith("### ")]

    # Fenced blocks
    fence_lines = [idx for idx, line in enumerate(lines, start=1) if line.strip().startswith("```")]
    balanced_fences = (len(fence_lines) % 2) == 0

    # Dates
    dates: set[str] = set()
    for pat in DATE_PATTERNS:
        for m in re.finditer(pat, text):
            dates.add(m.group(0))

    # Empirical metrics & counts
    metrics: set[str] = set()
    for pat in METRIC_PATTERNS:
        for m in re.finditer(pat, text):
            metrics.add(m.group(0))

    # Citations (platform citations + explicit artifact filenames)
    citations: set[str] = set()
    for m in re.finditer(r"(?:file)?cite[^]+", text):
        citations.add(m.group(0))
    for m in re.finditer(r"`([A-Za-z0-9_./*-]+\.(?:md|py|json|jsonl|ts|js|yaml|yml))`", text):
        citations.add(m.group(1))

    # Code / architectural identifiers in backticks
    identifiers: set[str] = set()
    for m in re.finditer(r"`([A-Za-z0-9_./*=-]{3,})`", text):
        identifiers.add(m.group(1))

    # Direct quotations (curly and straight quotes of 4+ words)
    quotations: set[str] = set()
    for m in re.finditer(r"[“\"]([^”\"\n]{18,160})[”\"]", text):
        q = m.group(1).strip()
        if len(q.split()) >= 4:
            quotations.add(q)

    # Paragraphs (excluding code blocks)
    in_code = False
    paragraphs: list[str] = []
    cur: list[str] = []
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line.strip():
            if cur:
                paragraphs.append(" ".join(cur))
                cur = []
        else:
            cur.append(line.strip())
    if cur:
        paragraphs.append(" ".join(cur))

    prose_paragraphs = [
        p for p in paragraphs
        if not p.startswith("#") and not p.startswith("<!--")
    ]

    # Causal transitions
    causal_markers = re.findall(
        r"\b(because|therefore|consequence|consequently|revealed|forced|discovered|killed|proved|"
        r"resurrected|transformed|transforming|outlive|internaliz\w+|changed|learned|turned|until)\b",
        text,
        re.IGNORECASE,
    )

    prose_text = " ".join(prose_paragraphs)
    prose_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prose_text) if len(s.split()) >= 4]

    return {
        "title": title,
        "h2_headings": h2_headings,
        "h3_headings": h3_headings,
        "balanced_fences": balanced_fences,
        "fence_block_count": len(fence_lines) // 2,
        "dates": sorted(dates),
        "metrics": sorted(metrics),
        "citations": sorted(citations),
        "identifiers": sorted(identifiers),
        "quotations": sorted(quotations),
        "paragraph_count": len(prose_paragraphs),
        "prose_sentence_count": len(prose_sentences),
        "causal_marker_count": len(causal_markers),
        "word_count": len(text.split()),
        "line_count": len(lines),
    }


# ---------------------------------------------------------------------------
# Layer 1: Objective Verification
# ---------------------------------------------------------------------------

def check_structural_consistency(text: str, inv: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not inv["title"]:
        issues.append("Missing top-level document title (`# Title`).")
    if len(inv["h2_headings"]) == 0:
        issues.append("Missing section headings (`## Section`).")
    if not inv["balanced_fences"]:
        issues.append("Unbalanced fenced code blocks (odd number of ``` delimiters).")
    if inv["paragraph_count"] == 0:
        issues.append("Document contains no prose paragraphs.")

    return {
        "passed": len(issues) == 0,
        "title": inv["title"],
        "section_count": len(inv["h2_headings"]),
        "subsection_count": len(inv["h3_headings"]),
        "balanced_fences": inv["balanced_fences"],
        "issues": issues,
    }


def infer_project_key(path: Path | None, text: str, explicit_project: str | None = None) -> str | None:
    if explicit_project:
        key = explicit_project.lower().strip()
        if key in REFERENCE_DISTINCTIONS:
            return key
    if path is not None:
        name_lower = path.name.lower()
        if "muadib" in name_lower:
            return "muadib"
        if "continuum" in name_lower:
            return "continuum"
        if "plot" in name_lower:
            return "plot"
    return None


def verify_historical_distinctions(text: str, project_key: str | None) -> dict[str, Any]:
    if not project_key or project_key not in REFERENCE_DISTINCTIONS:
        return {
            "applicable": False,
            "project": project_key,
            "passed": True,
            "distinctions_checked": 0,
            "missing_distinctions": [],
            "role_inversions": [],
        }

    spec = REFERENCE_DISTINCTIONS[project_key]
    missing_distinctions: list[dict[str, Any]] = []
    text_lower = text.lower()

    for dist in spec["required_distinctions"]:
        missing_groups: list[list[str]] = []
        for group in dist["required_groups"]:
            if not any(term.lower() in text_lower for term in group):
                missing_groups.append(group)
        if missing_groups:
            missing_distinctions.append({
                "id": dist["id"],
                "description": dist["description"],
                "missing_evidence_terms": missing_groups,
            })

    role_inversions: list[dict[str, str]] = []
    for inv_rule in spec.get("forbidden_role_inversions", []):
        if re.search(inv_rule["pattern"], text, re.IGNORECASE):
            role_inversions.append({
                "id": inv_rule["id"],
                "reason": inv_rule["reason"],
            })

    passed = (len(missing_distinctions) == 0) and (len(role_inversions) == 0)
    return {
        "applicable": True,
        "project": project_key,
        "passed": passed,
        "distinctions_checked": len(spec["required_distinctions"]),
        "missing_distinctions": missing_distinctions,
        "role_inversions": role_inversions,
    }


def load_canon_ledger(canon_path: Path) -> dict[str, Any]:
    content = canon_path.read_text(encoding="utf-8")
    if canon_path.suffix.lower() == ".json":
        return json.loads(content)

    # Parse Markdown FABLE_CANON.md table format:
    # | Claim or event | Best evidence | Date or version | Status | Narrative use |
    claims: list[dict[str, Any]] = []
    for line in content.splitlines():
        s = line.strip()
        if not s.startswith("|") or "---" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 4 and cells[0].lower() not in ("claim or event", "claim"):
            claims.append({
                "claim": cells[0],
                "evidence": cells[1],
                "date_or_version": cells[2],
                "status": cells[3].lower().strip("*` "),
                "narrative_use": cells[4] if len(cells) >= 5 else "",
            })
    return {"claims": claims}


def verify_source_discipline(
    text: str,
    inv: dict[str, Any],
    canon: dict[str, Any] | None = None,
    project_key: str | None = None,
) -> dict[str, Any]:
    """
    Verifies epistemic & source discipline:
    1. Detects fabricated/unsupported dates, metrics, or quotations not grounded in the supplied canon.
    2. Detects status violations (e.g., presenting 'proposed' claims as accomplished/implemented fact,
       or fabricating answers for 'unknown' claims).
    3. Detects architectural role inversions.
    4. Honestly reports when external source verification is required rather than certifying unbacked claims.
    """
    status_violations: list[str] = []
    role_violations: list[str] = []
    unverified_claims: list[str] = []

    # Check built-in role/status inversions if project_key is known
    if project_key and project_key in REFERENCE_DISTINCTIONS:
        for rule in REFERENCE_DISTINCTIONS[project_key].get("forbidden_role_inversions", []):
            if re.search(rule["pattern"], text, re.IGNORECASE):
                role_violations.append(f"{rule['id']}: {rule['reason']}")

    # Universal check against fabricating an English acronym for BB7 if BB7 is discussed
    if "BB7" in text:
        m_acr = re.search(r"\bBB7\s+(?:stands for|is an acronym for|expands to)\s+([A-Z][A-Za-z]+\s+[A-Z][A-Za-z]+)", text)
        if m_acr:
            status_violations.append(
                f"Fabricated acronym expansion for BB7 ('{m_acr.group(0)}'): record establishes no English acronym."
            )

    if canon is None:
        has_inline_citations = len(inv["citations"]) > 0
        verification_state = (
            "FAILED"
            if (status_violations or role_violations)
            else ("CITATIONS_PRESENT_EXTERNAL_SOURCES_NOT_LOADED" if has_inline_citations else "REQUIRES_SOURCE_VERIFICATION")
        )
        return {
            "passed": len(status_violations) == 0 and len(role_violations) == 0,
            "verification_state": verification_state,
            "inline_citation_count": len(inv["citations"]),
            "status_violations": status_violations,
            "role_violations": role_violations,
            "unverified_claims": unverified_claims,
            "note": (
                "No external canon ledger supplied; inline citations were inventoried, "
                "and any unbacked factual claims require primary source verification."
            ),
        }

    # When a canon ledger IS supplied, verify manuscript claims against it
    claims = canon.get("claims", [])
    canon_text_blob = json.dumps(canon, ensure_ascii=False).lower()

    # 1. Check each canon claim's epistemic status vs. how the manuscript treats it
    accomplished_assertion_re = re.compile(
        r"\b(already implemented|fully implemented|verified in production|is now complete and deployed|"
        r"has already achieved|proven in production across all|was completed in)\b",
        re.IGNORECASE,
    )

    sentences = re.split(r"(?<=[.!?])\s+", text)
    for item in claims:
        status = item.get("status", "").lower()
        keywords = item.get("keywords") or [
            w for w in re.findall(r"[A-Za-z0-9_.-]{4,}", item.get("claim", ""))
            if w.lower() not in ("that", "this", "with", "from", "were", "have", "been")
        ][:4]

        if status == "proposed":
            for sent in sentences:
                if keywords and all(k.lower() in sent.lower() for k in keywords[:2]):
                    if accomplished_assertion_re.search(sent):
                        status_violations.append(
                            f"Proposed capability presented as accomplished fact: '{sent.strip()}' "
                            f"(canon status: proposed — {item.get('claim')})"
                        )
            for forbidden in item.get("forbidden_assertions", []):
                if re.search(forbidden, text, re.IGNORECASE):
                    status_violations.append(
                        f"Status violation for proposed claim '{item.get('claim')}': matched '{forbidden}'."
                    )

        elif status in ("unknown", "conflicting"):
            for forbidden in item.get("forbidden_assertions", []):
                if re.search(forbidden, text, re.IGNORECASE):
                    status_violations.append(
                        f"Fabricated certainty for '{status}' claim '{item.get('claim')}': matched '{forbidden}'."
                    )

    for forbidden_role in canon.get("forbidden_role_inversions", []):
        pat = forbidden_role.get("pattern", "")
        if pat and re.search(pat, text, re.IGNORECASE):
            role_violations.append(forbidden_role.get("reason", f"Matched forbidden role pattern: {pat}"))

    # 2. Check for invented dates, metrics, or quotations not present in the canon ledger
    for d in inv["dates"]:
        if d.lower() not in canon_text_blob:
            unverified_claims.append(f"Unverified date not found in source ledger: '{d}'")

    for m in inv["metrics"]:
        m_norm = m.lower().strip()
        # Check either full metric string or its numeric core in canon
        num_core = re.findall(r"\d[\d,.]*", m_norm)
        if m_norm not in canon_text_blob and not (num_core and all(nc in canon_text_blob for nc in num_core)):
            unverified_claims.append(f"Unverified metric/count not found in source ledger: '{m}'")

    for q in inv["quotations"]:
        if q.lower() not in canon_text_blob:
            unverified_claims.append(f"Unverified quotation not found in source ledger: \"{q}\"")

    has_hard_violation = len(status_violations) > 0 or len(role_violations) > 0
    has_unverified = len(unverified_claims) > 0

    if has_hard_violation:
        v_state = "FAILED"
    elif has_unverified:
        v_state = "REQUIRES_SOURCE_VERIFICATION"
    else:
        v_state = "VERIFIED"

    return {
        "passed": (not has_hard_violation) and (not has_unverified),
        "verification_state": v_state,
        "inline_citation_count": len(inv["citations"]),
        "status_violations": status_violations,
        "role_violations": role_violations,
        "unverified_claims": unverified_claims,
    }


def verify_revision_retention(original_text: str, candidate_text: str) -> dict[str, Any]:
    """
    Compares a candidate revision against its original manuscript to detect
    substantive historical, empirical, or narrative loss (Test C & Section VI).
    """
    orig_inv = extract_manuscript_inventory(original_text)
    cand_inv = extract_manuscript_inventory(candidate_text)
    cand_lower = candidate_text.lower()

    missing_dates = [d for d in orig_inv["dates"] if d.lower() not in cand_lower]
    missing_metrics = [m for m in orig_inv["metrics"] if m.lower() not in cand_lower]
    missing_identifiers = [ident for ident in orig_inv["identifiers"] if ident.lower() not in cand_lower]
    missing_citations = [c for c in orig_inv["citations"] if c not in candidate_text and c.lower() not in cand_lower]
    missing_h2 = [h for h in orig_inv["h2_headings"] if h.lower() not in cand_lower]
    missing_h3 = [h for h in orig_inv["h3_headings"] if h.lower() not in cand_lower]
    missing_quotes = [q for q in orig_inv["quotations"] if q.lower() not in cand_lower]

    def retention_rate(orig_list: list[str], missing_list: list[str]) -> float:
        if not orig_list:
            return 1.0
        return round((len(orig_list) - len(missing_list)) / len(orig_list), 3)

    date_ret = retention_rate(orig_inv["dates"], missing_dates)
    metric_ret = retention_rate(orig_inv["metrics"], missing_metrics)
    ident_ret = retention_rate(orig_inv["identifiers"], missing_identifiers)
    cite_ret = retention_rate(orig_inv["citations"], missing_citations)
    quote_ret = retention_rate(orig_inv["quotations"], missing_quotes)
    h2_ret = retention_rate(orig_inv["h2_headings"], missing_h2)
    h3_ret = retention_rate(orig_inv["h3_headings"], missing_h3)

    # Substantive loss occurs if established dates, empirical metrics, key identifiers,
    # citations, quotations, or chronological sub-acts (h2/h3) are dropped.
    substantive_loss = (
        len(missing_dates) > 0
        or len(missing_metrics) > 2
        or ident_ret < 0.85
        or cite_ret < 0.85
        or (len(orig_inv["quotations"]) >= 3 and quote_ret < 0.80)
        or (len(orig_inv["h3_headings"]) >= 4 and h3_ret < 0.75)
        or (len(orig_inv["h2_headings"]) >= 3 and h2_ret < 0.75)
    )

    loss_summary: list[str] = []
    if missing_dates:
        loss_summary.append(f"Dropped {len(missing_dates)} historical date(s): {missing_dates[:6]}")
    if missing_metrics:
        loss_summary.append(f"Dropped {len(missing_metrics)} empirical metric(s)/count(s): {missing_metrics[:8]}")
    if missing_identifiers:
        loss_summary.append(f"Dropped {len(missing_identifiers)} technical/symbolic identifier(s): {missing_identifiers[:8]}")
    if missing_h2 or missing_h3:
        loss_summary.append(
            f"Collapsed narrative structure: dropped {len(missing_h2)} major section(s) and {len(missing_h3)} sub-act(s) "
            f"(e.g. {(missing_h2 + missing_h3)[:5]})."
        )
    if missing_citations:
        loss_summary.append(f"Dropped {len(missing_citations)} source citation(s)/locator(s).")
    if missing_quotes:
        loss_summary.append(f"Dropped {len(missing_quotes)} direct quotation(s) from the record.")

    return {
        "passed": not substantive_loss,
        "substantive_loss_detected": substantive_loss,
        "retention_rates": {
            "dates": date_ret,
            "metrics": metric_ret,
            "identifiers": ident_ret,
            "citations": cite_ret,
            "major_sections": h2_ret,
            "sub_acts": h3_ret,
        },
        "missing_dates": missing_dates,
        "missing_metrics": missing_metrics,
        "missing_identifiers": missing_identifiers,
        "missing_citations": missing_citations,
        "missing_h2_headings": missing_h2,
        "missing_h3_headings": missing_h3,
        "missing_quotations": missing_quotes,
        "loss_summary": loss_summary,
    }


# ---------------------------------------------------------------------------
# Layer 2: Qualitative Literary Assessment (Non-Formulaic)
# ---------------------------------------------------------------------------

SYMBOLIC_ARCHETYPE_PATTERNS: dict[str, str] = {
    "mask_and_costume": r"\b(mask|costume|mummer|farce|disguise)\b",
    "river_and_water": r"\b(river|mill|stream|current|water|fish|tide|harbor|vessel|sea|aquifer|well|cistern)\b",
    "gate_and_road": r"\b(gate|road|traveler|signpost|ledger|threshold|lock|arch|pass)\b",
    "desert_and_sand": r"\b(desert|sand|footstep|tracks)\b",
    "metamorphosis_and_animal": r"\b(larval|animal|creature|organism|species|sniper|organ)\b",
    "school_and_dream": r"\b(school|graduate|teacher|student|dream|memory|shadow)\b",
    "tree_and_seed": r"\b(tree|branch|branches|root|roots|seed|forest|furrow|soil)\b",
    "loom_and_fabric": r"\b(loom|fabric|weave|tapestry|thread|shuttle|warp)\b",
    "star_and_enclosure": r"\b(sun|star|dyson|sphere|bubble|shield|lantern)\b",
    "acre_and_kingdom": r"\b(acre|kingdom|city|mountain|grave|wall|fortress)\b",
    "bell_and_flash": r"\b(bell|flash|lightning|spark|quarry|mason)\b",
}


def assess_literary_qualities(
    text: str,
    inv: dict[str, Any],
    revision_retention: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Qualitative literary assessment of narrative development, causal continuity,
    symbolic coherence, and stylistic individuality.
    Never reduces literary judgment to a 0-100 formatting/paragraph-length score.
    Explicitly distinguishes genuine literary works from mechanically valid but
    artistically weak reports/outlines.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("<!--")]
    bullet_lines = [l for l in lines if re.match(r"^([-*]|\d+\.)\s+", l)]
    table_lines = [l for l in lines if l.startswith("|")]
    non_code_lines = max(1, len(lines))
    list_or_table_ratio = (len(bullet_lines) + len(table_lines)) / non_code_lines

    # Detect recurring symbolic motifs across sections (## headings)
    raw_sections = re.split(r"^##\s+", text, flags=re.MULTILINE)
    recurring_motifs: list[str] = []
    for motif_name, pat in SYMBOLIC_ARCHETYPE_PATTERNS.items():
        sections_with_motif = sum(1 for sec in raw_sections if re.search(pat, sec, re.IGNORECASE))
        if sections_with_motif >= 2 or len(re.findall(pat, text, re.IGNORECASE)) >= 4:
            recurring_motifs.append(motif_name)

    # Characterize stylistic profile neutrally (never penalizing any style)
    you_refs = len(re.findall(r"\b(you|your)\b", text, re.IGNORECASE))
    has_diagrams = inv["fence_block_count"] > 0

    style_traits: list[str] = []
    if you_refs >= 5:
        style_traits.append("direct chronicler address")
    else:
        style_traits.append("third-person literary chronicle / book narration")

    if has_diagrams:
        style_traits.append("integrates structural/conceptual diagrams alongside narrative prose")
    else:
        style_traits.append("pure continuous narrative prose")

    # Check narrative progression & causal storytelling vs. mechanical report/changelog
    # Notice: we check prose sentence progression and causal transitions, NEVER enforcing
    # a minimum or maximum paragraph count, line count, or word count.
    has_causal_arc = inv["causal_marker_count"] >= 3 and inv["prose_sentence_count"] >= 5
    has_symbolic_life = len(recurring_motifs) >= 1
    is_list_heavy_report = list_or_table_ratio > 0.35 or inv["prose_sentence_count"] < 4

    if revision_retention and revision_retention.get("substantive_loss_detected"):
        classification = "DEGRADED_REVISION_WITH_HISTORICAL_LOSS"
        artistic_judgment = (
            "Revision eliminated substantive historical scenes, dates, empirical details, or "
            "chronological movements from the original work through summary compression."
        )
    elif is_list_heavy_report or not has_causal_arc or not has_symbolic_life:
        classification = "MECHANICALLY_VALID_BUT_ARTISTICALLY_WEAK"
        reasons: list[str] = []
        if is_list_heavy_report:
            reasons.append("dominated by bullet lists, tables, or compressed outline entries rather than narrative scenes")
        if not has_causal_arc:
            reasons.append("lacks sustained causal progression (expectation -> pressure -> choice -> consequence)")
        if not has_symbolic_life:
            reasons.append("lacks recurring, load-bearing symbolic motifs that evolve across sections")
        artistic_judgment = (
            "Manuscript may satisfy mechanical keyword or formatting checks, but reads as a "
            "technical report, release log, or outline: " + "; ".join(reasons) + "."
        )
    else:
        classification = "SUBSTANTIAL_LITERARY_FABLE"
        artistic_judgment = (
            "Exhibits genuine narrative progression, causal pressure across historical turns, "
            "and recurring symbolic motifs grounded in the creation's actual history."
        )

    return {
        "classification": classification,
        "is_literary_fable": classification == "SUBSTANTIAL_LITERARY_FABLE",
        "artistic_judgment": artistic_judgment,
        "dimensions": {
            "narrative_development": (
                f"Unfolds across {len(inv['h2_headings'])} major movement(s) and "
                f"{len(inv['h3_headings'])} sub-act(s) with {inv['paragraph_count']} prose passages."
            ),
            "causal_continuity": (
                f"Contains {inv['causal_marker_count']} explicit causal transitions linking historical "
                "decisions, failures, and architectural transformations."
            ),
            "symbolic_coherence": {
                "recurring_motif_families": recurring_motifs,
                "has_sustained_symbolism": has_symbolic_life,
            },
            "stylistic_individuality": {
                "traits": style_traits,
                "formatting_freedom_respected": True,
                "note": (
                    "Paragraph lengths, standalone rhythmic lines, rhetorical repetition, "
                    "narrative person, and structural diagrams are treated as legitimate "
                    "literary instruments rather than scored against a formatting template."
                ),
            },
        },
    }


def evaluate_manuscript(
    path: Path,
    baseline_path: Path | None = None,
    canon_path: Path | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    inv = extract_manuscript_inventory(text)
    proj_key = infer_project_key(path, text, project)

    # 1. Protected integrity check (if evaluating one of the reference manuscripts)
    protected_check: dict[str, Any] = {"is_protected_reference": False, "intact": True}
    if is_protected_manuscript(path):
        meta = PROTECTED_REFERENCE_MANUSCRIPTS[path.name]
        actual_hash = compute_sha256(path)
        protected_check = {
            "is_protected_reference": True,
            "intact": actual_hash == meta["sha256"],
            "expected_sha256": meta["sha256"],
            "actual_sha256": actual_hash,
        }

    # 2. Structural consistency
    structural = check_structural_consistency(text, inv)

    # 3. Historical distinction coverage
    distinctions = verify_historical_distinctions(text, proj_key)

    # 4. Source & epistemic discipline
    canon_data = load_canon_ledger(canon_path) if canon_path else None
    source_disc = verify_source_discipline(text, inv, canon=canon_data, project_key=proj_key)

    # 5. Revision retention (if baseline provided)
    rev_retention: dict[str, Any] | None = None
    if baseline_path is not None:
        orig_text = baseline_path.read_text(encoding="utf-8")
        rev_retention = verify_revision_retention(orig_text, text)

    obj_passed = (
        protected_check["intact"]
        and structural["passed"]
        and distinctions["passed"]
        and source_disc["passed"]
        and (rev_retention["passed"] if rev_retention is not None else True)
    )

    if not obj_passed:
        if source_disc["verification_state"] == "REQUIRES_SOURCE_VERIFICATION" and (
            protected_check["intact"]
            and structural["passed"]
            and distinctions["passed"]
            and len(source_disc["status_violations"]) == 0
            and len(source_disc["role_violations"]) == 0
            and (rev_retention["passed"] if rev_retention is not None else True)
        ):
            obj_state = "REQUIRES_SOURCE_VERIFICATION"
        else:
            obj_state = "FAILED"
    else:
        obj_state = "VERIFIED"

    literary = assess_literary_qualities(text, inv, revision_retention=rev_retention)

    return {
        "file": path.name,
        "path": str(path),
        "project": proj_key,
        "objective_verification": {
            "passed": obj_passed,
            "verification_state": obj_state,
            "protected_integrity": protected_check,
            "structural_consistency": structural,
            "distinction_coverage": distinctions,
            "source_discipline": source_disc,
            "revision_retention": rev_retention,
        },
        "literary_assessment": literary,
        "inventory_summary": {
            "title": inv["title"],
            "lines": inv["line_count"],
            "words": inv["word_count"],
            "major_sections": len(inv["h2_headings"]),
            "sub_acts": len(inv["h3_headings"]),
            "dates_count": len(inv["dates"]),
            "metrics_count": len(inv["metrics"]),
            "citations_count": len(inv["citations"]),
        },
    }


# ---------------------------------------------------------------------------
# Workflow Operations: research, create, continue, revise
# ---------------------------------------------------------------------------

def classify_line_epistemic_status(line: str) -> str:
    lower = line.lower()
    if any(w in lower for w in ("unknown", "not recover", "no canonical source", "evidentiary gap", "could not recover", "conflicting")):
        return "unknown"
    if any(w in lower for w in ("propose", "future", "should eventually", "v0.7", "vnext", "ambition", "horizon", "unverified", "intended to")):
        return "proposed"
    if any(w in lower for w in ("telemetry", "measured", "p95", "audit", "observed", "recall", "passing", "checks")):
        return "observed"
    if any(w in lower for w in ("stated", "said", "correction", "doctrine", "wanted it for", "goal")):
        return "stated_intent"
    if any(w in lower for w in ("inferred", "synthesis", "implies")):
        return "inferred"
    return "implemented"


def research_sources(project: str, source_paths: list[Path]) -> dict[str, Any]:
    """
    Operation 1: Researching.
    Recovers and organizes historical evidence from supplied artifacts into a
    source-linked ledger without prematurely converting research into a Fable manuscript.
    """
    claims: list[dict[str, Any]] = []
    for spath in source_paths:
        if not spath.exists():
            continue
        lines = spath.read_text(encoding="utf-8").splitlines()
        for idx, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("```") or line.startswith("|"):
                continue
            has_date = any(re.search(pat, line) for pat in DATE_PATTERNS)
            has_metric = any(re.search(pat, line) for pat in METRIC_PATTERNS)
            has_quote = bool(re.search(r"[“\"][^”\"\n]{10,}[”\"]", line))
            has_epistemic_marker = any(
                k in line.lower()
                for k in ("implemented", "proposed", "unverified", "unknown", "correction", "because", "telemetry", "never")
            )
            if has_date or has_metric or has_quote or has_epistemic_marker:
                date_hit = ""
                for pat in DATE_PATTERNS:
                    m = re.search(pat, line)
                    if m:
                        date_hit = m.group(0)
                        break
                status = classify_line_epistemic_status(line)
                claims.append({
                    "claim": line[:220],
                    "evidence": f"{spath.name}:L{idx}",
                    "date_or_version": date_hit or "undated",
                    "status": status,
                    "narrative_use": "historical_evidence",
                })

    return {
        "project": project,
        "operation": "research",
        "source_files": [str(p) for p in source_paths],
        "claims": claims,
    }


def render_fable_canon_markdown(ledger: dict[str, Any]) -> str:
    project = ledger.get("project", "Project")
    lines = [
        f"# FABLE_CANON: {project}",
        "",
        "> Working source-linked evidence index (subordinate to primary artifacts; do not paste raw ledger tables into Fable prose).",
        "",
        "| Claim or event | Best evidence | Date or version | Status | Narrative use |",
        "|---|---|---|---|---|",
    ]
    for c in ledger.get("claims", []):
        claim_clean = c["claim"].replace("|", "\\|")
        ev_clean = c["evidence"].replace("|", "\\|")
        dt_clean = c.get("date_or_version", "undated").replace("|", "\\|")
        st_clean = c.get("status", "unknown")
        nu_clean = c.get("narrative_use", "historical_evidence").replace("|", "\\|")
        lines.append(f"| {claim_clean} | `{ev_clean}` | {dt_clean} | **{st_clean}** | {nu_clean} |")
    lines.append("")
    return "\n".join(lines)


def build_create_blueprint(project: str, canon: dict[str, Any]) -> str:
    """
    Operation 2: Creating.
    Constructs an 8-stage authoring brief grounded in the researched canon for a new Fable.
    Does not impose the structure, pronouns, or formatting of an unrelated Fable.
    """
    claims = canon.get("claims", [])
    by_status: dict[str, list[dict[str, Any]]] = {s: [] for s in VALID_CLAIM_STATUSES}
    for c in claims:
        st = c.get("status", "unknown").lower()
        by_status.setdefault(st, []).append(c)

    lines = [
        f"# Somnus Code Fable Authoring Blueprint: {project}",
        "",
        "## Purpose & Literary Identity",
        f"Write the Fable of **{project}** as a substantial work of literature—a book for readers that reveals why the creation came into existence, what its creator saw in it, how it evolved, what failed, what changed, and what it means.",
        "- Do **not** write a README, release log, executive summary, or conversation addressing the user or coding agents.",
        "- Choose a narrative structure, cadence, and symbolic family native to this creation rather than imitating the template of an unrelated Fable.",
        "",
        "## Eight-Stage Authoring Plan",
        "1. **Enter the actual record:** Ground every historical turn in the primary artifacts indexed below.",
        "2. **Quiet evidence map:** Respect the epistemic boundaries between `implemented`, `observed`, `stated_intent`, `proposed`, `inferred`, and `unknown` claims.",
        "3. **Story pressure:** Identify the birth, desire, central contradiction, trials, transformation, threshold, and single governing question of this work.",
        "4. **Load-bearing symbolism:** Derive causal symbols from the project's actual architecture, names, and history.",
        "5. **Turn chronology into plot:** Stage each historical turn through expectation, pressure, choice, and consequence.",
        "6. **Living prose center:** Let technical mechanisms be experienced through narrative movement without artificial word-count, line-count, or paragraph-length rules.",
        "7. **Provenance without breaking the spell:** Attach compact source locators near factual claims.",
        "8. **Four-pass revision:** Verify across Record, Story, Symbol, and Sound.",
        "",
        "## Epistemic Coverage Summary from Research Canon",
    ]
    for st in VALID_CLAIM_STATUSES:
        items = by_status.get(st, [])
        if not items:
            continue
        lines.append(f"### Status: `{st}` ({len(items)} item(s))")
        for item in items[:15]:
            lines.append(f"- [{item.get('date_or_version', 'undated')}] {item['claim']} (`{item['evidence']}`)")
        lines.append("")

    return "\n".join(lines)


def build_continuation_plan(
    manuscript_path: Path,
    new_source_paths: list[Path],
    candidate_path: Path | None = None,
) -> dict[str, Any]:
    """
    Operation 3: Continuing.
    Locks prior epoch history from an existing manuscript, extracts new epoch evidence,
    and optionally verifies that a continued manuscript preserves the prior epoch without
    retroactive rewriting while integrating the new epoch.
    """
    base_text = manuscript_path.read_text(encoding="utf-8")
    base_inv = extract_manuscript_inventory(base_text)
    new_research = research_sources(manuscript_path.stem, new_source_paths)

    result: dict[str, Any] = {
        "operation": "continue",
        "baseline_manuscript": str(manuscript_path),
        "locked_prior_epoch": {
            "title": base_inv["title"],
            "major_sections": base_inv["h2_headings"],
            "sub_acts": base_inv["h3_headings"],
            "established_dates": base_inv["dates"],
            "established_metrics": base_inv["metrics"],
            "established_identifiers": base_inv["identifiers"],
        },
        "new_epoch_claims": new_research["claims"],
        "continuation_Verification": None,
    }

    if candidate_path is not None:
        cand_text = candidate_path.read_text(encoding="utf-8")
        retention = verify_revision_retention(base_text, cand_text)
        # Check that new epoch claims are also represented and not projected backward
        new_dates = [
            c["date_or_version"] for c in new_research["claims"]
            if c["date_or_version"] != "undated"
        ]
        new_dates_present = [d for d in new_dates if d.lower() in cand_text.lower()]
        result["continuation_verification"] = {
            "prior_epoch_preserved": retention["passed"],
            "retention_details": retention,
            "new_epoch_dates_integrated": new_dates_present,
            "passed": retention["passed"] and (len(new_dates) == 0 or len(new_dates_present) > 0),
        }

    return result


# ---------------------------------------------------------------------------
# CLI Command Handlers
# ---------------------------------------------------------------------------

def cmd_verify_originals(_args: argparse.Namespace) -> int:
    res = verify_protected_manuscripts()
    print("=== Protected Reference Manuscript Integrity ===")
    for name, info in res["manuscripts"].items():
        status = "INTACT" if info["intact"] else "CORRUPTED / MODIFIED"
        print(
            f"• {name:<20} [{status}] | Lines: {info.get('lines')} | "
            f"Words: {info.get('words')} | Bytes: {info.get('bytes')} | SHA-256: {info.get('actual_sha256')}"
        )
    return 0 if res["all_intact"] else 1


def cmd_status(_args: argparse.Namespace) -> int:
    integrity = verify_protected_manuscripts()
    print("=== Somnus Code Fable System — Reference Archive Status ===")
    print(f"Protected Reference Manuscripts Intact: {integrity['all_intact']}\n")
    for p in sorted(FABLES_DIR.glob("*.md")):
        ev = evaluate_manuscript(p)
        obj = ev["objective_verification"]
        lit = ev["literary_assessment"]
        inv = ev["inventory_summary"]
        print(f"• {p.name}")
        print(f"  Title:                  {inv['title']}")
        print(f"  Forensic Profile:       {inv['lines']} lines | {inv['words']} words | {inv['major_sections']} sections ({inv['sub_acts']} sub-acts)")
        print(f"  Objective Verification: {obj['verification_state']} (passed={obj['passed']})")
        print(f"  Literary Assessment:    {lit['classification']}")
        print(f"  Stylistic Profile:      {', '.join(lit['dimensions']['stylistic_individuality']['traits'])}")
        print()
    return 0 if integrity["all_intact"] else 1


def cmd_evaluate(args: argparse.Namespace) -> int:
    if getattr(args, "all", False) or not getattr(args, "paths", None):
        targets = sorted(FABLES_DIR.glob("*.md"))
    else:
        targets = [Path(p) for p in args.paths]

    baseline = Path(args.baseline) if getattr(args, "baseline", None) else None
    canon = Path(args.canon) if getattr(args, "canon", None) else None
    project = getattr(args, "project", None)

    results = [
        evaluate_manuscript(p, baseline_path=baseline, canon_path=canon, project=project)
        for p in targets
    ]

    if getattr(args, "json", False):
        print(json.dumps(results if len(results) > 1 else results[0], indent=2, ensure_ascii=False))
    else:
        for r in results:
            obj = r["objective_verification"]
            lit = r["literary_assessment"]
            inv = r["inventory_summary"]
            print(f"=== {r['file']} ===")
            print(f"  Title:                  {inv['title']}")
            print(f"  Objective Verification: {obj['verification_state']} (passed={obj['passed']})")
            print(f"  Literary Assessment:    {lit['classification']}")
            print(f"  Artistic Judgment:      {lit['artistic_judgment']}")
            if not obj["structural_consistency"]["passed"]:
                for iss in obj["structural_consistency"]["issues"]:
                    print(f"  [Structural Issue] {iss}")
            if obj["distinction_coverage"]["applicable"] and not obj["distinction_coverage"]["passed"]:
                for md in obj["distinction_coverage"]["missing_distinctions"]:
                    print(f"  [Missing Distinction] {md['id']}: {md['description']}")
                for ri in obj["distinction_coverage"]["role_inversions"]:
                    print(f"  [Role Inversion] {ri['id']}: {ri['reason']}")
            for sv in obj["source_discipline"]["status_violations"]:
                print(f"  [Status Violation] {sv}")
            for rv in obj["source_discipline"]["role_violations"]:
                print(f"  [Role Violation] {rv}")
            for uc in obj["source_discipline"]["unverified_claims"]:
                print(f"  [Unverified Claim] {uc}")
            if obj["revision_retention"] and not obj["revision_retention"]["passed"]:
                for ls in obj["revision_retention"]["loss_summary"]:
                    print(f"  [Substantive Revision Loss] {ls}")
            print()

    all_passed = all(
        r["objective_verification"]["passed"] and r["literary_assessment"]["is_literary_fable"]
        for r in results
    )
    return 0 if all_passed else 1


def cmd_research(args: argparse.Namespace) -> int:
    source_paths = [Path(p) for p in args.sources]
    ledger = research_sources(args.project, source_paths)
    if args.json_out:
        jpath = Path(args.json_out)
        assert_not_protected_manuscript(jpath)
        jpath.write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")
    md_text = render_fable_canon_markdown(ledger)
    if args.output:
        opath = Path(args.output)
        assert_not_protected_manuscript(opath)
        opath.write_text(md_text, encoding="utf-8")
        print(f"Wrote research canon ({len(ledger['claims'])} claim(s)) to {opath}")
    else:
        print(md_text)
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    canon = load_canon_ledger(Path(args.canon)) if args.canon else {"claims": []}
    blueprint = build_create_blueprint(args.project, canon)
    if args.output:
        opath = Path(args.output)
        assert_not_protected_manuscript(opath)
        opath.write_text(blueprint, encoding="utf-8")
        print(f"Wrote authoring blueprint to {opath}")
    else:
        print(blueprint)
    return 0


def cmd_continue(args: argparse.Namespace) -> int:
    mpath = Path(args.manuscript)
    new_sources = [Path(p) for p in (args.new_sources or [])]
    cand = Path(args.candidate) if args.candidate else None
    plan = build_continuation_plan(mpath, new_sources, candidate_path=cand)
    out_json = json.dumps(plan, indent=2, ensure_ascii=False)
    if args.output:
        opath = Path(args.output)
        assert_not_protected_manuscript(opath)
        opath.write_text(out_json, encoding="utf-8")
        print(f"Wrote continuation plan to {opath}")
    else:
        print(out_json)
    if cand is not None:
        return 0 if plan["continuation_verification"]["passed"] else 1
    return 0


def cmd_revise(args: argparse.Namespace) -> int:
    orig_path = Path(args.original)
    cand_path = Path(args.candidate)
    ev = evaluate_manuscript(cand_path, baseline_path=orig_path, project=args.project)
    ret = ev["objective_verification"]["revision_retention"]
    if args.json:
        print(json.dumps(ev, indent=2, ensure_ascii=False))
    else:
        print(f"=== Revision Retention Audit: {orig_path.name} -> {cand_path.name} ===")
        print(f"  Retention Passed:          {ret['passed']}")
        print(f"  Substantive Loss Detected: {ret['substantive_loss_detected']}")
        print(f"  Retention Rates:           {ret['retention_rates']}")
        print(f"  Literary Assessment:       {ev['literary_assessment']['classification']}")
        for item in ret["loss_summary"]:
            print(f"  [!] {item}")
    return 0 if (ret["passed"] and ev["literary_assessment"]["is_literary_fable"]) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Somnus Code Fable Authoring, Research, and Evaluation Harness")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("verify-originals", help="Verify SHA-256 hashes of protected reference manuscripts")
    sub.add_parser("status", help="Display reference archive status and evaluation summary")

    for eval_cmd in ("evaluate", "lint"):
        p_eval = sub.add_parser(eval_cmd, help="Run Objective Verification and Qualitative Literary Assessment")
        p_eval.add_argument("paths", nargs="*", help="Manuscript file(s) to evaluate")
        p_eval.add_argument("--all", action="store_true", help="Evaluate all reference manuscripts in fables/")
        p_eval.add_argument("--baseline", help="Optional original manuscript path to verify revision retention")
        p_eval.add_argument("--canon", help="Optional FABLE_CANON.md or JSON canon ledger for source verification")
        p_eval.add_argument("--project", help="Optional project key (muadib, continuum, plot)")
        p_eval.add_argument("--json", action="store_true", help="Emit structured JSON output")

    p_res = sub.add_parser("research", help="Extract source-linked evidence ledger (FABLE_CANON.md)")
    p_res.add_argument("--project", required=True, help="Project name")
    p_res.add_argument("--sources", nargs="+", required=True, help="Source artifact paths")
    p_res.add_argument("--output", help="Output FABLE_CANON.md path")
    p_res.add_argument("--json-out", help="Optional output JSON ledger path")

    p_create = sub.add_parser("create", help="Generate an 8-stage authoring blueprint from a research canon")
    p_create.add_argument("--project", required=True, help="Project name")
    p_create.add_argument("--canon", help="Path to FABLE_CANON.md or JSON ledger")
    p_create.add_argument("--output", help="Output blueprint markdown path")

    p_cont = sub.add_parser("continue", help="Lock prior epoch claims and plan/verify a continuation")
    p_cont.add_argument("--manuscript", required=True, help="Existing manuscript path")
    p_cont.add_argument("--new-sources", nargs="*", default=[], help="New epoch source files")
    p_cont.add_argument("--candidate", help="Optional continued manuscript to verify against prior epoch lock")
    p_cont.add_argument("--output", help="Optional output path for continuation plan")

    p_rev = sub.add_parser("revise", help="Audit a candidate revision against an original manuscript")
    p_rev.add_argument("--original", required=True, help="Original manuscript path")
    p_rev.add_argument("--candidate", required=True, help="Candidate revised manuscript path")
    p_rev.add_argument("--project", help="Optional project key")
    p_rev.add_argument("--json", action="store_true", help="Emit structured JSON output")

    args = parser.parse_args()
    if not args.cmd or args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "verify-originals":
        return cmd_verify_originals(args)
    if args.cmd in ("evaluate", "lint"):
        return cmd_evaluate(args)
    if args.cmd == "research":
        return cmd_research(args)
    if args.cmd == "create":
        return cmd_create(args)
    if args.cmd == "continue":
        return cmd_continue(args)
    if args.cmd == "revise":
        return cmd_revise(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
