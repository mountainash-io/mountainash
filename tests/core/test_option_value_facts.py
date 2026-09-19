"""Exact option policies match one value; overlapping answers cannot compete."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
)

_SCOPE = Scope(CONST_BACKEND.POLARS, Dialect("polars"))


@pytest.fixture(autouse=True)
def isolated():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def _policy(selector=Selector(), *, subject="overflow"):
    return CapabilityPolicyRule(
        CapabilityKey(FK_ARITH.ABS, subject, selector), CapabilityLevel.UNSUPPORTED,
        "2026-09-18", "checked overflow unavailable",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )


def _publish(*policies):
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.arithmetic.option_cases",
        _SCOPE, CapabilitySegment(Domain.ARITHMETIC, policies=policies),
    ))


def test_exact_option_policy_does_not_block_other_values():
    policy = _policy(Selector("exact", "ERROR"))
    _publish(policy)
    assert CapabilityRegistry.capability_for(
        FK_ARITH.ABS, "overflow", CONST_BACKEND.POLARS, "polars", "ERROR"
    ) == policy.qualify(_SCOPE)
    for value in ("SATURATE", None):
        assert CapabilityRegistry.capability_for(
            FK_ARITH.ABS, "overflow", CONST_BACKEND.POLARS, "polars", value
        ) is None


def test_unconditioned_option_policy_covers_the_requested_value():
    policy = _policy()
    _publish(policy)
    assert CapabilityRegistry.capability_for(
        FK_ARITH.ABS, "overflow", CONST_BACKEND.POLARS, "polars", "ERROR"
    ) == policy.qualify(_SCOPE)


def test_overlapping_option_answers_are_rejected_atomically():
    before = CapabilityRegistry.snapshot()
    with pytest.raises(ValueError):
        _publish(_policy(), _policy(Selector("exact", "ERROR")))
    assert CapabilityRegistry.snapshot() is before
    assert CapabilityRegistry.capability_for(
        FK_ARITH.ABS, "overflow", CONST_BACKEND.POLARS, "polars", "ERROR"
    ) is None


def test_exact_option_requires_a_named_subject():
    with pytest.raises(ValueError):
        _publish(_policy(Selector("exact", "ERROR"), subject="*"))


def test_exact_option_rejects_a_materialization_boundary():
    policy = CapabilityPolicyRule(
        CapabilityKey(FK_ARITH.ABS, "overflow", Selector("exact", "ERROR")),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "native checked-overflow failure",
        PolicyConsumer.MATERIALIZATION_ERROR, PolicyAction.ENRICH,
        native_errors=(RuntimeError,), native_issue="test:checked-overflow",
    )
    before = CapabilityRegistry.snapshot()
    with pytest.raises(ValueError):
        _publish(policy)
    assert CapabilityRegistry.snapshot() is before


def test_exact_option_rejects_a_relation_argument():
    from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL

    policy = CapabilityPolicyRule(
        CapabilityKey(RKEY_SUBSTRAIT_REL.FETCH, "count", Selector("exact", "10")),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "synthetic relation selector",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    before = CapabilityRegistry.snapshot()
    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.relations.backends.capabilities.polars.dialects.polars.substrait.relation.option_case",
            _SCOPE, CapabilitySegment(Domain.RELATION, policies=(policy,)),
        ))
    assert CapabilityRegistry.snapshot() is before
