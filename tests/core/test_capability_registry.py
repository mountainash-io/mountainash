"""Explicit policy publication and exact-scope registry lookup."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
)
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


_SCOPE = Scope(CONST_BACKEND.POLARS, Dialect("polars"))


@pytest.fixture(autouse=True)
def isolated_registry():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def _policy(subject="substring", *, message="contains is unavailable", consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK, level=CapabilityLevel.UNSUPPORTED, **kwargs):
    return CapabilityPolicyRule(
        CapabilityKey(FK_STR.CONTAINS, subject), level, "2026-09-18", message,
        consumer, action, **kwargs,
    )


def _segment(*policies, scope=_SCOPE, suffix=""):
    home = "family" if scope.dialect is None else f"dialects.{scope.dialect.replace('-', '_')}"
    return BoundSegment(
        f"mountainash.expressions.backends.capabilities.polars.{home}.substrait.string{suffix}",
        scope,
        CapabilitySegment(Domain.STRING, policies=policies),
    )


def test_policy_publication_requires_a_concrete_scope():
    with pytest.raises(ValueError, match="concrete"):
        _segment(_policy(), scope=Scope(CONST_BACKEND.POLARS, FamilyWide()))


def test_duplicate_policy_rolls_back_the_whole_segment():
    initial = _segment(_policy(), suffix=".initial")
    duplicate = _segment(_policy(), suffix=".duplicate")
    CapabilityRegistry.register_segment(initial)

    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_segment(duplicate)

    assert CapabilityRegistry.segments() == (initial,)
    assert CapabilityRegistry.reader(_SCOPE).policy(_policy().key).assertion is initial.segment.policies[0]


def test_lookup_is_exact_to_the_concrete_dialect_and_consumer():
    gate = _policy()
    enrich = _policy(
        "input",
        consumer=PolicyConsumer.IMMEDIATE_ERROR,
        action=PolicyAction.ENRICH,
        native_errors=(TypeError,),
        native_issue="POLARS-CONTAINS-NATIVE",
        message="native contains failure",
    )
    CapabilityRegistry.register_segment(_segment(gate, enrich))

    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars") is not None
    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "input", CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.IMMEDIATE_ERROR).native_issue == "POLARS-CONTAINS-NATIVE"
    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars-unknown") is None
    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS) is None
