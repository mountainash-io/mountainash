"""Information cannot execute; publication and retained views remain atomic."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import CapabilityLevel, CapabilityRegistry
from mountainash.core.capabilities.declarations import BoundSegment, CapabilityKey, CapabilitySegment, Domain
from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING as FK


@pytest.fixture(autouse=True)
def isolated_registry():
    from mountainash.core.capabilities.registry import _LoadState, _empty_state

    before = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))
    try:
        yield
    finally:
        CapabilityRegistry.restore(before)


def _information(subject, message, *, public=False):
    from mountainash.core.capabilities.declarations import CapabilityInformation
    from mountainash.core.capabilities.schema import InformationLayer

    return CapabilityInformation(
        key=CapabilityKey(FK.CONTAINS, subject),
        layer=InformationLayer.PUBLIC if public else InformationLayer.NATIVE,
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message=message,
    )


def _policy(*, information=None):
    from mountainash.core.capabilities.declarations import CapabilityPolicyRule
    from mountainash.core.capabilities.schema import PolicyAction, PolicyConsumer

    return CapabilityPolicyRule(
        key=CapabilityKey(FK.CONTAINS, "substring"),
        level=CapabilityLevel.UNSUPPORTED,
        since="2026-09-18",
        message="Explicit refusal remains usable without an explanation record",
        consumer=PolicyConsumer.GATE,
        action=PolicyAction.BLOCK,
        information=information,
    )


def _segment(*, family=False, information=(), policies=(), suffix=""):
    scope = Scope(CONST_BACKEND.POLARS, FamilyWide() if family else Dialect("polars"))
    home = "family" if family else "dialects.polars"
    return BoundSegment(
        f"mountainash.expressions.backends.capabilities.polars.{home}.substrait.string{suffix}",
        scope,
        CapabilitySegment(Domain.STRING, information=information, policies=policies),
    )


def test_negative_information_does_not_create_a_refusal():
    CapabilityRegistry.register_segment(_segment(family=True, information=(_information("substring", "Description only"),)))
    assert CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars") is None

    CapabilityRegistry.register_segment(_segment(policies=(_policy(),)))
    decision = CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars")
    assert decision is not None
    assert decision.level is CapabilityLevel.UNSUPPORTED
    
    assert CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.POLARS, None) is None


def test_exact_and_composed_information_keep_scope_and_frozen_generation():
    from mountainash.core.capabilities.catalogue import InformationQuery

    family = _segment(family=True, information=(_information("substring", "Family native restriction"),))
    local = _segment(information=(_information("substring", "Local public behavior", public=True),))
    CapabilityRegistry.register_segment(family)
    CapabilityRegistry.register_segment(local)
    captured = CapabilityRegistry.capture()
    exact = captured.reader(local.scope).search(InformationQuery())
    assert {record.assertion.message for record in exact} == {"Local public behavior"}
    composed = captured.composed_information(local.scope)
    assert {(record.key.scope, record.assertion.message) for record in composed} == {
        (family.scope, "Family native restriction"),
        (local.scope, "Local public behavior"),
    }
    assert {origin.module for record in composed for origin in record.origins} == {family.module, local.module}

    CapabilityRegistry.register_segment(_segment(information=(_information("input", "Later description"),), suffix=".later"))
    assert {record.assertion.message for record in captured.composed_information(local.scope)} == {
        "Family native restriction", "Local public behavior",
    }
    assert {record.assertion.message for record in CapabilityRegistry.capture().composed_information(local.scope)} == {
        "Family native restriction", "Local public behavior", "Later description",
    }


def test_information_and_family_scope_cannot_manufacture_policy():
    with pytest.raises((TypeError, ValueError)):
        _segment(policies=(_information("substring", "Not a policy"),))
    with pytest.raises((TypeError, ValueError)):
        _segment(family=True, policies=(_policy(),))


def test_missing_information_reference_rolls_back_entire_segment():
    from mountainash.core.capabilities.catalogue import InformationQuery
    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    initial = _segment(information=(_information("input", "Previously published"),))
    CapabilityRegistry.register_segment(initial)
    captured = CapabilityRegistry.capture()
    missing = QualifiedInformationKey(
        initial.scope, CapabilityKey(FK.CONTAINS, "substring"), InformationLayer.PUBLIC,
    )
    invalid = _segment(
        information=(_information("substring", "Must not leak from failed publication"),),
        policies=(_policy(information=missing),),
        suffix=".invalid",
    )
    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(invalid)

    for view in (captured, CapabilityRegistry.capture()):
        assert {record.assertion.message for record in view.reader(initial.scope).search(InformationQuery())} == {
            "Previously published",
        }
    assert CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars") is None


def test_catalogue_queries_keep_information_and_policies_separate():
    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery, PolicyQuery
    from mountainash.core.capabilities.schema import InformationLayer, PolicyConsumer

    family = _segment(family=True, information=(_information("substring", "Native family description"),))
    local = _segment(
        information=(_information("substring", "Public local description", public=True),),
        policies=(_policy(),),
    )
    CapabilityRegistry.register_segment(family)
    CapabilityRegistry.register_segment(local)
    capture = CapabilityRegistry.capture()
    records = capture.search(CatalogueQuery(information=InformationQuery(), policies=PolicyQuery()))
    assert {(record.key.scope, record.key.layer) for record in records.information} == {
        (family.scope, InformationLayer.NATIVE), (local.scope, InformationLayer.PUBLIC),
    }
    assert records.policies == (capture.reader(local.scope).policy(_policy().key),)
    local_records = capture.search(CatalogueQuery(
        information=InformationQuery(), policies=PolicyQuery(consumer=PolicyConsumer.GATE),
        scopes=frozenset({local.scope}),
    ))
    assert tuple(record.key.scope for record in local_records.information) == (local.scope,)
    assert local_records.policies == records.policies
    assert capture.search(CatalogueQuery(information=InformationQuery())).policies is None


def test_direct_inventory_capture_distinguishes_unacquired_empty_and_duplicate():
    from mountainash.core.capabilities.capture import CapturedAddress
    from mountainash.core.capabilities.catalogue import CatalogueQuery, GapQuery, UncapturedNamespaceError
    from mountainash.core.capabilities.gaps import GapInventory

    with pytest.raises(UncapturedNamespaceError):
        CapabilityRegistry.capture().search(CatalogueQuery(gaps=GapQuery()))
    assert CapabilityRegistry.capture(inventories=()).search(CatalogueQuery(gaps=GapQuery())).gaps == ()
    inventory = GapInventory(
        "owned.empty", CapturedAddress("mountainash", "tests/owner.py", "GAPS", artifact=b"GAPS = {}"), (),
    )
    capture = CapabilityRegistry.capture(inventories=(inventory,))
    assert capture.search(CatalogueQuery(gaps=GapQuery(inventory="owned.empty"))).gaps == ()
    with pytest.raises(UncapturedNamespaceError):
        capture.search(CatalogueQuery(gaps=GapQuery(inventory="not.acquired")))
    with pytest.raises(ValueError):
        CapabilityRegistry.capture(inventories=(inventory, inventory))


def test_unknown_information_subject_rejects_entire_publication():
    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery

    CapabilityRegistry.register_segment(_segment(information=(_information("input", "Existing claim"),)))
    before = CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery()))
    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(_segment(
            information=(_information("substring", "Must not leak"), _information("typo_argument", "Invalid claim")),
            suffix=".invalid",
        ))
    assert CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery())) == before


@pytest.mark.parametrize("reference_home", ("family", "ibis_duckdb", "ibis_sqlite"))
def test_policy_explanation_scope_must_cover_its_dialect(reference_home):
    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    reference_scope = Scope(
        CONST_BACKEND.IBIS,
        FamilyWide() if reference_home == "family" else Dialect(reference_home.replace("_", "-")),
    )
    home = "family" if reference_home == "family" else f"dialects.{reference_home}"
    description = BoundSegment(
        f"mountainash.expressions.backends.capabilities.ibis.{home}.substrait.string",
        reference_scope,
        CapabilitySegment(Domain.STRING, information=(_information("substring", "Scoped explanation"),)),
    )
    CapabilityRegistry.register_segment(description)
    policy = _policy(information=QualifiedInformationKey(
        reference_scope, policy_key := CapabilityKey(FK.CONTAINS, "substring"), InformationLayer.NATIVE,
    ))
    target = BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string.policy",
        Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
        CapabilitySegment(Domain.STRING, policies=(policy,)),
    )
    if reference_home == "ibis_sqlite":
        with pytest.raises(ValueError):
            CapabilityRegistry.register_segment(target)
        assert CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.IBIS, "ibis-duckdb") is None
    else:
        CapabilityRegistry.register_segment(target)
        assert CapabilityRegistry.capture().reader(target.scope).policy(policy_key).assertion == policy
