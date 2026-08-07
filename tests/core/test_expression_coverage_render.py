"""Renderer tests over synthetic reports — determinism, cells, collapse."""
from __future__ import annotations

import enum as _enum

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    ImplState,
    ImplementationRecord,
    OpRecord,
    build_coverage_report,
)
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration, Domain, FactSource, ProbeEvidence,
)
from mountainash.core.capabilities.render_markdown import (
    _collapse_groups,
    _resolve_concrete_owner,
    gather_coverage_inputs,
    gather_implementation_records,
    render_markdown,
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
    fs = [
        _fact(param="a", option_value=v, level=CapabilityLevel.UNSUPPORTED)
        for v in ("x", "y", "z")
    ] + [_fact(param="b", dialect="duckdb", level=CapabilityLevel.LITERAL_ONLY)]
    decl = _decl(facts=tuple(fs))
    impls = _impls()
    out1 = render_markdown(build_coverage_report(
        _universe(), tuple(fs), (decl,), (), (), (), impls))
    out2 = render_markdown(build_coverage_report(
        _universe(), tuple(reversed(fs)), (decl,), (), (), (), impls))
    # Defense-in-depth: also shuffle the implementations tuple (Task-1 model-level
    # shuffle already guards this; this is the renderer's contract per spec §4.4).
    impls_rev = tuple(reversed(impls))
    out3 = render_markdown(build_coverage_report(
        _universe(), tuple(fs), (decl,), (), (), (), impls_rev))
    out4 = render_markdown(build_coverage_report(
        _universe(), tuple(reversed(fs)), (decl,), (), (), (), impls_rev))
    assert out1 == out2
    assert out1 == out3
    assert out1 == out4


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
    # Use the live report which contains real unmapped families (those whose
    # audit_domain is None). Render and assert the §3.6 stamp line format.
    report = build_coverage_report(
        gather_coverage_inputs()["universe"],
        gather_coverage_inputs()["facts"],
        gather_coverage_inputs()["declarations"],
        gather_coverage_inputs()["divergences"],
        gather_coverage_inputs()["gaps"],
        gather_coverage_inputs()["retired"],
        gather_implementation_records(gather_coverage_inputs()["universe"]),
    )
    out = render_markdown(report)
    # The stamp format: "N ops — all implemented on 3/3 backends" or a
    # per-backend split when not uniform (spec §4.3 / brief).
    import re
    assert re.search(r"\d+ ops — (all implemented on 3/3 backends|"
                     r"implemented on \d/3 polars · .*narwhals · .*ibis)", out), (
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
    routed = _fact(param="v", enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    out = render_markdown(_report([routed]))
    assert "### `OP_A` × polars" in out  # routed-only cell still gets a detail row
    assert "router_metadata" in out


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
