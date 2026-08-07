"""Renderer tests over synthetic reports — determinism, cells, collapse."""
from __future__ import annotations

import enum as _enum

from mountainash.core.capabilities.coverage import build_coverage_report, OpRecord
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration, Domain, FactSource, ProbeEvidence,
)
from mountainash.core.capabilities.render_markdown import (
    _collapse_groups,
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


# _fact, _decl, _universe: copy the Task 3 helper bodies verbatim here.


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


def _report(facts=(), decls=None, **kw):
    if decls is None:
        decls = (_decl(facts=tuple(facts)),) if facts else ()
    return build_coverage_report(
        _universe(), tuple(facts), tuple(decls),
        kw.get("divergences", ()), kw.get("gaps", ()), kw.get("retired", ()),
    )


def test_render_is_deterministic_under_input_shuffle():
    fs = [
        _fact(param="a", option_value=v, level=CapabilityLevel.UNSUPPORTED)
        for v in ("x", "y", "z")
    ] + [_fact(param="b", dialect="duckdb", level=CapabilityLevel.LITERAL_ONLY)]
    decl = _decl(facts=tuple(fs))
    out1 = render_markdown(build_coverage_report(
        _universe(), tuple(fs), (decl,), (), (), ()))
    out2 = render_markdown(build_coverage_report(
        _universe(), tuple(reversed(fs)), (decl,), (), (), ()))
    assert out1 == out2


def test_cell_texts():
    whole = _fact(level=CapabilityLevel.POLYMORPHIC)
    scoped = _fact(param="values", option_value="strict",
                   level=CapabilityLevel.UNSUPPORTED)
    out = render_markdown(_report([whole, scoped]))
    assert "poly + ◐ partial (1 params, 1 option-selectors, 0 value-classes, 0 dialects)" in out
    clean = render_markdown(_report([], decls=(_decl(),)))
    assert "| ✅ |" in clean
    empty = render_markdown(_report([]))
    assert "| — |" in empty


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
    assert "✅ ↻ routed" in out  # routed alone stays clean


def test_refinement_annotation_lists_dialects():
    refinement = _fact(param="v", dialect="duckdb",
                       level=CapabilityLevel.EXPR_CAPABLE)
    out = render_markdown(_report([refinement]))
    assert "✅ ✓ dialect-verified: duckdb" in out  # refinement alone stays clean


def test_undeclared_never_renders_clean_marker():
    out = render_markdown(_report([]))
    # No declarations at all -> no ✅ anywhere in matrix rows.
    matrix = out.split("## Per-family coverage", 1)[1]
    assert "✅" not in matrix


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


def test_legend_carries_inference_limit():
    out = render_markdown(_report([]))
    assert "domain-wave-level evidence" in out
    assert "not proof the specific op was exercised" in out


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
