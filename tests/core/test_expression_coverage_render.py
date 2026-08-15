"""Renderer tests over synthetic reports — determinism, cells, collapse."""
from __future__ import annotations

import builtins
import enum as _enum
import json

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    CoverageReport,
    ImplState,
    ImplementationRecord,
    OpRecord,
    build_coverage_report,
    fact_sort_key,
)
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration, Domain, FactSource, ProbeEvidence,
)
from mountainash.core.capabilities.render_markdown import (
    _collapse_groups,
    _fact_detail_row,
    _resolve_concrete_owner,
    gather_coverage_inputs,
    gather_implementation_records,
    render_json,
    render_markdown,
    render_scoped,
)
from mountainash.core.capabilities.retired import RetiredFact
from mountainash.core.capabilities.schema import (
    Boundary, CapabilityFact, CapabilityLevel, DivergenceFact, DivergenceKind,
    Enforcement, GapKind, KnownGap, WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND


class FKEY_SUBSTRAIT_SYNTH_SET(_enum.Enum):
    OP_A = _enum.auto()
    OP_B = _enum.auto()


# _impls, _fact, _decl, _universe: copy the Task 1 helper bodies verbatim here.
# Plan mandates duplication — test modules do not import from each other.


def _fact(**kw) -> CapabilityFact:
    base = dict(
        operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="synthetic",
        since="2026-08-01",
    )
    base.update(kw)
    return CapabilityFact(**base)


def _decl(backend=CONST_BACKEND.POLARS, facts=()):
    return CapabilityDeclaration(
        backend=backend, domain=Domain.SET, source=FactSource.SUBSTRAIT,
        facts=tuple(facts),
        evidence=ProbeEvidence(probe_date="2026-08-01",
                               library_versions=(("polars", "1.35.1"),),
                               fixtures=("synthetic",)),
    )


def _universe():
    return tuple(
        OpRecord(m, type(m).__name__) for m in FKEY_SUBSTRAIT_SYNTH_SET
    )


def _impls(state=ImplState.IMPLEMENTED, overrides=None):
    """One record per (universe op × RENDERED_BACKENDS); overrides is a
    dict keyed by (op, backend) -> ImplState that replaces per-cell."""
    if overrides is None:
        overrides = {}
    records = []
    for r in _universe():
        for b in RENDERED_BACKENDS:
            cell_state = overrides.get((r.operation_key, b), state)
            unknown = cell_state is ImplState.UNKNOWN
            records.append(ImplementationRecord(
                r.operation_key, b, cell_state,
                None if unknown else "synthetic",
                None if unknown else "SyntheticProtocol",
            ))
    return tuple(records)


def _report(facts=(), decls=None, impls=None, **kw):
    if decls is None:
        decls = (_decl(facts=tuple(facts)),) if facts else ()
    if impls is None:
        impls = _impls()
    return build_coverage_report(
        _universe(), tuple(facts), tuple(decls),
        kw.get("divergences", ()), kw.get("gaps", ()), kw.get("retired", ()),
        impls,
    )


def test_render_is_deterministic_under_input_shuffle():
    """Spec §4.4: input order does not affect output bytes (review M-6: every
    dict populated by iterating already-sorted sequences; no set iteration).
    Plan-review M-1: all THREE renderers (markdown, scoped, JSON) are
    pinned under input shuffle — the multi-artifact split is the load-bearing
    property, and a determinism regression in render_scoped / render_json
    would otherwise be invisible (the model-level shuffle test covers the
    model, this one covers the renderers end-to-end)."""
    fs = [
        _fact(param="a", option_value=v, level=CapabilityLevel.UNSUPPORTED)
        for v in ("x", "y", "z")
    ] + [_fact(param="b", dialect="duckdb", level=CapabilityLevel.LITERAL_ONLY)]
    decl = _decl(facts=tuple(fs))
    impls = _impls()
    impls_rev = tuple(reversed(impls))
    # Build the three baselines (facts in given order, impls in given order).
    base = build_coverage_report(_universe(), tuple(fs), (decl,), (), (), (), impls)
    # Three shuffled builds covering both axes: fact order and impl order.
    fs_rev = tuple(reversed(fs))
    build_facts_rev = lambda: build_coverage_report(  # noqa: E731
        _universe(), fs_rev, (decl,), (), (), (), impls)
    build_impls_rev = lambda: build_coverage_report(  # noqa: E731
        _universe(), tuple(fs), (decl,), (), (), (), impls_rev)
    build_both_rev = lambda: build_coverage_report(  # noqa: E731
        _universe(), fs_rev, (decl,), (), (), (), impls_rev)
    # All three renderers under all four input orderings.
    for renderer in (render_markdown, render_scoped, render_json):
        baseline = renderer(base)
        for builder in (build_facts_rev, build_impls_rev, build_both_rev):
            assert renderer(builder()) == baseline, (
                f"{renderer.__name__} output drift under input shuffle"
            )


def test_cell_texts():
    # Constrained composition (whole_op + scoped) — UNCHANGED across rev 5.
    whole = _fact(level=CapabilityLevel.POLYMORPHIC)
    scoped = _fact(param="values", option_value="strict",
                   level=CapabilityLevel.UNSUPPORTED)
    out = render_markdown(_report([whole, scoped]))
    assert "poly + ◐ partial (1 params, 1 option-selectors, 0 value-classes, 0 dialects)" in out

    # Clean default-capable (IMPLEMENTED + clean + no audit) -> `✓` (U+2713).
    clean = render_markdown(_report([], decls=(), impls=_impls()))
    assert "| ✓ |" in clean
    assert " audited" not in clean.split("## Per-family coverage", 1)[1].split(
        "## Unmapped families", 1)[0]

    # NOT_IMPLEMENTED + no facts + no audit -> `—` (only true blank).
    empty = render_markdown(_report(
        [], decls=(), impls=_impls(state=ImplState.NOT_IMPLEMENTED)))
    matrix = empty.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert "| — |" in matrix
    assert "⚠ contradiction" not in matrix

    # UNKNOWN -> `?` (no glyph change, no annotations).
    unknown = render_markdown(_report(
        [], decls=(), impls=_impls(state=ImplState.UNKNOWN)))
    assert "| ? |" in unknown


def test_handler_cell_uses_glyph():
    # IMPLEMENTED_VIA_HANDLER (clean, no audit) -> `✓ᴴ` (the ᴴ footnote).
    handler_impls = _impls(state=ImplState.IMPLEMENTED_VIA_HANDLER)
    out = render_markdown(_report([], decls=(), impls=handler_impls))
    assert "✓ᴴ" in out
    # Bare `✓` (without the ᴴ superscript) must not appear as a cell mark for
    # these synthetic cells — the handler glyph is the only clean mark.
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    for line in matrix.splitlines():
        if line.startswith("| `") and ("OP_A" in line or "OP_B" in line):
            assert "✓ᴴ" in line, f"expected handler glyph in row: {line!r}"
            assert " audited" not in line

    # IMPLEMENTED_VIA_HANDLER + audited -> `✓ᴴ audited`.
    out_audited = render_markdown(_report(
        [], decls=(_decl(),), impls=handler_impls))
    assert "✓ᴴ audited" in out_audited


def test_handler_cell_with_constraining_fact_renders_composition_not_glyph():
    # Spec §3.3: the `if oc.constrained` branch precedes the handler-glyph
    # branch in _cell_text, so a handler-dispatched cell that ALSO carries a
    # constraining whole-op GATE fact renders the constrained composition, NOT
    # the clean `✓ᴴ`. The live registry has no such cell (the three handler ops
    # are fact-free), so only a synthetic universe exercises the path (M-5).
    gates = [_fact(level=CapabilityLevel.UNSUPPORTED, backend=b)
             for b in RENDERED_BACKENDS]
    decls = tuple(_decl(backend=b, facts=(g,))
                  for b, g in zip(RENDERED_BACKENDS, gates))
    out = render_markdown(_report(
        gates, decls=decls,
        impls=_impls(state=ImplState.IMPLEMENTED_VIA_HANDLER)))
    matrix = out.split("## Per-family coverage", 1)[1].split(
        "## Unmapped families", 1)[0]
    op_a_rows = [ln for ln in matrix.splitlines()
                 if ln.startswith("| `") and "OP_A" in ln]
    assert op_a_rows, matrix
    row = op_a_rows[0]
    assert "✗ unsupported" in row   # constrained composition rendered
    assert "✓ᴴ" not in row           # NOT the clean handler glyph
    # OP_B carries no fact, so its handler cells still render `✓ᴴ` (control).
    op_b_rows = [ln for ln in matrix.splitlines()
                 if ln.startswith("| `") and "OP_B" in ln]
    assert op_b_rows and "✓ᴴ" in op_b_rows[0]


def test_contradiction_cell_renders_loudly():
    # NOT_IMPLEMENTED + constraining fact + applicable declaration -> contradiction.
    f = _fact(param="values", dialect="duckdb", level=CapabilityLevel.UNSUPPORTED)
    impls = _impls(overrides={
        (FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED,
    })
    out = render_markdown(_report([f], decls=(_decl(facts=(f,)),), impls=impls))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    # The cell renders the loud marker, not `—`.
    assert "⚠ contradiction" in matrix
    # And the summary section renders the count even when > 0.
    assert "contradictions: 1" in out

    # NOT_IMPLEMENTED + declaration only (no facts) is also a contradiction.
    out_decl_only = render_markdown(_report(
        [], decls=(_decl(),), impls=impls))
    assert "⚠ contradiction" in out_decl_only
    assert "contradictions: 1" in out_decl_only


def test_unknown_cell_never_carries_audited_badge():
    # Audited is stored on UNKNOWN cells (the field is not dead state), but
    # it must NEVER be rendered on the `?` cell (spec §3.3, legend says so).
    impls = _impls(state=ImplState.UNKNOWN)
    out = render_markdown(_report([], decls=(_decl(),), impls=impls))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    # Every matrix row containing `?` must not contain `audited`.
    for line in matrix.splitlines():
        if line.startswith("| `") and "?" in line:
            assert " audited" not in line, (
                f"unknown cell leaked audited badge: {line!r}")
    # The audited_unknown stat IS rendered (symmetric with contradictions).
    assert "audited_unknown: 2" in out  # both ops on POLARS


def test_unaudited_cell_never_renders_audit_badge():
    # With no declarations at all, no cell in the matrix may carry the
    # `audited` badge — the only mark is the unaudited `✓`.
    out = render_markdown(_report([], decls=(), impls=_impls()))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert " audited" not in matrix
    # And the U+2705 green-tick glyph is RETIRED — the marker is U+2713 only.
    assert "✓" in matrix
    assert "✅" not in out


def test_char_point_glyph_reconciliation():
    # Byte-level drift the eye cannot see: U+2713 (light check) is the only
    # success marker, U+2705 (green check) is RETIRED.
    out = render_markdown(_report([]))
    assert "\u2713" in out
    assert "\u2705" not in out
    # And the retired string literals `DECLARED_CLEAN` / `UNDECLARED` are gone.
    assert "DECLARED_CLEAN" not in out
    assert "UNDECLARED" not in out


def test_residue_and_routed_annotations():
    residue = _fact(param="v", enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE,
                    level=CapabilityLevel.UNSUPPORTED, native_errors=(ValueError,))
    routed = _fact(operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_B, param="v",
                   enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    out = render_markdown(_report([residue, routed]))
    assert "⚠ runtime" in out
    assert "↻ routed" in out
    # Routed alone stays clean — base mark is the light `✓` (U+2713), not
    # the retired `✅` (U+2705).
    assert "✓ ↻ routed" in out


def test_refinement_annotation_lists_dialects():
    refinement = _fact(param="v", dialect="duckdb",
                       level=CapabilityLevel.EXPR_CAPABLE)
    out = render_markdown(_report([refinement]))
    # Refinement alone stays clean (no constraining facts) — base mark `✓`,
    # then the audited badge (the declaration applies to the family), then
    # the `✓ dialect-verified: …` annotation listing the dialects.
    assert "✓ audited ✓ dialect-verified: duckdb" in out


def test_undeclared_never_renders_clean_marker():
    # No declarations at all -> no `audited` badge anywhere in matrix rows.
    out = render_markdown(_report([], decls=()))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert " audited" not in matrix


def test_summary_per_backend_table_consistency():
    # Mixed report: the summary must show the per-backend counts that sum to
    # ops_total (the per-backend sum law, spec §4.5) and the invariant lines
    # (rendered even when 0 — both invariants visible per spec §3.3 / §4.1).
    residue = _fact(param="v", enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE,
                    level=CapabilityLevel.UNSUPPORTED, native_errors=(ValueError,))
    routed = _fact(operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_B, param="v",
                   enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    overrides = {
        (FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED,
        (FKEY_SUBSTRAIT_SYNTH_SET.OP_B, CONST_BACKEND.POLARS): ImplState.UNKNOWN,
    }
    impls = _impls(overrides=overrides)
    out = render_markdown(_report([residue, routed], decls=(_decl(facts=(residue, routed)),), impls=impls))
    # Per-backend columns: default_capable / audited_clean / constrained / NOT_IMPLEMENTED / UNKNOWN / ops_total.
    assert "| Backend | default_capable | audited_clean | constrained | NOT_IMPLEMENTED | UNKNOWN | ops_total |" in out
    # Setup creates: OP_A×POLARS = NOT_IMPLEMENTED + constraining fact = 1 contradiction.
    # OP_B×POLARS = UNKNOWN + applicable declaration = 1 audited_unknown.
    assert "contradictions: 1" in out
    assert "audited_unknown: 1" in out

    # And the 0-case: an empty report renders BOTH invariant lines too
    # (the symmetic-rendering rule, spec §3.3 / §4.1).
    empty_out = render_markdown(_report([]))
    assert "contradictions: 0" in empty_out
    assert "audited_unknown: 0" in empty_out
    # Sum law visible: per-row count columns add up to ops_total.
    assert "polars" in empty_out and "narwhals" in empty_out and "ibis" in empty_out


def test_option_collapse_rule():
    same = [_fact(param="fmt", option_value=v, level=CapabilityLevel.UNSUPPORTED)
            for v in ("a", "b", "c")]
    groups = _collapse_groups(tuple(same))
    assert len(groups) == 1 and groups[0][1] == ["a", "b", "c"]

    two = _collapse_groups(tuple(same[:2]))
    assert len(two) == 2  # <3 renders per-fact

    split = same[:2] + [_fact(param="fmt", option_value="c",
                              message="different", level=CapabilityLevel.UNSUPPORTED)]
    assert len(_collapse_groups(tuple(split))) == 3  # metadata splits groups

    # Mixed group: a value-agnostic fact sharing the remaining identity blocks
    # collapse — all four render per-fact (the defined handling, Task 4 code).
    mixed = same + [_fact(param="fmt", level=CapabilityLevel.UNSUPPORTED)]
    assert len(_collapse_groups(tuple(mixed))) == 4


def test_legend_has_by_exception_rows_and_footnotes():
    out = render_markdown(_report([]))
    # The §3.3 render-map rows in prose (by-exception epistemics).
    for token in ("`✓`", "`—`", "`⚠ contradiction`", "`?`"):
        assert token in out, f"legend missing row for {token}"
    # Audit-badge inference-limit sentence retained verbatim.
    assert "domain-wave-level evidence" in out
    assert "not proof the specific op was exercised" in out
    # ᴴ footnote.
    assert "ᴴ" in out
    # ? footnote incl. "audited is stored but not rendered on `?` cells".
    assert "audited is stored but not rendered on `?` cells" in out


def test_unmapped_families_stamp_impl_summary():
    # Uses the live report. While unmapped families (audit_domain is None) exist,
    # assert the §3.6 stamp line format. When a future release maps every family,
    # _unmapped_families() emits no section at all — then the correct expectation
    # is the section's ABSENCE, not a stamp match. Branching here makes the
    # "every family mapped" day a passing test rather than a misleading regex
    # miss (T3 review: live-registry fragility, recorded as a dated expectation).
    inputs = gather_coverage_inputs()
    report = build_coverage_report(
        inputs["universe"],
        inputs["facts"],
        inputs["declarations"],
        inputs["divergences"],
        inputs["gaps"],
        inputs["retired"],
        inputs["implementations"],
    )
    out = render_markdown(report)
    if not any(f.audit_domain is None for f in report.families):
        assert "## Unmapped families" not in out
        return
    # The stamp format: "N ops — all implemented on 3/3 backends" or a
    # per-backend split when not uniform: "M/N polars · M/N narwhals · M/N ibis"
    # (render_markdown uses the ops count as denominator - final-review M-2).
    import re
    assert re.search(r"\d+ ops — (all implemented on 3/3 backends|"
                     r"\d+/\d+ polars · .*narwhals · .*ibis)", out), (
        f"unmapped stamp line missing or malformed: {out!r}")


def test_header_includes_implementation_record_count():
    out = render_markdown(_report([]))
    # Pinned label `· Implementation records: {N}` where N is the sum of
    # by_impl.values() across the three backends (2 ops × 3 backends = 6).
    assert "· Implementation records: 6" in out


def test_nonempty_gaps_divergences_retirements_render():
    dv = DivergenceFact(
        id="SY-TEST-01", kind=DivergenceKind.SEMANTICS,
        operation_keys=(FKEY_SUBSTRAIT_SYNTH_SET.OP_A,), backends=("polars",),
        summary="synthetic summary", impact="synthetic impact",
        workaround="synthetic workaround", since="2026-08-01",
    )
    keyless = DivergenceFact(
        id="SY-TEST-02", kind=DivergenceKind.PRECISION,
        operation_keys=(), backends=("ibis",),
        summary="keyless divergence", impact="none", since="2026-08-01",
    )
    gap = KnownGap(gap_kind=GapKind.UNTESTED_OPTION,
                   reason="synthetic gap reason", since="2026-08-01")
    ret = RetiredFact(
        operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_B, param="values",
        backend=CONST_BACKEND.POLARS, dialect=None, option_value=None,
        value_class=None, level=CapabilityLevel.UNSUPPORTED,
        since="2026-07-01", retired_on="2026-08-01",
        fixed_in_versions=(("polars", "1.36.0"),), upstream_ref=None,
        note="synthetic retirement",
    )
    out = render_markdown(_report(
        [], decls=(_decl(),), divergences=(dv, keyless), gaps=(gap,), retired=(ret,)))
    assert out.count("SY-TEST-01") == 1 and out.count("SY-TEST-02") == 1
    assert out.count("synthetic gap reason") == 1
    assert "2027-01-31" in out          # 2026-08-01 + 183 days: review_due from data
    assert out.count("synthetic retirement") == 1 and "polars 1.36.0" in out


def test_detail_section_written_for_every_cell_with_facts():
    # Rev 6 partition: a routed fact with a non-wildcard param is scoped
    # (param != WILDCARD_PARAM, so `is_whole_op` is False), so its detail
    # row lives in `render_scoped`, not the main doc. The spec's "every
    # cell with facts gets a detail row" rule is preserved across the
    # two artifacts (the partition-exactness invariant, §4.5 M-3).
    routed = _fact(param="v", enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    main = render_markdown(_report([routed]))
    scoped = render_scoped(_report([routed]))
    main_detail = main.split("## Per-op detail", 1)[1]
    assert "### `OP_A` × polars" not in main_detail
    assert "### `OP_A` × polars" in scoped
    assert "router_metadata" in scoped


# ---------------------------------------------------------------------------
# Task 2 — Derivation tests (spec §3.6).
# The renderer itself is Task 3; the pre-existing tests above fail on the
# Task-3 NotImplementedError stubs by design. Run only this section by node id.
# ---------------------------------------------------------------------------

class TestDerivation:
    """gather_implementation_records() + _resolve_concrete_owner() — spec §3.6."""

    def test_live_derivation_shape_and_counts(self):
        """Cardinality + per-state tallies against the real registries (spec §3.6
        empirical baseline + the rev-5 universe)."""
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL,
        )

        universe = gather_coverage_inputs()["universe"]
        recs = gather_implementation_records(universe)
        assert len(recs) == len(universe) * 3
        assert sum(1 for r in recs if r.state is ImplState.UNKNOWN) == 0
        assert sum(1 for r in recs if r.state is ImplState.NOT_IMPLEMENTED) == 0

        handler_ops = {RKEY_MOUNTAINASH_REL.SOURCE, RKEY_MOUNTAINASH_REL.REF,
                       RKEY_MOUNTAINASH_REL.CONFORM}
        hv = [r for r in recs if r.state is ImplState.IMPLEMENTED_VIA_HANDLER]
        assert len(hv) == 9
        assert {r.operation_key for r in hv} == handler_ops
        for r in hv:
            assert r.backend in {CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS,
                                 CONST_BACKEND.IBIS}

    def test_rank_sharing_ops_all_implemented_with_method_rank(self):
        """Three ops share `protocol_method = ...rank`; name-based dispatch
        (review M-4) means they all IMPLEMENT with method_name == 'rank'."""
        from mountainash.expressions.core.expression_system.function_keys.enums import (
            FKEY_MOUNTAINASH_WINDOW,
            SUBSTRAIT_ARITHMETIC_WINDOW,
        )

        recs = gather_implementation_records(gather_coverage_inputs()["universe"])
        rank_ops = {SUBSTRAIT_ARITHMETIC_WINDOW.RANK,
                    FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE,
                    FKEY_MOUNTAINASH_WINDOW.RANK_MAX}
        for op in rank_ops:
            matches = [r for r in recs if r.operation_key is op]
            assert len(matches) == 3
            for r in matches:
                assert r.state is ImplState.IMPLEMENTED
                assert r.method_name == "rank"

    def test_via_handler_provenance_locked_to_handler(self):
        """Every IMPLEMENTED_VIA_HANDLER record has protocol_name == 'handler'
        and method_name containing 'visit_' (the documented literal — Task 1
        test would have caught any drift here)."""
        recs = gather_implementation_records(gather_coverage_inputs()["universe"])
        for r in recs:
            if r.state is ImplState.IMPLEMENTED_VIA_HANDLER:
                assert r.protocol_name == "handler"
                assert "visit_" in (r.method_name or "")

    def test_resolve_concrete_owner_skips_protocol_stubs(self):
        """Spec §3.6 / review C-2: a bare Protocol subclass is a stub carrier,
        not an implementation. _resolve_concrete_owner returns None for the
        bare stub and the concrete class for a real override."""
        from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_arithmetic import (
            SubstraitScalarArithmeticExpressionSystemProtocol,
        )

        class _StubOnly(SubstraitScalarArithmeticExpressionSystemProtocol):
            pass

        assert _resolve_concrete_owner(_StubOnly, "add") is None

        class _Concrete(_StubOnly):
            def add(self, left, right):  # type: ignore[override]
                return left + right

        assert _resolve_concrete_owner(_Concrete, "add") is _Concrete

    def test_resolve_concrete_owner_returns_none_when_absent(self):
        class _Empty:
            pass

        assert _resolve_concrete_owner(_Empty, "no_such_method") is None


# ---------------------------------------------------------------------------
# Task 2 — JSON renderer (spec §4.6).
# Pure-function tests over synthetic universes: shape lock, round-trip,
# no-collapse, null-vs-empty. No registry calls; the model is the source of
# truth and `render_json` is the only function under test here.
# ---------------------------------------------------------------------------


_TOP_LEVEL_KEYS = [
    "stamp", "stats", "families", "declarations",
    "divergences", "gaps", "retired",
]

_CELL_KEYS = {
    "impl", "impl_method", "impl_protocol", "audited", "whole_op",
    "constrained", "contradiction", "selector_counts",
    "constraints", "residue", "routed", "refinements",
}


def _json_fact_semantic_identity(f_dict: dict) -> tuple:
    """Build the same identity tuple as `fact_sort_key` from a JSON fact dict.

    The JSON's `<fact>` object omits the operation_key (it's implicit on the
    cell / declaration entry), so this is the §4.4 fact identity minus
    operation_key and backend — enough to verify order equality with the
    model's canonicalized `.facts` (review I-3) since every fact in a single
    declaration shares the same operation_key."""
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


def _json_fact_multiset(obj: dict, universe: tuple[OpRecord, ...]) -> list:
    """Every fact across every cell, as (op_identity, backend, fact_sort_key) tuples."""
    key_to_member = {(r.family, r.operation_key.name): r for r in universe}
    out: list[tuple] = []
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            op_id = (op_entry["op"]["family"], op_entry["op"]["op"])
            assert op_id in key_to_member, f"unknown op identity in JSON: {op_id}"
            for backend_name, cell in op_entry["cells"].items():
                for bucket in ("constraints", "residue", "routed", "refinements"):
                    for f_dict in cell[bucket]:
                        out.append((op_id, backend_name,
                                    _json_fact_semantic_identity(f_dict)))
    return sorted(out)


def _model_fact_multiset(report: CoverageReport) -> list:
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


def test_json_shape_lock():
    """Spec §4.6: 7 top-level keys in spec order; cell keys exact;
    stats.backends.<backend>.by_impl nested per-backend and ImplState-.value-keyed
    (plan-review C3 — the model's tuple-keyed Mapping has no legal JSON key
    form); enum .value everywhere; ISO date strings; declarations carry a
    facts array; null vs [] distinction for option_value vs native_errors."""
    # Build a non-trivial report so the structure exercises every shape.
    fs = [
        _fact(param="a", option_value=v, level=CapabilityLevel.UNSUPPORTED)
        for v in ("x", "y", "z")
    ] + [_fact(param="b", dialect="duckdb", level=CapabilityLevel.LITERAL_ONLY)]
    decl = _decl(facts=tuple(fs))
    impls = _impls()
    out = render_json(build_coverage_report(
        _universe(), tuple(fs), (decl,), (), (), (), impls))
    obj = json.loads(out)

    # Top-level keys in spec order.
    assert list(obj.keys()) == _TOP_LEVEL_KEYS

    # Stamp counts (no timestamps per spec §4.4).
    assert set(obj["stamp"].keys()) == {
        "declarations", "facts", "operations", "implementation_records",
    }
    assert all(isinstance(obj["stamp"][k], int) for k in obj["stamp"])

    # Stats structure: per-backend nested with by_impl keyed by ImplState .value.
    stats = obj["stats"]
    assert set(stats["backends"].keys()) == {b.value for b in RENDERED_BACKENDS}
    impl_state_values = {s.value for s in ImplState}
    for b_name, b_stats in stats["backends"].items():
        assert set(b_stats["by_impl"].keys()) == impl_state_values, (
            f"by_impl for {b_name} must be keyed by ImplState .value: "
            f"{set(b_stats['by_impl'].keys())} != {impl_state_values}"
        )
        for k, v in b_stats["by_impl"].items():
            assert isinstance(k, str) and isinstance(v, int)
        for field in ("default_capable", "audited_clean",
                      "constrained", "audited_unknown"):
            assert field in b_stats and isinstance(b_stats[field], int)
    # Top-level stats fields.
    for field in ("contradictions", "ops_total", "facts_total"):
        assert field in stats and isinstance(stats[field], int)
    # facts_by_* are .value-keyed (string keys, int values).
    for k, v in stats["facts_by_level"].items():
        assert isinstance(k, str) and isinstance(v, int)
    for k, v in stats["facts_by_enforcement"].items():
        assert isinstance(k, str) and isinstance(v, int)
    for k, v in stats["facts_by_backend"].items():
        assert isinstance(k, str) and isinstance(v, int)

    # Cell keys (taken from the synthetic fact-decorated cell).
    target_cell = None
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                if cell["constraints"]:
                    target_cell = cell
                    break
            if target_cell:
                break
        if target_cell:
            break
    assert target_cell is not None, "expected at least one constraint cell"
    assert set(target_cell.keys()) == _CELL_KEYS
    # impl is .value; whole_op is .value or null.
    assert target_cell["impl"] in impl_state_values
    assert (target_cell["whole_op"] is None
            or target_cell["whole_op"] in {lv.value for lv in CapabilityLevel})
    # selector_counts shape.
    assert set(target_cell["selector_counts"].keys()) == {
        "params", "option_selectors", "value_classes", "dialects",
    }
    for v in target_cell["selector_counts"].values():
        assert isinstance(v, int)

    # Op keys: two-part {family, op} with string values.
    op_entry = obj["families"][0]["ops"][0]
    assert set(op_entry["op"].keys()) == {"family", "op"}
    assert isinstance(op_entry["op"]["family"], str)
    assert isinstance(op_entry["op"]["op"], str)

    # Family shape.
    fam = obj["families"][0]
    assert set(fam.keys()) == {"family", "source", "domain", "ops"}
    # source/domain are .value or null (unmapped families are None in the model).
    assert fam["source"] is None or isinstance(fam["source"], str)
    assert fam["domain"] is None or isinstance(fam["domain"], str)

    # ISO date strings: every fact's `since` matches the ISO grammar.
    iso_re = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}$")
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                for bucket in ("constraints", "residue", "routed", "refinements"):
                    for f in cell[bucket]:
                        assert iso_re.match(f["since"]), (
                            f"non-ISO since in JSON: {f['since']!r}")

    # Declarations carry a `facts` array (plan-review C2 — this is what makes
    # declarations JSON-recoverable per §4.4 I-3).
    for d in obj["declarations"]:
        assert "facts" in d and isinstance(d["facts"], list)
        for f in d["facts"]:
            assert isinstance(f, dict)
        # evidence is dict-or-null (preserves the absence-of-evidence signal).
        assert d["evidence"] is None or isinstance(d["evidence"], dict)
        if d["evidence"] is not None:
            assert set(d["evidence"].keys()) == {
                "probe_date", "library_versions", "fixtures",
            }
            assert iso_re.match(d["evidence"]["probe_date"])


def test_json_round_trip():
    """Spec §4.6: json.loads(render_json(report)) recovers exact fact multiset
    (identity tuples), op universe, declaration/divergence/gap/retirement
    counts, per-backend stats equal to the model's (by_impl re-keyed to
    tuples), canonicalized declaration .facts order, and builtins-resolved
    native_errors (review I-4)."""
    fs = [
        _fact(param="a", option_value=v, level=CapabilityLevel.UNSUPPORTED)
        for v in ("x", "y", "z")
    ] + [
        _fact(param="b", dialect="duckdb", level=CapabilityLevel.LITERAL_ONLY),
        _fact(param="c", enforcement=Enforcement.MATERIALIZE_RESIDUE,
              boundary=Boundary.MATERIALIZE,
              level=CapabilityLevel.UNSUPPORTED, native_errors=(ValueError,)),
    ]
    # Mix the declaration's fact order with a non-canonical input to prove the
    # canonicalization at ingest (review I-3) is what shows up in JSON.
    decl_facts = tuple(reversed(fs))
    decl = _decl(facts=decl_facts)
    impls = _impls()
    # Add a divergence, gap, and retirement to exercise the count assertions.
    dv = DivergenceFact(
        id="SY-TEST-01", kind=DivergenceKind.SEMANTICS,
        operation_keys=(FKEY_SUBSTRAIT_SYNTH_SET.OP_A,),
        backends=("ibis-duckdb",), summary="s", impact="i",
        workaround="w", since="2026-08-01",
    )
    gap = KnownGap(gap_kind=GapKind.UNTESTED_OPTION,
                   reason="synthetic", since="2026-08-01")
    ret = RetiredFact(
        operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_A, param="values",
        backend=CONST_BACKEND.POLARS, dialect=None, option_value=None,
        value_class=None, level=CapabilityLevel.UNSUPPORTED,
        since="2026-07-01", retired_on="2026-08-01",
        fixed_in_versions=(("polars", "1.36.0"),), upstream_ref=None,
        note="synthetic",
    )
    universe = _universe()
    report = build_coverage_report(
        universe, tuple(fs), (decl,), (dv,), (gap,), (ret,), impls)

    text = render_json(report)
    obj = json.loads(text)

    # 1. Op universe (by family+op name).
    expected_ops = {(r.family, r.operation_key.name) for r in universe}
    actual_ops = set()
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            actual_ops.add((op_entry["op"]["family"], op_entry["op"]["op"]))
    assert actual_ops == expected_ops

    # 2. Counts.
    assert len(obj["declarations"]) == len(report.declarations)
    assert len(obj["divergences"]) == len(report.divergences)
    assert len(obj["gaps"]) == len(report.gaps)
    assert len(obj["retired"]) == len(report.retired)
    # Retired emitted newest-first.
    retired_dates = [r["retired_on"] for r in obj["retired"]]
    assert retired_dates == sorted(retired_dates, reverse=True)

    # 3. Per-backend stats — by_impl re-keyed to tuples must equal the model.
    for b in RENDERED_BACKENDS:
        b_stats = obj["stats"]["backends"][b.value]
        for s in ImplState:
            assert b_stats["by_impl"][s.value] == report.stats.by_impl[(b, s)], (
                f"by_impl[{b.value},{s.value}] round-trip mismatch"
            )
        assert b_stats["default_capable"] == report.stats.default_capable[b]
        assert b_stats["audited_clean"] == report.stats.audited_clean[b]
        assert b_stats["constrained"] == report.stats.constrained[b]
        assert b_stats["audited_unknown"] == report.stats.audited_unknown[b]
    assert obj["stats"]["ops_total"] == report.stats.ops_total
    assert obj["stats"]["facts_total"] == report.stats.facts_total
    assert obj["stats"]["contradictions"] == report.stats.contradictions

    # 4. Fact multiset — equal to the model after sorting.
    assert _json_fact_multiset(obj, universe) == _model_fact_multiset(report)

    # 5. Canonicalized declaration .facts order (review I-3). The input was
    # reversed; the JSON must reflect the canonicalized order.
    assert len(obj["declarations"]) == 1
    json_facts = [_json_fact_semantic_identity(f) for f in obj["declarations"][0]["facts"]]
    model_facts = [fact_sort_key(f) for f in report.declarations[0].facts]
    assert json_facts == model_facts, (
        "declaration .facts order in JSON must match the canonicalized model "
        "order from fact_sort_key (review I-3)")

    # 6. native_errors round-trip via getattr(builtins, name) (review I-4).
    # Every native_errors entry in the JSON must resolve to a builtin exception
    # class — the model's ingest validator guarantees this; the JSON is the
    # wire form a consumer would use to do the same.
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                for bucket in ("constraints", "residue", "routed", "refinements"):
                    for f in cell[bucket]:
                        for name in f["native_errors"]:
                            resolved = getattr(builtins, name)
                            assert isinstance(resolved, type)
                            assert issubclass(resolved, BaseException)
    # The MODEL facts in fact_multiset have at least one native_errors tuple,
    # so the JSON is non-trivially exercising this code path.
    assert any(f.native_errors for fam in report.families
               for oc in fam.ops
               for bucket in (oc.constraints, oc.residue, oc.routed, oc.refinements)
               for f in bucket), "test setup must include a fact with native_errors"


def test_json_no_collapse():
    """A ≥3-option group that the markdown collapses (one row with sorted
    option_value list) appears as ≥3 distinct fact objects in JSON — the
    extract carries every fact row uncollapsed (spec §4.6 note: 'No
    option-collapse in JSON — that is a markdown readability device')."""
    same = [_fact(param="fmt", option_value=v, level=CapabilityLevel.UNSUPPORTED)
            for v in ("a", "b", "c")]
    out = render_json(_report(tuple(same), decls=(_decl(facts=tuple(same)),)))
    obj = json.loads(out)
    # Sanity: the scoped doc (rev 6) collapses these into one row. The
    # main doc has no detail section for them — they are scoped (param
    # is not WILDCARD_PARAM), and the partition sends scoped facts to
    # render_scoped (§4.3).
    scoped = render_scoped(_report(tuple(same), decls=(_decl(facts=tuple(same)),)))
    assert "a, b, c" in scoped  # the collapsed option list appears in the scoped doc
    # The JSON has all three as distinct fact objects with distinct option_value.
    fmt_facts: list[dict] = []
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                fmt_facts.extend(f for f in cell["constraints"] if f["param"] == "fmt")
    assert len(fmt_facts) == 3
    assert sorted(f["option_value"] for f in fmt_facts) == ["a", "b", "c"]
    # And the identity is distinct per row (the model never collapsed).
    identities = {_json_fact_semantic_identity(f) for f in fmt_facts}
    assert len(identities) == 3


def test_json_null_vs_empty():
    """Spec §4.6 serialization conventions: absent optional -> JSON null;
    empty collection -> JSON []. A fact with option_value=None must NOT
    serialize as []; a fact with native_errors=() must NOT serialize as null.
    This is the documented distinction; mixing them up would corrupt
    downstream consumers (e.g. parquet flattening, jq pipelines)."""
    fact = _fact()  # defaults: option_value=None, native_errors=()
    out = render_json(_report([fact]))
    obj = json.loads(out)
    found = False
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                for f in cell["constraints"]:
                    found = True
                    assert f["option_value"] is None, (
                        f"option_value=None must serialize as JSON null, "
                        f"got {f['option_value']!r}")
                    assert f["native_errors"] == [], (
                        f"native_errors=() must serialize as JSON [], "
                        f"got {f['native_errors']!r}")
    assert found, "test setup must produce a constraint cell"

    # Spot-check the parallel convention: empty evidence in a non-default
    # declaration is still serialized as a dict (not null), absent evidence
    # is null. We exercise the latter with a probe_exempt-only declaration.
    exempt = _fact(probe_exempt="synthetic exemption")
    out2 = render_json(_report(
        [exempt],
        decls=(CapabilityDeclaration(
            backend=CONST_BACKEND.POLARS, domain=Domain.SET,
            source=FactSource.SUBSTRAIT, facts=(exempt,),
            evidence=None),),))
    obj2 = json.loads(out2)
    assert obj2["declarations"][0]["evidence"] is None


def test_json_is_deterministic_under_input_shuffle():
    """Spec §4.4: input order does not affect output bytes (review M-6: every
    dict populated by iterating already-sorted sequences; no set iteration).
    The drift gate is a two-process PYTHONHASHSEED byte-identity check on the
    JSON artifact; this single-process test catches the input-shuffle axis."""
    fs = [
        _fact(param="a", option_value=v, level=CapabilityLevel.UNSUPPORTED)
        for v in ("x", "y", "z")
    ] + [_fact(param="b", dialect="duckdb", level=CapabilityLevel.LITERAL_ONLY)]
    decl = _decl(facts=tuple(fs))
    impls = _impls()
    base = build_coverage_report(_universe(), tuple(fs), (decl,), (), (), (), impls)
    out1 = render_json(base)
    out2 = render_json(build_coverage_report(
        _universe(), tuple(reversed(fs)), (decl,), (), (), (), tuple(reversed(impls))))
    assert out1 == out2
    # Also shuffle the declaration's facts (reversed input) — the canonical
    # sort at ingest (review I-3) must keep the output identical.
    decl_rev = _decl(facts=tuple(reversed(fs)))
    out3 = render_json(build_coverage_report(
        _universe(), tuple(fs), (decl_rev,), (), (), (), impls))
    assert out1 == out3


# ---------------------------------------------------------------------------
# Task 3 — Markdown split (spec §4.3 rev 6): render_scoped + main-doc
# partition + I-2b cell naming. The §4.5 M-3 partition-exactness invariant
# is the load-bearing test below; the other tests pin the surface.
# ---------------------------------------------------------------------------


def _cell_section(text: str, op_name: str, backend_value: str) -> str:
    """Slice a markdown artifact at the (op, backend) section header. The
    cell section runs to the next `\n### ` (the next op section) or
    end-of-text — `#### ` subheadings inside the same cell section are
    INCLUDED (e.g. the scoped doc's `Dialect-scoped whole-op` subheading
    lives within the (op, backend) cell)."""
    head = f"### `{op_name}` × {backend_value}"
    if head not in text:
        return ""
    after = text.split(head, 1)[1]
    idx = after.find("\n### ")
    return after[:idx] if idx >= 0 else after


def test_partition_exactness_over_mixed_cell():
    """§4.5 M-3: every input fact's identity appears in exactly one markdown
    artifact's detail body. Synthetic mixed cell: whole-op GATE +
    param UNSUPPORTED + dialect-scoped gate. Function-level goes to main;
    the other two go to scoped. None of the three facts can be collapsed
    (each has option_value=None, so the option-collapse rule doesn't
    apply — but the identity-based assertion would still hold if it did:
    a collapsed row counts each `option_value` fact once). Asserted on
    fact identities (via the rendered row), not row counts."""
    whole_op = _fact(
        param=WILDCARD_PARAM, level=CapabilityLevel.UNSUPPORTED,
    )
    param_fact = _fact(
        param="values", level=CapabilityLevel.UNSUPPORTED,
    )
    dialect_fact = _fact(
        param=WILDCARD_PARAM, dialect="ibis-duckdb",
        level=CapabilityLevel.UNSUPPORTED,
    )
    report = _report([whole_op, param_fact, dialect_fact])
    main = render_markdown(report)
    scoped = render_scoped(report)

    main_section = _cell_section(main, "OP_A", "polars")
    scoped_section = _cell_section(scoped, "OP_A", "polars")
    assert main_section, "main doc missing OP_A x polars section"
    assert scoped_section, "scoped doc missing OP_A x polars section"

    # Build the expected row for each fact (option_value=None -> []).
    main_whole_row = _fact_detail_row(whole_op, [])
    scoped_param_row = _fact_detail_row(param_fact, [])
    scoped_dialect_row = _fact_detail_row(dialect_fact, [])

    # Function-level (whole-op) lives in main; scoped lives in scoped; no
    # fact appears in both — the partition is exact.
    assert main_whole_row in main_section
    assert main_whole_row not in scoped_section
    assert scoped_param_row in scoped_section
    assert scoped_param_row not in main_section
    assert scoped_dialect_row in scoped_section
    assert scoped_dialect_row not in main_section


def test_scoped_only_cell_no_main_doc_section():
    """A cell with ONLY scoped facts (no whole-op) renders no main-doc
    detail section; the `◐` matrix cell is preserved; the scoped doc
    carries the detail row."""
    param_fact = _fact(param="values", level=CapabilityLevel.UNSUPPORTED)
    report = _report([param_fact])
    main = render_markdown(report)
    scoped = render_scoped(report)

    # Main doc has no detail section for the cell.
    main_detail = main.split("## Per-op detail", 1)[1]
    assert "### `OP_A` × polars" not in main_detail
    # But the matrix cell is still there with the partial annotation.
    matrix = main.split("## Per-family coverage", 1)[1].split(
        "## Unmapped families", 1)[0]
    assert "◐ partial (1 params, 0 option-selectors, 0 value-classes, 0 dialects)" in matrix
    # Scoped doc has the detail.
    scoped_detail = scoped.split("## Per-op detail (scoped)", 1)[1]
    assert "### `OP_A` × polars" in scoped_detail
    scoped_row = _fact_detail_row(param_fact, [])
    assert scoped_row in scoped_detail


def test_dialect_scoped_whole_op_subheading_and_i2b():
    """A dialect-scoped whole-op gate renders under the scoped doc's
    `Dialect-scoped whole-op` subheading AND its level+dialect appears
    in the main-doc matrix cell (I-2b, spec §4.3 example:
    `◐ partial (…) · unsupported on ibis-duckdb`)."""
    dialect_whole = _fact(
        param=WILDCARD_PARAM, dialect="ibis-duckdb",
        level=CapabilityLevel.UNSUPPORTED,
    )
    report = _report([dialect_whole])
    main = render_markdown(report)
    scoped = render_scoped(report)

    # Main doc matrix cell: I-2b suffix present (level + sorted dialect).
    matrix = main.split("## Per-family coverage", 1)[1].split(
        "## Unmapped families", 1)[0]
    assert "· unsupported on ibis-duckdb" in matrix

    # Scoped doc: under "Dialect-scoped whole-op" subheading.
    scoped_cell = _cell_section(scoped, "OP_A", "polars")
    assert "#### Dialect-scoped whole-op" in scoped_cell
    dialect_row = _fact_detail_row(dialect_whole, [])
    assert dialect_row in scoped_cell


def test_refinements_never_in_main_doc_detail():
    """Refinements are scoped by construction (schema requires dialect on
    EXPR_CAPABLE, so `is_whole_op` is False for every refinement).
    The main doc's per-op detail never carries a refinement row (§4.3
    structural) — it lives in the scoped doc; the matrix cell still
    carries the `✓ dialect-verified: …` annotation."""
    refinement = _fact(
        param="v", dialect="duckdb", level=CapabilityLevel.EXPR_CAPABLE,
    )
    report = _report([refinement])
    main = render_markdown(report)
    scoped = render_scoped(report)

    # Main doc has no detail section for the cell (refinement is scoped).
    main_detail = main.split("## Per-op detail", 1)[1]
    assert "### `OP_A` × polars" not in main_detail
    # But the matrix cell still carries the `✓ dialect-verified: duckdb` annotation.
    matrix = main.split("## Per-family coverage", 1)[1].split(
        "## Unmapped families", 1)[0]
    assert "dialect-verified: duckdb" in matrix
    # Scoped doc has the detail row.
    scoped_detail = scoped.split("## Per-op detail (scoped)", 1)[1]
    assert "### `OP_A` × polars" in scoped_detail
    ref_row = _fact_detail_row(refinement, [])
    assert ref_row in scoped_detail


def test_cross_references_in_both_headers():
    """Both artifacts cross-reference each other in their headers — the
    spec's "Both docs cross-reference each other in their headers"
    requirement (§4.3)."""
    report = _report([])
    main = render_markdown(report)
    scoped = render_scoped(report)

    # Main doc header (above ## Summary) points to the scoped doc.
    main_header = main.split("## Summary", 1)[0]
    assert "expression-coverage-scoped.md" in main_header
    # Scoped doc header (above ## Per-op detail (scoped)) points to the main doc.
    scoped_header = scoped.split("## Per-op detail (scoped)", 1)[0]
    assert "expression-coverage.md" in scoped_header
    # And the main doc's parquet consumer recipe (§4.6) is in the header block.
    assert "Parquet recipe" in main_header
    assert "expression-coverage.json" in main_header
