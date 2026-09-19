"""Predicate schema + engine tests (backlog 66b, spec 2026-07-28)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities.schema import (
    Boundary, CapabilityFact, CapabilityLevel, Clause, ClauseOp,
    Predicate, ValueClass,
)
from mountainash.core.constants import CONST_BACKEND


def test_clause_eq_requires_scalar_operand():
    with pytest.raises(ValueError, match="EQ"):
        Clause("unit", ClauseOp.EQ, frozenset({"WEEK"}))  # frozenset is IN's operand


def test_clause_eq_rejects_value_class_as_scalar():
    # ValueClass is an Enum, so it must be explicitly excluded from EQ operands.
    with pytest.raises(ValueError, match="EQ"):
        Clause("unit", ClauseOp.EQ, ValueClass.DURATION_MULTIPLIER)


def test_clause_in_requires_frozenset_of_str_int():
    with pytest.raises(ValueError, match="IN"):
        Clause("unit", ClauseOp.IN, "WEEK")


def test_clause_nullary_ops_take_no_operand():
    for op in (ClauseOp.IS_SET, ClauseOp.IS_NULL, ClauseOp.IS_LITERAL):
        with pytest.raises(ValueError, match=op.name):
            Clause("unit", op, "WEEK")


def test_clause_matches_class_requires_value_class():
    with pytest.raises(ValueError, match="MATCHES_CLASS"):
        Clause("unit", ClauseOp.MATCHES_CLASS, "WEEK")
    assert Clause("unit", ClauseOp.MATCHES_CLASS, ValueClass.DURATION_MULTIPLIER) is not None


def test_predicate_rejects_empty():
    with pytest.raises(ValueError, match="at least one"):
        Predicate(())


def test_predicate_rejects_duplicate_clauses():
    c = Clause("unit", ClauseOp.EQ, "WEEK")
    with pytest.raises(ValueError, match="duplicate"):
        Predicate((c, c))


def test_predicate_canonical_order_is_order_insensitive():
    a = Clause("unit", ClauseOp.EQ, "WEEK")
    b = Clause("origin", ClauseOp.IN, frozenset({"ISO"}))
    assert Predicate((a, b)) == Predicate((b, a))
    assert hash(Predicate((a, b))) == hash(Predicate((b, a)))


def test_fact_predicate_must_be_build_boundary():
    with pytest.raises(ValueError, match="BUILD"):
        CapabilityFact(
            operation_key="TRUNCATE", param="unit", level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
            boundary=Boundary.MATERIALIZE,
            native_errors=(ValueError,),  # satisfy the MATERIALIZE-native_errors check first
        )


def test_fact_predicate_is_value_agnostic():
    with pytest.raises(ValueError, match="value-agnostic"):
        CapabilityFact(
            operation_key="TRUNCATE", param="unit", level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15", option_value="WEEK",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
        )


def test_fact_predicate_rejects_wildcard_param():
    with pytest.raises(ValueError, match="WILDCARD_PARAM"):
        CapabilityFact(
            operation_key="TRUNCATE", param="*", level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
        )


def test_fact_predicate_param_must_be_a_clause_root():
    with pytest.raises(ValueError, match="clause roots"):
        CapabilityFact(
            operation_key="TRUNCATE", param="other", level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
        )



def test_fact_predicate_rejects_literal_only_level():
    # LITERAL_ONLY/POLYMORPHIC semantics live in the per-param loop; a predicate
    # fact at those levels would be silently unenforceable (review finding 3).
    with pytest.raises(ValueError, match="UNSUPPORTED.*EXPR_CAPABLE"):
        CapabilityFact(
            operation_key="TRUNCATE", param="unit", level=CapabilityLevel.LITERAL_ONLY,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
        )


def test_valid_predicate_fact_constructs():
    f = CapabilityFact(
        operation_key="TRUNCATE", param="unit", level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
        since="2026-08-15",
        predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
    )
    assert f.predicate is not None
    assert f.option_value is None and f.value_class is None


from mountainash.core.capabilities.predicates import (
    BoundCall, DomainRelation, bind_expression_call, compare_domains,
    evaluate_clause, predicate_holds, resolve_path,
)
from mountainash.expressions.core.expression_nodes import ExpressionNode, LiteralNode


class _DynamicExpr(ExpressionNode):
    """Minimal concrete non-literal expression node for dynamic-arg tests."""
    def accept(self, visitor, **kwargs):
        raise NotImplementedError


def _bound_call(**bindings):
    return BoundCall(
        operation_key="TRUNCATE", backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb",
        bindings=bindings, supplied=frozenset(bindings),
    )


def test_evaluate_eq_in_null_set_literal():
    bc = _bound_call(unit="WEEK", origin="ISO", multiple=LiteralNode(value=2))
    assert evaluate_clause(Clause("unit", ClauseOp.EQ, "WEEK"), bc.bindings, bc.supplied)
    assert evaluate_clause(Clause("origin", ClauseOp.IN, frozenset({"ISO", "REGULAR"})), bc.bindings, bc.supplied)
    assert evaluate_clause(Clause("unit", ClauseOp.IS_SET), bc.bindings, bc.supplied)
    assert not evaluate_clause(Clause("unit", ClauseOp.IS_NULL), bc.bindings, bc.supplied)
    assert evaluate_clause(Clause("multiple", ClauseOp.IS_LITERAL), bc.bindings, bc.supplied)


def test_dynamic_arg_makes_value_clauses_false_but_is_set_true():
    dynamic = _DynamicExpr()  # a non-literal expression node
    bc = _bound_call(unit=dynamic)
    assert not evaluate_clause(Clause("unit", ClauseOp.EQ, "WEEK"), bc.bindings, bc.supplied)
    assert not evaluate_clause(Clause("unit", ClauseOp.IN, frozenset({"WEEK"})), bc.bindings, bc.supplied)
    assert evaluate_clause(Clause("unit", ClauseOp.IS_SET), bc.bindings, bc.supplied)
    assert not evaluate_clause(Clause("unit", ClauseOp.IS_NULL), bc.bindings, bc.supplied)
    assert not evaluate_clause(Clause("unit", ClauseOp.IS_LITERAL), bc.bindings, bc.supplied)


def test_literal_none_round_trips_is_null_is_set():
    bc = _bound_call(unit=LiteralNode(value=None))
    assert evaluate_clause(Clause("unit", ClauseOp.IS_NULL), bc.bindings, bc.supplied)
    assert not evaluate_clause(Clause("unit", ClauseOp.IS_SET), bc.bindings, bc.supplied)
    assert evaluate_clause(Clause("unit", ClauseOp.IS_LITERAL), bc.bindings, bc.supplied)


def test_unresolvable_path_raises_not_false():
    bc = _bound_call(unit="WEEK")
    with pytest.raises(ValueError, match="not bound"):
        evaluate_clause(Clause("typo_unit", ClauseOp.EQ, "WEEK"), bc.bindings, bc.supplied)


def test_none_final_value_evaluates_per_operator():
    bc = _bound_call(resource={"dialect": {"escape_char": None}})
    assert evaluate_clause(Clause("resource.dialect.escape_char", ClauseOp.IS_NULL), bc.bindings, bc.supplied)
    assert not evaluate_clause(Clause("resource.dialect.escape_char", ClauseOp.IS_SET), bc.bindings, bc.supplied)


def test_none_intermediate_raises():
    bc = _bound_call(resource=None)
    with pytest.raises(ValueError, match="through None"):
        evaluate_clause(Clause("resource.dialect.escape_char", ClauseOp.EQ, "x"), bc.bindings, bc.supplied)


def test_matches_class_operand():
    bc = _bound_call(unit="2d")
    assert evaluate_clause(Clause("unit", ClauseOp.MATCHES_CLASS, ValueClass.DURATION_MULTIPLIER), bc.bindings, bc.supplied)


def test_predicate_holds_is_conjunction():
    p = Predicate((Clause("unit", ClauseOp.EQ, "WEEK"), Clause("origin", ClauseOp.EQ, "ISO")))
    assert predicate_holds(p, _bound_call(unit="WEEK", origin="ISO").bindings, frozenset({"unit", "origin"}))
    assert not predicate_holds(p, _bound_call(unit="WEEK", origin="REGULAR").bindings, frozenset({"unit", "origin"}))


def _assert_witness_holds(comparison, left, right):
    assert comparison.relation is DomainRelation.OVERLAP
    assert comparison.witness is not None
    bindings = comparison.witness
    supplied = frozenset(bindings)
    if left is not None:
        assert predicate_holds(left, bindings, supplied)
    if right is not None:
        assert predicate_holds(right, bindings, supplied)


def test_compare_domains_finds_broad_literal_and_narrow_value_overlap():
    broad = Predicate((Clause("multiple", ClauseOp.IS_LITERAL),))
    narrow = Predicate((
        Clause("multiple", ClauseOp.IS_LITERAL),
        Clause("multiple", ClauseOp.EQ, -7),
    ))

    _assert_witness_holds(compare_domains(broad, narrow), broad, narrow)


def test_compare_domains_combines_finite_constraints_within_each_predicate():
    impossible = Predicate((
        Clause("multiple", ClauseOp.EQ, 1),
        Clause("multiple", ClauseOp.IN, frozenset({2, 3})),
    ))

    comparison = compare_domains(impossible, None)

    assert comparison.relation is DomainRelation.DISJOINT
    assert comparison.witness is None


def test_compare_domains_distinguishes_integer_and_text_in_one_conjunction():
    impossible = Predicate((
        Clause("multiple", ClauseOp.EQ, 1),
        Clause("multiple", ClauseOp.EQ, "1"),
    ))

    assert compare_domains(impossible, None).relation is DomainRelation.DISJOINT


def test_compare_domains_respects_python_bool_integer_equality():
    true_domain = Predicate((Clause("flag", ClauseOp.EQ, True),))
    integer_domain = Predicate((Clause("flag", ClauseOp.IN, frozenset({1})),))

    _assert_witness_holds(compare_domains(true_domain, integer_domain), true_domain, integer_domain)


def test_compare_domains_proves_null_and_set_domains_disjoint():
    null_domain = Predicate((Clause("unit", ClauseOp.IS_NULL),))
    set_domain = Predicate((Clause("unit", ClauseOp.IS_SET),))

    comparison = compare_domains(null_domain, set_domain)

    assert comparison.relation is DomainRelation.DISJOINT
    assert comparison.witness is None


def test_compare_domains_checks_exact_value_class_membership():
    duration_domain = Predicate((
        Clause("unit", ClauseOp.MATCHES_CLASS, ValueClass.DURATION_MULTIPLIER),
    ))
    matching = Predicate((Clause("unit", ClauseOp.EQ, "2d"),))
    nonmatching = Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),))

    _assert_witness_holds(compare_domains(duration_domain, matching), duration_domain, matching)
    assert compare_domains(duration_domain, nonmatching).relation is DomainRelation.DISJOINT


def test_compare_domains_does_not_invent_correlated_nested_witness():
    kind_domain = Predicate((Clause("resource.kind", ClauseOp.EQ, "duration"),))
    storage_domain = Predicate((Clause("resource.storage", ClauseOp.EQ, "int64"),))

    comparison = compare_domains(kind_domain, storage_domain)

    assert comparison.relation is DomainRelation.NOT_PROVEN
    assert comparison.witness is None


def test_compare_domains_keeps_operand_metadata_domains_unknown():
    metadata_domain = Predicate((
        Clause("__operand_types__.input.logical_kind", ClauseOp.EQ, "int"),
    ))

    comparison = compare_domains(metadata_domain, None)

    assert comparison.relation is DomainRelation.NOT_PROVEN
    assert comparison.witness is None


def test_bind_expression_call_aggregates_varargs():
    def protocol(self, input, /, a, *varargs, b=None, **kwargs):
        pass

    bc = bind_expression_call(
        operation_key="OP", backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb",
        protocol_method=protocol, arguments=["in", "A", "V1", "V2"], options={"b": "B"},
    )
    assert bc.bindings["a"] == "A"
    assert bc.bindings["b"] == "B"
    assert bc.bindings["varargs"] == ("V1", "V2")
    assert "a" in bc.supplied and "b" in bc.supplied and "varargs" in bc.supplied


def test_bind_expression_call_applies_defaults_outside_supplied():
    def protocol(self, x, /, overflow=None):
        pass

    bc = bind_expression_call(
        operation_key="OP", backend=CONST_BACKEND.POLARS, dialect="polars",
        protocol_method=protocol, arguments=[LiteralNode(value=7)], options={},
    )
    assert bc.bindings["overflow"] is None
    assert "overflow" not in bc.supplied
