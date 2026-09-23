"""Genuine capability and gap history retains immutable source evidence."""
from __future__ import annotations

from dataclasses import replace

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.capture import CapturedAddress, CapturedAssertion, Environment, EnvironmentCoordinate
from mountainash.core.capabilities.catalogue import CatalogueQuery, ChangeQuery
from mountainash.core.capabilities.declarations import (
    BoundSegment,
    CapabilityKey,
    CapabilityPolicyRule,
    CapabilitySegment,
    Domain,
    QualifiedCapabilityKey,
)
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


def test_unknown_introduction_survives_history_without_matching_earlier_versions():
    from mountainash.core.capabilities import CapabilityRegistry
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ApplicabilityResult,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.catalogue import CatalogueQuery, ChangeQuery
    from mountainash.core.capabilities.declarations import BoundSegment, CapabilitySegment, Domain
    from mountainash.core.capabilities.registry import _LoadState, _empty_state
    from mountainash.core.capabilities.retired import HistoricalBoundary

    prior = _captured("provisional restriction", "prior-unknown")
    claim = Applicability((Region((CoordinateConstraint(
        "engine",
        "duckdb",
        ComparisonScheme.NUMERIC_RELEASE,
        lower="1.4",
    ),)),))
    successor = replace(
        prior,
        payload=replace(prior.payload, applicability=claim),
        address=_address("forward-only"),
    )
    uncertainty = HistoricalBoundary(
        "engine",
        "duckdb",
        "introduced",
        "item236",
        (_address("first-observed-failure"),),
        "next-normal-release",
        _address("backtesting-obligation"),
    )
    change = AssertionChange(
        _address("narrowed"),
        prior,
        ChangeDisposition.NARROWED_APPLICABILITY,
        "2026-09-21",
        "first observed failure is not an introduction boundary",
        successors=(successor,),
        evidence_refs=(_address("first-observed-failure"),),
        unresolved_boundaries=(uncertainty,),
    )
    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string",
            _SCOPE,
            CapabilitySegment(Domain.STRING, changes=(change,)),
        ))
        retained = CapabilityRegistry.capture().search(
            CatalogueQuery(changes=ChangeQuery(family="capability"))
        ).changes[0]
        assert retained.prior == prior
        assert retained.unresolved_boundaries == (uncertainty,)
        assert retained.unresolved_boundaries[0].backtesting_obligation == _address("backtesting-obligation")
        retained_claim = retained.successors[0].payload.applicability
        earlier = Environment((EnvironmentCoordinate("engine", "duckdb", "1.3"),))
        assert retained_claim.match(
            prepare_environment(earlier, retained_claim.requirements)
        ) is ApplicabilityResult.NOT_APPLICABLE
        assert Applicability().match(prepare_environment(earlier, frozenset())) is ApplicabilityResult.APPLICABLE
    finally:
        CapabilityRegistry.restore(snapshot)


def test_catalogue_history_retains_controlled_lifecycle_captures():
    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )
    from mountainash.core.capabilities.registry import _LoadState, _empty_state

    def captured(message, entry, *, subject="length", variant=None, applicability=Applicability()):
        rule = CapabilityPolicyRule(
            key=CapabilityKey(FK_STR.CENTER, subject, variant=variant),
            level=CapabilityLevel.LITERAL_ONLY,
            since="2026-09-21",
            message=message,
            consumer=PolicyConsumer.GATE,
            action=PolicyAction.BLOCK,
            applicability=applicability,
        )
        return CapturedAssertion(
            "capability",
            QualifiedCapabilityKey(_SCOPE, rule.key),
            rule.qualify(_SCOPE),
            _address(entry),
        )

    broad = Applicability((Region((CoordinateConstraint(
        "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
        lower="1.0", upper="1.3", upper_inclusive=False,
    ),)),))
    narrowed = Applicability((Region((CoordinateConstraint(
        "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
        lower="1.0", upper="1.2", upper_inclusive=False,
    ),)),))
    first_interval = Applicability((Region((CoordinateConstraint(
        "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
        lower="1.0", upper="1.1", upper_inclusive=False,
    ),)),))
    later_interval = Applicability((Region((CoordinateConstraint(
        "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE,
        lower="1.2", upper="1.3", upper_inclusive=False,
    ),)),))

    narrowed_prior = captured("controlled broad applicability", "narrowed-prior", applicability=broad)
    narrowed_successor = captured(
        "controlled narrowed applicability", "narrowed-successor", applicability=narrowed,
    )
    narrowing = AssertionChange(
        change_ref=_address("change-narrowing"),
        prior=narrowed_prior,
        disposition=ChangeDisposition.NARROWED_APPLICABILITY,
        recorded_at="2026-09-21T10:00:00",
        reason="controlled fixture narrows the retained affected interval",
        successors=(narrowed_successor,),
        evidence_refs=(_address("evidence-narrowing"),),
    )

    correction_prior = captured("controlled incorrect description", "correction-prior")
    correction_successor = captured("controlled corrected description", "correction-successor")
    correction = AssertionChange(
        change_ref=_address("change-correction"),
        prior=correction_prior,
        disposition=ChangeDisposition.INCORRECT_DECLARATION,
        recorded_at="2026-09-21T10:01:00",
        reason="controlled fixture corrects description without calling it an upstream fix",
        successors=(correction_successor,),
        evidence_refs=(_address("evidence-correction"),),
    )

    local_prior = captured("controlled local implementation limitation", "local-prior")
    local_successor = captured("controlled local implementation repaired", "local-successor")
    fixed_versions = Environment((
        EnvironmentCoordinate("package", "ibis", "12.0.0"),
        EnvironmentCoordinate("engine", "duckdb", "1.2.0"),
    ))
    local_fix = AssertionChange(
        change_ref=_address("change-local"),
        prior=local_prior,
        disposition=ChangeDisposition.LOCAL_IMPLEMENTATION_FIX,
        recorded_at="2026-09-21T10:02:00",
        reason="controlled fixture records a Mountainash implementation repair",
        successors=(local_successor,),
        evidence_refs=(_address("evidence-local"),),
        fixed_versions=fixed_versions,
    )

    split_prior = captured("controlled combined history", "split-prior")
    split_first = captured(
        "controlled length-expression restriction", "split-first", applicability=first_interval,
    )
    split_second = captured(
        "controlled character-expression restriction",
        "split-second",
        subject="character",
        applicability=later_interval,
    )
    split = AssertionChange(
        change_ref=_address("change-split"),
        prior=split_prior,
        disposition=ChangeDisposition.SUPERSESSION,
        recorded_at="2026-09-21T10:03:00",
        reason="controlled fixture replaces one capture with two separately addressed regions",
        successors=(split_first, split_second),
        evidence_refs=(_address("evidence-split"),),
    )

    merge_first = captured(
        "controlled first historical region", "merge-first-prior", applicability=first_interval,
    )
    merge_second = captured(
        "controlled second historical region", "merge-second-prior", applicability=later_interval,
    )
    merged = captured(
        "controlled merged history",
        "merge-successor",
        applicability=Applicability(first_interval.regions + later_interval.regions),
    )
    merge_left = AssertionChange(
        change_ref=_address("change-merge-left"),
        prior=merge_first,
        disposition=ChangeDisposition.SUPERSESSION,
        recorded_at="2026-09-21T10:04:00",
        reason="controlled fixture records the first predecessor of a merge",
        successors=(merged,),
        evidence_refs=(_address("evidence-merge-left"),),
    )
    merge_right = AssertionChange(
        change_ref=_address("change-merge-right"),
        prior=merge_second,
        disposition=ChangeDisposition.SUPERSESSION,
        recorded_at="2026-09-21T10:05:00",
        reason="controlled fixture records the second predecessor of the same merge",
        successors=(merged,),
        evidence_refs=(_address("evidence-merge-right"),),
    )

    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))
        CapabilityRegistry.register_segment(BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string.history",
            _SCOPE,
            CapabilitySegment(
                Domain.STRING,
                changes=(narrowing, correction, local_fix, split, merge_left, merge_right),
            ),
        ))
        retained = CapabilityRegistry.capture().search(
            CatalogueQuery(changes=ChangeQuery(family="capability"))
        ).changes
    finally:
        CapabilityRegistry.restore(snapshot)

    assert retained == (correction, local_fix, merge_left, merge_right, narrowing, split)
    # From this point assert the objects returned by the catalogue consumer.
    correction, local_fix, merge_left, merge_right, narrowing, split = retained
    assert narrowing.prior == narrowed_prior
    assert narrowing.successors == (narrowed_successor,)
    assert narrowing.successors[0].payload.applicability == narrowed
    assert narrowing.evidence_refs == (_address("evidence-narrowing"),)
    assert correction.prior == correction_prior
    assert correction.successors == (correction_successor,)
    assert correction.successors[0].payload.message == "controlled corrected description"
    assert correction.evidence_refs == (_address("evidence-correction"),)
    assert local_fix.prior == local_prior
    assert local_fix.successors == (local_successor,)
    assert local_fix.fixed_versions == fixed_versions
    assert local_fix.evidence_refs == (_address("evidence-local"),)
    assert split.prior == split_prior
    assert split.successors == (split_first, split_second)
    assert tuple(successor.address for successor in split.successors) == (
        _address("split-first"),
        _address("split-second"),
    )
    assert split.evidence_refs == (_address("evidence-split"),)
    assert merge_left.prior == merge_first
    assert merge_right.prior == merge_second
    assert merge_left.successors == merge_right.successors == (merged,)
    assert merge_left.successors[0].address == _address("merge-successor")
    assert merge_left.evidence_refs == (_address("evidence-merge-left"),)
    assert merge_right.evidence_refs == (_address("evidence-merge-right"),)
