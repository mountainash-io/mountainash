"""Explicit policy publication and exact-scope registry lookup."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.applicability import unbounded
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


def _policy(
    subject="substring",
    *,
    message="contains is unavailable",
    consumer=PolicyConsumer.GATE,
    action=PolicyAction.BLOCK,
    level=CapabilityLevel.UNSUPPORTED,
    **kwargs,
):
    return CapabilityPolicyRule(
        CapabilityKey(FK_STR.CONTAINS, subject),
        level,
        message,
        consumer,
        action,
        applicability=kwargs.pop("applicability", unbounded),
        **kwargs,
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
    new_operation = replace(_policy(), key=CapabilityKey(FK_STR.CENTER, "length"))
    duplicate = _segment(new_operation, _policy(), suffix=".duplicate")
    CapabilityRegistry.register_segment(initial)

    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_segment(duplicate)

    assert CapabilityRegistry.segments() == (initial,)
    assert CapabilityRegistry.reader(_SCOPE).policy(_policy().key).assertion is initial.segment.policies[0]
    assert CapabilityRegistry.has_policy_candidates(
        FK_STR.CONTAINS, CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.GATE,
    )
    assert not CapabilityRegistry.has_policy_candidates(
        FK_STR.CENTER, CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.GATE,
    )


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
    assert (
        CapabilityRegistry.capability_for(
            FK_STR.CONTAINS, "input", CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.IMMEDIATE_ERROR
        ).native_issue
        == "POLARS-CONTAINS-NATIVE"
    )
    assert (
        CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars-unknown") is None
    )
    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS) is None


def test_presence_follows_publication_reset_and_restore():
    def present():
        return CapabilityRegistry.has_policy_candidates(
            FK_STR.CONTAINS, CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.GATE,
        )

    assert present() is False
    CapabilityRegistry.register_segment(_segment(_policy()))
    assert present() is True
    accepted = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert present() is False
    CapabilityRegistry.restore(accepted)
    assert present() is True


@pytest.mark.parametrize(
    ("consumer", "action", "error_fields"),
    [
        (PolicyConsumer.GATE, PolicyAction.BLOCK, {}),
        (PolicyConsumer.IMMEDIATE_ERROR, PolicyAction.ENRICH,
         {"native_errors": (TypeError,), "native_issue": "CONTAINS-NATIVE"}),
        (PolicyConsumer.MATERIALIZATION_ERROR, PolicyAction.ENRICH,
         {"native_errors": (TypeError,), "native_issue": "CONTAINS-NATIVE"}),
        (PolicyConsumer.RESULT_PROTECTION, PolicyAction.DETECT_NON_NULL_TO_NULL, {}),
    ],
)
def test_presence_is_exact_to_operation_backend_dialect_and_consumer(consumer, action, error_fields):
    CapabilityRegistry.register_segment(_segment(_policy(consumer=consumer, action=action, **error_fields)))
    for queried_consumer in PolicyConsumer:
        assert CapabilityRegistry.has_policy_candidates(
            FK_STR.CONTAINS, CONST_BACKEND.POLARS, "polars", consumer=queried_consumer,
        ) is (queried_consumer is consumer)
    for operation, backend, dialect in (
        (FK_STR.CENTER, CONST_BACKEND.POLARS, "polars"),
        (FK_STR.CONTAINS, CONST_BACKEND.IBIS, "polars"),
        (FK_STR.CONTAINS, CONST_BACKEND.POLARS, "polars-unknown"),
        (FK_STR.CONTAINS, CONST_BACKEND.POLARS, None),
        (FK_STR.CONTAINS, "polars", "polars"),
    ):
        assert not CapabilityRegistry.has_policy_candidates(operation, backend, dialect, consumer=consumer)


def test_presence_includes_nonblocking_rules():
    CapabilityRegistry.register_segment(
        _segment(_policy(level=CapabilityLevel.EXPR_CAPABLE, action=PolicyAction.PERMIT))
    )
    assert CapabilityRegistry.has_policy_candidates(
        FK_STR.CONTAINS, CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.GATE,
    )


def test_context_aware_direct_lookup_selects_only_the_applicable_enabled_versioned_variant():
    from types import SimpleNamespace

    from mountainash.core.capabilities.applicability import (
        Applicability,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate
    from mountainash.core.capabilities.policy import CapabilityPolicy
    from tests.fixtures.capability_observations import require_observations

    def interval(lower, upper):
        return Applicability(
            (Region((CoordinateConstraint("package", "polars", specifier=">=" + lower + ",<" + upper),)),)
        )

    earlier = replace(
        _policy(),
        key=replace(_policy().key, variant="earlier"),
        applicability=interval("1", "2"),
    )
    later = replace(
        earlier,
        key=replace(earlier.key, variant="later"),
        applicability=interval("2", "3"),
    )
    CapabilityRegistry.register_segment(_segment(earlier, later, suffix=".versioned_direct"))
    assert CapabilityRegistry.has_policy_candidates(
        FK_STR.CONTAINS, CONST_BACKEND.POLARS, "polars", consumer=PolicyConsumer.GATE,
    )

    def context(version, policy=CapabilityPolicy.checked()):
        observed = Environment((EnvironmentCoordinate("package", "polars", version),))
        return SimpleNamespace(
            policy=policy,
            environment=require_observations(earlier.applicability, observed),
        )

    assert CapabilityRegistry.capability_for(
        FK_STR.CONTAINS,
        "substring",
        CONST_BACKEND.POLARS,
        "polars",
        execution_context=context("1.5"),
    ) == earlier.qualify(_SCOPE)
    assert CapabilityRegistry.capability_for(
        FK_STR.CONTAINS,
        "substring",
        CONST_BACKEND.POLARS,
        "polars",
        execution_context=context("2.5"),
    ) == later.qualify(_SCOPE)
    assert (
        CapabilityRegistry.capability_for(
            FK_STR.CONTAINS,
            "substring",
            CONST_BACKEND.POLARS,
            "polars",
            execution_context=SimpleNamespace(
                policy=CapabilityPolicy.checked(),
                environment=prepare_environment(Environment(), earlier.applicability.requirements),
            ),
        )
        is None
    )
    assert (
        CapabilityRegistry.capability_for(
            FK_STR.CONTAINS,
            "substring",
            CONST_BACKEND.POLARS,
            "polars",
            execution_context=context("1.5", CapabilityPolicy.trusted()),
        )
        is None
    )
    assert (
        CapabilityRegistry.capability_for(
            FK_STR.CONTAINS,
            "substring",
            CONST_BACKEND.POLARS,
            "polars",
        )
        is None
    )
