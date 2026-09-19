"""Integrity guards for retained information and explicit executable policies."""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityRegistry, load_all_capability_declarations
from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery, PolicyQuery
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer


def test_loaded_publication_has_only_concrete_policy_scopes():
    load_all_capability_declarations()
    result = CapabilityRegistry.capture().search(CatalogueQuery(
        information=InformationQuery(), policies=PolicyQuery(),
    ))
    assert result.information is not None
    assert result.policies is not None
    for record in result.policies:
        assert record.key.scope.dialect is not None
        assert record.assertion.consumer is not None
        assert record.assertion.action is not None


def test_native_error_policies_carry_their_native_identity():
    policies = CapabilityRegistry.capture().search(CatalogueQuery(policies=PolicyQuery())).policies
    assert policies is not None
    for record in policies:
        policy = record.assertion
        if policy.consumer in (PolicyConsumer.IMMEDIATE_ERROR, PolicyConsumer.MATERIALIZATION_ERROR):
            assert policy.action is PolicyAction.ENRICH
            assert policy.native_errors
            assert policy.native_issue


def test_result_protection_uses_its_distinct_consumer_contract():
    policies = CapabilityRegistry.capture().search(CatalogueQuery(
        policies=PolicyQuery(consumer=PolicyConsumer.RESULT_PROTECTION),
    )).policies
    assert policies is not None
    for record in policies:
        assert record.assertion.action is PolicyAction.DETECT_NON_NULL_TO_NULL
