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
)

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
    assert committed == renderer(report), (
        f"{rel_path} is stale; regenerate with: {_REGEN_CMD}"
    )


# ---------------------------------------------------------------------------
# JSON-completeness invariant (spec §4.5 / §4.6): parsing the committed
# `expression-coverage.json` recovers the fact multiset, op universe,
# declaration/divergence/gap/retirement counts, and per-backend stats equal
# to the live-registry model. Identity-based, not string-match.
# ---------------------------------------------------------------------------


def _json_fact_identity(f_dict: dict) -> tuple:
    """The §4.4 fact identity (minus operation_key / backend, which the JSON
    carries on the cell) rebuilt from a JSON fact dict. Mirrors `fact_sort_key`'s
    field order so the multiset comparison is total over the same lexicographic
    key. Strings are kept (not enum-typed) because the JSON form is wire-only."""
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
        (),  # predicate term — empty for synthetic facts (none carry a predicate)
    )


def _json_fact_multiset(
    obj: dict, universe: tuple[OpRecord, ...]
) -> list:
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
                    out.append((
                        (type(f.operation_key).__name__, f.operation_key.name),
                        f.backend.value,
                        fact_sort_key(f),
                    ))
    return sorted(out)


def test_json_completeness(report, inputs):
    """Spec §4.5 / §4.6: parsing the committed `expression-coverage.json`
    recovers the full model — fact multiset (identity-based), op universe,
    declaration/divergence/gap/retirement counts, and per-backend stats equal
    to the live-registry model. A committed JSON that is byte-equal to the
    regen but missing a fact here would mean the renderer silently dropped
    a row — this invariant closes that gap."""
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
    assert len(obj["declarations"]) == len(report.declarations)
    assert len(obj["divergences"]) == len(report.divergences)
    assert len(obj["gaps"]) == len(report.gaps)
    assert len(obj["retired"]) == len(report.retired)

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
    from mountainash.core.capabilities.coverage import _declaration_identity

    # plan-review C1: build_coverage_report canonicalizes each declaration's
    # .facts via dataclasses.replace, so report.declarations is a multiset of
    # NEW objects — id() comparison no longer holds by design. Compare by
    # the canonical _declaration_identity tuple (spec §4.4 evidence-keyed
    # identity: backend, source, domain, probe_date, library_versions, fixtures).
    report_keys = sorted(
        _declaration_identity(d) for d in report.declarations
    )
    input_keys = sorted(
        _declaration_identity(d) for d in inputs["declarations"]
    )
    assert report_keys == input_keys
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


def test_json_byte_identity_under_hash_seed():
    """Plan-review I2: two-process PYTHONHASHSEED byte-identity check on
    the JSON output. Each subprocess runs the full
    gather_coverage_inputs → build_coverage_report → render_json pipeline
    to stdout; the test asserts the two stdout captures are byte-equal."""
    driver = (
        "import sys; "
        "from mountainash.core.capabilities.render_markdown import "
        "gather_coverage_inputs, render_json; "
        "from mountainash.core.capabilities.coverage import build_coverage_report; "
        "sys.stdout.write(render_json(build_coverage_report(**gather_coverage_inputs())))"
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
            f"PYTHONHASHSEED={seed} subprocess emitted stderr: "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )
        captured.append(result.stdout)
    assert captured[0] == captured[1], (
        f"JSON output differs between PYTHONHASHSEED=0 and PYTHONHASHSEED=1 "
        f"({len(captured[0])} vs {len(captured[1])} bytes); set-iteration "
        f"nondeterminism leaked into the build (spec §4.4 M-6)"
    )
