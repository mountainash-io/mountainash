"""Executable policies require an explicit consumer, action, and native identity."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel
from mountainash.core.capabilities.declarations import CapabilityKey, CapabilityPolicyRule
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR


def _rule(*, consumer=PolicyConsumer.GATE, action=PolicyAction.BLOCK,
          level=CapabilityLevel.UNSUPPORTED, **kwargs):
    return CapabilityPolicyRule(
        CapabilityKey(FK_STR.CONTAINS, "substring"), level, "2026-09-18",
        "explicit test policy", consumer, action, **kwargs,
    )


def test_gate_policy_requires_matching_block_or_permit_action():
    with pytest.raises(ValueError, match="gate BLOCK"):
        _rule(action=PolicyAction.PERMIT)
    with pytest.raises(ValueError, match="PERMIT"):
        _rule(level=CapabilityLevel.EXPR_CAPABLE, action=PolicyAction.BLOCK)
    assert _rule().consumer is PolicyConsumer.GATE


@pytest.mark.parametrize("consumer", (PolicyConsumer.IMMEDIATE_ERROR, PolicyConsumer.MATERIALIZATION_ERROR))
def test_native_error_enrichment_requires_native_identity(consumer):
    with pytest.raises(ValueError, match="native"):
        _rule(consumer=consumer, action=PolicyAction.ENRICH)
    rule = _rule(
        consumer=consumer,
        action=PolicyAction.ENRICH,
        native_errors=(TypeError,),
        native_issue="TEST-NATIVE-FAILURE",
    )
    assert rule.native_errors == (TypeError,)
    assert rule.native_issue == "TEST-NATIVE-FAILURE"


def test_result_protection_has_its_own_detection_action():
    with pytest.raises(ValueError, match="result-protection"):
        _rule(consumer=PolicyConsumer.RESULT_PROTECTION, action=PolicyAction.BLOCK)
    rule = _rule(
        consumer=PolicyConsumer.RESULT_PROTECTION,
        action=PolicyAction.DETECT_NON_NULL_TO_NULL,
    )
    assert rule.action is PolicyAction.DETECT_NON_NULL_TO_NULL
