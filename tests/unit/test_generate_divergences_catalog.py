"""Unit tests for scripts/generate_divergences_catalog.py."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from generate_divergences_catalog import (
    CATEGORY_DISPLAY_NAMES,
    CATEGORY_ORDER,
    STATUS_DISPLAY,
    WORKAROUND_DISPLAY,
    DivergenceEntry,
    group_by_category,
    parse_entries,
    render_catalog,
    render_detail_section,
    render_summary_table,
)


def _minimal_raw_entry(**overrides) -> dict:
    """Create a minimal valid raw entry dict."""
    base = {
        "id": "TEST-01",
        "project": "test",
        "category": "string-ops",
        "summary": "Test divergence",
        "root_cause": "upstream_bug",
        "affected_backends": ["polars", "ibis"],
        "status": "open",
        "our_workaround": "xfail_strict",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# TestParseEntries
# ---------------------------------------------------------------------------


class TestParseEntries:
    def test_parses_minimal_entry(self):
        raw = [_minimal_raw_entry()]
        entries = parse_entries(raw)
        assert len(entries) == 1
        assert entries[0].id == "TEST-01"
        assert entries[0].project == "test"
        assert entries[0].category == "string-ops"
        assert entries[0].affected_backends == ["polars", "ibis"]

    def test_skips_entry_missing_required_field(self, capsys):
        raw = [{"id": "BAD-01", "project": "test"}]  # missing most required fields
        entries = parse_entries(raw)
        assert len(entries) == 0
        captured = capsys.readouterr()
        assert "WARNING" in captured.err
        assert "BAD-01" in captured.err

    def test_handles_empty_list(self):
        entries = parse_entries([])
        assert entries == []


# ---------------------------------------------------------------------------
# TestGroupByCategory
# ---------------------------------------------------------------------------


class TestGroupByCategory:
    def test_groups_by_category(self):
        entries = parse_entries([
            _minimal_raw_entry(id="A-01", category="string-ops"),
            _minimal_raw_entry(id="B-01", category="math-ops"),
            _minimal_raw_entry(id="A-02", category="string-ops"),
        ])
        grouped = group_by_category(entries)
        assert "string-ops" in grouped
        assert "math-ops" in grouped
        assert len(grouped["string-ops"]) == 2
        assert len(grouped["math-ops"]) == 1

    def test_sorts_entries_by_id_within_category(self):
        entries = parse_entries([
            _minimal_raw_entry(id="Z-99", category="string-ops"),
            _minimal_raw_entry(id="A-01", category="string-ops"),
            _minimal_raw_entry(id="M-50", category="string-ops"),
        ])
        grouped = group_by_category(entries)
        ids = [e.id for e in grouped["string-ops"]]
        assert ids == ["A-01", "M-50", "Z-99"]

    def test_unknown_category_still_grouped(self):
        entries = parse_entries([_minimal_raw_entry(category="exotic-ops")])
        grouped = group_by_category(entries)
        assert "exotic-ops" in grouped

    def test_category_display_names_covers_all_known_categories(self):
        for cat in CATEGORY_ORDER:
            assert cat in CATEGORY_DISPLAY_NAMES, f"Missing display name for {cat}"


# ---------------------------------------------------------------------------
# TestRenderSummaryTable
# ---------------------------------------------------------------------------


class TestRenderSummaryTable:
    def test_renders_markdown_table(self):
        entries = parse_entries([_minimal_raw_entry()])
        table = render_summary_table(entries)
        assert "| ID |" in table
        assert "| TEST-01 |" in table
        assert "polars, ibis" in table

    def test_status_display_maps_correctly(self):
        for key, display in STATUS_DISPLAY.items():
            entries = parse_entries([_minimal_raw_entry(status=key)])
            table = render_summary_table(entries)
            assert display in table

    def test_workaround_display_maps_correctly(self):
        for key, display in WORKAROUND_DISPLAY.items():
            entries = parse_entries([_minimal_raw_entry(our_workaround=key)])
            table = render_summary_table(entries)
            assert display in table


# ---------------------------------------------------------------------------
# TestRenderDetailSection
# ---------------------------------------------------------------------------


class TestRenderDetailSection:
    def test_renders_heading_with_id_and_summary(self):
        entry = parse_entries([_minimal_raw_entry()])[0]
        section = render_detail_section(entry)
        assert "### TEST-01: Test divergence" in section

    def test_renders_all_fields(self):
        entry = parse_entries([_minimal_raw_entry(
            upstream_issue="https://github.com/example/issue/1",
            known_expr_limitations=["limit_a"],
            xfail_refs=["tests/foo.py:10"],
            notes="Some note",
            last_verified="2026-05-01",
        )])[0]
        section = render_detail_section(entry)
        assert "Upstream Issue" in section
        assert "https://github.com/example/issue/1" in section
        assert "Known Expr Limitations" in section
        assert "limit_a" in section
        assert "Xfail Refs" in section
        assert "tests/foo.py:10" in section
        assert "Notes" in section
        assert "Some note" in section
        assert "Last Verified" in section
        assert "2026-05-01" in section

    def test_omits_empty_optional_fields(self):
        entry = parse_entries([_minimal_raw_entry()])[0]
        section = render_detail_section(entry)
        assert "Upstream Issue" not in section
        assert "Known Expr Limitations" not in section
        assert "Xfail Refs" not in section
        assert "Notes" not in section
        assert "Last Verified" not in section


# ---------------------------------------------------------------------------
# TestRenderCatalog
# ---------------------------------------------------------------------------


class TestRenderCatalog:
    def _make_entries(self):
        return parse_entries([
            _minimal_raw_entry(id="A-01", category="string-ops"),
            _minimal_raw_entry(id="B-01", category="math-ops"),
        ])

    def test_renders_overview_section(self):
        catalog = render_catalog(self._make_entries())
        assert "## Overview" in catalog
        assert "Total divergences tracked: **2**" in catalog

    def test_renders_summary_tables_section(self):
        catalog = render_catalog(self._make_entries())
        assert "## Summary" in catalog
        assert "### String Operations" in catalog
        assert "### Math Operations" in catalog

    def test_renders_detailed_reference_section(self):
        catalog = render_catalog(self._make_entries())
        assert "## Detailed Reference" in catalog
        assert "### A-01: Test divergence" in catalog
        assert "### B-01: Test divergence" in catalog

    def test_omits_empty_categories(self):
        entries = parse_entries([_minimal_raw_entry(category="string-ops")])
        catalog = render_catalog(entries)
        assert "Math Operations" not in catalog

    def test_header_contains_do_not_edit_warning(self):
        catalog = render_catalog(self._make_entries())
        assert "DO NOT EDIT" in catalog

    def test_categories_ordered_by_category_order(self):
        entries = parse_entries([
            _minimal_raw_entry(id="M-01", category="math-ops"),
            _minimal_raw_entry(id="S-01", category="string-ops"),
        ])
        catalog = render_catalog(entries)
        # string-ops comes before math-ops in CATEGORY_ORDER
        str_pos = catalog.index("String Operations")
        math_pos = catalog.index("Math Operations")
        assert str_pos < math_pos
