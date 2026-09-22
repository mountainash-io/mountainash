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

def test_information_variants_do_not_overwrite_or_become_unqualified_fallback():
    from dataclasses import replace

    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery
    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    first = replace(
        _information("substring", "First named description"),
        key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="first"),
    )
    second = replace(
        first,
        key=replace(first.key, variant="second"),
        message="Second named description",
    )
    segment = _segment(information=(first, second))
    CapabilityRegistry.register_segment(segment)

    captured = CapabilityRegistry.capture()
    assert {
        item.key.local.variant
        for item in captured.search(CatalogueQuery(information=InformationQuery())).information
    } == {"first", "second"}
    assert captured.get_optional(
        QualifiedInformationKey(
            segment.scope,
            CapabilityKey(FK.CONTAINS, "substring"),
            InformationLayer.NATIVE,
        )
    ) is None
    assert captured.get(
        QualifiedInformationKey(segment.scope, second.key, InformationLayer.NATIVE)
    ).assertion is second


def test_duplicate_full_keys_roll_back_information_and_policy_publication():
    from dataclasses import replace

    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery, PolicyQuery

    information = replace(
        _information("substring", "Initially published named information"),
        key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="duplicate-information"),
    )
    policy = replace(
        _policy(),
        key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="duplicate-policy"),
    )
    CapabilityRegistry.register_segment(_segment(information=(information,), policies=(policy,)))
    before = CapabilityRegistry.capture().search(CatalogueQuery(
        information=InformationQuery(),
        policies=PolicyQuery(),
    ))

    with pytest.raises(ValueError, match="duplicate information key"):
        CapabilityRegistry.register_segment(
            _segment(information=(information,), suffix=".duplicate_information")
        )
    assert CapabilityRegistry.capture().search(CatalogueQuery(
        information=InformationQuery(),
        policies=PolicyQuery(),
    )) == before

    with pytest.raises(ValueError, match="duplicate policy key"):
        CapabilityRegistry.register_segment(_segment(
            information=(
                replace(
                    information,
                    key=replace(information.key, variant="separate-information"),
                ),
            ),
            policies=(policy,),
            suffix=".duplicate_policy",
        ))
    assert CapabilityRegistry.capture().search(CatalogueQuery(
        information=InformationQuery(),
        policies=PolicyQuery(),
    )) == before


def test_disjoint_policy_variants_coexist_and_require_exact_lookup():
    from dataclasses import replace

    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )

    older = Applicability((
        Region((
            CoordinateConstraint(
                "engine",
                "polars",
                ComparisonScheme.NUMERIC_RELEASE,
                upper="1.0.0",
                upper_inclusive=False,
            ),
        )),
    ))
    newer = Applicability((
        Region((
            CoordinateConstraint(
                "engine",
                "polars",
                ComparisonScheme.NUMERIC_RELEASE,
                lower="1.0.0",
            ),
        )),
    ))
    first = replace(
        _policy(),
        key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="older-engine"),
        applicability=older,
    )
    second = replace(
        first,
        key=replace(first.key, variant="newer-engine"),
        applicability=newer,
    )
    segment = _segment(policies=(first, second))
    CapabilityRegistry.register_segment(segment)

    reader = CapabilityRegistry.capture().reader(segment.scope)
    assert reader.policy(first.key).assertion is first
    assert reader.policy(second.key).assertion is second
    assert reader.policy_optional(CapabilityKey(FK.CONTAINS, "substring")) is None

def test_adjacent_version_policies_publish_and_overlap_rolls_back():
    from dataclasses import replace

    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
    )
    from mountainash.core.capabilities.catalogue import CatalogueQuery, PolicyQuery

    def interval(lower, upper):
        return Applicability((
            Region((
                CoordinateConstraint(
                    "package",
                    "polars",
                    ComparisonScheme.PEP440,
                    lower=lower,
                    upper=upper,
                    upper_inclusive=False,
                ),
            )),
        ))

    first = replace(
        _policy(),
        key=replace(_policy().key, variant="older"),
        applicability=interval("1", "2"),
    )
    second = replace(
        first,
        key=replace(first.key, variant="newer"),
        applicability=interval("2", "3"),
    )
    CapabilityRegistry.register_segment(_segment(policies=(first, second)))
    before = CapabilityRegistry.capture()
    overlapping = replace(
        first,
        key=replace(first.key, variant="overlap"),
        applicability=interval("1.5", "2.5"),
    )

    with pytest.raises(ValueError):
        CapabilityRegistry.register_segment(
            _segment(policies=(overlapping,), suffix=".overlap")
        )

    current = CapabilityRegistry.capture()
    query = CatalogueQuery(policies=PolicyQuery())
    assert current.search(query).policies == before.search(query).policies
    assert {
        record.key.local.variant for record in current.search(query).policies
    } == {"older", "newer"}


def test_registry_selects_recurrence_but_not_gap_or_unknown_engine():
    from dataclasses import replace

    from mountainash.core.capabilities.applicability import (
        Applicability,
        ComparisonScheme,
        CoordinateConstraint,
        Region,
        prepare_environment,
    )
    from mountainash.core.capabilities.capture import Environment, EnvironmentCoordinate
    from mountainash.core.capabilities.identity import BackendIdentity
    from mountainash.core.capabilities.policy import (
        CapabilityPolicy,
        _CapabilityTarget,
        _ExecutionContext,
    )

    claim = Applicability(tuple(Region((
        CoordinateConstraint("package", "ibis", ComparisonScheme.PEP440, equal="12"),
        CoordinateConstraint(
            "engine",
            "duckdb",
            ComparisonScheme.NUMERIC_RELEASE,
            lower=lower,
            upper=upper,
            upper_inclusive=False,
        ),
    )) for lower, upper in (("1.2", "1.3"), ("1.4", "1.5"))))
    # Coordinates are deliberately test-owned, not claimed Polars/Ibis evidence.
    rule = replace(_policy(), applicability=claim)
    CapabilityRegistry.register_segment(_segment(policies=(rule,)))
    target = _CapabilityTarget(BackendIdentity(CONST_BACKEND.POLARS, "polars"), object())
    for engine, expected in (
        ("1.1", False),
        ("1.2", True),
        ("1.3", False),
        ("1.4", True),
        (None, False),
        ("vendor", False),
    ):
        observed = Environment((
            EnvironmentCoordinate("package", "ibis", "12"),
            EnvironmentCoordinate("engine", "duckdb", engine),
        ))
        context = _ExecutionContext(
            CapabilityPolicy.checked(),
            target,
            observed,
            prepare_environment(observed, claim.requirements),
        )
        selected = CapabilityRegistry.capability_for(
            FK.CONTAINS,
            "substring",
            CONST_BACKEND.POLARS,
            "polars",
            execution_context=context,
        )
        assert (selected is not None) is expected


@pytest.mark.parametrize(
    ("information_variant", "policy_variant"),
    (("native-description", "gate-rule"), (None, "named-gate-rule")),
    ids=("named-information", "unqualified-information"),
)
def test_policy_can_reference_independently_named_or_unqualified_information(
    information_variant,
    policy_variant,
):
    from dataclasses import replace

    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    information = replace(
        _information("substring", "Explanation belongs to this exact information record"),
        key=replace(
            CapabilityKey(FK.CONTAINS, "substring"),
            variant=information_variant,
        ),
    )
    reference = QualifiedInformationKey(
        _segment().scope,
        information.key,
        InformationLayer.NATIVE,
    )
    policy = replace(
        _policy(information=reference),
        key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant=policy_variant),
    )
    segment = _segment(information=(information,), policies=(policy,))
    CapabilityRegistry.register_segment(segment)

    capture = CapabilityRegistry.capture()
    assert capture.get(reference).assertion is information
    assert capture.reader(segment.scope).policy(policy.key).assertion.information is reference


def test_missing_named_information_reference_rolls_back_entire_segment():
    from dataclasses import replace

    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery
    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    initial = _segment(information=(_information("input", "Previously published"),))
    CapabilityRegistry.register_segment(initial)
    before = CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery()))
    missing = QualifiedInformationKey(
        initial.scope,
        CapabilityKey(FK.CONTAINS, "substring", variant="missing-explanation"),
        InformationLayer.NATIVE,
    )
    invalid = _segment(
        information=(_information("substring", "Must not leak from failed publication"),),
        policies=(
            replace(
                _policy(information=missing),
                key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="missing-reference"),
            ),
        ),
        suffix=".missing_variant",
    )

    with pytest.raises(ValueError, match="information reference"):
        CapabilityRegistry.register_segment(invalid)

    assert CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery())) == before
    assert CapabilityRegistry.capability_for(FK.CONTAINS, "substring", CONST_BACKEND.POLARS, "polars") is None


def test_policy_reference_with_wrong_base_identity_rolls_back_publication():
    from dataclasses import replace

    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery
    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    prior = _segment(information=(_information("input", "Existing different subject"),))
    CapabilityRegistry.register_segment(prior)
    before = CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery()))
    reference = QualifiedInformationKey(
        prior.scope,
        CapabilityKey(FK.CONTAINS, "input"),
        InformationLayer.NATIVE,
    )
    invalid = _segment(
        information=(_information("substring", "Must not leak from failed publication"),),
        policies=(
            replace(
                _policy(information=reference),
                key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="wrong-base"),
            ),
        ),
        suffix=".wrong_base",
    )

    with pytest.raises(ValueError, match="call identity"):
        CapabilityRegistry.register_segment(invalid)

    assert CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery())) == before


def test_policy_reference_with_wrong_scope_rolls_back_publication():
    from dataclasses import replace

    from mountainash.core.capabilities.catalogue import CatalogueQuery, InformationQuery
    from mountainash.core.capabilities.declarations import QualifiedInformationKey
    from mountainash.core.capabilities.schema import InformationLayer

    foreign_scope = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    foreign_information = _information("substring", "Foreign backend explanation")
    CapabilityRegistry.register_segment(BoundSegment(
        "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string.reference",
        foreign_scope,
        CapabilitySegment(Domain.STRING, information=(foreign_information,)),
    ))
    before = CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery()))
    invalid = _segment(
        information=(_information("substring", "Must not leak from failed publication"),),
        policies=(
            replace(
                _policy(information=QualifiedInformationKey(
                    foreign_scope,
                    foreign_information.key,
                    InformationLayer.NATIVE,
                )),
                key=replace(CapabilityKey(FK.CONTAINS, "substring"), variant="wrong-scope"),
            ),
        ),
        suffix=".wrong_scope",
    )

    with pytest.raises(ValueError, match="backend"):
        CapabilityRegistry.register_segment(invalid)

    assert CapabilityRegistry.capture().search(CatalogueQuery(information=InformationQuery())) == before


def test_backend_override_uses_destination_not_source_coordinates():
    from mountainash.core.capabilities.registry import _LoadState, _empty_state
    from dataclasses import replace
    from importlib.metadata import version
    import duckdb
    import ibis
    import polars as pl
    import mountainash as ma
    from mountainash.core.capabilities.applicability import Applicability, ComparisonScheme, CoordinateConstraint, Region
    from mountainash.core.types import BackendCapabilityError
    source_only = Applicability((Region((CoordinateConstraint(
        "engine", "duckdb", ComparisonScheme.NUMERIC_RELEASE, equal=duckdb.__version__,
    ),)),))
    destination_only = Applicability((Region((CoordinateConstraint(
        "package", "polars", ComparisonScheme.PEP440, equal=version("polars"),
    ),)),))
    connection = ibis.duckdb.connect(":memory:")
    try:
        source = connection.create_table("destination_context", obj=pl.DataFrame({"text": ["a", "b"]}))
        dag = ma.RelationDAG()
        dag.add("source", ma.relation(source))
        dag.add("result", dag.ref("source").select(ma.col("text").str.contains("a").alias("found")))
        # A source-side policy for an UNUSED operation requires actual DuckDB
        # coordinates, without gating this pipeline. Thus borrowing that
        # source context in the Polars destination is observably wrong.
        source_rule = replace(
            _policy(), key=CapabilityKey(FK.CENTER, "length"), applicability=source_only,
        )
        source_segment = BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.dialects.ibis_duckdb.substrait.string",
            Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb")),
            CapabilitySegment(Domain.STRING, policies=(source_rule,)),
        )
        with ma.capability_policy(ma.CapabilityPolicy.checked()):
            CapabilityRegistry.register_segment(source_segment)
            CapabilityRegistry.register_segment(_segment(policies=(
                replace(_policy(), applicability=source_only),
            )))
            converted = dag.collect("result", backend="polars")
            assert ma.relation(converted).to_polars()["found"].to_list() == [True, False]
            CapabilityRegistry.restore(_empty_state(_LoadState.LOADED))  # explicit setup BETWEEN requests
            CapabilityRegistry.register_segment(source_segment)
            CapabilityRegistry.register_segment(_segment(policies=(
                replace(_policy(), applicability=destination_only),
            )))
            with pytest.raises(BackendCapabilityError):
                dag.collect("result", backend="polars")
            native = dag.collect("result")
            assert ma.relation(native).to_polars()["found"].to_list() == [True, False]
    finally:
        connection.con.close()


def test_direct_validation_keeps_entry_policy_during_preparation(monkeypatch):
    import polars as pl
    import mountainash as ma
    from mountainash.validation import RelationRule, ValidationRunner
    import mountainash.validation.prepared as prepared_module
    CapabilityRegistry.register_segment(_segment(policies=(_policy(),)))
    relation = ma.relation(pl.DataFrame({"text": ["a"]})).select(
        ma.col("text").str.contains("a").alias("found")
    )
    checks = [RelationRule(id="no_failures", plan=lambda rel: rel.head(0))]
    original = prepared_module.prepare_validation_input
    def inside_trusted_scope(*args, **kwargs):
        with ma.capability_policy(ma.CapabilityPolicy.trusted()):
            return original(*args, **kwargs)
    monkeypatch.setattr(prepared_module, "prepare_validation_input", inside_trusted_scope)
    with ma.capability_policy(ma.CapabilityPolicy.checked()):
        checked = ValidationRunner().validate_relation(relation, checks)
    assert checked.passes is False
    assert checked.check_summaries["status"].to_list() == ["error"]
    with ma.capability_policy(ma.CapabilityPolicy.trusted()):
        trusted = ValidationRunner().validate_relation(relation, checks)
    assert trusted.passes is True
    assert trusted.failure_cases.height == 0
