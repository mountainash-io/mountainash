"""Model-level tests for the coverage module (synthetic + universe identity)."""
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
    _validate_backends,
    _validate_dates,
    _validate_declarations,
    _validate_divergences,
)
from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    DivergenceFact,
    DivergenceKind,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND


class FKEY_SUBSTRAIT_SYNTH_SET(_enum.Enum):
    """Synthetic key class: prefix FKEY_SUBSTRAIT -> SUBSTRAIT source, suffix
    _SET -> SET domain (mirrors the real validators; cannot collide with the
    real FKEY_SUBSTRAIT_SCALAR_SET class)."""

    OP_A = _enum.auto()
    OP_B = _enum.auto()


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


def _registered_universe() -> list[OpRecord]:
    from mountainash.expressions.core.expression_system.function_mapping.registry import (
        ExpressionFunctionRegistry,
    )
    from mountainash.relations.core.relation_system.relation_mapping.registry import (
        RelationOperationRegistry,
    )

    keys = list(ExpressionFunctionRegistry.list_all()) + list(
        RelationOperationRegistry.list_all()
    )
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
    legacy = next(iter(SUBSTRAIT_ARITHMETIC_WINDOW))
    assert audit_domain_for(legacy) is None  # unmapped family, not an error


def test_known_gaps_register_importable_and_typed():
    from mountainash.core.capabilities.gaps import KNOWN_GAPS
    from mountainash.core.capabilities.schema import KnownGap

    assert isinstance(KNOWN_GAPS, tuple)
    assert all(isinstance(g, KnownGap) for g in KNOWN_GAPS)


def test_classify_fact_partition_by_enforcement_precedence():
    # Precedence 1: ROUTER_METADATA wins even at EXPR_CAPABLE level (legal overlap).
    # (Schema validators: EXPR_CAPABLE requires dialect; MATERIALIZE requires
    # native_errors — schema.py __post_init__.)
    routed = _fact(level=CapabilityLevel.EXPR_CAPABLE, dialect="duckdb",
                   enforcement=Enforcement.ROUTER_METADATA)
    assert classify_fact(routed) == "routed"
    # Precedence 2: MATERIALIZE_RESIDUE wins even at EXPR_CAPABLE level.
    residue = _fact(level=CapabilityLevel.EXPR_CAPABLE, dialect="duckdb",
                    enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE, native_errors=(ValueError,))
    assert classify_fact(residue) == "residue"
    # Precedence 3: GATE + EXPR_CAPABLE (dialect-scoped refinement).
    refinement = _fact(level=CapabilityLevel.EXPR_CAPABLE, param="values",
                       dialect="duckdb")
    assert classify_fact(refinement) == "refinements"
    # Precedence 4: GATE + constraining level.
    for level in (CapabilityLevel.UNSUPPORTED, CapabilityLevel.POLYMORPHIC):
        assert classify_fact(_fact(level=level)) == "constraints"
    lit = _fact(level=CapabilityLevel.LITERAL_ONLY, param="values")
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


def test_ingest_rejects_duplicate_declaration_identity():
    from mountainash.core.capabilities.declarations import Domain, FactSource

    d = CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS, domain=Domain.SET,
        source=FactSource.SUBSTRAIT, facts=(),
        evidence=ProbeEvidence(probe_date="2026-08-01",
                               library_versions=(("polars", "1.35.1"),),
                               fixtures=("t",)),
    )
    with pytest.raises(ValueError, match="duplicate declaration identity"):
        _validate_declarations((d, d))


def test_ingest_rejects_duplicate_divergence_id():
    dv = DivergenceFact(id="XX-DUP-01", kind=DivergenceKind.SEMANTICS,
                        operation_keys=(), backends=("polars",),
                        summary="s", impact="i", since="2026-08-01")
    with pytest.raises(ValueError, match="XX-DUP-01"):
        _validate_divergences((dv, dv))



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


def _cell(report, member, backend):
    (fam,) = report.families
    return next(o for o in fam.ops
                if o.op.operation_key is member and o.backend is backend)


def test_undeclared_when_no_declaration():
    # No declaration -> audited is False; an UNKNOWN impl still surfaces impl.
    report = build_coverage_report(
        _universe(), (), (), (), (), (), _impls(state=ImplState.IMPLEMENTED)
    )
    for fam in report.families:
        for oc in fam.ops:
            assert oc.impl is ImplState.IMPLEMENTED
            assert oc.audited is False  # no applicable declaration
            assert oc.constrained is False


def test_audited_true_when_declaration_present():
    report = build_coverage_report(
        _universe(), (), (_decl(),), (), (), (), _impls()
    )
    a_pol = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert a_pol.audited is True   # SET/SUBSTRAIT declaration applies
    a_ibis = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.IBIS)
    assert a_ibis.audited is False  # declaration is per-backend


def test_dialect_scoped_gate_constraint_constrains():
    f = _fact(param="values", dialect="duckdb", level=CapabilityLevel.UNSUPPORTED)
    report = build_coverage_report(
        _universe(), (f,), (_decl(facts=(f,)),), (), (), (), _impls()
    )
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.constrained is True
    assert oc.selector_counts.dialects == 1 and oc.selector_counts.params == 1


def test_residue_constrains_routed_and_refinement_do_not():
    residue = _fact(param="values", enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE, level=CapabilityLevel.UNSUPPORTED,
                    native_errors=(ValueError,))
    report = build_coverage_report(
        _universe(), (residue,), (_decl(facts=(residue,)),), (), (), (), _impls()
    )
    assert _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
                 CONST_BACKEND.POLARS).constrained is True

    routed = _fact(param="values", enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    refinement = _fact(operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_B, param="values",
                       dialect="duckdb", level=CapabilityLevel.EXPR_CAPABLE)
    report2 = build_coverage_report(
        _universe(), (routed, refinement),
        (_decl(facts=(routed, refinement)),), (), (), (), _impls()
    )
    assert _cell(report2, FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
                 CONST_BACKEND.POLARS).constrained is False  # routed-only is clean
    assert _cell(report2, FKEY_SUBSTRAIT_SYNTH_SET.OP_B,
                 CONST_BACKEND.POLARS).constrained is False  # refinement-only clean


def test_whole_op_and_scoped_compose():
    whole = _fact(level=CapabilityLevel.POLYMORPHIC)  # wildcard, value-agnostic
    scoped = _fact(param="values", level=CapabilityLevel.UNSUPPORTED,
                   option_value="strict")
    report = build_coverage_report(
        _universe(), (whole, scoped), (_decl(facts=(whole, scoped)),), (), (), (),
        _impls()
    )
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.whole_op is CapabilityLevel.POLYMORPHIC
    assert oc.selector_counts.option_selectors == 1


def test_selector_counts_are_distinct_key_sets():
    fs = (
        _fact(param="a", option_value="x", level=CapabilityLevel.UNSUPPORTED),
        _fact(param="b", option_value="x", level=CapabilityLevel.UNSUPPORTED),
        _fact(param="a", option_value="y", level=CapabilityLevel.UNSUPPORTED),
    )
    report = build_coverage_report(
        _universe(), fs, (_decl(facts=fs),), (), (), (), _impls()
    )
    sc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS).selector_counts
    assert sc.params == 2                 # {a, b}
    assert sc.option_selectors == 3       # {(a,x),(b,x),(a,y)} — (param, value) pairs


def test_selector_counts_value_classes_and_dialects():
    from mountainash.core.capabilities.schema import ValueClass

    vc_member = next(iter(ValueClass))
    fs = (
        # value-class facts need non-wildcard param, no option_value, BUILD boundary.
        _fact(param="values", value_class=vc_member,
              level=CapabilityLevel.UNSUPPORTED),
        _fact(param="values", value_class=vc_member, dialect="duckdb",
              level=CapabilityLevel.UNSUPPORTED),  # same class again -> counts once
        _fact(param="values", dialect="sqlite", level=CapabilityLevel.UNSUPPORTED),
    )
    report = build_coverage_report(
        _universe(), fs, (_decl(facts=fs),), (), (), (), _impls()
    )
    sc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
               CONST_BACKEND.POLARS).selector_counts
    assert sc.value_classes == 1          # deduplicated ValueClass set
    assert sc.dialects == 2               # {duckdb, sqlite}


def test_constraining_fact_without_declaration_raises():
    f = _fact()
    with pytest.raises(ValueError, match="without applicable declaration"):
        build_coverage_report(_universe(), (f,), (), (), (), (), _impls())


def test_fact_partition_exactly_once():
    fs = (
        _fact(level=CapabilityLevel.UNSUPPORTED),
        _fact(param="values", enforcement=Enforcement.ROUTER_METADATA,
              level=CapabilityLevel.UNSUPPORTED),
        _fact(param="values", dialect="duckdb", level=CapabilityLevel.EXPR_CAPABLE),
    )
    report = build_coverage_report(
        _universe(), fs, (_decl(facts=fs),), (), (), (), _impls()
    )
    scattered = [f for fam in report.families for oc in fam.ops for f in oc.all_facts]
    assert sorted(map(id, scattered)) == sorted(map(id, fs))


def test_whole_op_resolution_is_input_order_independent():
    # Final-review I-1: two schema-legal whole-op GATE facts with different
    # levels on one cell must resolve whole_op identically regardless of
    # input order (fact_sort_key applies BEFORE the first-wins pick).
    unsupp = _fact(level=CapabilityLevel.UNSUPPORTED)
    poly = _fact(level=CapabilityLevel.POLYMORPHIC, message="poly wave")
    reports = [
        build_coverage_report(
            _universe(), fs, (_decl(facts=fs),), (), (), (), _impls()
        )
        for fs in ((unsupp, poly), (poly, unsupp))
    ]
    cells = [
        _cell(r, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
        for r in reports
    ]
    assert cells[0].whole_op is cells[1].whole_op
    assert cells[0].constraints == cells[1].constraints


# --- Task 1 new tests (rev 5 model cutover) ---


def test_ingest_rejects_missing_implementation_record():
    # Drop one record (OP_A × polars); expect ValueError naming the cell.
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
    f = _fact(param="values", dialect="duckdb", level=CapabilityLevel.UNSUPPORTED)
    # Only OP_A × POLARS is NOT_IMPLEMENTED; the rest stay IMPLEMENTED so the
    # contradiction count isolates to the one cell we want to assert.
    overrides = {(FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED}
    impls = _impls(overrides=overrides)
    report = build_coverage_report(
        _universe(), (f,), (_decl(facts=(f,)),), (), (), (), impls
    )
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.impl is ImplState.NOT_IMPLEMENTED
    assert oc.constrained is True
    assert oc.contradiction is True
    assert report.stats.contradictions == 1


def test_not_implemented_with_declaration_only_is_contradiction():
    # audited, no facts — the catalog-declared op with no implementation
    # must be surfaced as a contradiction too.
    overrides = {(FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED}
    impls = _impls(overrides=overrides)
    report = build_coverage_report(
        _universe(), (), (_decl(),), (), (), (), impls
    )
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.audited is True
    assert oc.constrained is False
    assert oc.contradiction is True
    assert report.stats.contradictions == 1


def test_unknown_with_declaration_is_audited_unknown_not_contradiction():
    impls = _impls(state=ImplState.UNKNOWN)
    report = build_coverage_report(
        _universe(), (), (_decl(),), (), (), (), impls
    )
    for fam in report.families:
        for oc in fam.ops:
            assert oc.impl is ImplState.UNKNOWN
            assert oc.contradiction is False
    # Only POLARS carries the declaration, so only POLARS is audited.
    assert report.stats.audited_unknown[CONST_BACKEND.POLARS] == len(_universe())
    assert report.stats.audited_unknown[CONST_BACKEND.NARWHALS] == 0
    assert report.stats.audited_unknown[CONST_BACKEND.IBIS] == 0
    assert report.stats.contradictions == 0


def test_routed_only_cell_is_clean_and_default_capable():
    routed = _fact(param="values", enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    impls = _impls()
    report = build_coverage_report(
        _universe(), (routed,), (_decl(facts=(routed,)),), (), (), (), impls
    )
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.constrained is False
    # Routed is an annotation, not a constraint — it does NOT count as
    # constrained (spec I-2). The cell lands in audited_clean or default_capable
    # depending on the audit badge; here both OP_A and OP_B are audited on POLARS
    # (the declaration's (backend, source, domain) coordinate covers the family),
    # so POLARS's audited_clean is the only bucket they enter.
    assert report.stats.constrained[CONST_BACKEND.POLARS] == 0
    pol_clean = (
        report.stats.audited_clean[CONST_BACKEND.POLARS]
        + report.stats.default_capable[CONST_BACKEND.POLARS]
    )
    assert pol_clean == 2  # both ops are clean on POLARS
    # And audited_clean carries the audited half (the declaration applies to
    # the whole SET family on POLARS, not just to ops with facts in it).
    assert report.stats.audited_clean[CONST_BACKEND.POLARS] == 2


def test_per_backend_sum_law_holds():
    # Mixed report: one constrained, one clean, one UNKNOWN, one NOT_IMPLEMENTED.
    residue = _fact(param="values", enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE, level=CapabilityLevel.UNSUPPORTED,
                    native_errors=(ValueError,))
    routed = _fact(operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_B, param="values",
                   enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    overrides = {
        (FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS): ImplState.NOT_IMPLEMENTED,
        (FKEY_SUBSTRAIT_SYNTH_SET.OP_B, CONST_BACKEND.POLARS): ImplState.UNKNOWN,
    }
    impls = _impls(overrides=overrides)
    report = build_coverage_report(
        _universe(), (residue, routed), (_decl(facts=(residue, routed)),),
        (), (), (), impls
    )
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
    decls = (_decl(),)
    out1 = build_coverage_report(_universe(), fs, decls, (), (), (), impls)
    out2 = build_coverage_report(_universe(), fs, decls, (), (), (), tuple(reversed(impls)))
    # Compare the OpCoverage tuples cell-by-cell.
    cells1 = sorted(
        (oc.op.operation_key.name, str(oc.backend), oc.impl, oc.audited)
        for fam in out1.families for oc in fam.ops
    )
    cells2 = sorted(
        (oc.op.operation_key.name, str(oc.backend), oc.impl, oc.audited)
        for fam in out2.families for oc in fam.ops
    )
    assert cells1 == cells2
    # Stats must also be deterministic over the shuffled implementations.
    assert out1.stats.by_impl == out2.stats.by_impl
    assert out1.stats.audited_clean == out2.stats.audited_clean
    assert out1.stats.default_capable == out2.stats.default_capable
