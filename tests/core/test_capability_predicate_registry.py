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


def test_register_backend_routes_predicate_facts(isolated):
    f = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [f])
    assert f in CapabilityRegistry._predicate_facts
    assert CapabilityRegistry.capability_for(_OP, "x", CONST_BACKEND.POLARS, "polars") is None
    assert not any(x.predicate is not None for x in CapabilityRegistry._facts.values())


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


def test_no_conflict_when_strictly_subsumed(isolated):
    block = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    permit = _fact("x", CapabilityLevel.EXPR_CAPABLE, Predicate(
        (Clause("x", ClauseOp.EQ, 7), Clause("overflow", ClauseOp.EQ, "saturating"))))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [block, permit])  # no raise


def test_no_conflict_when_disjoint(isolated):
    block = _fact("x", CapabilityLevel.UNSUPPORTED, Predicate((Clause("x", ClauseOp.EQ, 7),)))
    permit = _fact("x", CapabilityLevel.EXPR_CAPABLE, Predicate((Clause("x", ClauseOp.EQ, 9),)))
    CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, [block, permit])  # disjoint: no raise


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
