"""Renderer tests over local reports — determinism, cells, and collapse."""

from __future__ import annotations

import builtins
import json

import pytest

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
    BoundSegment,
    CapabilityAssertion,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    LocalOrigin,
)
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.capabilities.render_markdown import (
    _collapse_groups,
    _fact_detail_row,
    _resolve_concrete_owner,
    gather_coverage_inputs,
    render_json,
    render_markdown,
    render_scoped,
)
from mountainash.core.capabilities.capture import (
    CapturedAddress,
    CapturedAssertion,
    Environment,
    EnvironmentCoordinate,
)
from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Clause,
    ClauseOp,
    DivergenceFact,
    DivergenceKind,
    Enforcement,
    GapKind,
    KnownGap,
    Predicate,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING,
)




# _impls, _fact, _segment, and _universe are local fixture builders over
# registered Substrait string operations.


def _fact(**kw) -> CapabilityFact:
    base = dict(
        operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="fixture",
        since="2026-08-01",
    )
    base.update(kw)
    return CapabilityFact(**base)


def _assertion(fact: CapabilityFact) -> CapabilityAssertion:
    return CapabilityAssertion(
        CapabilityKey.from_fact(fact),
        fact.level,
        fact.since,
        (LocalOrigin("fixture"),),
        message=fact.message,
        workaround=fact.workaround,
        issue=fact.upstream_ref,
        boundary=fact.boundary,
        native_errors=fact.native_errors,
        condition=fact.condition,
        probe_exempt=fact.probe_exempt,
        enforcement=fact.enforcement,
        signal=fact.residue_signal,
    )


def _segment(
    backend=CONST_BACKEND.POLARS,
    dialect: str | None = None,
    facts=(),
    module_suffix="",
):
    if any(
        fact.backend is not backend or fact.dialect != dialect
        for fact in facts
    ):
        raise ValueError("fixture segment facts must match its scope")
    scope = Scope(backend, FamilyWide() if dialect is None else Dialect(dialect))
    physical_scope = (
        "family"
        if dialect is None
        else f"dialects.{dialect.replace('-', '_')}"
    )
    return BoundSegment(
        f"mountainash.expressions.backends.capabilities.{backend.value}."
        f"{physical_scope}.substrait.string{module_suffix}",
        scope,
        CapabilitySegment(Domain.STRING, tuple(_assertion(fact) for fact in facts)),
    )


def _segments(facts: tuple[CapabilityFact, ...]) -> tuple[BoundSegment, ...]:
    grouped: dict[tuple[CONST_BACKEND, str | None], list[CapabilityFact]] = {}
    for fact in facts:
        grouped.setdefault((fact.backend, fact.dialect), []).append(fact)
    return tuple(
        _segment(backend, dialect, tuple(group))
        for (backend, dialect), group in grouped.items()
    )


def _universe():
    return tuple(
        OpRecord(member, type(member).__name__)
        for member in (
            FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,
            FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
        )
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
            records.append(
                ImplementationRecord(
                    r.operation_key,
                    b,
                    cell_state,
                    None if unknown else r.operation_key.name.lower(),
                    None if unknown else "SubstraitScalarStringExpressionSystemProtocol",
                )
            )
    return tuple(records)


def _report(facts=(), segments=None, impls=None, **kw):
    if segments is None:
        segments = _segments(tuple(facts)) if facts else ()
    if impls is None:
        impls = _impls()
    return build_coverage_report(
        _universe(),
        tuple(facts),
        tuple(segments),
        kw.get("divergences", ()),
        kw.get("gaps", ()),
        kw.get("changes", ()),
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
    fs = [_fact(param="length", option_value=v, level=CapabilityLevel.UNSUPPORTED) for v in ("x", "y", "z")] + [
        _fact(param="characters", dialect="polars", level=CapabilityLevel.LITERAL_ONLY)
    ]
    segments = _segments(tuple(fs))
    impls = _impls()
    impls_rev = tuple(reversed(impls))
    # Build the three baselines (facts in given order, impls in given order).
    base = build_coverage_report(_universe(), tuple(fs), segments, (), (), (), impls)
    # Three shuffled builds covering both axes: fact order and impl order.
    fs_rev = tuple(reversed(fs))
    build_facts_rev = lambda: build_coverage_report(  # noqa: E731
        _universe(), fs_rev, segments, (), (), (), impls
    )
    build_impls_rev = lambda: build_coverage_report(  # noqa: E731
        _universe(), tuple(fs), segments, (), (), (), impls_rev
    )
    build_both_rev = lambda: build_coverage_report(  # noqa: E731
        _universe(), fs_rev, segments, (), (), (), impls_rev
    )
    # All three renderers under all four input orderings.
    for renderer in (render_markdown, render_scoped, render_json):
        baseline = renderer(base)
        for builder in (build_facts_rev, build_impls_rev, build_both_rev):
            assert renderer(builder()) == baseline, f"{renderer.__name__} output drift under input shuffle"


def test_cell_texts():
    # Constrained composition (whole_op + scoped) — UNCHANGED across rev 5.
    whole = _fact(level=CapabilityLevel.POLYMORPHIC)
    scoped = _fact(param="input", option_value="strict", level=CapabilityLevel.UNSUPPORTED)
    out = render_markdown(_report([whole, scoped]))
    assert "poly + ◐ partial (1 params, 1 option-selectors, 0 metadata-selectors, 0 value-classes, 0 dialects)" in out

    # Clean default-capable (IMPLEMENTED + clean + no audit) -> `✓` (U+2713).
    clean = render_markdown(_report([], segments=(), impls=_impls()))
    assert "| ✓ |" in clean
    assert " audited" not in clean.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]

    # NOT_IMPLEMENTED + no facts + no audit -> `—` (only true blank).
    empty = render_markdown(_report([], segments=(), impls=_impls(state=ImplState.NOT_IMPLEMENTED)))
    matrix = empty.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert "| — |" in matrix
    assert "⚠ contradiction" not in matrix

    # UNKNOWN -> `?` (no glyph change, no annotations).
    unknown = render_markdown(_report([], segments=(), impls=_impls(state=ImplState.UNKNOWN)))
    assert "| ? |" in unknown


def test_handler_cell_uses_glyph():
    # IMPLEMENTED_VIA_HANDLER (clean, no audit) -> `✓ᴴ` (the ᴴ footnote).
    handler_impls = _impls(state=ImplState.IMPLEMENTED_VIA_HANDLER)
    out = render_markdown(_report([], segments=(), impls=handler_impls))
    assert "✓ᴴ" in out
    # Each real string operation uses the handler glyph and remains unaudited.
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    for line in matrix.splitlines():
        if line.startswith("| `") and ("LPAD" in line or "RPAD" in line):
            assert "✓ᴴ" in line, f"expected handler glyph in row: {line!r}"
            assert " audited" not in line

    # IMPLEMENTED_VIA_HANDLER + audited -> `✓ᴴ audited`.
    out_audited = render_markdown(_report([], segments=(_segment(),), impls=handler_impls))
    assert "✓ᴴ audited" in out_audited


def test_handler_cell_with_constraining_fact_renders_composition_not_glyph():
    # A constrained whole-op gate takes precedence over the handler glyph.
    gates = [_fact(level=CapabilityLevel.UNSUPPORTED, backend=b) for b in RENDERED_BACKENDS]
    segments = tuple(_segment(backend=b, facts=(g,)) for b, g in zip(RENDERED_BACKENDS, gates))
    out = render_markdown(_report(gates, segments=segments, impls=_impls(state=ImplState.IMPLEMENTED_VIA_HANDLER)))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    lpad_rows = [ln for ln in matrix.splitlines() if ln.startswith("| `") and "LPAD" in ln]
    assert lpad_rows, matrix
    row = lpad_rows[0]
    assert "✗ unsupported" in row
    assert "✓ᴴ" not in row
    # RPAD carries no fact, so its handler cells still render `✓ᴴ`.
    rpad_rows = [ln for ln in matrix.splitlines() if ln.startswith("| `") and "RPAD" in ln]
    assert rpad_rows and "✓ᴴ" in rpad_rows[0]


def test_contradiction_cell_renders_loudly():
    # NOT_IMPLEMENTED + constraining fact + applicable segment -> contradiction.
    f = _fact(param="input", dialect="polars", level=CapabilityLevel.UNSUPPORTED)
    impls = _impls(
        overrides={
            (FKEY_SUBSTRAIT_SCALAR_STRING.LPAD, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED,
        }
    )
    out = render_markdown(_report([f], segments=_segments((f,)), impls=impls))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    # The cell renders the loud marker, not `—`.
    assert "⚠ contradiction" in matrix
    # And the summary section renders the count even when > 0.
    assert "contradictions: 1" in out

    # NOT_IMPLEMENTED + segment only (no facts) is also a contradiction.
    out_segment_only = render_markdown(_report([], segments=(_segment(),), impls=impls))
    assert "⚠ contradiction" in out_segment_only
    assert "contradictions: 1" in out_segment_only


def test_unknown_cell_never_carries_audited_badge():
    # Audited is stored on UNKNOWN cells (the field is not dead state), but
    # it must NEVER be rendered on the `?` cell (spec §3.3, legend says so).
    impls = _impls(state=ImplState.UNKNOWN)
    out = render_markdown(_report([], segments=(_segment(),), impls=impls))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    # Every matrix row containing `?` must not contain `audited`.
    for line in matrix.splitlines():
        if line.startswith("| `") and "?" in line:
            assert " audited" not in line, f"unknown cell leaked audited badge: {line!r}"
    # The audited_unknown stat IS rendered (symmetric with contradictions).
    assert "audited_unknown: 2" in out  # both ops on POLARS


    # With no active segments, no cell in the matrix may carry the audit badge.
    out = render_markdown(_report([], segments=(), impls=_impls()))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert " audited" not in matrix
    # And the U+2705 green-tick glyph is RETIRED — the marker is U+2713 only.
    assert "✓" in matrix
    assert "✅" not in out




def test_residue_and_routed_annotations():
    residue = _fact(
        param="input",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(ValueError,),
    )
    routed = _fact(
        operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
        param="characters",
        enforcement=Enforcement.ROUTER_METADATA,
        level=CapabilityLevel.UNSUPPORTED,
    )
    out = render_markdown(_report([residue, routed]))
    assert "⚠ runtime" in out
    assert "↻ routed" in out
    # Routed alone stays clean — base mark is the light `✓` (U+2713), not
    # the retired `✅` (U+2705).
    assert "✓ ↻ routed" in out


def test_refinement_annotation_lists_dialects():
    refinement = _fact(param="input", dialect="polars", level=CapabilityLevel.EXPR_CAPABLE)
    out = render_markdown(_report([refinement]))
    # Refinement alone stays clean; the applicable segment adds the audit badge.
    assert "✓ audited ✓ dialect-verified: polars" in out


def test_unsegmented_cells_never_render_an_audit_badge():
    out = render_markdown(_report([], segments=()))
    matrix = out.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert " audited" not in matrix


def test_summary_per_backend_table_consistency():
    # Mixed report: the summary must show the per-backend counts that sum to
    # ops_total (the per-backend sum law, spec §4.5) and the invariant lines
    # (rendered even when 0 — both invariants visible per spec §3.3 / §4.1).
    residue = _fact(
        param="input",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(ValueError,),
    )
    routed = _fact(
        operation_key=FKEY_SUBSTRAIT_SCALAR_STRING.RPAD,
        param="characters",
        enforcement=Enforcement.ROUTER_METADATA,
        level=CapabilityLevel.UNSUPPORTED,
    )
    overrides = {
        (FKEY_SUBSTRAIT_SCALAR_STRING.LPAD, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED,
        (FKEY_SUBSTRAIT_SCALAR_STRING.RPAD, CONST_BACKEND.POLARS): ImplState.UNKNOWN,
    }
    impls = _impls(overrides=overrides)
    out = render_markdown(
        _report([residue, routed], segments=_segments((residue, routed)), impls=impls)
    )
    # Per-backend columns: default_capable / audited_clean / constrained / NOT_IMPLEMENTED / UNKNOWN / ops_total.
    assert "| Backend | default_capable | audited_clean | constrained | NOT_IMPLEMENTED | UNKNOWN | ops_total |" in out
    # LPAD×POLARS is a contradiction; RPAD×POLARS is audited unknown.
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
    same = [_fact(param="characters", option_value=v, level=CapabilityLevel.UNSUPPORTED) for v in ("a", "b", "c")]
    groups = _collapse_groups(tuple(same))
    assert len(groups) == 1 and groups[0][1] == ["a", "b", "c"]

    two = _collapse_groups(tuple(same[:2]))
    assert len(two) == 2  # <3 renders per-fact

    split = same[:2] + [_fact(param="characters", option_value="c", message="different", level=CapabilityLevel.UNSUPPORTED)]
    assert len(_collapse_groups(tuple(split))) == 3  # metadata splits groups

    # Mixed group: a value-agnostic fact sharing the remaining identity blocks
    # collapse — all four render per-fact (the defined handling, Task 4 code).
    mixed = same + [_fact(param="characters", level=CapabilityLevel.UNSUPPORTED)]
    assert len(_collapse_groups(tuple(mixed))) == 4


def test_scoped_report_keeps_same_message_metadata_predicates_distinguishable():
    """Consumers receive every executable metadata selector, not a collapsed label."""
    facts = (
        _fact(
            param="input",
            predicate=Predicate((Clause("__operand_types__.input.storage_kind", ClauseOp.EQ, "polars_object"),)),
        ),
        _fact(
            param="input",
            predicate=Predicate((Clause("__operand_types__.input.logical_kind", ClauseOp.EQ, "float"),)),
        ),
    )

    scoped = render_scoped(_report(facts))

    assert scoped.count("| * | input |") == 2
    assert "__operand_types__.input.storage_kind == 'polars_object'" in scoped
    assert "__operand_types__.input.logical_kind == 'float'" in scoped


def test_scoped_report_keeps_option_constraints_in_their_dialects():
    facts = tuple(
        _fact(
            param="characters",
            option_value=value,
            backend=CONST_BACKEND.IBIS,
            dialect=dialect,
        )
        for dialect in ("ibis-duckdb", "ibis-sqlite")
        for value in ("a", "b", "c")
    )
    scoped = render_scoped(_report(facts))
    for dialect in ("ibis-duckdb", "ibis-sqlite"):
        assert f"| {dialect} | characters | a, b, c |" in scoped



def _change(
    *,
    successors: tuple[CapturedAssertion, ...] = (),
    fixed_versions: Environment | None = None,
) -> AssertionChange:
    prior = _fact(param="input", message="prior limitation")
    prior_capture = CapturedAssertion(
        "capability",
        prior.fact_key,
        prior,
        CapturedAddress("mountainash", "old.py", "prior", artifact=b"old"),
    )
    return AssertionChange(
        CapturedAddress("mountainash", "changes.py", "changes[0]", artifact=b"change"),
        prior_capture,
        ChangeDisposition.INCORRECT_DECLARATION,
        "2026-08-01T12:34:56",
        "fixture correction",
        successors,
        (CapturedAddress("mountainash", "evidence.py", "cases[0]", artifact=b"evidence"),),
        fixed_versions,
    )


def test_nonempty_gaps_divergences_and_changes_render():
    dv = DivergenceFact(
        id="SY-TEST-01",
        kind=DivergenceKind.SEMANTICS,
        operation_keys=(FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,),
        backends=("polars",),
        summary="fixture summary",
        impact="fixture impact",
        workaround="fixture workaround",
        since="2026-08-01",
    )
    keyless = DivergenceFact(
        id="SY-TEST-02",
        kind=DivergenceKind.PRECISION,
        operation_keys=(),
        backends=("ibis",),
        summary="keyless divergence",
        impact="none",
        since="2026-08-01",
    )
    gap = _gap("fixture gap reason")
    successor_fact = _fact(param="input", message="corrected limitation")
    successor = CapturedAssertion(
        "capability",
        successor_fact.fact_key,
        successor_fact,
        CapturedAddress("mountainash", "new.py", "successor", artifact=b"new"),
    )
    change = _change(
        successors=(successor,),
        fixed_versions=Environment((
            EnvironmentCoordinate("package", "ibis", "13.0.0"),
            EnvironmentCoordinate("engine", "duckdb", "1.2.2"),
        )),
    )
    report = _report(
        [],
        segments=(_segment(),),
        divergences=(dv, keyless),
        gaps=(gap,),
        changes=(change,),
    )
    out = render_markdown(report)
    rendered = json.loads(render_json(report))
    change_json = rendered["changes"][0]
    assert out.count("SY-TEST-01") == 1 and out.count("SY-TEST-02") == 1
    assert "2027-01-31" in out
    assert rendered["divergences"][0]["operation_keys"] == [{
        "family": "FKEY_SUBSTRAIT_SCALAR_STRING",
        "op": "LPAD",
    }]
    assert list(change_json) == [
        "change_ref",
        "prior",
        "disposition",
        "recorded_at",
        "reason",
        "successors",
        "evidence_refs",
        "fixed_versions",
    ]
    prior_payload = change_json["prior"]["payload"]
    assert prior_payload["operation_key"]["enum"].endswith("FKEY_SUBSTRAIT_SCALAR_STRING")
    assert prior_payload["operation_key"]["name"] == "LPAD"
    assert prior_payload["param"] == "input"
    assert change_json["prior"]["address"]["entry"] == "prior"
    assert change_json["successors"][0]["address"]["entry"] == "successor"
    assert change_json["evidence_refs"][0]["entry"] == "cases[0]"
    assert change_json["fixed_versions"]["coordinates"][0]["kind"] == "engine"

def test_report_rejects_duplicate_change_capture_address():
    with pytest.raises(ValueError, match="duplicate change_ref"):
        _report(changes=(_change(), _change()))


def test_detail_section_written_for_every_cell_with_facts():
    # Rev 6 partition: a routed fact with a non-wildcard param is scoped
    # (param != WILDCARD_PARAM, so `is_whole_op` is False), so its detail
    # row lives in `render_scoped`, not the main doc. The spec's "every
    # cell with facts gets a detail row" rule is preserved across the
    # two artifacts (the partition-exactness invariant, §4.5 M-3).
    routed = _fact(param="characters", enforcement=Enforcement.ROUTER_METADATA, level=CapabilityLevel.UNSUPPORTED)
    main = render_markdown(_report([routed]))
    scoped = render_scoped(_report([routed]))
    main_detail = main.split("## Per-op detail", 1)[1]
    assert "### `LPAD` × polars" not in main_detail
    assert "### `LPAD` × polars" in scoped
    assert "router_metadata" in scoped


# ---------------------------------------------------------------------------
# Registry reporting capture — one LOADED generation for facts and evidence.
# ---------------------------------------------------------------------------


def _report_from_inputs(inputs):
    return build_coverage_report(**inputs)


def test_gather_coverage_inputs_refuses_isolated_registry():
    from mountainash.core.capabilities import CapabilityRegistry

    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        with pytest.raises(RuntimeError):
            gather_coverage_inputs()
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("before", [False, True])
@pytest.mark.parametrize("mutation", ["reset", "restore"])
def test_gather_coverage_inputs_keeps_captured_generation_after_reset_restore(
    monkeypatch,
    before,
    mutation,
):
    from mountainash.core.capabilities import CapabilityRegistry

    expected_facts, expected_segments = CapabilityRegistry._report_inputs()
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    isolated = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(snapshot)
    acquire = CapabilityRegistry._acquire_state

    def change():
        if mutation == "reset":
            CapabilityRegistry.reset()
        else:
            CapabilityRegistry.restore(isolated)

    def acquire_with_change(cls, *, enumeration=False):
        if before:
            change()
        state = acquire(enumeration=enumeration)
        if not before:
            change()
        return state

    monkeypatch.setattr(CapabilityRegistry, "_acquire_state", classmethod(acquire_with_change))
    try:
        if before:
            with pytest.raises(RuntimeError, match="ISOLATED"):
                gather_coverage_inputs()
        else:
            inputs = gather_coverage_inputs()
            assert inputs["facts"] == expected_facts
            assert inputs["segments"] == expected_segments
    finally:
        CapabilityRegistry.restore(snapshot)


def test_gather_coverage_inputs_keeps_fact_and_segment_capture_coherent(
    monkeypatch,
):
    from mountainash.core.capabilities import CapabilityRegistry

    expected_facts, expected_segments = CapabilityRegistry._report_inputs()
    snapshot = CapabilityRegistry.snapshot()
    assert sorted(fact.fact_key for fact in expected_facts) == sorted(
        fact.fact_key
        for segment in expected_segments
        for fact in segment.facts
    )
    late_segment = BoundSegment(
        "mountainash.expressions.backends.capabilities.polars.family.substrait.string.late",
        Scope(CONST_BACKEND.POLARS, FamilyWide()),
        CapabilitySegment(Domain.STRING),
    )
    report_inputs = CapabilityRegistry._report_inputs

    def capture_then_publish():
        facts, segments = report_inputs()
        CapabilityRegistry.register_segment(late_segment)
        return facts, segments

    monkeypatch.setattr(CapabilityRegistry, "_report_inputs", capture_then_publish)
    try:
        inputs = gather_coverage_inputs()
        assert inputs["facts"] == expected_facts
        assert inputs["segments"] == expected_segments
        assert late_segment in CapabilityRegistry.segments()
        rendered_segments = json.loads(render_json(_report_from_inputs(inputs)))["segments"]
        assert late_segment.module not in {
            segment["module"] for segment in rendered_segments
        }
    finally:
        CapabilityRegistry.restore(snapshot)


# ---------------------------------------------------------------------------
# Implementation derivation helpers.
# ---------------------------------------------------------------------------


class TestDerivation:
    """_resolve_concrete_owner() excludes protocol stub carriers."""


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
# Pure-function tests over local registered operations: shape lock, round-trip,
# no-collapse, null-vs-empty. No registry calls; the model is the source of
# truth and `render_json` is the only function under test here.
# ---------------------------------------------------------------------------


_TOP_LEVEL_KEYS = [
    "stamp",
    "stats",
    "families",
    "segments",
    "historical_bundles",
    "divergences",
    "gaps",
    "changes",
]

_CELL_KEYS = {
    "impl",
    "impl_method",
    "impl_protocol",
    "audited",
    "whole_op",
    "constrained",
    "contradiction",
    "selector_counts",
    "constraints",
    "residue",
    "routed",
    "refinements",
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
        (),  # predicate term — empty for these local fixture facts
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
                        out.append((op_id, backend_name, _json_fact_semantic_identity(f_dict)))
    return sorted(out)


def _model_fact_multiset(report: CoverageReport) -> list:
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


def test_json_shape_lock():
    """The report serializes current segments separately from historical capture."""
    fs = [_fact(param="length", option_value=value, level=CapabilityLevel.UNSUPPORTED) for value in ("x", "y", "z")] + [
        _fact(param="characters", dialect="polars", level=CapabilityLevel.LITERAL_ONLY)
    ]
    segments = _segments(tuple(fs))
    impls = _impls()
    out = render_json(build_coverage_report(_universe(), tuple(fs), segments, (), (), (), impls))
    obj = json.loads(out)

    # Top-level keys in spec order.
    assert list(obj.keys()) == _TOP_LEVEL_KEYS

    # Stamp counts are deliberately timeless.
    assert set(obj["stamp"].keys()) == {
        "segments",
        "historical_bundles",
        "facts",
        "operations",
        "implementation_records",
    }
    assert all(isinstance(obj["stamp"][key], int) for key in obj["stamp"])

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
        for field in ("default_capable", "audited_clean", "constrained", "audited_unknown"):
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

    # Cell keys (taken from a real LPAD fact-decorated cell).
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
    assert target_cell["whole_op"] is None or target_cell["whole_op"] in {lv.value for lv in CapabilityLevel}
    # selector_counts shape.
    assert set(target_cell["selector_counts"].keys()) == {
        "params",
        "option_selectors",
        "metadata_selectors",
        "value_classes",
        "dialects",
    }
    for v in target_cell["selector_counts"].values():
        assert isinstance(v, int)

    # Operation and family identity use the registered canonical authority.
    op_entry = obj["families"][0]["ops"][0]
    assert op_entry["op"] == {
        "family": "FKEY_SUBSTRAIT_SCALAR_STRING",
        "op": "LPAD",
    }

    fam = obj["families"][0]
    assert set(fam.keys()) == {"family", "source", "domain", "ops"}
    assert fam["family"] == "FKEY_SUBSTRAIT_SCALAR_STRING"
    assert fam["source"] == "substrait"
    assert fam["domain"] == "string"

    # ISO date strings: every fact's `since` matches the ISO grammar.
    iso_re = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}$")
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                for bucket in ("constraints", "residue", "routed", "refinements"):
                    for f in cell[bucket]:
                        assert iso_re.match(f["since"]), f"non-ISO since in JSON: {f['since']!r}"

    segment_rows = obj["segments"]
    assert len(segment_rows) == len(segments)
    for row in segment_rows:
        assert set(row) == {
            "module", "scope", "source", "domain", "facts", "evidence_refs", "changes",
        }
        assert row["module"].endswith(".substrait.string")
        assert row["source"] == "substrait"
        assert row["domain"] == "string"
    assert {row["scope"]["dialect"] for row in segment_rows} == {None, "polars"}
    assert obj["historical_bundles"] == []

def test_json_round_trip():
    fs = [
        _fact(param="length", option_value=value, level=CapabilityLevel.UNSUPPORTED)
        for value in ("x", "y", "z")
    ] + [
        _fact(param="characters", dialect="polars", level=CapabilityLevel.LITERAL_ONLY),
        _fact(
            param="input",
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            boundary=Boundary.MATERIALIZE,
            level=CapabilityLevel.UNSUPPORTED,
            native_errors=(ValueError,),
        ),
    ]
    divergence = DivergenceFact(
        id="SY-TEST-01",
        kind=DivergenceKind.SEMANTICS,
        operation_keys=(FKEY_SUBSTRAIT_SCALAR_STRING.LPAD,),
        backends=("ibis-duckdb",),
        summary="s",
        impact="i",
        workaround="w",
        since="2026-08-01",
    )
    gap = _gap("fixture")
    change = _change()
    universe = _universe()
    report = build_coverage_report(
        universe,
        tuple(fs),
        _segments(tuple(fs)),
        (divergence,),
        (gap,),
        (change,),
        _impls(),
    )
    obj = json.loads(render_json(report))

    expected_ops = {(record.family, record.operation_key.name) for record in universe}
    actual_ops = {
        (entry["op"]["family"], entry["op"]["op"])
        for family in obj["families"]
        for entry in family["ops"]
    }
    assert actual_ops == expected_ops
    assert len(obj["segments"]) == len(report.segments)
    assert len(obj["historical_bundles"]) == len(report.bundles)
    assert len(obj["divergences"]) == len(report.divergences)
    assert len(obj["gaps"]) == len(report.gaps)
    assert len(obj["changes"]) == len(report.changes)
    assert _json_fact_multiset(obj, universe) == _model_fact_multiset(report)
    assert obj["segments"][0]["module"] == report.segments[0].module
    assert any(
        fact.native_errors
        for family in report.families
        for coverage in family.ops
        for bucket in (coverage.constraints, coverage.residue, coverage.routed, coverage.refinements)
        for fact in bucket
    )


def test_json_no_collapse():
    """A ≥3-option group that the markdown collapses (one row with sorted
    option_value list) appears as ≥3 distinct fact objects in JSON — the
    extract carries every fact row uncollapsed (spec §4.6 note: 'No
    option-collapse in JSON — that is a markdown readability device')."""
    same = [_fact(param="characters", option_value=v, level=CapabilityLevel.UNSUPPORTED) for v in ("a", "b", "c")]
    out = render_json(_report(tuple(same), segments=_segments(tuple(same))))
    obj = json.loads(out)
    # Sanity: the scoped doc (rev 6) collapses these into one row. The
    # main doc has no detail section for them — they are scoped (param
    # is not WILDCARD_PARAM), and the partition sends scoped facts to
    # render_scoped (§4.3).
    scoped = render_scoped(_report(tuple(same), segments=_segments(tuple(same))))
    assert "a, b, c" in scoped  # the collapsed option list appears in the scoped doc
    # The JSON has all three as distinct fact objects with distinct option_value.
    character_facts: list[dict] = []
    for fam in obj["families"]:
        for op_entry in fam["ops"]:
            for cell in op_entry["cells"].values():
                character_facts.extend(
                    f for f in cell["constraints"] if f["param"] == "characters"
                )
    assert len(character_facts) == 3
    assert sorted(f["option_value"] for f in character_facts) == ["a", "b", "c"]
    # And the identity is distinct per row (the model never collapsed).
    identities = {_json_fact_semantic_identity(f) for f in character_facts}
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
                        f"option_value=None must serialize as JSON null, " f"got {f['option_value']!r}"
                    )
                    assert f["native_errors"] == [], (
                        f"native_errors=() must serialize as JSON [], " f"got {f['native_errors']!r}"
                    )
    assert found, "test setup must produce a constraint cell"



def test_historical_bundles_preserve_empty_wave_provenance():
    from mountainash.core.capabilities.evidence.legacy_bundles import BUNDLES

    report = build_coverage_report(
        _universe(), (), (), (), (), (), _impls(), bundles=BUNDLES
    )
    historical = json.loads(render_json(report))["historical_bundles"]
    assert len(BUNDLES) == 72
    assert sum(not bundle.members for bundle in BUNDLES) == 10
    assert len(historical) == len(BUNDLES)
    assert sum(not bundle["members"] for bundle in historical) == 10


def test_json_is_deterministic_under_input_shuffle():
    fs = [_fact(param="length", option_value=value, level=CapabilityLevel.UNSUPPORTED) for value in ("x", "y", "z")] + [
        _fact(param="characters", dialect="polars", level=CapabilityLevel.LITERAL_ONLY)
    ]
    segments = _segments(tuple(fs))
    impls = _impls()
    out1 = render_json(build_coverage_report(
        _universe(), tuple(fs), segments, (), (), (), impls
    ))
    out2 = render_json(build_coverage_report(
        _universe(), tuple(reversed(fs)), segments, (), (), (), tuple(reversed(impls))
    ))
    assert out1 == out2


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
    """Every input fact identity appears in exactly one report detail artifact."""
    whole_op = _fact(
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
    )
    param_fact = _fact(
        param="input",
        level=CapabilityLevel.UNSUPPORTED,
    )
    dialect_fact = _fact(
        param=WILDCARD_PARAM,
        dialect="polars",
        level=CapabilityLevel.UNSUPPORTED,
    )
    report = _report([whole_op, param_fact, dialect_fact])
    main = render_markdown(report)
    scoped = render_scoped(report)

    main_section = _cell_section(main, "LPAD", "polars")
    scoped_section = _cell_section(scoped, "LPAD", "polars")
    assert main_section, "main doc missing LPAD x polars section"
    assert scoped_section, "scoped doc missing LPAD x polars section"

    main_whole_row = _fact_detail_row(whole_op, [])
    scoped_param_row = _fact_detail_row(param_fact, [])
    scoped_dialect_row = _fact_detail_row(dialect_fact, [])

    assert main_whole_row in main_section
    assert main_whole_row not in scoped_section
    assert scoped_param_row in scoped_section
    assert scoped_param_row not in main_section
    assert scoped_dialect_row in scoped_section
    assert scoped_dialect_row not in main_section


def test_scoped_only_cell_no_main_doc_section():
    """A cell with only scoped facts keeps its detail out of the main document."""
    param_fact = _fact(param="input", level=CapabilityLevel.UNSUPPORTED)
    report = _report([param_fact])
    main = render_markdown(report)
    scoped = render_scoped(report)

    main_detail = main.split("## Per-op detail", 1)[1]
    assert "### `LPAD` × polars" not in main_detail
    matrix = main.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert "◐ partial (1 params, 0 option-selectors, 0 metadata-selectors, 0 value-classes, 0 dialects)" in matrix
    scoped_detail = scoped.split("## Per-op detail (scoped)", 1)[1]
    assert "### `LPAD` × polars" in scoped_detail
    assert _fact_detail_row(param_fact, []) in scoped_detail


def test_dialect_scoped_whole_op_subheading():
    """A dialect-scoped whole-op gate remains scoped and annotates its matrix cell."""
    dialect_whole = _fact(
        param=WILDCARD_PARAM,
        dialect="polars",
        level=CapabilityLevel.UNSUPPORTED,
    )
    report = _report([dialect_whole])
    main = render_markdown(report)
    scoped = render_scoped(report)

    matrix = main.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert "· unsupported on polars" in matrix
    scoped_cell = _cell_section(scoped, "LPAD", "polars")
    assert "#### Dialect-scoped whole-op" in scoped_cell
    assert _fact_detail_row(dialect_whole, []) in scoped_cell


def test_refinements_never_in_main_doc_detail():
    """Refinements stay scoped while retaining their matrix dialect annotation."""
    refinement = _fact(
        param="input",
        dialect="polars",
        level=CapabilityLevel.EXPR_CAPABLE,
    )
    report = _report([refinement])
    main = render_markdown(report)
    scoped = render_scoped(report)

    main_detail = main.split("## Per-op detail", 1)[1]
    assert "### `LPAD` × polars" not in main_detail
    matrix = main.split("## Per-family coverage", 1)[1].split("## Unmapped families", 1)[0]
    assert "dialect-verified: polars" in matrix
    scoped_detail = scoped.split("## Per-op detail (scoped)", 1)[1]
    assert "### `LPAD` × polars" in scoped_detail
    assert _fact_detail_row(refinement, []) in scoped_detail




def _gap(reason):
    from mountainash.core.capabilities.gaps import GapKey, InventoryGap, InventoryWide
    from mountainash.core.capabilities.schema import OperationTarget

    return InventoryGap(
        GapKey(
            "fixture.options", OperationTarget(FKEY_SUBSTRAIT_SCALAR_STRING.LPAD),
            "option behavior coverage:length", InventoryWide(),
        ),
        ("SubstraitScalarStringExpressionSystemProtocol", "lpad", "length"),
        KnownGap(gap_kind=GapKind.UNTESTED_OPTION, reason=reason, since="2026-08-01"),
        (CapturedAddress("fixture", "guard.py", "options[length]", artifact=b"fixture gap source"),),
    )
