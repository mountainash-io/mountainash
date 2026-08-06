"""Deterministic enumeration + bucketed value-class index (spec rev 3, §2/§6)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
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


def _vc_fact(op, dialect=None, vc=ValueClass.DURATION_MULTIPLIER):
    return CapabilityFact(
        operation_key=op, param="unit", level=CapabilityLevel.UNSUPPORTED,
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
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.DURATION_MULTIPLIER),
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.POLARS_OFFSET),
    ])
    out = CapabilityRegistry.facts()
    assert [f.value_class for f in out] == sorted(
        [f.value_class for f in out], key=lambda v: v.value
    )
    # registration order reversed must give the same enumeration
    CapabilityRegistry.reset()
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.POLARS_OFFSET),
        _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.DURATION_MULTIPLIER),
    ])
    assert CapabilityRegistry.facts() == out
