"""Deterministic enumeration + bucketed value-class index (spec rev 3, §2/§6)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)


@pytest.fixture
def isolated():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _vc_fact(op, dialect=None, vc=ValueClass.DURATION_MULTIPLIER, param="unit"):
    return CapabilityFact(
        operation_key=op, param=param, level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS, dialect=dialect, value_class=vc,
        message="t", since="2026-08-07", probe_exempt="test",
    )


def test_value_class_lookup_still_resolves(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])
    fact = CapabilityRegistry.capability_for(
        FK_DT.TRUNCATE, "unit", CONST_BACKEND.IBIS,
        dialect="ibis-duckdb", option_value="2d",
    )
    assert fact is not None and fact.value_class is ValueClass.DURATION_MULTIPLIER


def test_duplicate_value_class_key_rejected(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_backend(
            CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)]
        )


def test_facts_enumeration_is_sorted_and_total(isolated):
    # Facts spanning op, dialect AND value_class so the assertion pins the FULL
    # canonical ordering, not just the value_class component (T3 review).
    def _facts():
        return [
            _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.DURATION_MULTIPLIER),
            _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.POLARS_OFFSET),
            _vc_fact(FK_DT.TRUNCATE, dialect="ibis-duckdb",
                     vc=ValueClass.DURATION_MULTIPLIER),
            _vc_fact(FK_DT.ADD_DAYS, vc=ValueClass.DURATION_MULTIPLIER, param="days"),
        ]
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, _facts())
    out = CapabilityRegistry.facts()
    # Explicit expected order pins op (ADD_DAYS < TRUNCATE), dialect
    # (family None < "ibis-duckdb") and value_class (duration < polars_offset) —
    # a value_class-only fixture would leave op/dialect ordering unexercised.
    assert [(f.operation_key, f.dialect, f.value_class) for f in out] == [
        (FK_DT.ADD_DAYS, None, ValueClass.DURATION_MULTIPLIER),
        (FK_DT.TRUNCATE, None, ValueClass.DURATION_MULTIPLIER),
        (FK_DT.TRUNCATE, None, ValueClass.POLARS_OFFSET),
        (FK_DT.TRUNCATE, "ibis-duckdb", ValueClass.DURATION_MULTIPLIER),
    ]
    # Registration order must not change enumeration (determinism).
    CapabilityRegistry.reset()
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, list(reversed(_facts())))
    assert CapabilityRegistry.facts() == out


def _residue_fact(op, option_value):
    return CapabilityFact(
        operation_key=op, param="length", level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS, dialect=None, option_value=option_value,
        boundary=Boundary.MATERIALIZE, native_errors=(ValueError,),
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        message="t", since="2026-08-07", probe_exempt="test",
    )


def test_residue_for_rejects_equal_specificity_collision(isolated):
    # residue_for groups MATERIALIZE_RESIDUE facts by (op, param); two at
    # IDENTICAL dialect-specificity (both family-level, dialect=None) are
    # ambiguous and must raise. register_backend's dedup plus its
    # "value-scoped => BUILD boundary" rule make this state unreachable via the
    # public path, so we seed the two facts directly into the internal index to
    # exercise the defensive guard (implemented at T3, untested — final M-5).
    CapabilityRegistry._facts[
        (FK_DT.TRUNCATE, "length", CONST_BACKEND.IBIS, None, "a")] = _residue_fact(
            FK_DT.TRUNCATE, "a")
    CapabilityRegistry._facts[
        (FK_DT.TRUNCATE, "length", CONST_BACKEND.IBIS, None, "b")] = _residue_fact(
            FK_DT.TRUNCATE, "b")
    with pytest.raises(ValueError, match="ambiguous MATERIALIZE_RESIDUE"):
        CapabilityRegistry.residue_for(CONST_BACKEND.IBIS)
