"""Drift gate + identity invariants for docs/reference/expression-coverage.md.

The committed artifact must equal the regenerated output byte-for-byte
(spec §4.5). On failure: hatch -e test run python -m mountainash.core.capabilities.render_markdown
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mountainash.core.capabilities.coverage import (
    CoverageState,
    build_coverage_report,
)
from mountainash.core.capabilities.render_markdown import (
    _ARTIFACT_PATH,
    _REGEN_CMD,
    gather_coverage_inputs,
    render_markdown,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def inputs() -> dict:
    return gather_coverage_inputs()


@pytest.fixture(scope="module")
def report(inputs):
    return build_coverage_report(**inputs)


def test_coverage_doc_is_current(report):
    committed = (_REPO_ROOT / _ARTIFACT_PATH).read_text(encoding="utf-8")
    assert committed == render_markdown(report), (
        f"docs/reference/expression-coverage.md is stale; regenerate with: {_REGEN_CMD}"
    )


def test_universe_partition_exact(inputs, report):
    from collections import Counter

    scattered = Counter(
        (oc.op.family, oc.op.operation_key.name)
        for fam in report.families
        for oc in fam.ops
    )
    expected = Counter(
        {(r.family, r.operation_key.name): 3 for r in inputs["universe"]}
    )
    assert scattered == expected, (
        "universe not partitioned exactly across families×backends"
    )


def test_every_fact_bucketed_exactly_once(inputs, report):
    from collections import Counter

    scattered = Counter(
        id(f) for fam in report.families for oc in fam.ops for f in oc.all_facts
    )
    original = Counter(id(f) for f in inputs["facts"])
    assert scattered == original


def test_declarations_rendered_exactly_once(inputs, report):
    assert sorted(map(id, report.declarations)) == sorted(
        map(id, inputs["declarations"])
    )
    doc = render_markdown(report)
    pairs_body = doc.split("### Audited pairs", 1)[1].split("\n## ", 1)[0]
    rows = [
        ln for ln in pairs_body.splitlines()
        if ln.startswith("|") and "---" not in ln and not ln.startswith("| Backend")
    ]
    assert len(rows) == len(report.declarations)
    for d in report.declarations:
        if d.evidence is not None:
            assert any(d.evidence.probe_date in r for r in rows)
            if d.evidence.fixtures:
                assert any(d.evidence.fixtures[0] in r for r in rows)


def test_gaps_and_retirements_rendered_exactly_once(report):
    doc = render_markdown(report)
    for heading, records in (
        ("## Known gaps", report.gaps),
        ("## Retirement changelog", report.retired),
    ):
        body = doc.split(heading, 1)[1].split("\n## ", 1)[0]
        rows = [ln for ln in body.splitlines()
                if ln.startswith("|") and "---" not in ln]
        expected = len(records) + 1 if records else 0
        assert len(rows) == expected


def test_divergence_operation_keys_within_universe(inputs, report):
    universe_keys = {r.operation_key for r in inputs["universe"]}
    for dv in report.divergences:
        for k in dv.operation_keys:
            assert k in universe_keys, f"divergence {dv.id} references unknown op {k!r}"


def test_undeclared_never_renders_clean(report):
    for fam in report.families:
        for oc in fam.ops:
            if not oc.declarations:
                assert oc.state is not CoverageState.DECLARED_CLEAN
