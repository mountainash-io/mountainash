# tests/core/test_capability_value_class_gate.py
import pytest
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    CapabilityFact,
    CapabilityLevel,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK,
)


@pytest.fixture(autouse=True)
def _isolate():
    snap = CapabilityRegistry.snapshot()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _class_fact(**kw):
    base = dict(
        operation_key=FK.TRUNCATE,
        param="unit",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        since="2026-07-25",
        value_class=ValueClass.DURATION_MULTIPLIER,
        message="no multiplier",
    )
    base.update(kw)
    return CapabilityFact(**base)


def test_class_fact_resolves_on_exact_miss():
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_class_fact()])
    fact = CapabilityRegistry.capability_for(
        FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="2d"
    )
    assert fact is not None and fact.level is CapabilityLevel.UNSUPPORTED


def test_class_fact_ignores_non_matching_value():
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_class_fact()])
    # "1d" is not a multiplier — no class match, no other fact => None
    assert (
        CapabilityRegistry.capability_for(
            FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="1d"
        )
        is None
    )


def test_exact_fact_wins_over_class_fact():
    exact = _class_fact(
        value_class=None,
        option_value="2d",
        message="exact",
    )
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [exact, _class_fact()])
    fact = CapabilityRegistry.capability_for(
        FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="2d"
    )
    assert fact.message == "exact"


def test_dialect_class_beats_family_class_no_raise():
    family = _class_fact(dialect=None, message="family")
    dialect = _class_fact(dialect="ibis-duckdb", message="dialect")
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [family, dialect])
    fact = CapabilityRegistry.capability_for(
        FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="2d"
    )
    assert fact.message == "dialect"


def test_two_distinct_classes_matching_one_value_raise():
    # Design-review M-2: the predicates genuinely overlap — "2d" matches BOTH
    # DURATION_MULTIPLIER and POLARS_OFFSET. Register both classes on one
    # (op, param, backend, dialect) and query "2d": the disjointness guard must
    # raise. No monkeypatch needed — this is a real overlap.
    a = _class_fact(value_class=ValueClass.POLARS_OFFSET, message="offset")
    b = _class_fact(value_class=ValueClass.DURATION_MULTIPLIER, message="mult")
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [a, b])
    with pytest.raises((ValueError, RuntimeError), match="two distinct value classes"):
        CapabilityRegistry.capability_for(
            FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="2d"
        )


def test_class_facts_are_enumerable_via_facts_api():
    # Design-review I-4: facts() must surface class facts, not only _facts.
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_class_fact()])
    all_facts = CapabilityRegistry.facts()
    assert any(f.value_class is ValueClass.DURATION_MULTIPLIER for f in all_facts)


def test_snapshot_restore_round_trips_class_facts():
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_class_fact()])
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert (
        CapabilityRegistry.capability_for(
            FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="2d"
        )
        is None
    )
    CapabilityRegistry.restore(snap)
    assert (
        CapabilityRegistry.capability_for(
            FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", option_value="2d"
        )
        is not None
    )
