"""Concrete value-class policies resolve only when their selector matches."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer, ValueClass
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))


@pytest.fixture(autouse=True)
def isolate():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def _rule(value_class=ValueClass.DURATION_MULTIPLIER):
    return CapabilityPolicyRule(
        CapabilityKey(FK.TRUNCATE, "unit", Selector("value_class", value_class)),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "multiplier units are unavailable",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )


def _publish(*rules):
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.extensions_mountainash.datetime",
        _SCOPE, CapabilitySegment(Domain.DATETIME, policies=rules),
    ))


def test_value_class_policy_resolves_only_for_matching_value():
    _publish(_rule())
    matching = CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "2d")
    assert matching is not None
    assert matching.value_class is ValueClass.DURATION_MULTIPLIER
    assert CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "1d") is None


def test_snapshot_restore_retains_value_class_policy():
    _publish(_rule())
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "2d") is None
    CapabilityRegistry.restore(snapshot)
    assert CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "2d") is not None
