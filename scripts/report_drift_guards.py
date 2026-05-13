#!/usr/bin/env python3
"""Drift guard report: xfail population across protocol_alignment and argument_types suites.

Usage:
    python scripts/report_drift_guards.py
    python scripts/report_drift_guards.py --report-file scripts/outputs/drift-guards-report.md
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TESTS_DIR = PROJECT_ROOT / "tests"
ARG_TYPES_DIR = TESTS_DIR / "cross_backend" / "argument_types"
PROTOCOL_ALIGNMENT_FILE = TESTS_DIR / "unit" / "test_protocol_alignment.py"
BACKEND_BASE_FILES = {
    "polars": PROJECT_ROOT / "src/mountainash/expressions/backends/expression_systems/polars/base.py",
    "narwhals": PROJECT_ROOT / "src/mountainash/expressions/backends/expression_systems/narwhals/base.py",
    "ibis": PROJECT_ROOT / "src/mountainash/expressions/backends/expression_systems/ibis/base.py",
}


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def render_report() -> str:
    return "# Drift Guard Report\n\n(stub)\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-file",
        metavar="PATH",
        help="Write markdown report to this file in addition to printing to stdout.",
    )
    args = parser.parse_args()
    report = render_report()
    print(report)
    if args.report_file:
        out = Path(args.report_file)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
        print(f"Report saved to {out}")


if __name__ == "__main__":
    main()
