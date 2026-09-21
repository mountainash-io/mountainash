"""Concrete value-class policies resolve only when their selector matches."""
from __future__ import annotations

from dataclasses import replace

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.applicability import (
    Applicability,
    ComparisonScheme,
    CoordinateConstraint,
    Region,
)
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilityPolicyRule, CapabilitySegment, Domain, Selector
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.schema import Clause, ClauseOp, PolicyAction, PolicyConsumer, Predicate, ValueClass
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME as FK

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))


@pytest.fixture(autouse=True)
def isolate():
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    try:
        yield
    finally:
        CapabilityRegistry.restore(snapshot)


def _rule(value_class=ValueClass.DURATION_MULTIPLIER):
    return CapabilityPolicyRule(
        CapabilityKey(FK.TRUNCATE, "unit", Selector("value_class", value_class)),
        CapabilityLevel.UNSUPPORTED, "2026-09-18", "multiplier units are unavailable",
        PolicyConsumer.GATE, PolicyAction.BLOCK,
    )


def _segment(*rules, suffix=""):
    return BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects."
        f"ibis_duckdb.extensions_mountainash.datetime{suffix}",
        _SCOPE,
        CapabilitySegment(Domain.DATETIME, policies=rules),
    )


def _publish(*rules, suffix=""):
    segment = _segment(*rules, suffix=suffix)
    CapabilityRegistry.register_segment(segment)
    return segment


def test_value_class_policy_resolves_only_for_matching_value():
    _publish(_rule())
    matching = CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "2d")
    assert matching is not None
    assert matching.value_class is ValueClass.DURATION_MULTIPLIER
    assert CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "1d") is None


def test_snapshot_restore_retains_value_class_policy():
    _publish(_rule())
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    assert CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "2d") is None
    CapabilityRegistry.restore(snapshot)
    assert CapabilityRegistry.capability_for(FK.TRUNCATE, "unit", CONST_BACKEND.IBIS, "ibis-duckdb", "2d") is not None


def _interval(lower, upper):
    return Applicability(
        regions=(
            Region(
                constraints=(
                    CoordinateConstraint(
                        "package",
                        "ibis-framework",
                        ComparisonScheme.PEP440,
                        lower=lower,
                        upper=upper,
                        upper_inclusive=False,
                    ),
                ),
            ),
        ),
    )


def _versioned_rule(selector, *, variant, lower, upper):
    return replace(
        _rule(),
        key=CapabilityKey(FK.TRUNCATE, "unit", selector, variant=variant),
        applicability=_interval(lower, upper),
    )


_SELECTORS = {
    "general": Selector(),
    "exact": Selector("exact", "2d"),
    "value-class": Selector("value_class", ValueClass.DURATION_MULTIPLIER),
    "predicate": Selector(
        "predicate",
        Predicate((Clause("unit", ClauseOp.EQ, "2d"),)),
    ),
}


def test_adjacent_cross_selector_policies_publish_as_sibling_records(isolate):
    general = _versioned_rule(
        _SELECTORS["general"],
        variant="broad-contract",
        lower="1",
        upper="2",
    )
    exact = _versioned_rule(
        _SELECTORS["exact"],
        variant="literal-contract",
        lower="2",
        upper="3",
    )

    segment = _publish(general, exact, suffix=".adjacent_selectors")

    reader = CapabilityRegistry.reader(_SCOPE)
    assert CapabilityRegistry.segments() == (segment,)
    assert reader.policy(general.key).assertion == general
    assert reader.policy(exact.key).assertion == exact


@pytest.mark.parametrize(
    ("left_name", "right_name"),
    (
        ("general", "exact"),
        ("general", "value-class"),
        ("general", "predicate"),
        ("exact", "value-class"),
        ("exact", "predicate"),
        ("value-class", "predicate"),
    ),
    ids=(
        "general-exact",
        "general-value-class",
        "general-predicate",
        "exact-value-class",
        "exact-predicate",
        "value-class-predicate",
    ),
)
def test_overlapping_versioned_selector_forms_reject_later_publication_and_preserve_prior(
    isolate,
    left_name,
    right_name,
):
    prior = _versioned_rule(
        _SELECTORS[left_name],
        variant=f"{left_name}-published",
        lower="1",
        upper="3",
    )
    competing = _versioned_rule(
        _SELECTORS[right_name],
        variant=f"{right_name}-rejected",
        lower="1",
        upper="3",
    )
    initial = _publish(prior, suffix=f".initial_{left_name}")

    with pytest.raises(ValueError) as raised:
        _publish(competing, suffix=f".overlap_{right_name}")

    message = str(raised.value)
    assert initial.module in message
    assert ".overlap_" in message
    assert "call=overlap" in message
    assert "environment=overlap" in message
    assert "call_witness" in message
    assert CapabilityRegistry.segments() == (initial,)
    reader = CapabilityRegistry.reader(_SCOPE)
    assert reader.policy(prior.key).assertion == prior
    assert reader.policy_optional(competing.key) is None
