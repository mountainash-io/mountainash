"""Typed information and policy declaration contracts."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityInformation,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    FactSource,
    Selector,
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.capabilities.schema import Clause, ClauseOp, InformationLayer, PolicyAction, PolicyConsumer, Predicate
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL


def _policy(key=None):
    key = key or CapabilityKey(FK_STR.CENTER, "length")
    return CapabilityPolicyRule(
        key,
        CapabilityLevel.LITERAL_ONLY if key.selector.kind == "unconditioned" else CapabilityLevel.UNSUPPORTED,
        "2026-09-18", "test policy", PolicyConsumer.GATE, PolicyAction.BLOCK,
    )


def test_classification_preserves_operation_homes():
    assert classify_source(FK_STR.CENTER) is FactSource.SUBSTRAIT
    assert classify_source(FK_DT.ADD_DAYS) is FactSource.MOUNTAINASH
    assert classify_domain(FK_STR.CENTER) is Domain.STRING
    assert classify_domain(FK_DT.ADD_DAYS) is Domain.DATETIME
    assert classify_domain(RKEY_MOUNTAINASH_REL.UNNEST) is Domain.RELATION


def test_selector_identity_distinguishes_typed_predicate_operands():
    true_key = CapabilityKey(FK_STR.CENTER, "length", Selector("predicate", Predicate((Clause("length", ClauseOp.EQ, True),))))
    one_key = CapabilityKey(FK_STR.CENTER, "length", Selector("predicate", Predicate((Clause("length", ClauseOp.EQ, 1),))))
    assert true_key != one_key
    segment = CapabilitySegment(Domain.STRING, policies=(_policy(true_key), _policy(one_key)))
    assert len(segment.policies) == 2


def test_segment_rejects_duplicate_explicit_policy_keys():
    rule = _policy()
    with pytest.raises(ValueError, match="duplicate policy key"):
        CapabilitySegment(Domain.STRING, policies=(rule, rule))


def test_bound_segment_qualifies_policy_only_for_its_concrete_scope():
    scope = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    segment = CapabilitySegment(Domain.STRING, information=(
        CapabilityInformation(CapabilityKey(FK_STR.CENTER, "length"), InformationLayer.PUBLIC,
                              CapabilityLevel.LITERAL_ONLY, "2026-09-18", "public limitation"),
    ), policies=(_policy(),))
    bound = BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string",
        scope,
        segment,
    )
    assert bound.scope is scope
    with pytest.raises(ValueError, match="policy requires a concrete"):
        BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.family.substrait.string",
            Scope(CONST_BACKEND.IBIS, FamilyWide()), segment,
        )


@pytest.mark.parametrize("variant", ("", 1, False), ids=("empty", "integer", "boolean"))
def test_capability_key_rejects_malformed_variant(variant):
    with pytest.raises(ValueError, match="variant"):
        CapabilityKey(FK_STR.CENTER, "length", variant=variant)


def test_policy_issue_classes_reject_unknown_and_mixed_unclassified_inputs():
    from dataclasses import replace

    from mountainash.core.capabilities.schema import CapabilityIssueClass

    rule = _policy()
    with pytest.raises(TypeError, match="issue classes"):
        replace(rule, issue_classes=frozenset({"semantics"}))
    with pytest.raises(ValueError, match="unclassified"):
        replace(
            rule,
            issue_classes=frozenset({
                CapabilityIssueClass.UNCLASSIFIED,
                CapabilityIssueClass.SEMANTICS,
            }),
        )
