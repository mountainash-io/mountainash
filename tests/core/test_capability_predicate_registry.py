"""Predicate policy publication, resolution, and metadata boundaries."""

from __future__ import annotations

from dataclasses import replace

import polars as pl
import pytest

import mountainash as ma
from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.predicates import BoundCall
from mountainash.core.capabilities.schema import (
    Clause,
    ClauseOp,
    PolicyAction,
    PolicyConsumer,
    Predicate,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.core.dtypes.metadata import OperandType
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC as FK_ARITH,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


_OP = FK_ARITH.ABS
_SCOPE = Scope(CONST_BACKEND.POLARS, Dialect("polars"))


def _policy(subject, action, predicate, *, message=None):
    return CapabilityPolicyRule(
        key=CapabilityKey(_OP, subject, Selector("predicate", predicate)),
        level=(
            CapabilityLevel.UNSUPPORTED
            if action is PolicyAction.BLOCK
            else CapabilityLevel.EXPR_CAPABLE
        ),
        since="2026-09-18",
        message=message or f"{subject} {action.value}",
        consumer=PolicyConsumer.GATE,
        action=action,
    )


def _segment(*policies, suffix=""):
    return BoundSegment(
        "mountainash.expressions.backends.capabilities.polars."
        f"dialects.polars.substrait.arithmetic{suffix}",
        _SCOPE,
        CapabilitySegment(Domain.ARITHMETIC, policies=policies),
    )


def _call(**bindings):
    return BoundCall(
        operation_key=_OP,
        backend=CONST_BACKEND.POLARS,
        dialect="polars",
        bindings=bindings,
        supplied=frozenset(bindings),
    )


@pytest.fixture()
def isolated():
    snap = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snap)


def test_initial_ambiguous_policy_segment_rolls_back_every_rule(isolated):
    broad_block = _policy(
        "x",
        PolicyAction.BLOCK,
        Predicate((Clause("x", ClauseOp.IS_LITERAL),)),
        message="all literals are blocked",
    )
    narrow_permit = _policy(
        "x",
        PolicyAction.PERMIT,
        Predicate((Clause("x", ClauseOp.EQ, -7),)),
        message="minus seven is permitted",
    )
    segment = _segment(broad_block, narrow_permit, suffix=".ambiguous_initial")

    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(segment)

    assert CapabilityRegistry.segments() == ()
    reader = CapabilityRegistry.reader(_SCOPE)
    assert reader.policy_optional(broad_block.key) is None
    assert reader.policy_optional(narrow_permit.key) is None


def test_later_cross_segment_ambiguity_rolls_back_and_names_both_origins(isolated):
    broad_block = _policy(
        "x",
        PolicyAction.BLOCK,
        Predicate((Clause("x", ClauseOp.IS_LITERAL),)),
        message="all literals are blocked",
    )
    initial = _segment(broad_block, suffix=".initial_block")
    narrow_permit = _policy(
        "x",
        PolicyAction.PERMIT,
        Predicate((Clause("x", ClauseOp.EQ, -7),)),
        message="minus seven is permitted",
    )
    later = _segment(narrow_permit, suffix=".later_permit")
    CapabilityRegistry.register_segment(initial)

    with pytest.raises(ValueError) as raised:
        CapabilityRegistry.register_segment(later)

    # The origin addresses, rather than formatter-owned error prose, make the
    # failed publication actionable to declaration authors.
    assert initial.module in str(raised.value)
    assert later.module in str(raised.value)
    assert CapabilityRegistry.segments() == (initial,)
    reader = CapabilityRegistry.reader(_SCOPE)
    assert reader.policy(broad_block.key).assertion is broad_block
    assert reader.policy_optional(narrow_permit.key) is None


def test_opposing_predicate_policies_compete_across_subject_labels(isolated):
    broad_block = _policy(
        "x",
        PolicyAction.BLOCK,
        Predicate((Clause("x", ClauseOp.IS_LITERAL),)),
    )
    other_subject_permit = _policy(
        "overflow",
        PolicyAction.PERMIT,
        Predicate((Clause("x", ClauseOp.EQ, -7),)),
    )

    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(
            _segment(broad_block, other_subject_permit, suffix=".cross_subject")
        )


def test_same_subject_single_answer_selectors_compete(isolated):
    block_all = CapabilityPolicyRule(
        key=CapabilityKey(_OP, "overflow"),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message="all overflow modes are blocked",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
    )
    permit_error = CapabilityPolicyRule(
        key=CapabilityKey(_OP, "overflow", Selector("exact", "ERROR")),
        level=CapabilityLevel.EXPR_CAPABLE,
        since="2026-09-18",
        message="ERROR mode is permitted",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.PERMIT,
    )

    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(
            _segment(block_all, permit_error, suffix=".single_answer")
        )

def test_literal_only_protection_and_literal_permit_have_disjoint_call_shapes(isolated):
    dynamic_block = CapabilityPolicyRule(
        key=CapabilityKey(_OP, "x"),
        level=CapabilityLevel.LITERAL_ONLY,
        since="2026-09-18",
        message="Dynamic arguments are refused",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
    )
    literal_permit = _policy("x", PolicyAction.PERMIT, Predicate((Clause("x", ClauseOp.IS_LITERAL),)))
    CapabilityRegistry.register_segment(_segment(dynamic_block, literal_permit, suffix=".call_shapes"))

    dataframe = pl.DataFrame({"value": [-7, -8]})
    assert dataframe.select(ma.lit(-7).abs().compile(dataframe)).to_series().to_list() == [7]
    with pytest.raises(BackendCapabilityError):
        ma.col("value").abs().compile(dataframe)


def test_disjoint_finite_expression_partition_executes_allowed_literal_and_blocks_remainder(isolated):
    permitted = _policy(
        "x",
        PolicyAction.PERMIT,
        Predicate((Clause("x", ClauseOp.EQ, -7),)),
    )
    blocked = _policy(
        "x",
        PolicyAction.BLOCK,
        Predicate((Clause("x", ClauseOp.IN, frozenset({-8, -6})),)),
        message="the finite remainder is blocked",
    )
    CapabilityRegistry.register_segment(_segment(permitted, blocked, suffix=".finite_partition"))

    dataframe = pl.DataFrame({"value": [1, 2]})
    allowed = ma.lit(-7).abs().compile(dataframe)
    assert dataframe.select(allowed.alias("result"))["result"].to_list() == [7]
    with pytest.raises(BackendCapabilityError):
        ma.lit(-8).abs().compile(dataframe)


def test_multiple_independent_predicate_blockers_remain_visible_to_expression_visitor(isolated):
    x_block = _policy(
        "x",
        PolicyAction.BLOCK,
        Predicate((Clause("x", ClauseOp.EQ, -8),)),
    )
    overflow_block = _policy(
        "overflow",
        PolicyAction.BLOCK,
        Predicate((Clause("overflow", ClauseOp.EQ, "ERROR"),)),
    )
    CapabilityRegistry.register_segment(_segment(x_block, overflow_block, suffix=".collecting"))

    with pytest.raises(BackendCapabilityError) as raised:
        ma.lit(-8).abs(overflow="ERROR").compile(pl.DataFrame({"value": [1]}))
    assert set(raised.value.candidate_fact_keys) == {
        x_block.qualify(_SCOPE).fact_key,
        overflow_block.qualify(_SCOPE).fact_key,
    }


def _metadata_policy():
    return _policy(
        "overflow",
        PolicyAction.BLOCK,
        Predicate(
            (
                Clause("overflow", ClauseOp.EQ, "saturating"),
                Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),
            )
        ),
        message="floating saturating abs is blocked",
    )


def test_raw_metadata_gate_defers_and_complete_gate_requires_descriptors(isolated):
    policy = _metadata_policy()
    CapabilityRegistry.register_segment(_segment(policy, suffix=".metadata_raw"))

    assert CapabilityRegistry.violations_for(_call(x=1, overflow="saturating"), phase="raw") == frozenset()
    with pytest.raises(ValueError):
        CapabilityRegistry.violations_for(_call(x=1, overflow="saturating"))


def test_complete_metadata_gate_distinguishes_operand_type_and_option(isolated):
    policy = _metadata_policy()
    CapabilityRegistry.register_segment(_segment(policy, suffix=".metadata_complete"))
    call = _call(x=1, overflow="saturating")
    floating = replace(call, operand_types={"x": OperandType("float", "native", True)})
    integer = replace(call, operand_types={"x": OperandType("integer", "native", True)})

    assert CapabilityRegistry.violations_for(floating) == frozenset({policy.qualify(_SCOPE)})
    assert CapabilityRegistry.violations_for(integer) == frozenset()
    assert CapabilityRegistry.violations_for(
        replace(floating, bindings={"x": 1, "overflow": "other"})
    ) == frozenset()


@pytest.mark.parametrize(
    "path, operand",
    [
        ("__operand_types__", "float"),
        ("__operand_types__.x", "float"),
        ("__operand_types__.x.native_dtype", "float"),
        ("__operand_types__.overflow.logical_kind", "float"),
        ("__operand_types__.missing.logical_kind", "float"),
        ("__operand_types__.x.logical_kind", "decimal"),
        ("__operand_types__.x.storage_kind", "arbitrary"),
        ("__operand_types__.x.nullable", 1),
    ],
)
def test_policy_publication_rejects_invalid_metadata_selectors(isolated, path, operand):
    policy = _policy(
        "x",
        PolicyAction.BLOCK,
        Predicate((Clause("x", ClauseOp.IS_SET), Clause(path, ClauseOp.EQ, operand))),
    )
    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(_segment(policy, suffix=".invalid_metadata"))


def test_metadata_predicate_policy_cannot_permit(isolated):
    policy = _policy(
        "x",
        PolicyAction.PERMIT,
        Predicate((Clause("__operand_types__.x.logical_kind", ClauseOp.EQ, "float"),)),
    )
    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(_segment(policy, suffix=".metadata_permit"))


def test_metadata_names_are_exact_scope_declaration_data(isolated):
    policy = _metadata_policy()
    CapabilityRegistry.register_segment(_segment(policy, suffix=".metadata_names"))

    assert CapabilityRegistry.metadata_operand_names(_OP, CONST_BACKEND.POLARS, "polars") == frozenset({"x"})
    assert CapabilityRegistry.metadata_operand_names(_OP, CONST_BACKEND.POLARS, "unknown") == frozenset()
    assert CapabilityRegistry.metadata_operand_names(FK_STR.LPAD, CONST_BACKEND.POLARS, "polars") == frozenset()


def test_whole_operation_policy_is_not_a_parameter_fallback(isolated):
    policy = CapabilityPolicyRule(
        key=CapabilityKey(_OP, "*"),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message="The operation is refused in this concrete scope",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
    )
    CapabilityRegistry.register_segment(_segment(policy, suffix=".whole_operation"))

    assert CapabilityRegistry.capability_for(_OP, "x", CONST_BACKEND.POLARS, "polars") is None
    assert CapabilityRegistry.capability_for(_OP, "*", CONST_BACKEND.POLARS, "polars") == policy.qualify(_SCOPE)
    assert CapabilityRegistry.capability_for(_OP, "*", CONST_BACKEND.POLARS) is None
    assert CapabilityRegistry.capability_for(_OP, "*", CONST_BACKEND.POLARS, "unknown") is None
    assert [
        violation.operation_key
        for violation in CapabilityRegistry.validate_plan_capabilities([_OP], CONST_BACKEND.POLARS, "polars")
    ] == [_OP]


def test_single_answer_queries_select_the_named_consumer_without_selector_priority(isolated):
    gate = CapabilityPolicyRule(
        key=CapabilityKey(_OP, "overflow", Selector("exact", "ERROR")),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message="ERROR mode is refused",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
    )
    enrichment = CapabilityPolicyRule(
        key=CapabilityKey(_OP, "overflow"),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message="An identified native failure can be explained",
        consumer=PolicyConsumer.IMMEDIATE_ERROR,
        action=PolicyAction.ENRICH,
        native_errors=(TypeError,),
        native_issue="test:overflow-native-failure",
    )
    CapabilityRegistry.register_segment(_segment(gate, enrichment, suffix=".named_consumers"))

    assert CapabilityRegistry.capability_for(
        _OP, "overflow", CONST_BACKEND.POLARS, "polars", option_value="ERROR"
    ) == gate.qualify(_SCOPE)
    assert CapabilityRegistry.capability_for(
        _OP, "overflow", CONST_BACKEND.POLARS, "polars", option_value="NULL"
    ) is None
    assert CapabilityRegistry.capability_for(
        _OP, "overflow", CONST_BACKEND.POLARS, "polars",
        option_value="ERROR", consumer=PolicyConsumer.IMMEDIATE_ERROR,
    ) == enrichment.qualify(_SCOPE)
