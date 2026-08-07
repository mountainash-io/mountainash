"""Model-level tests for the coverage module (synthetic + universe identity)."""
from __future__ import annotations

import enum as _enum
import inspect

import pytest

from mountainash.core.capabilities.coverage import (
    RENDERED_BACKENDS,
    _UNREGISTERED_OPS,
    CoverageState,
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


def _cell(report, member, backend):
    (fam,) = report.families
    return next(o for o in fam.ops
                if o.op.operation_key is member and o.backend is backend)


def test_undeclared_when_no_declaration():
    report = build_coverage_report(_universe(), (), (), (), (), ())
    for fam in report.families:
        for oc in fam.ops:
            assert oc.state is CoverageState.UNDECLARED


def test_declared_clean_requires_declaration_and_no_constraint():
    report = build_coverage_report(_universe(), (), (_decl(),), (), (), ())
    a_pol = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert a_pol.state is CoverageState.DECLARED_CLEAN
    a_ibis = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.IBIS)
    assert a_ibis.state is CoverageState.UNDECLARED  # declaration is per-backend


def test_dialect_scoped_gate_constraint_constrains():
    f = _fact(param="values", dialect="duckdb", level=CapabilityLevel.UNSUPPORTED)
    report = build_coverage_report(_universe(), (f,), (_decl(facts=(f,)),), (), (), ())
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.state is CoverageState.CONSTRAINED
    assert oc.selector_counts.dialects == 1 and oc.selector_counts.params == 1


def test_residue_constrains_routed_and_refinement_do_not():
    residue = _fact(param="values", enforcement=Enforcement.MATERIALIZE_RESIDUE,
                    boundary=Boundary.MATERIALIZE, level=CapabilityLevel.UNSUPPORTED,
                    native_errors=(ValueError,))
    report = build_coverage_report(
        _universe(), (residue,), (_decl(facts=(residue,)),), (), (), ())
    assert _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
                 CONST_BACKEND.POLARS).state is CoverageState.CONSTRAINED

    routed = _fact(param="values", enforcement=Enforcement.ROUTER_METADATA,
                   level=CapabilityLevel.UNSUPPORTED)
    refinement = _fact(operation_key=FKEY_SUBSTRAIT_SYNTH_SET.OP_B, param="values",
                       dialect="duckdb", level=CapabilityLevel.EXPR_CAPABLE)
    report2 = build_coverage_report(
        _universe(), (routed, refinement),
        (_decl(facts=(routed, refinement)),), (), (), ())
    assert _cell(report2, FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
                 CONST_BACKEND.POLARS).state is CoverageState.DECLARED_CLEAN
    assert _cell(report2, FKEY_SUBSTRAIT_SYNTH_SET.OP_B,
                 CONST_BACKEND.POLARS).state is CoverageState.DECLARED_CLEAN


def test_whole_op_and_scoped_compose():
    whole = _fact(level=CapabilityLevel.POLYMORPHIC)  # wildcard, value-agnostic
    scoped = _fact(param="values", level=CapabilityLevel.UNSUPPORTED,
                   option_value="strict")
    report = build_coverage_report(
        _universe(), (whole, scoped), (_decl(facts=(whole, scoped)),), (), (), ())
    oc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A, CONST_BACKEND.POLARS)
    assert oc.whole_op is CapabilityLevel.POLYMORPHIC
    assert oc.selector_counts.option_selectors == 1


def test_selector_counts_are_distinct_key_sets():
    fs = (
        _fact(param="a", option_value="x", level=CapabilityLevel.UNSUPPORTED),
        _fact(param="b", option_value="x", level=CapabilityLevel.UNSUPPORTED),
        _fact(param="a", option_value="y", level=CapabilityLevel.UNSUPPORTED),
    )
    report = build_coverage_report(_universe(), fs, (_decl(facts=fs),), (), (), ())
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
    report = build_coverage_report(_universe(), fs, (_decl(facts=fs),), (), (), ())
    sc = _cell(report, FKEY_SUBSTRAIT_SYNTH_SET.OP_A,
               CONST_BACKEND.POLARS).selector_counts
    assert sc.value_classes == 1          # deduplicated ValueClass set
    assert sc.dialects == 2               # {duckdb, sqlite}


def test_constraining_fact_without_declaration_raises():
    f = _fact()
    with pytest.raises(ValueError, match="without applicable declaration"):
        build_coverage_report(_universe(), (f,), (), (), (), ())


def test_fact_partition_exactly_once():
    fs = (
        _fact(level=CapabilityLevel.UNSUPPORTED),
        _fact(param="values", enforcement=Enforcement.ROUTER_METADATA,
              level=CapabilityLevel.UNSUPPORTED),
        _fact(param="values", dialect="duckdb", level=CapabilityLevel.EXPR_CAPABLE),
    )
    report = build_coverage_report(_universe(), fs, (_decl(facts=fs),), (), (), ())
    scattered = [f for fam in report.families for oc in fam.ops for f in oc.all_facts]
    assert sorted(map(id, scattered)) == sorted(map(id, fs))
