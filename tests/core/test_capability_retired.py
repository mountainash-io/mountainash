"""Genuine capability and gap history retains immutable source evidence."""
from __future__ import annotations

from dataclasses import replace

import pytest

from mountainash.core.capabilities import CapabilityLevel
from mountainash.core.capabilities.capture import CapturedAddress, CapturedAssertion, Environment, EnvironmentCoordinate
from mountainash.core.capabilities.declarations import CapabilityKey, CapabilityPolicyRule, QualifiedCapabilityKey
from mountainash.core.capabilities.identity import Dialect, Scope
from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR

_SCOPE = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))


def _address(entry):
    return CapturedAddress("mountainash", "history.py", entry, artifact=b"history")


def _captured(message, entry):
    rule = CapabilityPolicyRule(
        CapabilityKey(FK_STR.CENTER, "length"), CapabilityLevel.LITERAL_ONLY,
        "2026-09-18", message, PolicyConsumer.GATE, PolicyAction.BLOCK,
    )
    return CapturedAssertion(
        "capability", QualifiedCapabilityKey(_SCOPE, rule.key), rule.qualify(_SCOPE), _address(entry),
    )


def test_assertion_change_retains_complete_same_key_replacement():
    prior = _captured("old limitation", "prior")
    successor = CapturedAssertion(
        "capability", prior.key, replace(prior.payload, message="corrected limitation"), _address("successor"),
    )
    change = AssertionChange(
        _address("change"), prior, ChangeDisposition.INCORRECT_DECLARATION, "2026-09-18T10:11:12",
        "correct explanatory claim", (successor,), (_address("evidence"),),
        Environment((EnvironmentCoordinate("package", "ibis", "13.0.0"),)),
    )
    assert change.prior.payload.message == "old limitation"
    assert change.successors[0].payload.message == "corrected limitation"
    assert change.prior.key == change.successors[0].key
    assert change.fixed_versions.coordinates[0].name == "ibis-framework"


def test_assertion_change_allows_removal_without_successor():
    change = AssertionChange(
        _address("change"), _captured("removed limitation", "prior"),
        ChangeDisposition.UPSTREAM_FIX, "2026-09-18", "observed upstream fix",
    )
    assert change.successors == ()
    assert change.fixed_versions is None


@pytest.mark.parametrize("replacement", [
    {"reason": ""},
    {"recorded_at": "2026-99-99"},
    {"successors": (_captured("changed", "prior"),)},
])
def test_assertion_change_rejects_invalid_history(replacement):
    change = AssertionChange(
        _address("change"), _captured("old limitation", "prior"),
        ChangeDisposition.INCORRECT_DECLARATION, "2026-09-18", "correct explanatory claim",
    )
    with pytest.raises(ValueError):
        replace(change, **replacement)


def test_environment_preserves_stack_and_rejects_conflicts():
    environment = Environment((
        EnvironmentCoordinate("package", "ibis", "12.0.0"),
        EnvironmentCoordinate("engine", "duckdb", "1.2.2"),
    ))
    assert environment.coordinates[1].name == "ibis-framework"
    with pytest.raises(ValueError, match="conflicting"):
        Environment((
            EnvironmentCoordinate("package", "ibis", "12.0.0"),
            EnvironmentCoordinate("package", "ibis-framework", "11.0.0"),
        ))

def test_gap_history_retains_its_inventory_scoped_claim():
    from mountainash.core.capabilities.gaps import GapKey, InventoryGap, InventoryWide
    from mountainash.core.capabilities.schema import GapKind, KnownGap, OperationTarget

    key = GapKey("owned.gaps", OperationTarget(FK_STR.CENTER), "coverage", InventoryWide())
    gap = InventoryGap(
        key, ("legacy observation",), KnownGap(GapKind.OTHER, "test gap", "2026-09-18"), (_address("gap"),),
    )
    prior = CapturedAssertion("gap", key, gap, _address("prior gap"))
    change = AssertionChange(
        _address("gap change"), prior, ChangeDisposition.INCORRECT_DECLARATION,
        "2026-09-18", "correct the captured gap record",
    )
    assert change.prior.family == "gap"
    assert change.prior.key == key
