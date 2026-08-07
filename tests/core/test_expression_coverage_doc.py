"""Drift gate + identity invariants for docs/reference/expression-coverage.md.

The committed artifact must equal the regenerated output byte-for-byte
(spec §4.5). On failure: hatch -e test run python -m mountainash.core.capabilities.render_markdown
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    ImplState,
    build_coverage_report,
)
from mountainash.core.capabilities.render_markdown import (
    _ARTIFACT_PATH,
    _REGEN_CMD,
    _cell_text,
    gather_coverage_inputs,
    render_markdown,
)
from mountainash.core.constants import CONST_BACKEND

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def inputs() -> dict:
    return gather_coverage_inputs()


@pytest.fixture(scope="module")
def report(inputs):
    return build_coverage_report(**inputs)


def _matrix_body(doc: str) -> str:
    """The per-family matrix section, between '## Per-family coverage' and
    '## Unmapped families'. The legend and summary legitimately contain
    'audited'; scoping the badge assertion to the matrix body excludes them."""
    return doc.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]


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


def test_unaudited_never_renders_audit_badge(report):
    """No op without an applicable declaration renders the `audited` badge in
    its cell. SCOPED to the matrix body (## Per-family coverage ...
    ## Unmapped families) because the legend and summary legitimately contain
    'audited'. The default-capable mark `✓` requires IMPLEMENTED, never mere
    absence of facts (spec §3.3 / §4.5)."""
    doc = render_markdown(report)
    matrix = _matrix_body(doc)
    for fam in report.families:
        if fam.audit_domain is None:
            continue  # unmapped families render in their own section
        for oc in fam.ops:
            if not oc.declarations:
                cell = _cell_text(oc)
                assert " audited" not in cell, (
                    f"un-audited cell renders ' audited' badge: "
                    f"{oc.op.family}.{oc.op.operation_key.name}/{oc.backend.value} -> {cell!r}"
                )
                # The cell text must appear in the matrix body (proves the
                # assertion is scoped to where the cells are actually rendered).
                assert cell in matrix, (
                    f"expected cell text {cell!r} for "
                    f"{oc.op.family}.{oc.op.operation_key.name}/{oc.backend.value} "
                    f"not found in matrix body"
                )


def test_no_contradictions_in_live_registry(report):
    """Spec §3.3 / §4.5 / §5: the live registry must produce zero contradictions.
    A failing test here is the early-warning that catalog and registry disagree
    on a cell's implementation status; the renderer would have rendered `⚠
    contradiction` for each but did not crash."""
    assert report.stats.contradictions == 0, (
        f"live registry has {report.stats.contradictions} contradiction(s); "
        f"investigate the offending op×backend cell(s) in the matrix body"
    )


def test_no_audited_unknown_in_live_registry(report):
    """Spec §3.6 / review I-1: every backend's audited_unknown count must be
    zero. Fires the moment a declaration covers a family whose ops the
    implementation axis cannot see (registry/derivation drift)."""
    for b in RENDERED_BACKENDS:
        n = report.stats.audited_unknown[b]
        assert n == 0, (
            f"audited_unknown == {n} on {b.value}; a declaration covers ops "
            f"the impl-axis cannot resolve — investigate the declaration's "
            f"audit domain vs the registered ops"
        )


def test_per_backend_sum_law_in_live_report(report):
    """Spec §4.5 / review I-2: for every rendered backend,
    default_capable + audited_clean + constrained
    + by_impl[NOT_IMPLEMENTED] + by_impl[UNKNOWN] == ops_total."""
    s = report.stats
    for b in RENDERED_BACKENDS:
        total = (
            s.default_capable[b]
            + s.audited_clean[b]
            + s.constrained[b]
            + s.by_impl[(b, ImplState.NOT_IMPLEMENTED)]
            + s.by_impl[(b, ImplState.UNKNOWN)]
        )
        assert total == s.ops_total, (
            f"sum law violated for {b.value}: {total} != {s.ops_total} "
            f"(default_capable={s.default_capable[b]}, "
            f"audited_clean={s.audited_clean[b]}, "
            f"constrained={s.constrained[b]}, "
            f"not_impl={s.by_impl[(b, ImplState.NOT_IMPLEMENTED)]}, "
            f"unknown={s.by_impl[(b, ImplState.UNKNOWN)]})"
        )


def test_implementation_via_handler_live_baseline_pin(inputs):
    """Spec §3.6 / review C-1: live-baseline pin on the implementation axis.

    The 9 IMPLEMENTED_VIA_HANDLER records are the SOURCE / REF / CONFORM
    relation ops (RKEY_MOUNTAINASH_REL) × 3 backends, dispatched through the
    visitor's `handler` path. The 0 UNKNOWN / 0 NOT_IMPLEMENTED counts assert
    the implementation axis sees every registered op today.

    DATA PIN: when this test breaks, the fix is to UPDATE THE PIN after
    verifying the registry change was intentional (e.g. a new handler-only
    op, a stub move, a real implementation gap). The pin is a snapshot of
    the develop @ PR #256 merge baseline; do not let the test 'correct' the
    numbers silently.
    """
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )

    impls = inputs["implementations"]

    # Exact key set: SOURCE / REF / CONFORM × POLARS / NARWHALS / IBIS.
    expected_handler_keys = frozenset(
        (op, backend)
        for op in (RKEY_MOUNTAINASH_REL.SOURCE,
                   RKEY_MOUNTAINASH_REL.REF,
                   RKEY_MOUNTAINASH_REL.CONFORM)
        for backend in RENDERED_BACKENDS
    )
    actual_handler_keys = frozenset(
        (r.operation_key, r.backend) for r in impls
        if r.state is ImplState.IMPLEMENTED_VIA_HANDLER
    )
    assert actual_handler_keys == expected_handler_keys, (
        f"IMPLEMENTED_VIA_HANDLER key set drifted from the live baseline pin.\n"
        f"  expected: {sorted(k[0].name + '/' + k[1].value for k in expected_handler_keys)}\n"
        f"  actual:   {sorted(k[0].name + '/' + k[1].value for k in actual_handler_keys)}\n"
        f"  missing:  {sorted(k[0].name + '/' + k[1].value for k in expected_handler_keys - actual_handler_keys)}\n"
        f"  extra:    {sorted(k[0].name + '/' + k[1].value for k in actual_handler_keys - expected_handler_keys)}\n"
        f"DATA PIN — update the pin after verifying the registry change is intentional."
    )
    assert len(actual_handler_keys) == 9

    # 0 UNKNOWN across the live registry.
    n_unknown = sum(1 for r in impls if r.state is ImplState.UNKNOWN)
    assert n_unknown == 0, (
        f"live registry has {n_unknown} UNKNOWN implementation record(s); "
        f"a registered op is no longer resolvable on the implementation axis. "
        f"DATA PIN — update the pin if this drift is intentional."
    )

    # 0 NOT_IMPLEMENTED across the live registry.
    n_not_impl = sum(1 for r in impls if r.state is ImplState.NOT_IMPLEMENTED)
    assert n_not_impl == 0, (
        f"live registry has {n_not_impl} NOT_IMPLEMENTED implementation record(s); "
        f"a registered op's protocol-method override is missing on a backend "
        f"leaf class. DATA PIN — update the pin if this drift is intentional."
    )
