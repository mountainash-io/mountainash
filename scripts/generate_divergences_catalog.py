#!/usr/bin/env python3
"""Generate a Markdown catalog of cross-backend divergences from the YAML registry.

Usage:
    python scripts/generate_divergences_catalog.py
    python scripts/generate_divergences_catalog.py --report-file docs/known-divergences.md
    python scripts/generate_divergences_catalog.py --check
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "known-divergences.md"
YAML_REGISTRY = (
    PROJECT_ROOT.parent
    / "mountainash-central"
    / "01.principles"
    / "mountainash"
    / "h.backlog"
    / "upstream-issues"
    / "upstream-issues.yaml"
)

TIMESTAMP_PREFIX = "> Last generated: "

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"id", "project", "category", "summary", "root_cause", "affected_backends", "status", "our_workaround"}


@dataclass(frozen=True)
class DivergenceEntry:
    id: str
    project: str
    category: str
    summary: str
    root_cause: str
    affected_backends: list[str] = field(default_factory=list)
    upstream_issue: str | None = None
    upstream_issue_filed_by: str | None = None
    status: str = "open"
    our_workaround: str = "none"
    known_expr_limitations: list[str] = field(default_factory=list)
    xfail_refs: list[str] = field(default_factory=list)
    notes: str | None = None
    last_verified: str | None = None


def parse_entries(raw_issues: list[dict]) -> list[DivergenceEntry]:
    """Parse YAML dicts into DivergenceEntry objects, skipping malformed entries."""
    entries: list[DivergenceEntry] = []
    for raw in raw_issues:
        missing = REQUIRED_FIELDS - set(raw.keys())
        if missing:
            print(
                f"WARNING: Skipping entry {raw.get('id', '<unknown>')}: missing fields {sorted(missing)}",
                file=sys.stderr,
            )
            continue
        entries.append(
            DivergenceEntry(
                id=raw["id"],
                project=raw["project"],
                category=raw["category"],
                summary=raw["summary"],
                root_cause=raw["root_cause"],
                affected_backends=raw.get("affected_backends") or [],
                upstream_issue=raw.get("upstream_issue"),
                upstream_issue_filed_by=raw.get("upstream_issue_filed_by"),
                status=raw.get("status", "open"),
                our_workaround=raw.get("our_workaround", "none"),
                known_expr_limitations=raw.get("known_expr_limitations") or [],
                xfail_refs=raw.get("xfail_refs") or [],
                notes=raw.get("notes"),
                last_verified=raw.get("last_verified"),
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Category display
# ---------------------------------------------------------------------------

CATEGORY_DISPLAY_NAMES: dict[str, str] = {
    "string-ops": "String Operations",
    "datetime-ops": "Datetime Operations",
    "math-ops": "Math Operations",
    "type-inference": "Type System",
    "type-system": "Type System",
    "relation-ops": "Relational Operations",
    "aggregate-ops": "Aggregate Operations",
    "list-ops": "List Operations",
    "cast-semantics": "Cast Semantics",
    "interval-ops": "Interval Operations",
    "recursive-cte": "Recursive CTEs",
    "wiring-gaps": "Internal Wiring Gaps",
}

CATEGORY_ORDER: list[str] = [
    "string-ops",
    "datetime-ops",
    "math-ops",
    "type-inference",
    "type-system",
    "relation-ops",
    "aggregate-ops",
    "list-ops",
    "cast-semantics",
    "interval-ops",
    "recursive-cte",
    "wiring-gaps",
]


def group_by_category(entries: list[DivergenceEntry]) -> dict[str, list[DivergenceEntry]]:
    """Group entries by category, sorted by ID within each group."""
    groups: dict[str, list[DivergenceEntry]] = {}
    for entry in entries:
        groups.setdefault(entry.category, []).append(entry)
    for group in groups.values():
        group.sort(key=lambda e: e.id)
    return groups


# ---------------------------------------------------------------------------
# Display mappings
# ---------------------------------------------------------------------------

STATUS_DISPLAY: dict[str, str] = {
    "open": "Open",
    "needs_filing": "Needs Filing",
    "needs_investigation": "Investigating",
    "closed": "Closed",
    "wont_fix": "Won't Fix",
    "by_design": "By Design",
    "resolved_in_mountainash": "Resolved (internal)",
}

WORKAROUND_DISPLAY: dict[str, str] = {
    "xfail_strict": "Strict xfail",
    "xfail_nonstrict": "Non-strict xfail",
    "error_enrichment": "Enhanced error message",
    "fallback_impl": "Fallback implementation",
    "accepted_divergence": "Accepted (documented)",
    "none": "None",
}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_summary_table(entries: list[DivergenceEntry]) -> str:
    """Render a Markdown table summarising the given entries."""
    lines = [
        "| ID | Summary | Backends | Root Cause | Workaround | Status |",
        "|---|---|---|---|---|---|",
    ]
    for e in entries:
        backends = ", ".join(e.affected_backends)
        workaround = WORKAROUND_DISPLAY.get(e.our_workaround, e.our_workaround)
        status = STATUS_DISPLAY.get(e.status, e.status)
        lines.append(f"| {e.id} | {e.summary} | {backends} | {e.root_cause} | {workaround} | {status} |")
    return "\n".join(lines)


def render_detail_section(entry: DivergenceEntry) -> str:
    """Render a detailed section for a single entry."""
    lines = [f"### {entry.id}: {entry.summary}", ""]
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Project | {entry.project} |")
    lines.append(f"| Category | {CATEGORY_DISPLAY_NAMES.get(entry.category, entry.category)} |")
    lines.append(f"| Root Cause | {entry.root_cause} |")
    lines.append(f"| Affected Backends | {', '.join(entry.affected_backends)} |")
    lines.append(f"| Status | {STATUS_DISPLAY.get(entry.status, entry.status)} |")
    lines.append(f"| Workaround | {WORKAROUND_DISPLAY.get(entry.our_workaround, entry.our_workaround)} |")

    # Optional fields — only render if non-empty
    if entry.upstream_issue:
        lines.append(f"| Upstream Issue | {entry.upstream_issue} |")
    if entry.known_expr_limitations:
        lines.append(f"| Known Expr Limitations | {', '.join(entry.known_expr_limitations)} |")
    if entry.xfail_refs:
        lines.append(f"| Xfail Refs | {', '.join(entry.xfail_refs)} |")
    if entry.notes:
        lines.append(f"| Notes | {entry.notes} |")
    if entry.last_verified:
        lines.append(f"| Last Verified | {entry.last_verified} |")

    return "\n".join(lines)


def render_catalog(entries: list[DivergenceEntry]) -> str:
    """Assemble the full catalog document."""
    lines: list[str] = []

    # Header
    lines.append("# Known Cross-Backend Divergences")
    lines.append("")
    lines.append("<!-- DO NOT EDIT — this file is auto-generated by scripts/generate_divergences_catalog.py -->")
    lines.append("")
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append(f"{TIMESTAMP_PREFIX}{timestamp}")
    lines.append("")

    # Overview stats
    lines.append("## Overview")
    lines.append("")
    lines.append(f"Total divergences tracked: **{len(entries)}**")
    lines.append("")

    grouped = group_by_category(entries)

    # Determine category order: CATEGORY_ORDER first, then extras alphabetically
    ordered_categories: list[str] = []
    for cat in CATEGORY_ORDER:
        if cat in grouped:
            ordered_categories.append(cat)
    extras = sorted(set(grouped.keys()) - set(CATEGORY_ORDER))
    ordered_categories.extend(extras)

    # Summary tables by category
    lines.append("## Summary")
    lines.append("")
    for cat in ordered_categories:
        display_name = CATEGORY_DISPLAY_NAMES.get(cat, cat)
        lines.append(f"### {display_name}")
        lines.append("")
        lines.append(render_summary_table(grouped[cat]))
        lines.append("")

    # Horizontal rule
    lines.append("---")
    lines.append("")

    # Detailed reference
    lines.append("## Detailed Reference")
    lines.append("")
    for cat in ordered_categories:
        display_name = CATEGORY_DISPLAY_NAMES.get(cat, cat)
        lines.append(f"## {display_name}")
        lines.append("")
        for entry in grouped[cat]:
            lines.append(render_detail_section(entry))
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# I/O and CLI
# ---------------------------------------------------------------------------


def load_yaml_registry(path: Path | None = None) -> list[dict]:
    """Load the YAML registry file. Exits with error if missing."""
    if yaml is None:
        print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    registry_path = path or YAML_REGISTRY
    if not registry_path.exists():
        print(f"ERROR: YAML registry not found at {registry_path}", file=sys.stderr)
        sys.exit(1)
    with open(registry_path) as f:
        data = yaml.safe_load(f)
    return data.get("issues", [])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate known divergences catalog from YAML registry.")
    parser.add_argument(
        "--report-file",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output file path (default: docs/known-divergences.md)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if the catalog is up-to-date (exits non-zero if stale).",
    )
    return parser.parse_args()


def _strip_timestamp(content: str) -> str:
    """Remove the timestamp line for comparison."""
    return "\n".join(
        line for line in content.splitlines() if not line.startswith(TIMESTAMP_PREFIX)
    )


def main() -> None:
    args = parse_args()

    raw_issues = load_yaml_registry()
    entries = parse_entries(raw_issues)
    catalog = render_catalog(entries)

    if args.check:
        if not args.report_file.exists():
            print(f"CHECK FAILED: {args.report_file} does not exist.", file=sys.stderr)
            sys.exit(1)
        existing = args.report_file.read_text()
        if _strip_timestamp(existing) != _strip_timestamp(catalog):
            print(f"CHECK FAILED: {args.report_file} is out of date. Re-run the generator.", file=sys.stderr)
            sys.exit(1)
        print("OK: catalog is up to date.")
        return

    args.report_file.parent.mkdir(parents=True, exist_ok=True)
    args.report_file.write_text(catalog)
    print(f"Catalog written to {args.report_file} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
