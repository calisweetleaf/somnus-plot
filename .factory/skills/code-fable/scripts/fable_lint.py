#!/usr/bin/env python3
"""
fable_lint.py — Wrapper entry point for the Code-Fable Mini-Harness Linter.

Delegates to `fable_harness.py lint`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fable_harness import main as harness_main  # noqa: E402


if __name__ == "__main__":
    sys.argv = [sys.argv[0], "lint", *sys.argv[1:]]
    sys.exit(harness_main())
