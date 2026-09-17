"""Model-level tests for the coverage-report universe and identities."""

from __future__ import annotations

import enum as _enum
import inspect

import pytest

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    _UNREGISTERED_OPS,
    ImplementationRecord,
    ImplState,
    build_coverage_report,
    OpRecord,
    audit_domain_for,
    classify_fact,
    is_dialect_scoped_whole_op,
    is_whole_op,
    _validate_backends,
    _validate_dates,
    _validate_segments,
    _validate_native_errors_builtins,
)
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityAssertion,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    FactSource,
)
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Clause,
    ClauseOp,
    DivergenceKind,
    Enforcement,
    Predicate,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _fact(**kw) -> CapabilityFact:
    base = dict(
        operation_key=FK_STR.LPAD,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.POLARS,
        message="fixture",
        since="2026-08-01",
    )
    base.update(kw)
    return CapabilityFact(**base)


def _registered_universe() -> list[OpRecord]:
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    keys = list(ExpressionFunctionRegistry.list_all()) + list(RelationOperationRegistry.list_all())
    return [OpRecord(k, type(k).__name__) for k in keys]


def _all_key_enum_members() -> list[tuple[str, str, object]]:
    """(class_name, member_name, member) for EVERY Enum class in the two key
    modules — module introspection, NOT prefix filtering (spec §3.1)."""
    from mountainash.expressions.core.expression_system.function_keys import enums as fk
    from mountainash.relations.core.relation_system.relation_keys import enums as rk

    out: list[tuple[str, str, object]] = []
    for module in (fk, rk):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, _enum.Enum) and cls.__module__ == module.__name__:
                out.extend((name, m.name, m) for m in cls)
    return out


def test_enum_members_registered_or_excepted():
    universe = {(r.family, r.operation_key.name) for r in _registered_universe()}
    excepted = {(u.family, u.member) for u in _UNREGISTERED_OPS}
    members = {(cls, name) for cls, name, _ in _all_key_enum_members()}

    unaccounted = members - universe - excepted
    assert not unaccounted, (
        f"enum members neither registered nor excepted: {sorted(unaccounted)}; "
        "register them or add a dated UnregisteredOp with a reason"
    )
    stale = excepted & universe
    assert not stale, f"_UNREGISTERED_OPS entries now registered — remove: {sorted(stale)}"
    phantom = excepted - members
    assert not phantom, f"_UNREGISTERED_OPS entries match no enum member: {sorted(phantom)}"


def test_unregistered_ops_governance():
    from datetime import date as _date

    seen: set[tuple[str, str]] = set()
    for u in _UNREGISTERED_OPS:
        assert (u.family, u.member) not in seen, f"duplicate exception {u}"
        seen.add((u.family, u.member))
        assert u.reason.strip(), f"empty reason on {u.family}.{u.member}"
        _date.fromisoformat(u.since)  # raises on impossible dates


def test_audit_domain_mirrors_validators():
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_SET,
        SUBSTRAIT_ARITHMETIC_WINDOW,
    )
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )

    op = next(iter(FKEY_SUBSTRAIT_SCALAR_SET))
    assert audit_domain_for(op) == (FactSource.SUBSTRAIT, Domain.SET)
    rel = next(iter(RKEY_MOUNTAINASH_REL))
    assert audit_domain_for(rel) == (FactSource.MOUNTAINASH, Domain.RELATION)
    window = next(iter(SUBSTRAIT_ARITHMETIC_WINDOW))
    assert audit_domain_for(window) == (FactSource.SUBSTRAIT, Domain.WINDOW)


def test_classify_fact_partition_by_enforcement_precedence():
    # Precedence 1: ROUTER_METADATA wins even at EXPR_CAPABLE level (legal overlap).
    # (Schema validators: EXPR_CAPABLE requires dialect; MATERIALIZE requires
    # native_errors — schema.py __post_init__.)
    routed = _fact(level=CapabilityLevel.EXPR_CAPABLE, dialect="polars", enforcement=Enforcement.ROUTER_METADATA)
    assert classify_fact(routed) == "routed"
    # Precedence 2: MATERIALIZE_RESIDUE wins even at EXPR_CAPABLE level.
    residue = _fact(
        level=CapabilityLevel.EXPR_CAPABLE,
        dialect="polars",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        native_errors=(ValueError,),
    )
    assert classify_fact(residue) == "residue"
    # Precedence 3: GATE + EXPR_CAPABLE (dialect-scoped refinement).
    refinement = _fact(level=CapabilityLevel.EXPR_CAPABLE, param="input", dialect="polars")
    assert classify_fact(refinement) == "refinements"
    # Precedence 4: GATE + constraining level.
    for level in (CapabilityLevel.UNSUPPORTED, CapabilityLevel.POLYMORPHIC):
        assert classify_fact(_fact(level=level)) == "constraints"
    lit = _fact(level=CapabilityLevel.LITERAL_ONLY, param="input")
    assert classify_fact(lit) == "constraints"


def test_ingest_rejects_impossible_calendar_date():
    bad = _fact(since="2026-99-99")
    with pytest.raises(ValueError, match="2026-99-99"):
        _validate_dates((bad,), (), (), (), ())


def test_ingest_rejects_pandas_pyarrow_facts():
    with pytest.raises(ValueError, match="non-rendered backend"):
        _validate_backends((_fact(backend=CONST_BACKEND.PANDAS),))
    with pytest.raises(ValueError, match="non-rendered backend"):
        _validate_backends((_fact(backend=CONST_BACKEND.PYARROW),))
    _validate_backends(tuple(_fact(backend=b) for b in RENDERED_BACKENDS))  # no raise


def test_ingest_rejects_duplicate_segment_address():
    segment = _segment()
    with pytest.raises(ValueError, match="duplicate segment address"):
        _validate_segments((segment, segment))


def test_report_keeps_same_scenario_in_independent_dialects():
    from mountainash.core.capabilities.capture import SourceOrigin
    from mountainash.core.capabilities.declarations import (
        DivergenceManifestation,
        ManifestationKey,
        QualifiedManifestation,
        QualifiedManifestationKey,
    )
    from mountainash.core.capabilities.schema import CaptureValue, OperationTarget, Scenario

    local = DivergenceManifestation(
        ManifestationKey(OperationTarget(FK_STR.LPAD), Scenario()),
        DivergenceKind.SEMANTICS,
        CaptureValue.of("expected"),
        CaptureValue.of("observed"),
        "dialect-specific result",
        "2026-09-17",
    )
    records = tuple(
        QualifiedManifestation(
            QualifiedManifestationKey(Scope(CONST_BACKEND.IBIS, Dialect(dialect)), local.key),
            local,
            (
                SourceOrigin(
                    f"mountainash.expressions.backends.capabilities.ibis.dialects.{dialect.replace('-', '_')}.substrait.string",
                    Scope(CONST_BACKEND.IBIS, Dialect(dialect)),
                    FactSource.SUBSTRAIT,
                    Domain.STRING,
                    "manifestations[0]",
                ),
            ),
        )
        for dialect in ("ibis-duckdb", "ibis-sqlite")
    )
    report = build_coverage_report(_universe(), (), (), records, (), (), _impls())
    assert {record.key.scope for record in report.divergences} == {record.key.scope for record in records}
    with pytest.raises(ValueError, match="duplicate"):
        build_coverage_report(_universe(), (), (), (records[0], records[0]), (), (), _impls())


def _assertion(fact: CapabilityFact) -> CapabilityAssertion:
    return CapabilityAssertion(
        CapabilityKey.from_fact(fact),
        fact.level,
        fact.since,
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
    if any(fact.backend is not backend or fact.dialect != dialect for fact in facts):
        raise ValueError("fixture segment facts must match its scope")
    scope = Scope(backend, FamilyWide() if dialect is None else Dialect(dialect))
    physical_scope = "family" if dialect is None else f"dialects.{dialect.replace('-', '_')}"
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
    return tuple(_segment(backend, dialect, tuple(group)) for (backend, dialect), group in grouped.items())


def _universe():
    return tuple(OpRecord(operation, type(operation).__name__) for operation in (FK_STR.LPAD, FK_STR.RPAD))


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


def _cell(report, member, backend):
    (fam,) = report.families
    return next(o for o in fam.ops if o.op.operation_key is member and o.backend is backend)


def test_undeclared_when_no_segment():
    # No segment -> audited is False; an UNKNOWN impl still surfaces impl.
    report = build_coverage_report(_universe(), (), (), (), (), (), _impls(state=ImplState.IMPLEMENTED))
    for fam in report.families:
        for oc in fam.ops:
            assert oc.impl is ImplState.IMPLEMENTED
            assert oc.audited is False  # no applicable segment
            assert oc.constrained is False


def test_audited_true_when_segment_present():
    report = build_coverage_report(_universe(), (), (_segment(),), (), (), (), _impls())
    lpad_polars = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert lpad_polars.audited is True  # STRING/SUBSTRAIT segment applies
    lpad_ibis = _cell(report, FK_STR.LPAD, CONST_BACKEND.IBIS)
    assert lpad_ibis.audited is False  # segment is per-backend


def test_dialect_scoped_gate_constraint_constrains():
    f = _fact(param="input", dialect="polars", level=CapabilityLevel.UNSUPPORTED)
    report = build_coverage_report(_universe(), (f,), _segments((f,)), (), (), (), _impls())
    oc = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert oc.constrained is True
    assert oc.selector_counts.dialects == 1 and oc.selector_counts.params == 1


def test_residue_constrains_routed_and_refinement_do_not():
    residue = _fact(
        param="input",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(ValueError,),
    )
    report = build_coverage_report(_universe(), (residue,), _segments((residue,)), (), (), (), _impls())
    assert _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS).constrained is True

    routed = _fact(param="input", enforcement=Enforcement.ROUTER_METADATA, level=CapabilityLevel.UNSUPPORTED)
    refinement = _fact(operation_key=FK_STR.RPAD, param="input", dialect="polars", level=CapabilityLevel.EXPR_CAPABLE)
    report2 = build_coverage_report(
        _universe(), (routed, refinement), _segments((routed, refinement)), (), (), (), _impls()
    )
    assert _cell(report2, FK_STR.LPAD, CONST_BACKEND.POLARS).constrained is False  # routed-only is clean
    assert _cell(report2, FK_STR.RPAD, CONST_BACKEND.POLARS).constrained is False  # refinement-only clean


def test_whole_op_and_scoped_compose():
    whole = _fact(level=CapabilityLevel.POLYMORPHIC)  # wildcard, value-agnostic
    scoped = _fact(param="input", level=CapabilityLevel.UNSUPPORTED, option_value="strict")
    report = build_coverage_report(_universe(), (whole, scoped), _segments((whole, scoped)), (), (), (), _impls())
    oc = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert oc.whole_op is CapabilityLevel.POLYMORPHIC
    assert oc.selector_counts.option_selectors == 1


def test_selector_counts_are_distinct_key_sets():
    fs = (
        _fact(param="length", option_value="x", level=CapabilityLevel.UNSUPPORTED),
        _fact(param="characters", option_value="x", level=CapabilityLevel.UNSUPPORTED),
        _fact(param="length", option_value="y", level=CapabilityLevel.UNSUPPORTED),
    )
    report = build_coverage_report(_universe(), fs, _segments(fs), (), (), (), _impls())
    sc = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS).selector_counts
    assert sc.params == 2  # {length, characters}
    assert sc.option_selectors == 3  # {(length,x),(characters,x),(length,y)}


def test_selector_counts_value_classes_and_dialects():
    from mountainash.core.capabilities.schema import ValueClass

    vc_member = next(iter(ValueClass))
    fs = (
        # value-class facts need non-wildcard param, no option_value, BUILD boundary.
        _fact(param="input", value_class=vc_member, backend=CONST_BACKEND.IBIS, level=CapabilityLevel.UNSUPPORTED),
        _fact(
            param="input",
            value_class=vc_member,
            backend=CONST_BACKEND.IBIS,
            dialect="ibis-duckdb",
            level=CapabilityLevel.UNSUPPORTED,
        ),
        _fact(param="input", backend=CONST_BACKEND.IBIS, dialect="ibis-sqlite", level=CapabilityLevel.UNSUPPORTED),
    )
    report = build_coverage_report(_universe(), fs, _segments(fs), (), (), (), _impls())
    sc = _cell(report, FK_STR.LPAD, CONST_BACKEND.IBIS).selector_counts
    assert sc.value_classes == 1  # deduplicated ValueClass set
    assert sc.dialects == 2  # {ibis-duckdb, ibis-sqlite}


def test_selector_counts_keep_metadata_clauses_out_of_option_selectors():
    metadata = (
        _fact(
            param="input",
            predicate=Predicate((Clause("__operand_types__.input.storage_kind", ClauseOp.EQ, "polars_object"),)),
        ),
        _fact(
            param="input",
            predicate=Predicate(
                (
                    Clause("__operand_types__.input.storage_kind", ClauseOp.EQ, "polars_object"),
                    Clause("__operand_types__.input.logical_kind", ClauseOp.EQ, "float"),
                )
            ),
        ),
    )
    report = build_coverage_report(_universe(), metadata, _segments(metadata), (), (), (), _impls())

    counts = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS).selector_counts
    assert counts.metadata_selectors == 2
    assert counts.option_selectors == 0


def test_constraining_fact_without_segment_raises():
    f = _fact()
    with pytest.raises(ValueError, match="without applicable segment"):
        build_coverage_report(_universe(), (f,), (), (), (), (), _impls())


def test_fact_partition_exactly_once():
    fs = (
        _fact(level=CapabilityLevel.UNSUPPORTED),
        _fact(param="input", enforcement=Enforcement.ROUTER_METADATA, level=CapabilityLevel.UNSUPPORTED),
        _fact(param="input", dialect="polars", level=CapabilityLevel.EXPR_CAPABLE),
    )
    report = build_coverage_report(_universe(), fs, _segments(fs), (), (), (), _impls())
    scattered = [f for fam in report.families for oc in fam.ops for f in oc.all_facts]
    assert sorted(map(id, scattered)) == sorted(map(id, fs))


# --- Task 1 new tests (rev 5 model cutover) ---


def test_ingest_rejects_missing_implementation_record():
    # Drop one implementation record; expect ValueError naming the cell.
    full = _impls()
    cells = {(r.operation_key, r.backend) for r in full}
    full_list = list(full)
    full_list.pop(0)  # lose one
    with pytest.raises(ValueError, match="missing implementation record"):
        build_coverage_report(_universe(), (), (), (), (), (), tuple(full_list))
    # sanity: the popped cell was indeed in the expected set
    assert len(cells) == len(_universe()) * len(RENDERED_BACKENDS)


def test_ingest_rejects_duplicate_implementation_record():
    # Duplicate one (same op+backend twice). The list length is preserved
    # (one missing + one duplicate keeps the total at the cell count), so a
    # set-based guard would silently pass — the Counter guard MUST catch it.
    full = list(_impls())
    dup = full[0]
    # Remove one DIFFERENT cell and add the duplicate -> same total length.
    full.pop(1)
    full.append(dup)
    with pytest.raises(ValueError, match="duplicate implementation record"):
        build_coverage_report(_universe(), (), (), (), (), (), tuple(full))


def test_not_implemented_with_constraining_fact_is_contradiction():
    f = _fact(param="input", dialect="polars", level=CapabilityLevel.UNSUPPORTED)
    # Only LPAD × POLARS is NOT_IMPLEMENTED; the rest stay IMPLEMENTED so the
    # contradiction count isolates to the one cell we want to assert.
    overrides = {(FK_STR.LPAD, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED}
    impls = _impls(overrides=overrides)
    report = build_coverage_report(_universe(), (f,), _segments((f,)), (), (), (), impls)
    oc = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert oc.impl is ImplState.NOT_IMPLEMENTED
    assert oc.constrained is True
    assert oc.contradiction is True
    assert report.stats.contradictions == 1


def test_not_implemented_with_segment_only_is_contradiction():
    # audited, no facts — the catalog-declared op with no implementation
    # must be surfaced as a contradiction too.
    overrides = {(FK_STR.LPAD, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED}
    impls = _impls(overrides=overrides)
    report = build_coverage_report(_universe(), (), (_segment(),), (), (), (), impls)
    oc = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert oc.audited is True
    assert oc.constrained is False
    assert oc.contradiction is True
    assert report.stats.contradictions == 1


def test_unknown_with_segment_is_audited_unknown_not_contradiction():
    impls = _impls(state=ImplState.UNKNOWN)
    report = build_coverage_report(_universe(), (), (_segment(),), (), (), (), impls)
    for fam in report.families:
        for oc in fam.ops:
            assert oc.impl is ImplState.UNKNOWN
            assert oc.contradiction is False
    # Only POLARS carries the segment, so only POLARS is audited.
    assert report.stats.audited_unknown[CONST_BACKEND.POLARS] == len(_universe())
    assert report.stats.audited_unknown[CONST_BACKEND.NARWHALS] == 0
    assert report.stats.audited_unknown[CONST_BACKEND.IBIS] == 0
    assert report.stats.contradictions == 0


def test_routed_only_cell_is_clean_and_default_capable():
    routed = _fact(param="input", enforcement=Enforcement.ROUTER_METADATA, level=CapabilityLevel.UNSUPPORTED)
    impls = _impls()
    report = build_coverage_report(_universe(), (routed,), _segments((routed,)), (), (), (), impls)
    oc = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert oc.constrained is False
    # Routed is an annotation, not a constraint — it does NOT count as
    # constrained (spec I-2). The cell lands in audited_clean or default_capable
    # depending on the audit badge; LPAD and RPAD are audited on POLARS
    # (the segment's (backend, source, domain) coordinate covers the family),
    # so POLARS's audited_clean is the only bucket they enter.
    assert report.stats.constrained[CONST_BACKEND.POLARS] == 0
    pol_clean = report.stats.audited_clean[CONST_BACKEND.POLARS] + report.stats.default_capable[CONST_BACKEND.POLARS]
    assert pol_clean == 2  # both ops are clean on POLARS
    # And audited_clean carries the audited half (the segment applies to
    # the whole STRING family on POLARS, not just to ops with facts in it).
    assert report.stats.audited_clean[CONST_BACKEND.POLARS] == 2


def test_per_backend_sum_law_holds():
    # Mixed report: one constrained, one clean, one UNKNOWN, one NOT_IMPLEMENTED.
    residue = _fact(
        param="input",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(ValueError,),
    )
    routed = _fact(
        operation_key=FK_STR.RPAD,
        param="input",
        enforcement=Enforcement.ROUTER_METADATA,
        level=CapabilityLevel.UNSUPPORTED,
    )
    overrides = {
        (FK_STR.LPAD, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED,
        (FK_STR.RPAD, CONST_BACKEND.POLARS): ImplState.UNKNOWN,
    }
    impls = _impls(overrides=overrides)
    report = build_coverage_report(_universe(), (residue, routed), _segments((residue, routed)), (), (), (), impls)
    ops_total = report.stats.ops_total
    for b in RENDERED_BACKENDS:
        s = report.stats
        total = (
            s.default_capable[b]
            + s.audited_clean[b]
            + s.constrained[b]
            + s.by_impl[(b, ImplState.NOT_IMPLEMENTED)]
            + s.by_impl[(b, ImplState.UNKNOWN)]
        )
        assert total == ops_total, (
            f"sum law violated for {b}: {total} != {ops_total} "
            f"(default_capable={s.default_capable[b]}, audited_clean={s.audited_clean[b]}, "
            f"constrained={s.constrained[b]}, not_impl={s.by_impl[(b, ImplState.NOT_IMPLEMENTED)]}, "
            f"unknown={s.by_impl[(b, ImplState.UNKNOWN)]})"
        )


def test_determinism_under_shuffled_implementations():
    impls = _impls()
    fs = (_fact(),)
    segments = _segments(fs)
    out1 = build_coverage_report(_universe(), fs, segments, (), (), (), impls)
    out2 = build_coverage_report(_universe(), fs, segments, (), (), (), tuple(reversed(impls)))
    # Compare the OpCoverage tuples cell-by-cell.
    cells1 = sorted(
        (oc.op.operation_key.name, str(oc.backend), oc.impl, oc.audited) for fam in out1.families for oc in fam.ops
    )
    cells2 = sorted(
        (oc.op.operation_key.name, str(oc.backend), oc.impl, oc.audited) for fam in out2.families for oc in fam.ops
    )
    assert cells1 == cells2
    # Stats must also be deterministic over the shuffled implementations.
    assert out1.stats.by_impl == out2.stats.by_impl
    assert out1.stats.audited_clean == out2.stats.audited_clean
    assert out1.stats.default_capable == out2.stats.default_capable


# --- Task 1 new tests (rev 6 model hardening) ---


def test_whole_op_helpers_classify_facts():
    whole = _fact(level=CapabilityLevel.UNSUPPORTED)
    assert is_whole_op(whole) is True
    assert is_dialect_scoped_whole_op(whole) is False
    scoped_whole = _fact(level=CapabilityLevel.UNSUPPORTED, dialect="polars")
    assert is_whole_op(scoped_whole) is False
    assert is_dialect_scoped_whole_op(scoped_whole) is True
    param_fact = _fact(param="input", level=CapabilityLevel.UNSUPPORTED)
    assert is_whole_op(param_fact) is False
    assert is_dialect_scoped_whole_op(param_fact) is False


def test_segments_are_sorted_by_physical_address():
    last = _segment(module_suffix=".z")
    first = _segment(module_suffix=".a")
    report = build_coverage_report(_universe(), (), (last, first), (), (), (), _impls())
    assert tuple(segment.module for segment in report.segments) == (
        first.module,
        last.module,
    )
    polars_cell = _cell(report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert polars_cell.segments == (first, last)


def test_impl_protocol_carried_for_known_states_and_none_for_unknown():
    # IMPLEMENTED: protocol_name from record, method_name from record.
    impl_report = build_coverage_report(_universe(), (), (), (), (), (), _impls(state=ImplState.IMPLEMENTED))
    lpad_polars = _cell(impl_report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert lpad_polars.impl is ImplState.IMPLEMENTED
    assert lpad_polars.impl_protocol == "SubstraitScalarStringExpressionSystemProtocol"
    assert lpad_polars.impl_method == "lpad"

    # IMPLEMENTED_VIA_HANDLER: protocol_name is the literal "handler".
    via_handler_impls = [
        ImplementationRecord(
            r.operation_key,
            b,
            ImplState.IMPLEMENTED_VIA_HANDLER,
            "handler_qualname",
            "handler",
        )
        for r in _universe()
        for b in RENDERED_BACKENDS
    ]
    via_handler_report = build_coverage_report(_universe(), (), (), (), (), (), tuple(via_handler_impls))
    lpad_handler = _cell(via_handler_report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert lpad_handler.impl is ImplState.IMPLEMENTED_VIA_HANDLER
    assert lpad_handler.impl_protocol == "handler"
    assert lpad_handler.impl_method == "handler_qualname"

    # NOT_IMPLEMENTED: still carries provenance (per spec §3.6, method_name
    # is the protocol-method name; protocol_name is the protocol class).
    ni_overrides = {(FK_STR.LPAD, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED}
    ni_impls = _impls(overrides=ni_overrides)
    ni_report = build_coverage_report(_universe(), (), (), (), (), (), ni_impls)
    lpad_not_implemented = _cell(ni_report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert lpad_not_implemented.impl is ImplState.NOT_IMPLEMENTED
    assert lpad_not_implemented.impl_protocol == "SubstraitScalarStringExpressionSystemProtocol"
    assert lpad_not_implemented.impl_method == "lpad"

    # UNKNOWN: both provenance fields None.
    unknown_report = build_coverage_report(_universe(), (), (), (), (), (), _impls(state=ImplState.UNKNOWN))
    lpad_unknown = _cell(unknown_report, FK_STR.LPAD, CONST_BACKEND.POLARS)
    assert lpad_unknown.impl is ImplState.UNKNOWN
    assert lpad_unknown.impl_protocol is None
    assert lpad_unknown.impl_method is None


def test_ingest_rejects_non_builtin_native_errors_on_top_level_facts():
    class _LocalError(Exception):
        pass

    bad = _fact(
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(_LocalError,),
    )
    with pytest.raises(ValueError, match="_LocalError"):
        _validate_native_errors_builtins((bad,), ())


def test_ingest_rejects_non_builtin_native_errors_on_nested_facts():
    class _OtherError(Exception):
        pass

    valid = _fact(
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(ValueError,),
    )
    segment = _segment(facts=(valid,))
    # Deliberately bypass frozen facts to exercise publication-time rejection.
    object.__setattr__(segment.facts[0], "native_errors", (_OtherError,))
    with pytest.raises(ValueError, match="segment .*_OtherError"):
        _validate_native_errors_builtins((), (segment,))


def test_ingest_accepts_builtin_native_errors():
    builtin = _fact(
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        level=CapabilityLevel.UNSUPPORTED,
        native_errors=(ValueError, TypeError),
    )
    _validate_native_errors_builtins((builtin,), ())  # no raise
    # Empty native_errors tuple is also fine (BUILD-boundary facts).
    _validate_native_errors_builtins((_fact(),), ())
