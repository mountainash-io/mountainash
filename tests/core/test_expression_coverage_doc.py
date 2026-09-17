"""Drift gate + identity invariants for the three committed coverage artifacts
(spec §4.5, §4.6 — main md + scoped md + JSON).

The committed artifact must equal the regenerated output byte-for-byte
(spec §4.5). On failure: hatch -e test run python -m mountainash.core.capabilities.render_markdown
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import mountainash.core.capabilities.render_markdown as render_markdown_module
from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    CoverageReport,
    ImplState,
    OpRecord,
    build_coverage_report,
    fact_sort_key,
)
from mountainash.core.capabilities.render_markdown import (
    _ARTIFACT_RENDERERS,
    _REGEN_CMD,
    _cell_text,
    gather_coverage_inputs,
    render_json,
    render_markdown,
    write_coverage_artifacts,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def inputs() -> dict:
    return gather_coverage_inputs()


@pytest.fixture(scope="module")
def report(inputs):
    return build_coverage_report(**inputs)


def test_coverage_renders_all_outputs_before_first_write(tmp_path, monkeypatch):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("old first")
    second.write_text("old second")

    def render_first(report):
        return "new first"

    def render_second(report):
        raise RuntimeError("second renderer failed")

    monkeypatch.setattr(
        render_markdown_module,
        "_ARTIFACT_RENDERERS",
        (("first.txt", render_first), ("second.txt", render_second)),
    )

    with pytest.raises(RuntimeError, match="second renderer failed"):
        write_coverage_artifacts(tmp_path, object())

    assert first.read_text() == "old first"
    assert second.read_text() == "old second"


def _matrix_body(doc: str) -> str:
    """The per-family matrix section, excluding an optional unmapped section."""
    matrix_and_tail = doc.split("## Per-family coverage", 1)[1]
    return matrix_and_tail.split("## Unmapped families", 1)[0]


# The artifact id is the relative path (the parametrize id for the renderer
# would otherwise be its repr — opaque and noisy). parametrize(..., ids=...)
# receives the parameter VALUES as a tuple, so the lambda returns the path
# for the (path, renderer) pair.
@pytest.mark.parametrize(
    ("rel_path", "renderer"),
    _ARTIFACT_RENDERERS,
    ids=lambda v: v if isinstance(v, str) else v.__name__,
)
def test_coverage_doc_is_current(report, rel_path, renderer):
    committed = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
    assert committed == renderer(report), f"{rel_path} is stale; regenerate with: {_REGEN_CMD}"


# JSON completeness invariant: parsing the committed artifact recovers the
# fact multiset, operation universe, segment/divergence/gap/change counts,
# and per-backend statistics from the live model.
# ---------------------------------------------------------------------------


def _operand_key_from_json(d: dict) -> tuple:
    """Inverse of render_markdown._operand_json — rebuilds the exact
    schema._operand_key tuple shape from the wire (kind-tagged) form."""
    kind = d["kind"]
    if kind == 0:
        return (0,)
    if kind == 1:
        return (1, tuple(d["value"]))
    if kind == 2:
        return (2, d["value"])
    if kind == 3:
        return (3, d["type"], d["value"])
    return (4, d["value"])


def _clause_key_from_json(c: dict) -> tuple:
    return (c["path"], c["op"], _operand_key_from_json(c["operand"]))


def _json_fact_identity(f_dict: dict) -> tuple:
    """The §4.4 fact identity (minus operation_key / backend, which the JSON
    carries on the cell) rebuilt from a JSON fact dict. Mirrors `fact_sort_key`'s
    field order so the multiset comparison is total over the same lexicographic
    key. Strings are kept (not enum-typed) because the JSON form is wire-only."""
    predicate = f_dict.get("predicate")
    return (
        f_dict["dialect"] or "",
        f_dict["param"],
        f_dict["option_value"] or "",
        f_dict["value_class"] or "",
        f_dict["level"],
        f_dict["enforcement"],
        f_dict["boundary"],
        f_dict["condition"] or "",
        f_dict["since"],
        f_dict["message"],
        f_dict["workaround"] or "",
        f_dict["upstream_ref"] or "",
        tuple(f_dict["native_errors"]),
        f_dict["probe_exempt"] or "",
        tuple(_clause_key_from_json(c) for c in predicate) if predicate else (),
    )


def _json_fact_multiset(obj: dict, universe: tuple[OpRecord, ...]) -> list:
    """Every fact across every cell, as (op_identity, backend, identity_tuple)
    tuples — sorted, ready for multiset equality."""
    key_to_member = {(r.family, r.operation_key.name): r for r in universe}
    out: list[tuple] = []
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            op_id = (op_entry["op"]["family"], op_entry["op"]["op"])
            assert op_id in key_to_member, f"unknown op identity in JSON: {op_id}"
            for backend_name, cell in op_entry["cells"].items():
                for bucket in ("constraints", "residue", "routed", "refinements"):
                    for f_dict in cell[bucket]:
                        out.append((op_id, backend_name, _json_fact_identity(f_dict)))
    return sorted(out)


def _model_fact_multiset(report: CoverageReport) -> list:
    """Mirror of _json_fact_multiset over the live CoverageReport."""
    out: list[tuple] = []
    for fam in report.families:
        for oc in fam.ops:
            for bucket in (oc.constraints, oc.residue, oc.routed, oc.refinements):
                for f in bucket:
                    out.append(
                        (
                            (type(f.operation_key).__name__, f.operation_key.name),
                            f.backend.value,
                            fact_sort_key(f),
                        )
                    )
    return sorted(out)


def test_committed_json_matches_live_model(inputs, report):
    """The committed JSON recovers the report's complete live-model projection."""
    json_path = next(p for p, r in _ARTIFACT_RENDERERS if r is render_json)
    committed = (_REPO_ROOT / json_path).read_text(encoding="utf-8")
    obj = json.loads(committed)

    # 1. Op universe: every (family, op) in the JSON == universe in the model.
    universe = inputs["universe"]
    expected_ops = {(r.family, r.operation_key.name) for r in universe}
    actual_ops: set[tuple[str, str]] = set()
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            actual_ops.add((op_entry["op"]["family"], op_entry["op"]["op"]))
    assert actual_ops == expected_ops, (
        f"op universe drift between committed JSON and live registry: "
        f"missing={sorted(expected_ops - actual_ops)} "
        f"extra={sorted(actual_ops - expected_ops)}"
    )

    # 2. Counts.
    assert len(obj["segments"]) == len(report.segments)
    assert len(obj["divergences"]) == len(report.divergences)
    assert obj["gaps"] is None  # Package-only reporting did not request guard inventories.
    assert len(obj["changes"]) == len(report.changes)

    # 3. Per-backend stats — by_impl re-keyed to tuples must equal the model.
    for b in RENDERED_BACKENDS:
        b_stats = obj["stats"]["backends"][b.value]
        for s in ImplState:
            assert b_stats["by_impl"][s.value] == report.stats.by_impl[(b, s)], (
                f"by_impl[{b.value},{s.value}] JSON vs model mismatch: "
                f"json={b_stats['by_impl'][s.value]} model={report.stats.by_impl[(b, s)]}"
            )
        assert b_stats["default_capable"] == report.stats.default_capable[b]
        assert b_stats["audited_clean"] == report.stats.audited_clean[b]
        assert b_stats["constrained"] == report.stats.constrained[b]
        assert b_stats["audited_unknown"] == report.stats.audited_unknown[b]
    assert obj["stats"]["ops_total"] == report.stats.ops_total
    assert obj["stats"]["facts_total"] == report.stats.facts_total
    assert obj["stats"]["contradictions"] == report.stats.contradictions

    # 4. Fact multiset — equal to the model after sorting.
    assert _json_fact_multiset(obj, universe) == _model_fact_multiset(report), (
        "fact multiset drift between committed JSON and live registry model"
    )

    # 5. JSON's `render_json` of the live model is byte-equal to the
    # committed file (defense-in-depth — the parametrize drift gate asserts
    # the same property, but pinning it here keeps the invariant self-contained).
    assert committed == render_json(report)


def test_universe_partition_exact(inputs, report):
    from collections import Counter

    scattered = Counter((oc.op.family, oc.op.operation_key.name) for fam in report.families for oc in fam.ops)
    expected = Counter({(r.family, r.operation_key.name): 3 for r in inputs["universe"]})
    assert scattered == expected, "universe not partitioned exactly across families×backends"


def test_every_fact_bucketed_exactly_once(inputs, report):
    from collections import Counter

    scattered = Counter(id(f) for fam in report.families for oc in fam.ops for f in oc.all_facts)
    original = Counter(id(f) for f in inputs["facts"])
    assert scattered == original


def test_segments_rendered_exactly_once(inputs, report):
    report_modules = [segment.module for segment in report.segments]
    input_modules = [segment.module for segment in inputs["segments"]]
    assert report_modules == sorted(input_modules)

    doc = render_markdown(report)
    active_body = doc.split("### Active segments", 1)[1].split("\n## ", 1)[0]
    rows = [
        line
        for line in active_body.splitlines()
        if line.startswith("|") and "---" not in line and not line.startswith("| Module")
    ]
    assert len(rows) == len(report.segments)
    for segment in report.segments:
        assert any(segment.module in row for row in rows)


def test_gaps_and_changes_rendered_exactly_once(report):
    doc = render_markdown(report)
    for heading, records in (
        ("## Known gaps", report.gaps),
        ("## Assertion change history", report.changes),
    ):
        body = doc.split(heading, 1)[1].split("\n## ", 1)[0]
        rows = [ln for ln in body.splitlines() if ln.startswith("|") and "---" not in ln]
        expected = len(records) + 1 if records else 0
        assert len(rows) == expected


def test_divergence_operation_keys_within_universe(inputs, report):
    universe_keys = {r.operation_key for r in inputs["universe"]}
    for dv in report.divergences:
        for k in dv.operation_keys:
            assert k in universe_keys, f"divergence {dv.id} references unknown op {k!r}"


def test_unaudited_never_renders_audit_badge(report):
    """No op without an applicable segment renders the `audited` badge in its
    cell. The default-capable mark `✓` requires implementation, never mere
    absence of facts."""
    doc = render_markdown(report)
    matrix = _matrix_body(doc)
    for fam in report.families:
        if fam.audit_domain is None:
            continue  # unmapped families render in their own section
        for oc in fam.ops:
            if not oc.segments:
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
    """Every audited scope resolves to a visible implementation record."""
    for b in RENDERED_BACKENDS:
        n = report.stats.audited_unknown[b]
        assert n == 0, (
            f"audited_unknown == {n} on {b.value}; a segment covers ops "
            f"the impl-axis cannot resolve — investigate the segment scope"
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


# ---------------------------------------------------------------------------
# PYTHONHASHSEED byte-identity test (spec §4.4 M-6 / M-7 / plan-review I2):
# determinism rests on insertion order — every dict populated by iterating
# already-sorted sequences, no set iteration. PYTHONHASHSEED controls
# CPython's set/dict iteration order, so two seeds byte-equal means the
# build is order-stable across hash randomization. The test spawns two
# subprocesses (one per seed) that each render the JSON to stdout; the
# captured bytes must be equal. `main()` keeps its fixed artifact paths
# (no --out-dir flag) — the committed artifacts are never touched.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("renderer", ["render_json", "render_scoped"])
def test_artifact_byte_identity_under_hash_seed(renderer):
    """Artifact bytes must not depend on Python set iteration order."""
    driver = (
        "import sys; "
        "from mountainash.core.capabilities.render_markdown import "
        f"gather_coverage_inputs, {renderer}; "
        "from mountainash.core.capabilities.coverage import build_coverage_report; "
        f"sys.stdout.write({renderer}(build_coverage_report(**gather_coverage_inputs())))"
    )
    captured: list[bytes] = []
    for seed in ("0", "1"):
        result = subprocess.run(
            [sys.executable, "-c", driver],
            env={**os.environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            check=True,
            timeout=300,
        )
        assert not result.stderr, (
            f"PYTHONHASHSEED={seed} subprocess emitted stderr: {result.stderr.decode('utf-8', errors='replace')}"
        )
        captured.append(result.stdout)
    assert captured[0] == captured[1], (
        f"JSON output differs between PYTHONHASHSEED=0 and PYTHONHASHSEED=1 "
        f"({len(captured[0])} vs {len(captured[1])} bytes); set-iteration "
        f"nondeterminism leaked into the build (spec §4.4 M-6)"
    )
