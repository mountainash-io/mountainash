"""Registry integration for predicate facts (backlog 66b)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.capabilities.predicates import BoundCall
from mountainash.core.capabilities.schema import (
    CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)

# abs(self, x, /, overflow=None) — params "x" (arg) and "overflow" (option).
_OP = FK_ARITH.ABS


def _fact(param, level, predicate, *, backend=CONST_BACKEND.POLARS, dialect="polars"):
    return CapabilityFact(
        operation_key=_OP, param=param, level=level, backend=backend,
        dialect=dialect, message=f"{param} limitation", since="2026-08-15",
        predicate=predicate,
    )


def _call(**bindings):
    return BoundCall(
        operation_key=_OP, backend=CONST_BACKEND.POLARS, dialect="polars",
        bindings=bindings, supplied=frozenset(bindings),
    )


@pytest.fixture()
def isolated():
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    yield
    CapabilityRegistry.restore(snap)




def test_violations_for_collects_matching_blocking_fact(isolated):
    f = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [f])
    assert CapabilityRegistry.violations_for(_call(x=7)) == frozenset({f})
    assert CapabilityRegistry.violations_for(_call(x=9)) == frozenset()


def test_violations_for_filters_backend_dialect_level(isolated):
    f = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [f])
    ibis_call = BoundCall(_OP, CONST_BACKEND.IBIS, "ibis-duckdb", {"x": 7}, frozenset({"x"}))
    assert CapabilityRegistry.violations_for(ibis_call) == frozenset()
    fam = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)), dialect=None)
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fam])
    assert fam in CapabilityRegistry.violations_for(_call(x=7))


def test_violations_for_skips_non_blocking(isolated):
    perm = _fact("x", CapabilityLevel.EXPR_CAPABLE, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [perm])
    assert CapabilityRegistry.violations_for(_call(x=7)) == frozenset()


def test_conflict_raise_on_incomparable_block_and_permit(isolated):
    block = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    permit = _fact("overflow", CapabilityLevel.EXPR_CAPABLE, Predicate((Clause("overflow", ClauseOp.EQ, "saturating"),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [block])
    with pytest.raises(ValueError, match="conflict"):
        CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [permit])


def test_conflict_detected_across_different_params(isolated):
    # review finding 1: param is a reporting label, not a conflict-scope key.
    pred = Predicate((Clause("x", ClauseOp.EQ, 7), Clause("overflow", ClauseOp.EQ, "saturating")))
    block = _fact("x", CapabilityLevel.UNSUPPORTED, pred)
    permit = _fact("overflow", CapabilityLevel.EXPR_CAPABLE, pred)
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [block])
    with pytest.raises(ValueError, match="conflict"):
        CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [permit])






def test_facts_includes_predicate_facts(isolated):
    f = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [f])
    assert f in CapabilityRegistry.facts()


def test_snapshot_round_trips_predicate_facts(isolated):
    f = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [f])
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert CapabilityRegistry.violations_for(_call(x=7)) == frozenset()
    CapabilityRegistry.restore(snap)
    assert CapabilityRegistry.violations_for(_call(x=7)) == frozenset({f})


def _metadata_fact():
    return _fact("overflow", CapabilityLevel.UNSUPPORTED, Predicate((
        Clause("overflow", ClauseOp.EQ, "saturating"),
        Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),
    )))


def test_raw_gate_defers_whole_metadata_conjunction(isolated):
    fact = _metadata_fact()
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fact])
    assert CapabilityRegistry.violations_for(_call(x=1, overflow="saturating"), phase="raw") == frozenset()
    with pytest.raises(ValueError):
        CapabilityRegistry.violations_for(_call(x=1, overflow="other"))


def test_complete_gate_distinguishes_operand_type_and_option(isolated):
    from dataclasses import replace
    from mountainash.core.dtypes.metadata import OperandType

    fact = _metadata_fact()
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fact])
    call = _call(x=1, overflow="saturating")
    floating = replace(call, operand_types={"x": OperandType("float", "native", True)})
    integer = replace(call, operand_types={"x": OperandType("integer", "native", True)})
    assert CapabilityRegistry.violations_for(floating) == frozenset({fact})
    assert CapabilityRegistry.violations_for(integer) == frozenset()
    assert CapabilityRegistry.violations_for(replace(floating, bindings={"x": 1, "overflow": "other"})) == frozenset()


@pytest.mark.parametrize("path, operand", [
    ("__operand_types__", "float"),
    ("__operand_types__.x", "float"),
    ("__operand_types__.x.native_dtype", "float"),
    ("__operand_types__.overflow.logical_kind", "float"),
    ("__operand_types__.missing.logical_kind", "float"),
    ("__operand_types__.x.logical_kind", "decimal"),
    ("__operand_types__.x.storage_kind", "arbitrary"),
    ("__operand_types__.x.nullable", 1),
])
def test_registration_rejects_invalid_metadata_selectors(isolated, path, operand):
    fact = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((
        Clause("x", ClauseOp.IS_SET), Clause(path, ClauseOp.EQ, operand),
    )))
    with pytest.raises(ValueError):
        CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fact])


def test_metadata_facts_cannot_declare_permitting_refinements(isolated):
    from dataclasses import replace

    fact = replace(_metadata_fact(), level=CapabilityLevel.EXPR_CAPABLE)
    with pytest.raises(ValueError):
        CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fact])


def test_bound_call_rejects_user_supplied_metadata_namespace():
    with pytest.raises(ValueError):
        _call(__operand_types__={"x": {"logical_kind": "integer"}})


def test_complete_metadata_gate_requires_each_referenced_descriptor(isolated):
    from dataclasses import replace
    from mountainash.core.dtypes.metadata import OperandType

    fact = _metadata_fact()
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fact])
    call = replace(_call(x=1, overflow="other"), operand_types={"different": OperandType("integer", "native", True)})
    with pytest.raises(ValueError):
        CapabilityRegistry.violations_for(call)


def test_metadata_only_fact_keeps_operand_reporting_identity(isolated):
    from dataclasses import replace
    from mountainash.core.dtypes.metadata import OperandType

    fact = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((
        Clause("__operand_types__.x.storage_kind", ClauseOp.EQ, "polars_object"),
    )))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [fact])
    call = replace(_call(x=1), operand_types={"x": OperandType("unknown", "polars_object", None)})
    assert CapabilityRegistry.violations_for(call) == frozenset({fact})
    assert fact in CapabilityRegistry.facts()
