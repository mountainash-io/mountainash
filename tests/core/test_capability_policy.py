"""Immutable capability-policy selections and ambient scope isolation."""
from __future__ import annotations


def test_policy_configuration_is_frozen_and_rejects_malformed_fields():
    from dataclasses import FrozenInstanceError

    import pytest

    from mountainash.core.capabilities.policy import CapabilityPolicy, ProtectionMechanism
    from mountainash.core.capabilities.schema import CapabilityIssueClass

    policy = CapabilityPolicy.checked()
    assert type(policy.mechanisms) is frozenset
    with pytest.raises(FrozenInstanceError):
        policy.protection = "none"

    with pytest.raises((TypeError, ValueError)):
        CapabilityPolicy(protection={CapabilityIssueClass.AVAILABILITY})
    with pytest.raises((TypeError, ValueError)):
        CapabilityPolicy(protection="availability")
    with pytest.raises((TypeError, ValueError)):
        CapabilityPolicy(error_enrichment=lambda _: True)
    with pytest.raises((TypeError, ValueError)):
        CapabilityPolicy(disclosure=frozenset({"arbitrary-rule-id"}))
    with pytest.raises((TypeError, ValueError)):
        CapabilityPolicy(mechanisms={ProtectionMechanism.GATE})
    with pytest.raises((TypeError, ValueError)):
        CapabilityPolicy(mechanisms=frozenset({"GATE"}))


def test_presets_apply_closed_action_and_mechanism_selection_after_overrides():
    from mountainash.core.capabilities.policy import CapabilityPolicy, ProtectionMechanism
    from mountainash.core.capabilities.schema import CapabilityIssueClass, PolicyConsumer

    availability = frozenset({CapabilityIssueClass.AVAILABILITY})
    unclassified = frozenset({CapabilityIssueClass.UNCLASSIFIED})
    default_checked = CapabilityPolicy.checked()
    for issue_classes in (availability, unclassified):
        for consumer in PolicyConsumer:
            assert default_checked.selects(consumer, issue_classes) is True
            assert default_checked.has_demand(consumer) is True
        assert default_checked.discloses(issue_classes) is True

    checked = CapabilityPolicy.checked(
        protection=availability,
        error_enrichment="none",
        disclosure="none",
        mechanisms=frozenset({ProtectionMechanism.GATE}),
    )

    assert checked.selects(PolicyConsumer.GATE, availability) is True
    assert checked.has_demand(PolicyConsumer.GATE) is True
    assert checked.selects(PolicyConsumer.RESULT_PROTECTION, availability) is False
    assert checked.has_demand(PolicyConsumer.RESULT_PROTECTION) is False
    assert checked.selects(PolicyConsumer.IMMEDIATE_ERROR, availability) is False
    assert checked.selects(PolicyConsumer.MATERIALIZATION_ERROR, availability) is False
    assert checked.discloses(availability) is False

    debugging = CapabilityPolicy.native_debugging()
    trusted = CapabilityPolicy.trusted()
    assert debugging.selects(PolicyConsumer.GATE, availability) is True
    assert debugging.selects(PolicyConsumer.RESULT_PROTECTION, availability) is True
    assert debugging.selects(PolicyConsumer.IMMEDIATE_ERROR, availability) is False
    assert debugging.selects(PolicyConsumer.MATERIALIZATION_ERROR, availability) is False
    assert debugging.discloses(availability) is True
    assert trusted.selects(PolicyConsumer.GATE, availability) is False
    assert trusted.selects(PolicyConsumer.IMMEDIATE_ERROR, availability) is False
    assert trusted.discloses(availability) is False


def test_multiclass_and_empty_selections_remain_closed_per_consumer():
    from mountainash.core.capabilities.policy import CapabilityPolicy, ProtectionMechanism
    from mountainash.core.capabilities.schema import CapabilityIssueClass, PolicyConsumer

    availability = CapabilityIssueClass.AVAILABILITY
    semantics = CapabilityIssueClass.SEMANTICS
    argument_contract = CapabilityIssueClass.ARGUMENT_CONTRACT
    issue_classes = frozenset({availability, semantics})
    policy = CapabilityPolicy(
        protection=issue_classes,
        error_enrichment=issue_classes,
        disclosure=issue_classes,
        mechanisms=frozenset({
            ProtectionMechanism.GATE,
            ProtectionMechanism.MATERIALIZATION,
        }),
    )

    assert policy.selects(PolicyConsumer.GATE, frozenset({availability})) is True
    assert policy.selects(PolicyConsumer.GATE, frozenset({argument_contract, semantics})) is True
    assert policy.selects(PolicyConsumer.RESULT_PROTECTION, frozenset({semantics})) is True
    assert policy.selects(PolicyConsumer.IMMEDIATE_ERROR, frozenset({availability})) is True
    assert policy.selects(PolicyConsumer.MATERIALIZATION_ERROR, frozenset({semantics})) is True
    assert policy.discloses(frozenset({availability, semantics})) is True
    assert policy.selects(PolicyConsumer.GATE, frozenset({argument_contract})) is False
    assert policy.selects(PolicyConsumer.GATE, frozenset()) is False
    assert policy.discloses(frozenset()) is False

    empty = CapabilityPolicy(
        protection=frozenset(),
        error_enrichment=frozenset(),
        disclosure=frozenset(),
        mechanisms=frozenset({
            ProtectionMechanism.GATE,
            ProtectionMechanism.MATERIALIZATION,
        }),
    )
    for consumer in PolicyConsumer:
        assert empty.selects(consumer, frozenset({availability})) is False
        assert empty.has_demand(consumer) is False
    assert empty.discloses(frozenset({availability})) is False


def test_nested_policy_replacement_restores_on_error_and_isolates_tasks():
    import asyncio

    import pytest

    from mountainash.core.capabilities.policy import (
        CapabilityPolicy,
        _resolve_policy,
        capability_policy,
    )
    from mountainash.core.capabilities.schema import CapabilityIssueClass, PolicyConsumer

    availability = frozenset({CapabilityIssueClass.AVAILABILITY})

    def selected():
        return _resolve_policy().selects(PolicyConsumer.GATE, availability)

    before = selected()
    with capability_policy(CapabilityPolicy.checked(protection=availability)):
        assert selected()
        with pytest.raises(RuntimeError):
            with capability_policy(CapabilityPolicy(protection="none")):
                assert not selected()
                raise RuntimeError("scope must restore")
        assert selected()
    assert selected() == before

    async def worker(policy):
        with capability_policy(policy):
            await asyncio.sleep(0)
            return selected()

    async def run():
        return await asyncio.gather(
            worker(CapabilityPolicy.checked(protection=availability)),
            worker(CapabilityPolicy.trusted()),
        )

    assert asyncio.run(run()) == [True, False]


def test_explicit_thread_scopes_remain_independent():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from mountainash.core.capabilities.policy import (
        CapabilityPolicy,
        _resolve_policy,
        capability_policy,
    )
    from mountainash.core.capabilities.schema import CapabilityIssueClass, PolicyConsumer

    availability = frozenset({CapabilityIssueClass.AVAILABILITY})
    with capability_policy(CapabilityPolicy.trusted()):
        with ThreadPoolExecutor(max_workers=1) as unrelated:
            inherited = unrelated.submit(
                lambda: _resolve_policy().selects(PolicyConsumer.GATE, availability),
            )
            assert inherited.result(timeout=15) is True

    barrier = Barrier(2)

    def selected(policy):
        with capability_policy(policy):
            barrier.wait(timeout=10)
            return _resolve_policy().selects(PolicyConsumer.GATE, availability)

    with ThreadPoolExecutor(max_workers=2) as pool:
        checked = pool.submit(selected, CapabilityPolicy.checked())
        trusted = pool.submit(selected, CapabilityPolicy.trusted())
        assert checked.result(timeout=15) is True
        assert trusted.result(timeout=15) is False
