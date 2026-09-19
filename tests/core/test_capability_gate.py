"""Expression gating consumes concrete, explicitly authored policy records."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)

_POLARS = Scope(CONST_BACKEND.POLARS, Dialect("polars"))
_DF = pl.DataFrame({"text": ["abc"], "pat": ["b"], "number": [7]})


@pytest.fixture(autouse=True)
def isolated_registry():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def _publish_string(rule):
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.string",
        _POLARS, CapabilitySegment(Domain.STRING, policies=(rule,)),
    ))


def _publish_arithmetic(rule):
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.expressions.backends.capabilities.polars.dialects.polars.substrait.arithmetic",
        _POLARS, CapabilitySegment(Domain.ARITHMETIC, policies=(rule,)),
    ))


def test_literal_only_policy_blocks_dynamic_argument_but_allows_literal():
    rule = CapabilityPolicyRule(
        CapabilityKey(FK_STR.CONTAINS, "substring"), CapabilityLevel.LITERAL_ONLY,
        "2026-09-18", "substring must be literal", PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    _publish_string(rule)
    with pytest.raises(BackendCapabilityError, match="substring must be literal"):
        ma.col("text").str.contains(ma.col("pat")).compile(_DF)
    assert _DF.select(ma.col("text").str.contains("b").compile(_DF)).to_series().to_list() == [True]


def test_predicate_policy_blocks_only_its_matching_call():
    rule = CapabilityPolicyRule(
        CapabilityKey(FK_ARITH.ABS, "x", Selector("predicate", Predicate((Clause("x", ClauseOp.EQ, 7),)))),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "seven is intentionally blocked",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    _publish_arithmetic(rule)
    with pytest.raises(BackendCapabilityError, match="seven is intentionally blocked"):
        ma.lit(7).abs().compile(_DF)
    assert _DF.select(ma.lit(9).abs().compile(_DF)).to_series().to_list() == [9]


def test_policy_lookup_defaults_to_gate_and_never_uses_a_family_scope():
    rule = CapabilityPolicyRule(
        CapabilityKey(FK_STR.CONTAINS, "substring"), CapabilityLevel.UNSUPPORTED,
        "2026-09-18", "concrete only", PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    _publish_string(rule)
    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars") is not None
    assert CapabilityRegistry.capability_for(FK_STR.CONTAINS, "substring", CONST_BACKEND.POLARS) is None
