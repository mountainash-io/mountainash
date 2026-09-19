"""Predicate policies evaluate the supplied concrete call without cross-axis leakage."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.predicates import BoundCall
from mountainash.core.capabilities.schema import Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate
from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-polars"))


@pytest.fixture(autouse=True)
def isolate():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def test_strategy_predicate_ignores_co_bound_tolerance():
    rule = CapabilityPolicyRule(
        CapabilityKey(
            RKEY_MOUNTAINASH_REL.JOIN_ASOF,
            "strategy",
            Selector("predicate", Predicate((Clause("strategy", ClauseOp.EQ, "forward"),))),
        ),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "forward as-of joins are unavailable",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.relations.backends.capabilities.ibis.dialects.ibis_polars.extensions_mountainash.relation",
        _SCOPE, CapabilitySegment(Domain.RELATION, policies=(rule,)),
    ))
    backward = BoundCall(
        RKEY_MOUNTAINASH_REL.JOIN_ASOF, CONST_BACKEND.IBIS, "ibis-polars",
        {"strategy": "backward", "tolerance": 1}, frozenset({"strategy", "tolerance"}),
    )
    forward = BoundCall(
        RKEY_MOUNTAINASH_REL.JOIN_ASOF, CONST_BACKEND.IBIS, "ibis-polars",
        {"strategy": "forward", "tolerance": 1}, frozenset({"strategy", "tolerance"}),
    )
    assert CapabilityRegistry.violations_for(backward) == frozenset()
    assert CapabilityRegistry.violations_for(forward) == frozenset({rule.qualify(_SCOPE)})
