#!/usr/bin/env python3
"""Compare our current function definitions against Substrait standard.

This script analyzes:
1. Which Substrait functions we implement
2. Which Substrait functions we're missing
3. Which of our functions are extensions (not in Substrait)
4. Name mapping differences (our name vs Substrait name)

Usage:
    python scripts/compare_substrait_coverage.py
    python scripts/compare_substrait_coverage.py --verbose
    python scripts/compare_substrait_coverage.py --category comparison
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import our definitions
try:
    from mountainash_expressions.core.functions.definitions import (
        COMPARISON_FUNCTIONS,
        BOOLEAN_FUNCTIONS,
        ARITHMETIC_FUNCTIONS,
        STRING_FUNCTIONS,
        TEMPORAL_FUNCTIONS,
        NULL_FUNCTIONS,
        NAME_FUNCTIONS,
        TYPE_FUNCTIONS,
        CONSTANT_FUNCTIONS,
        TERNARY_FUNCTIONS,
    )
    from mountainash_expressions.core.functions.registry import FunctionDef
    HAS_DEFINITIONS = True
except ImportError as e:
    print(f"Warning: Could not import definitions: {e}")
    HAS_DEFINITIONS = False

# Import the generator for Substrait parsing
from generate_from_substrait import load_all_substrait, SubstraitFunction


@dataclass
class CoverageReport:
    """Report comparing our coverage to Substrait."""
    # Functions we implement that are in Substrait
    implemented: list[tuple[str, str]]  # (our_name, substrait_name)

    # Substrait functions we don't implement
    missing: list[SubstraitFunction]

    # Our functions that extend beyond Substrait
    extensions: list[str]

    # Name differences (we use different name than Substrait)
    name_mappings: list[tuple[str, str]]  # (our_name, substrait_name)

    # Category breakdown
    by_category: dict[str, dict[str, int]]


def get_our_functions() -> list[FunctionDef]:
    """Get all our registered functions."""
    if not HAS_DEFINITIONS:
        return []

    all_funcs = []
    for func_list in [
        COMPARISON_FUNCTIONS,
        BOOLEAN_FUNCTIONS,
        ARITHMETIC_FUNCTIONS,
        STRING_FUNCTIONS,
        TEMPORAL_FUNCTIONS,
        NULL_FUNCTIONS,
        NAME_FUNCTIONS,
        TYPE_FUNCTIONS,
        CONSTANT_FUNCTIONS,
        TERNARY_FUNCTIONS,
    ]:
        all_funcs.extend(func_list)

    return all_funcs


def analyze_coverage(
    categories: list[str] | None = None,
    cache_dir: Path | None = None,
) -> CoverageReport:
    """Analyze our coverage of Substrait functions."""

    # Load Substrait definitions
    substrait_by_category = load_all_substrait(categories, cache_dir)

    # Build lookup of all Substrait functions by name
    substrait_funcs: dict[str, SubstraitFunction] = {}
    for category, funcs in substrait_by_category.items():
        for func in funcs:
            substrait_funcs[func.name] = func

    # Get our functions
    our_funcs = get_our_functions()

    # Analyze
    implemented = []
    extensions = []
    name_mappings = []

    our_substrait_names = set()

    for func in our_funcs:
        substrait_name = func.substrait_name
        our_substrait_names.add(substrait_name)

        if func.is_extension:
            extensions.append(func.name)
        elif substrait_name in substrait_funcs:
            implemented.append((func.name, substrait_name))
            if func.name != substrait_name:
                name_mappings.append((func.name, substrait_name))
        else:
            # We claim a Substrait name that doesn't exist
            extensions.append(func.name)  # Treat as extension

    # Find missing Substrait functions
    missing = []
    for name, func in substrait_funcs.items():
        if name not in our_substrait_names:
            missing.append(func)

    # Category breakdown
    by_category: dict[str, dict[str, int]] = {}
    for category, funcs in substrait_by_category.items():
        total = len(funcs)
        implemented_count = sum(1 for f in funcs if f.name in our_substrait_names)
        by_category[category] = {
            "total": total,
            "implemented": implemented_count,
            "missing": total - implemented_count,
            "percent": round(100 * implemented_count / total, 1) if total > 0 else 0,
        }

    return CoverageReport(
        implemented=implemented,
        missing=missing,
        extensions=extensions,
        name_mappings=name_mappings,
        by_category=by_category,
    )


def print_report(report: CoverageReport, verbose: bool = False):
    """Print the coverage report."""

    print("=" * 70)
    print("SUBSTRAIT COVERAGE REPORT")
    print("=" * 70)
    print()

    # Summary
    total_substrait = sum(c["total"] for c in report.by_category.values())
    total_implemented = sum(c["implemented"] for c in report.by_category.values())
    overall_percent = round(100 * total_implemented / total_substrait, 1) if total_substrait > 0 else 0

    print(f"Overall Coverage: {total_implemented}/{total_substrait} ({overall_percent}%)")
    print(f"Our Extensions: {len(report.extensions)}")
    print()

    # By category
    print("Coverage by Category:")
    print("-" * 50)
    for category, stats in report.by_category.items():
        bar_len = int(stats["percent"] / 5)  # 20 chars = 100%
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {category:20} {bar} {stats['implemented']:3}/{stats['total']:3} ({stats['percent']:5.1f}%)")
    print()

    # Name mappings (our name differs from Substrait)
    if report.name_mappings:
        print("Name Mappings (our name → Substrait name):")
        print("-" * 50)
        for our_name, substrait_name in sorted(report.name_mappings):
            print(f"  {our_name:25} → {substrait_name}")
        print()

    # Missing functions
    if report.missing:
        print(f"Missing Substrait Functions ({len(report.missing)}):")
        print("-" * 50)

        # Group by category
        by_cat: dict[str, list[str]] = {}
        for func in report.missing:
            cat = func.category
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(func.name)

        for cat, names in sorted(by_cat.items()):
            print(f"  {cat}:")
            if verbose:
                for name in sorted(names):
                    print(f"    - {name}")
            else:
                # Show first 5
                shown = sorted(names)[:5]
                remaining = len(names) - 5
                for name in shown:
                    print(f"    - {name}")
                if remaining > 0:
                    print(f"    ... and {remaining} more")
        print()

    # Our extensions
    if report.extensions and verbose:
        print(f"Our Extensions ({len(report.extensions)}):")
        print("-" * 50)
        for name in sorted(report.extensions):
            print(f"  - {name}")
        print()

    # Priority recommendations
    print("Priority Functions to Consider Implementing:")
    print("-" * 50)
    priority_functions = [
        "is_nan", "is_finite", "is_infinite",  # Useful for data validation
        "nullif",  # Common SQL pattern
        "round", "ceil", "floor",  # Rounding
        "ln", "log10", "log2",  # Logarithms
        "abs", "sign",  # Basic math
        "reverse", "repeat", "lpad", "rpad",  # String utilities
        "strpos",  # String search
        "count",  # Aggregate
    ]

    missing_names = {f.name for f in report.missing}
    for name in priority_functions:
        if name in missing_names:
            func = next(f for f in report.missing if f.name == name)
            print(f"  - {name}: {func.description[:60]}...")
    print()


def main():
    parser = argparse.ArgumentParser(description="Compare our coverage to Substrait")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all details")
    parser.add_argument("--category", "-c", action="append", dest="categories", help="Specific categories")
    parser.add_argument("--cache-dir", type=Path, default=Path(".substrait_cache"))

    args = parser.parse_args()

    report = analyze_coverage(args.categories, args.cache_dir)
    print_report(report, args.verbose)


if __name__ == "__main__":
    main()
