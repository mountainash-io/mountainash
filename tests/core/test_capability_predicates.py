"""Predicate schema + engine tests (backlog 66b, spec 2026-07-28)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities.schema import (
    Boundary, CapabilityFact, CapabilityLevel, Clause, ClauseOp, Enforcement,
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


def test_fact_predicate_requires_gate_enforcement():
    with pytest.raises(ValueError, match="GATE"):
        CapabilityFact(
            operation_key="TRUNCATE", param="unit", level=CapabilityLevel.UNSUPPORTED,
            backend=CONST_BACKEND.IBIS, dialect="ibis-duckdb", message="x",
            since="2026-08-15",
            predicate=Predicate((Clause("unit", ClauseOp.EQ, "WEEK"),)),
            enforcement=Enforcement.ROUTER_METADATA,
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
