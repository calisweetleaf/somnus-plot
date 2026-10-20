#!/usr/bin/env python3
"""
MD2TeX v4: Markdown → LuaLaTeX Transcreation Engine

Converts Markdown manuscripts to publication-grade LuaLaTeX source files
using the Somnus academic publication system.

Canonical build chain:
  Markdown → (md2tex.py normalization) → Pandoc → LuaLaTeX .tex
  → biblatex + biber → LuaLaTeX (×2) → validated PDF

v4 changes from audit:
  - Default engine: lualatex (not xelatex)
  - Math fence parser: correctly handles ```math blocks
  - No unsafe math rewriting: never infers display math from punctuation
  - Unicode classification: domain-based (prose/math/semantic/control/disallowed)
  - Deterministic cross-reference labels: document-wide registry with collision handling
  - Bibliography: biblatex + biber integrated into build graph
  - No import-time pip installs
  - Structured error reporting with exit codes

This is a PORTABLE SCRIPT — no sibling imports, no dynamic dependency installs.
Required: Python 3.10+, pandoc on PATH.
Optional: lualatex, biber, latexmk, pdftotext (poppler-utils) on PATH.
"""

import re
import json
import sys
import subprocess
import argparse
import hashlib
import time
import shutil
import unicodedata
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional


# ═══════════════════════════════════════════════════════════════════════════
# UNICODE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════

class UnicodeClassifier:
    """
    Classifies Unicode characters into semantic domains instead of
    blanket-rejecting all non-ASCII.

    Domains:
      - prose_typography: smart quotes, dashes, ellipsis, accented chars
      - mathematical_symbol: Greek, operators, arrows, set notation
      - control_invisible: zero-width chars, BOM, directional marks
      - disallowed: homoglyphs, confusables
    """

    # Prose typography: characters that are normal in UTF-8 text
    PROSE_CATEGORIES = {"Pd", "Pi", "Pf", "Po", "Ps", "Pe", "Zs"}
    PROSE_RANGES = set(range(0x00C0, 0x0250))  # Latin Extended (accented chars)
    PROSE_CODEPOINTS = {
        0x2013, 0x2014,  # en-dash, em-dash
        0x2018, 0x2019,  # single quotes
        0x201C, 0x201D,  # double quotes
        0x2026,          # ellipsis
        0x00A0,          # non-breaking space
        0x00AB, 0x00BB,  # guillemets
        0x2010, 0x2011,  # hyphens
        0x2012,          # figure dash
    }

    # Mathematical symbols
    MATH_BLOCKS = [
        (0x0370, 0x03FF),  # Greek and Coptic
        (0x1D400, 0x1D7FF),  # Mathematical Alphanumeric Symbols
        (0x2200, 0x22FF),  # Mathematical Operators
        (0x2190, 0x21FF),  # Arrows
        (0x27C0, 0x27EF),  # Miscellaneous Mathematical Symbols-A
        (0x2980, 0x29FF),  # Miscellaneous Mathematical Symbols-B
        (0x2A00, 0x2AFF),  # Supplemental Mathematical Operators
    ]
    MATH_CODEPOINTS = {
        0x00B1,  # ±
        0x00D7,  # ×
        0x00F7,  # ÷
        0x2202,  # ∂
        0x2207,  # ∇
        0x221A,  # √
        0x221E,  # ∞
        0x2260,  # ≠
        0x2264,  # ≤
        0x2265,  # ≥
        0x2248,  # ≈
    }

    # Control / invisible characters
    CONTROL_CATEGORIES = {"Cc", "Cf"}
    ALLOWED_CONTROL = {0x0A, 0x0D, 0x09}  # LF, CR, TAB

    @classmethod
    def classify(cls, char: str) -> str:
        """Classify a single character into a domain."""
        cp = ord(char)

        # ASCII is always fine
        if cp < 128:
            return "ascii"

        # Control / invisible
        cat = unicodedata.category(char)
        if cat in cls.CONTROL_CATEGORIES and cp not in cls.ALLOWED_CONTROL:
            return "control_invisible"

        # Prose typography
        if cp in cls.PROSE_CODEPOINTS or cp in cls.PROSE_RANGES:
            return "prose_typography"
        if cat in cls.PROSE_CATEGORIES:
            return "prose_typography"
        # Accented letters
        if cat.startswith("L") and cp > 127:
            name = unicodedata.name(char, "")
            if "LATIN" in name or "WITH" in name:
                return "prose_typography"

        # Mathematical symbols
        if cp in cls.MATH_CODEPOINTS:
            return "mathematical_symbol"
        for start, end in cls.MATH_BLOCKS:
            if start <= cp <= end:
                return "mathematical_symbol"
        if cat == "Sm":  # Symbol, math
            return "mathematical_symbol"

        # Currency, modifier symbols, etc. — generally safe
        if cat in {"Sc", "Sk", "So"}:
            return "prose_typography"

        # Everything else: flag for review but don't reject
        return "unclassified"

    @classmethod
    def validate_text(cls, text: str) -> List[dict]:
        """Validate text and return issues for problematic characters."""
        issues = []
        for line_num, line in enumerate(text.split("\n"), 1):
            for col, char in enumerate(line, 1):
                domain = cls.classify(char)
                if domain == "control_invisible":
                    issues.append({
                        "line": line_num,
                        "col": col,
                        "char": repr(char),
                        "codepoint": f"U+{ord(char):04X}",
                        "domain": domain,
                        "severity": "error",
                        "message": f"Invisible/control character {repr(char)} at line {line_num}",
                    })
        return issues


# ═══════════════════════════════════════════════════════════════════════════
# SYMBOL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

class SymbolRegistry:
    """Manages project-specific symbolic operators and their semantics."""

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path
        self.symbols: Dict = {}
        if registry_path and registry_path.exists():
            self._load_registry()

    def _load_registry(self) -> None:
        """Load symbol registry from JSON."""
        with open(self.registry_path, "r", encoding="utf-8") as f:
            self.symbols = json.load(f)

    def save_registry(self) -> None:
        """Save registry to JSON."""
        if self.registry_path:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.symbols, f, indent=2, ensure_ascii=False)

    def is_registered(self, symbol: str) -> bool:
        return symbol in self.symbols

    def get_semantic(self, symbol: str) -> str:
        return self.symbols.get(symbol, {}).get("semantic", "unknown")

    def get_contexts(self, symbol: str) -> List[str]:
        return self.symbols.get(symbol, {}).get("context", [])


# ═══════════════════════════════════════════════════════════════════════════
# SYMBOL LINTER
# ═══════════════════════════════════════════════════════════════════════════

class SymbolLinter:
    """Lints documents for Unicode symbol usage with domain-aware classification."""

    def __init__(self, registry: SymbolRegistry):
        self.registry = registry
        self.issues: List[str] = []
        self.usage_stats: Dict = {}

    def lint_file(self, filepath: Path) -> Tuple[List[str], Dict]:
        """Lint a markdown or tex file using domain classification."""
        self.issues = []
        self.usage_stats = defaultdict(lambda: {"count": 0, "contexts": [], "lines": []})

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_code_block = False
        in_math_block = False

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track code block state
            if stripped.startswith("```") and not stripped.startswith("```math"):
                in_code_block = not in_code_block
                continue
            if stripped.startswith("```math"):
                in_math_block = True
                continue
            if in_math_block and stripped == "```":
                in_math_block = False
                continue

            if "$$" in line:
                in_math_block = not in_math_block

            context = "code" if in_code_block else ("math" if in_math_block or "$" in line else "prose")

            for char in line:
                if ord(char) <= 127:
                    continue

                domain = UnicodeClassifier.classify(char)

                if domain == "control_invisible":
                    self.issues.append(
                        f"Line {line_num}: Invisible control character "
                        f"U+{ord(char):04X} — should be removed"
                    )
                elif domain == "unclassified" and not self.registry.is_registered(char):
                    self.issues.append(
                        f"Line {line_num}: Unclassified character '{char}' "
                        f"(U+{ord(char):04X}) — consider adding to registry"
                    )

                if domain in ("mathematical_symbol", "prose_typography") or self.registry.is_registered(char):
                    self.usage_stats[char]["count"] += 1
                    self.usage_stats[char]["contexts"].append(context)
                    self.usage_stats[char]["lines"].append(line_num)

        return self.issues, dict(self.usage_stats)

    def generate_report(self, issues: List[str], stats: Dict) -> str:
        """Generate lint report."""
        report = ["=" * 60, "SYMBOL LINT REPORT (v4 — Domain-Classified)", "=" * 60]

        if issues:
            report.append("\n⚠ ISSUES FOUND:")
            for issue in issues:
                report.append(f"  • {issue}")
        else:
            report.append("\n✓ No issues found")

        report.append("\n" + "=" * 60)
        report.append("SYMBOL USAGE STATISTICS")
        report.append("=" * 60)

        for symbol, data in sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True):
            domain = UnicodeClassifier.classify(symbol)
            semantic = self.registry.get_semantic(symbol) if self.registry.is_registered(symbol) else domain
            context_counts = Counter(data["contexts"])
            report.append(f"\n{symbol} (U+{ord(symbol):04X}) — {semantic}")
            report.append(f"  Domain: {domain}")
            report.append(f"  Total: {data['count']} occurrences")
            report.append(f"  Contexts: {dict(context_counts)}")
            lines_preview = ", ".join(map(str, data["lines"][:10]))
            if len(data["lines"]) > 10:
                lines_preview += "..."
            report.append(f"  Lines: {lines_preview}")

        return "\n".join(report)


# ═══════════════════════════════════════════════════════════════════════════
# MATH NORMALIZER (SAFE — NO INFERENCE)
# ═══════════════════════════════════════════════════════════════════════════

class MathNormalizer:
    """
    Normalizes math blocks in Markdown without unsafe inference.

    v4 rules:
      - Convert ```math ... ``` fenced blocks to $$ ... $$
      - NEVER infer display math from punctuation (=, +, ∈, etc.)
      - Require explicit delimiters: $...$, $$...$$, \\(...\\), \\[...\\]
      - May WARN about likely bare equations but must NOT rewrite them
    """

    def normalize(self, content: str) -> str:
        """Normalize math fencing in markdown."""
        lines = content.split("\n")
        normalized = []
        in_code_block = False
        in_math_fence = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Handle ```math opening
            if not in_code_block and stripped.startswith("```math"):
                in_math_fence = True
                normalized.append("$$")
                i += 1
                continue

            # Handle ``` closing for math fence
            if in_math_fence and stripped == "```":
                in_math_fence = False
                normalized.append("$$")
                i += 1
                continue

            # Track non-math code blocks
            if not in_math_fence and stripped.startswith("```"):
                in_code_block = not in_code_block

            # Pass through everything else unchanged
            normalized.append(line)
            i += 1

        return "\n".join(normalized)

    def warn_bare_equations(self, content: str) -> List[str]:
        """
        Warn about lines that look like bare equations without delimiters.
        Does NOT modify the content — advisory only.
        """
        warnings = []
        lines = content.split("\n")
        in_code = False
        in_math = False

        latex_commands = {
            "\\sum", "\\int", "\\frac", "\\partial", "\\mathcal",
            "\\left", "\\right", "\\overbrace", "\\underbrace",
            "\\lim", "\\prod", "\\inf", "\\sup",
        }

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if "$$" in stripped:
                in_math = not in_math
                continue
            if in_code or in_math or not stripped:
                continue
            if "$" in stripped:
                continue  # Already has math delimiters

            # Check for LaTeX commands outside math mode
            if any(cmd in stripped for cmd in latex_commands):
                warnings.append(
                    f"Line {line_num}: Possible bare equation (contains LaTeX commands "
                    f"without math delimiters): {stripped[:80]}..."
                )

        return warnings


# ═══════════════════════════════════════════════════════════════════════════
# ADMONITION PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════

class AdmonitionProcessor:
    """Processes markdown admonitions into LaTeX theorem environments."""

    SUPPORTED_ENVS = {
        "theorem", "definition", "lemma", "proof", "note",
        "proposition", "corollary", "invariant",
    }

    def process(self, content: str) -> str:
        """Transform Markdown blockquotes into LaTeX environments."""
        lines = content.split("\n")
        new_lines = []
        current_env = None
        env_content = []

        for line in lines:
            stripped = line.strip()

            # Detect environment start: > [!THEOREM] Title
            match = re.match(
                r">\s*\[!(" + "|".join(self.SUPPORTED_ENVS) + r")\]\s*(.*)",
                stripped, re.IGNORECASE,
            )
            if match:
                # Close previous environment if open
                if current_env:
                    new_lines.append(f"\\begin{{{current_env['type']}}}{current_env['title']}")
                    new_lines.extend(env_content)
                    new_lines.append(f"\\end{{{current_env['type']}}}")
                    env_content = []

                env_type = match.group(1).lower()
                title = match.group(2).strip()
                title_opt = f"[{title}]" if title else ""
                current_env = {"type": env_type, "title": title_opt}
                continue

            # Continuation of environment body
            if current_env and stripped.startswith(">"):
                content_line = line.replace(">", "", 1).lstrip()
                env_content.append(content_line)
                continue

            # End of environment (non-blockquote line)
            if current_env and not stripped.startswith(">"):
                new_lines.append(f"\\begin{{{current_env['type']}}}{current_env['title']}")
                new_lines.extend(env_content)
                new_lines.append(f"\\end{{{current_env['type']}}}")
                current_env = None
                env_content = []
                new_lines.append(line)
                continue

            new_lines.append(line)

        # Close any remaining environment
        if current_env:
            new_lines.append(f"\\begin{{{current_env['type']}}}{current_env['title']}")
            new_lines.extend(env_content)
            new_lines.append(f"\\end{{{current_env['type']}}}")

        return "\n".join(new_lines)


# ═══════════════════════════════════════════════════════════════════════════
# CITATION PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════

class CitationProcessor:
    """Processes custom citation formats into LaTeX citation commands."""

    def process(self, content: str) -> str:
        """Handle both traditional @cite and custom [[Author YEAR]] refs."""
        # [[Pribram 1991: Holographic Brain Theory]] → \cite[Holographic Brain Theory]{Pribram1991}
        content = re.sub(
            r"\[\[([^\]]+?)\s+(\d{4})[:\s]+([^\]]+)\]\]",
            r"\\cite[\3]{\1\2}",
            content,
        )
        # [[#theorem-name]] → \ref{theorem-name}
        content = re.sub(
            r"\[\[#([^\]]+)\]\]",
            r"\\ref{\1}",
            content,
        )
        return content


# ═══════════════════════════════════════════════════════════════════════════
# CROSS-REFERENCE LINKER (DETERMINISTIC LABELS)
# ═══════════════════════════════════════════════════════════════════════════

class CrossReferenceLinker:
    """
    Manages cross-references with deterministic, collision-free label generation.

    v4 fix: uses a document-wide counter per environment type instead of
    relying on len(self.labels) which was never populated.
    """

    def __init__(self):
        self.labels: Dict[str, str] = {}  # label → source location
        self._counters: Dict[str, int] = defaultdict(int)

    def process(self, content: str) -> str:
        """Add deterministic labels to theorem-like environments."""
        lines = content.split("\n")
        new_lines = []

        env_pattern = re.compile(
            r"\\begin\{(theorem|definition|lemma|proposition|corollary|invariant)\}"
        )

        for line in lines:
            match = env_pattern.search(line)
            if match:
                env_type = match.group(1)
                # Extract optional title
                title_match = re.search(r"\[([^\]]+)\]", line)
                title = title_match.group(1) if title_match else ""
                label = self._create_label(env_type, title)
                new_lines.append(line)
                new_lines.append(f"\\label{{{label}}}")
                continue
            new_lines.append(line)

        return "\n".join(new_lines)

    def _create_label(self, env_type: str, title: str) -> str:
        """Create a deterministic, collision-free label."""
        if title:
            clean_title = re.sub(r"[^\w\s-]", "", title.lower())
            clean_title = re.sub(r"[-\s]+", "-", clean_title).strip("-")
            candidate = f"{env_type}:{clean_title}"
        else:
            self._counters[env_type] += 1
            candidate = f"{env_type}:unnamed-{self._counters[env_type]}"

        # Handle collisions
        if candidate in self.labels:
            suffix = 2
            while f"{candidate}-{suffix}" in self.labels:
                suffix += 1
            candidate = f"{candidate}-{suffix}"

        self.labels[candidate] = env_type
        return candidate


# ═══════════════════════════════════════════════════════════════════════════
# TENSOR NOTATION VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

class TensorNotationValidator:
    """Validates tensor notation consistency."""

    def validate(self, content: str) -> List[str]:
        issues = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            if "_" not in line and "^" not in line:
                continue
            if "$" in line:
                math_parts = re.findall(r"\$([^\$]+)\$", line)
                for math in math_parts:
                    open_b = math.count("{")
                    close_b = math.count("}")
                    if open_b != close_b:
                        issues.append(
                            f"Line {line_num}: Unbalanced braces in math expression"
                        )
        return issues


# ═══════════════════════════════════════════════════════════════════════════
# MD2TEX CONVERTER
# ═══════════════════════════════════════════════════════════════════════════

class MD2TeXConverter:
    """
    Core Markdown → LuaLaTeX conversion engine.

    v4 default engine: lualatex
    v4 bibliography: biblatex + biber
    """

    def __init__(
        self,
        registry: SymbolRegistry,
        mode: str = "pub",
        engine: str = "lualatex",
    ):
        self.registry = registry
        self.mode = mode
        self.engine = engine
        self.normalizer = MathNormalizer()
        self.admonition_processor = AdmonitionProcessor()
        self.citation_processor = CitationProcessor()
        self.xref_linker = CrossReferenceLinker()
        self.tensor_validator = TensorNotationValidator()

    def convert(
        self,
        input_path: Path,
        output_path: Path,
        template_path: Optional[Path] = None,
        bib_path: Optional[Path] = None,
        add_version: bool = False,
        keep_normalized: bool = False,
    ):
        """Convert markdown to LaTeX."""
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Unicode validation
        unicode_issues = UnicodeClassifier.validate_text(content)
        if unicode_issues:
            print("\n⚠ Unicode issues found:", file=sys.stderr)
            for issue in unicode_issues:
                print(f"  • {issue['message']}", file=sys.stderr)

        # Tensor notation validation
        tensor_issues = self.tensor_validator.validate(content)
        if tensor_issues:
            print("\n⚠ Tensor notation issues:", file=sys.stderr)
            for issue in tensor_issues:
                print(f"  • {issue}", file=sys.stderr)

        # Math fence warnings (advisory only)
        bare_eq_warnings = self.normalizer.warn_bare_equations(content)
        if bare_eq_warnings:
            print("\n⚠ Possible bare equations (not auto-wrapped):", file=sys.stderr)
            for w in bare_eq_warnings[:5]:
                print(f"  • {w}", file=sys.stderr)

        # 1. Normalize math fences (```math → $$)
        content = self.normalizer.normalize(content)

        # 2. Process admonitions
        content = self.admonition_processor.process(content)

        # 3. Process citations
        content = self.citation_processor.process(content)

        # 4. Add version info if requested
        if add_version:
            content = self._add_version_info(content, input_path)

        # Write intermediate normalized markdown
        temp_md = output_path.with_suffix(".normalized.md")
        with open(temp_md, "w", encoding="utf-8") as f:
            f.write(content)

        # Convert with Pandoc
        self._run_pandoc(temp_md, output_path, template_path, bib_path)

        # Post-process: add cross-reference labels to TeX output
        if output_path.suffix == ".tex" and output_path.exists():
            with open(output_path, "r", encoding="utf-8") as f:
                tex_content = f.read()
            tex_content = self.xref_linker.process(tex_content)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(tex_content)

        # Clean up intermediate file unless requested to keep
        if not keep_normalized and temp_md.exists():
            temp_md.unlink()

    def _add_version_info(self, content: str, input_path: Path) -> str:
        """Add version and hash information as TeX comments."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return (
            f"% === VERSION INFO ===\n"
            f"% Document Hash: {content_hash}\n"
            f"% Source File: {input_path.name}\n"
            f"% Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"% === END VERSION INFO ===\n\n"
            + content
        )

    def _run_pandoc(
        self,
        input_path: Path,
        output_path: Path,
        template_path: Optional[Path] = None,
        bib_path: Optional[Path] = None,
    ):
        """Run Pandoc conversion."""
        if not shutil.which("pandoc"):
            print(
                "✗ pandoc not found on PATH. Install it: https://pandoc.org/installing.html",
                file=sys.stderr,
            )
            sys.exit(2)

        cmd = [
            "pandoc",
            str(input_path),
            "-o", str(output_path),
            f"--pdf-engine={self.engine}",
            "-f", "markdown",
            "-t", "latex",
            "--standalone",
        ]

        if template_path and template_path.exists():
            cmd.extend(["--template", str(template_path)])

        if bib_path and bib_path.exists():
            cmd.extend([
                "--bibliography", str(bib_path),
                "--citeproc",
            ])

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if result.stderr:
                print(f"Pandoc warnings:\n{result.stderr}", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"✗ Pandoc conversion failed:\n{e.stderr}", file=sys.stderr)
            raise


# ═══════════════════════════════════════════════════════════════════════════
# PDF VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

class PDFValidator:
    """Validates PDF output against source for symbol preservation."""

    def validate(
        self,
        source_path: Path,
        pdf_path: Path,
        registry: SymbolRegistry,
    ) -> str:
        if not shutil.which("pdftotext"):
            return "⚠ pdftotext not found. Install poppler-utils for PDF validation."

        try:
            result = subprocess.run(
                ["pdftotext", "-enc", "UTF-8", str(pdf_path), "-"],
                capture_output=True, text=True, check=True,
            )
            pdf_text = result.stdout
        except subprocess.CalledProcessError:
            return "✗ Failed to extract text from PDF"

        with open(source_path, "r", encoding="utf-8") as f:
            source_text = f.read()

        report = ["=" * 60, "PDF RENDER FIDELITY REPORT", "=" * 60, ""]
        missing = []
        preserved = []

        for symbol in registry.symbols:
            src_count = source_text.count(symbol)
            pdf_count = pdf_text.count(symbol)
            if src_count > 0:
                if pdf_count == 0:
                    missing.append(f"✗ {symbol} (U+{ord(symbol):04X}): {src_count} in source, 0 in PDF")
                elif pdf_count < src_count:
                    missing.append(f"⚠ {symbol} (U+{ord(symbol):04X}): {src_count} in source, {pdf_count} in PDF")
                else:
                    preserved.append(f"✓ {symbol} (U+{ord(symbol):04X}): {src_count} preserved")

        if preserved:
            report.append("PRESERVED SYMBOLS:")
            report.extend(f"  {p}" for p in preserved)
            report.append("")
        if missing:
            report.append("MISSING/REDUCED SYMBOLS:")
            report.extend(f"  {m}" for m in missing)
        else:
            report.append("✓ All symbols preserved correctly!")

        return "\n".join(report)


# ═══════════════════════════════════════════════════════════════════════════
# APPENDIX GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class AppendixGenerator:
    """Generates symbolic operator reference appendix for LaTeX."""

    def __init__(self, registry: SymbolRegistry):
        self.registry = registry

    def generate(self, stats: Dict) -> str:
        lines = [
            "\\section*{SYMBOLIC OPERATOR REFERENCE}",
            "\\begin{table}[H]",
            "\\centering",
            "\\begin{tabular}{cllr}",
            "\\toprule",
            "Symbol & Semantic & Type & Usage \\\\",
            "\\midrule",
        ]

        sorted_symbols = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)
        for symbol, data in sorted_symbols:
            info = self.registry.symbols.get(symbol, {})
            semantic = info.get("semantic", "unknown").replace("_", " ").title()
            sym_type = info.get("type", "unknown").replace("_", " ").title()
            count = data["count"]
            lines.append(f"{symbol} & {semantic} & {sym_type} & {count} \\\\")

        lines.extend(["\\bottomrule", "\\end{tabular}",
                      "\\caption{Symbolic operators used in this document}", "\\end{table}"])
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# BUILD DRIVER
# ═══════════════════════════════════════════════════════════════════════════

def compile_pdf(tex_path: Path, engine: str = "lualatex") -> bool:
    """
    Compile TeX to PDF using the canonical build graph:
      latexmk -lualatex  (preferred)
      OR: lualatex → biber → lualatex × 2  (fallback)

    Returns True on success, False on failure.
    """
    output_dir = tex_path.parent

    # Prefer latexmk
    if shutil.which("latexmk"):
        cmd = [
            "latexmk",
            f"-{engine}",
            "-interaction=nonstopmode",
            f"-output-directory={output_dir}",
            str(tex_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=output_dir)
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            print(f"✗ latexmk failed:\n{stderr[:500]}", file=sys.stderr)
            return False

    # Fallback: manual build graph
    if not shutil.which(engine):
        print(f"✗ {engine} not found on PATH", file=sys.stderr)
        return False

    tex_cmds = [
        [engine, "-interaction=nonstopmode", str(tex_path)],
    ]

    # Run biber if biblatex is used
    aux_path = tex_path.with_suffix(".aux")
    if shutil.which("biber"):
        tex_cmds.append(["biber", str(tex_path.stem)])

    # Two more engine passes for references
    tex_cmds.append([engine, "-interaction=nonstopmode", str(tex_path)])
    tex_cmds.append([engine, "-interaction=nonstopmode", str(tex_path)])

    for cmd in tex_cmds:
        try:
            subprocess.run(cmd, check=True, capture_output=True, cwd=output_dir)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            print(f"✗ {cmd[0]} failed:\n{stderr[:500]}", file=sys.stderr)
            # Don't fail on biber if aux doesn't exist yet
            if cmd[0] != "biber":
                return False

    return True


# ═══════════════════════════════════════════════════════════════════════════
# SYMBOL TEST RENDERER
# ═══════════════════════════════════════════════════════════════════════════

class SymbolTestRenderer:
    """Generates test document for symbol rendering validation."""

    def __init__(self, registry: SymbolRegistry):
        self.registry = registry

    def generate_test_doc(self, output_path: Path, engine: str = "lualatex"):
        """Generate a test PDF with all registered symbols."""
        test_symbols = [s for s, d in self.registry.symbols.items()
                       if d.get("test_render", False)]

        latex_content = self._create_test_latex(test_symbols)

        tex_path = output_path.with_suffix(".tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        success = compile_pdf(tex_path, engine)
        if success:
            print(f"✓ Test document generated: {output_path}")
        else:
            print(f"✗ Failed to compile test document", file=sys.stderr)

    def _create_test_latex(self, symbols: List[str]) -> str:
        content = r"""\documentclass{article}
\usepackage{fontspec}
\usepackage{unicode-math}
\setmainfont{Latin Modern Roman}
\setmathfont{Latin Modern Math}
\usepackage{booktabs}
\usepackage{geometry}
\geometry{margin=1in}

\title{Symbol Rendering Test}
\author{MD2TeX v4}
\date{\today}

\begin{document}
\maketitle

\section*{Registered Symbols Test}

This document tests the rendering of all registered symbolic operators.

\begin{table}[h]
\centering
\begin{tabular}{clll}
\toprule
Symbol & Unicode & Inline Math & Display Math \\
\midrule
"""
        for symbol in symbols:
            codepoint = f"U+{ord(symbol):04X}"
            content += f"{symbol} & {codepoint} & ${symbol}$ & $\\displaystyle {symbol}$ \\\\\n"

        content += r"""\bottomrule
\end{tabular}
\caption{Symbol rendering test results}
\end{table}

\section*{Context Tests}

\subsection*{In Equations}
$$
\Psi \otimes \Phi \rightarrow \nabla(\text{frequency space})
$$

\subsection*{In Text}
The operator $\otimes$ represents tensor product in frequency space.

\end{document}
"""
        return content


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION SUITE
# ═══════════════════════════════════════════════════════════════════════════

def run_validation_suite(args, registry: SymbolRegistry) -> bool:
    """Run comprehensive validation checks."""
    print("=" * 60)
    print("VALIDATION SUITE (v4)")
    print("=" * 60)

    issues = []

    # 1. Symbol lint
    print("\n[1/5] Running symbol linter (domain-classified)...")
    linter = SymbolLinter(registry)
    lint_issues, stats = linter.lint_file(args.input)
    if lint_issues:
        issues.extend(lint_issues)
        print(f"  ⚠ Found {len(lint_issues)} symbol issues")
    else:
        print("  ✓ No symbol issues")

    # 2. Unicode validation
    print("\n[2/5] Validating Unicode characters...")
    with open(args.input, "r", encoding="utf-8") as f:
        content = f.read()
    unicode_issues = UnicodeClassifier.validate_text(content)
    if unicode_issues:
        issues.extend([i["message"] for i in unicode_issues])
        print(f"  ⚠ Found {len(unicode_issues)} Unicode issues")
    else:
        print("  ✓ No problematic Unicode characters")

    # 3. Math fence check
    print("\n[3/5] Checking math fences...")
    dollar_count = content.count("$")
    if dollar_count % 2 != 0:
        issues.append("Unbalanced $ delimiters in document")
        print("  ⚠ Unbalanced $ delimiters")
    else:
        print("  ✓ Math delimiters balanced")

    # 3b. Bare equation warnings
    normalizer = MathNormalizer()
    bare_warnings = normalizer.warn_bare_equations(content)
    if bare_warnings:
        print(f"  ⚠ {len(bare_warnings)} possible bare equation(s) — review recommended")

    # 4. Tensor notation check
    print("\n[4/5] Validating tensor notation...")
    validator = TensorNotationValidator()
    tensor_issues = validator.validate(content)
    if tensor_issues:
        issues.extend(tensor_issues)
        print(f"  ⚠ Found {len(tensor_issues)} tensor notation issues")
    else:
        print("  ✓ Tensor notation valid")

    # 5. Figure existence check
    print("\n[5/5] Checking figure references...")
    figures = re.findall(r"!\[.*?\]\((.+?)\)", content)
    missing_figs = [fig for fig in figures if not (args.input.parent / fig).exists()]
    if missing_figs:
        issues.extend([f"Missing figure: {fig}" for fig in missing_figs])
        print(f"  ⚠ Found {len(missing_figs)} missing figures")
    else:
        print("  ✓ All figures exist")

    # Summary
    print("\n" + "=" * 60)
    if issues:
        print("VALIDATION COMPLETED WITH ISSUES")
        print("=" * 60)
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print("✓ ALL CHECKS PASSED")
        print("=" * 60)
        return True


# ═══════════════════════════════════════════════════════════════════════════
# WATCH MODE
# ═══════════════════════════════════════════════════════════════════════════

def watch_mode(args, main_conversion_func):
    """Watch file for changes and auto-convert."""
    print(f"👁 Watching {args.input} for changes... (Ctrl+C to stop)")
    last_mtime = args.input.stat().st_mtime

    try:
        while True:
            time.sleep(1)
            if not args.input.exists():
                print(f"⚠ File {args.input} no longer exists")
                break
            current_mtime = args.input.stat().st_mtime
            if current_mtime > last_mtime:
                print(f"\n[Change detected at {time.strftime('%H:%M:%S')}]")
                last_mtime = current_mtime
                try:
                    main_conversion_func(args)
                    print("✓ Conversion complete")
                except Exception as e:
                    print(f"✗ Conversion failed: {e}")
    except KeyboardInterrupt:
        print("\n\nStopped watching.")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CONVERSION LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def main_conversion_logic(args):
    """Main conversion logic separated for reuse in watch mode."""
    registry = SymbolRegistry(args.registry)

    output = args.output or args.input.with_suffix(".tex")

    # Auto-detect template if not specified
    template = args.template
    if template is None:
        # Look for canonical template relative to script location
        engine_root = Path(__file__).resolve().parent.parent
        default_template = engine_root / "templates" / "somnus-pandoc-template.tex"
        if default_template.exists():
            template = default_template
            print(f"  Using default template: {template}")

    print(f"Converting {args.input} → {output} (engine: {args.engine})")
    converter = MD2TeXConverter(registry, args.mode, args.engine)
    converter.convert(
        args.input, output, template, args.bib,
        args.add_version, args.keep_normalized,
    )
    print(f"✓ Conversion complete: {output}")

    # Generate appendix if requested
    if args.appendix:
        linter = SymbolLinter(registry)
        _, stats = linter.lint_file(args.input)
        gen = AppendixGenerator(registry)
        appendix = gen.generate(stats)
        with open(output, "a", encoding="utf-8") as f:
            f.write("\n\n" + appendix)
        print(f"✓ Appendix added to {output}")

    # Compile PDF if requested
    if args.compile_pdf:
        print(f"Compiling to PDF with {args.engine}...")
        success = compile_pdf(output, args.engine)
        if success:
            pdf_path = output.with_suffix(".pdf")
            print(f"✓ PDF compiled: {pdf_path}")
            if args.validate:
                validator = PDFValidator()
                report = validator.validate(args.input, pdf_path, registry)
                print(f"\n{report}")
        else:
            print("✗ PDF compilation failed", file=sys.stderr)
            sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MD2TeX v4: Markdown → LuaLaTeX Transcreation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Canonical build chain:
  Markdown → md2tex.py → Pandoc → LuaLaTeX .tex → biber → LuaLaTeX ×2 → PDF

Examples:
  # Basic conversion (uses default Somnus template)
  %(prog)s paper.md

  # With explicit template and bibliography
  %(prog)s paper.md --template somnus-pandoc-template.tex --bib refs.bib --compile-pdf

  # Watch mode for live editing
  %(prog)s paper.md --watch --compile-pdf

  # Full validation suite
  %(prog)s paper.md --validate-all

  # Test symbol rendering
  %(prog)s --test-symbols symbol_test.pdf

  # Lint only
  %(prog)s paper.md --lint
        """,
    )

    parser.add_argument("input", type=Path, nargs="?", help="Input markdown file")
    parser.add_argument("-o", "--output", type=Path, help="Output file (default: input.tex)")
    parser.add_argument(
        "--mode", choices=["pub", "dev", "compute"], default="pub",
        help="Output mode: pub (clean), dev (annotated), compute (with byte metadata)",
    )
    parser.add_argument(
        "--engine", choices=["lualatex", "xelatex"], default="lualatex",
        help="LaTeX engine (default: lualatex)",
    )
    parser.add_argument("--template", type=Path, help="LaTeX template file")
    parser.add_argument("--bib", type=Path, help="Bibliography file (.bib)")
    parser.add_argument("--registry", type=Path, help="Symbol registry JSON file")
    parser.add_argument("--lint", action="store_true", help="Run linter and exit")
    parser.add_argument("--validate", action="store_true", help="Validate PDF after compilation")
    parser.add_argument("--validate-all", action="store_true", help="Run comprehensive validation suite")
    parser.add_argument("--appendix", action="store_true", help="Generate symbol reference appendix")
    parser.add_argument("--add-version", action="store_true", help="Add version hash to output")
    parser.add_argument("--compile-pdf", action="store_true", help="Compile to PDF")
    parser.add_argument("--watch", action="store_true", help="Watch file for changes and auto-convert")
    parser.add_argument("--test-symbols", type=Path, help="Generate symbol rendering test document")
    parser.add_argument(
        "--keep-normalized", action="store_true",
        help="Keep intermediate normalized Markdown file",
    )

    args = parser.parse_args()

    # Test symbols mode
    if args.test_symbols:
        registry = SymbolRegistry(args.registry)
        renderer = SymbolTestRenderer(registry)
        renderer.generate_test_doc(args.test_symbols, args.engine)
        return

    # Require input for other operations
    if not args.input:
        parser.error("input file is required")
    if not args.input.exists():
        print(f"✗ Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    registry = SymbolRegistry(args.registry)

    # Validation suite mode
    if args.validate_all:
        success = run_validation_suite(args, registry)
        sys.exit(0 if success else 1)

    # Lint mode
    if args.lint:
        linter = SymbolLinter(registry)
        issues, stats = linter.lint_file(args.input)
        report = linter.generate_report(issues, stats)
        print(report)
        if args.appendix:
            gen = AppendixGenerator(registry)
            appendix = gen.generate(stats)
            appendix_path = args.input.with_suffix(".appendix.tex")
            with open(appendix_path, "w", encoding="utf-8") as f:
                f.write(appendix)
            print(f"\n✓ Appendix generated at {appendix_path}")
        sys.exit(0 if not issues else 1)

    # Watch mode
    if args.watch:
        watch_mode(args, main_conversion_logic)
        return

    # Normal conversion
    try:
        main_conversion_logic(args)
    except Exception as e:
        print(f"\n✗ Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
