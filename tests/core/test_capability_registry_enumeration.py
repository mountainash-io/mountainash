"""Deterministic enumeration + bucketed value-class index (spec rev 3, §2/§6)."""

from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    Enforcement,
    ValueClass,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)


@pytest.fixture
def isolated():
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        yield
    finally:
        CapabilityRegistry.restore(snap)


def _vc_fact(op, dialect=None, vc=ValueClass.DURATION_MULTIPLIER, param="unit"):
    return CapabilityFact(
        operation_key=op,
        param=param,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect=dialect,
        value_class=vc,
        message="t",
        since="2026-08-07",
        probe_exempt="test",
    )


def test_value_class_lookup_still_resolves(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])
    fact = CapabilityRegistry.capability_for(
        FK_DT.TRUNCATE,
        "unit",
        CONST_BACKEND.IBIS,
        dialect="ibis-duckdb",
        option_value="2d",
    )
    assert fact is not None and fact.value_class is ValueClass.DURATION_MULTIPLIER


def test_duplicate_value_class_key_rejected(isolated):
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])
    with pytest.raises(ValueError, match="duplicate"):
        CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [_vc_fact(FK_DT.TRUNCATE)])


def test_facts_enumeration_is_sorted_and_total(isolated):
    # Facts spanning op, dialect AND value_class so the assertion pins the FULL
    # canonical ordering, not just the value_class component (T3 review).
    def _facts():
        return [
            _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.DURATION_MULTIPLIER),
            _vc_fact(FK_DT.TRUNCATE, vc=ValueClass.POLARS_OFFSET),
            _vc_fact(FK_DT.TRUNCATE, dialect="ibis-duckdb", vc=ValueClass.DURATION_MULTIPLIER),
            _vc_fact(FK_DT.ADD_DAYS, vc=ValueClass.DURATION_MULTIPLIER, param="days"),
        ]

    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, _facts())
    out = CapabilityRegistry.facts()
    # Explicit expected order pins op (ADD_DAYS < TRUNCATE), dialect
    # (family None < "ibis-duckdb") and value_class (duration < polars_offset) —
    # a value_class-only fixture would leave op/dialect ordering unexercised.
    assert [(f.operation_key, f.dialect, f.value_class) for f in out] == [
        (FK_DT.ADD_DAYS, None, ValueClass.DURATION_MULTIPLIER),
        (FK_DT.TRUNCATE, None, ValueClass.DURATION_MULTIPLIER),
        (FK_DT.TRUNCATE, None, ValueClass.POLARS_OFFSET),
        (FK_DT.TRUNCATE, "ibis-duckdb", ValueClass.DURATION_MULTIPLIER),
    ]
    # Registration order must not change enumeration (determinism).
    CapabilityRegistry.reset()
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, list(reversed(_facts())))
    assert CapabilityRegistry.facts() == out


def _residue_fact(op, option_value):
    return CapabilityFact(
        operation_key=op,
        param="length",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.IBIS,
        dialect=None,
        option_value=option_value,
        boundary=Boundary.MATERIALIZE,
        native_errors=(ValueError,),
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        message="t",
        since="2026-08-07",
        probe_exempt="test",
    )


def test_residue_for_rejects_equal_specificity_collision(isolated):
    # residue_for groups MATERIALIZE_RESIDUE facts by (op, param); two at
    # IDENTICAL dialect-specificity (both family-level, dialect=None) are
    # ambiguous and must raise. register_backend's dedup plus its
    # "value-scoped => BUILD boundary" rule make this state unreachable via the
    # public path, so we seed the two facts directly into the internal index to
    # exercise the defensive guard (implemented at T3, untested — final M-5).
    from mountainash.core.capabilities.registry import _LoadState, _prepare_state

    facts = {
        (FK_DT.TRUNCATE, "length", CONST_BACKEND.IBIS, None, value): _residue_fact(FK_DT.TRUNCATE, value)
        for value in ("a", "b")
    }
    CapabilityRegistry.restore(
        _prepare_state(
            facts=facts,
            kinds={},
            value_class_facts={},
            predicate_facts=(),
            segments=(),
            stored={},
            origins={},
            load_state=_LoadState.ISOLATED,
        )
    )
    with pytest.raises(ValueError, match="ambiguous MATERIALIZE_RESIDUE"):
        CapabilityRegistry.residue_for(CONST_BACKEND.IBIS)


def test_exact_scope_reader_has_no_fallback_and_retains_old_view(isolated):
    from mountainash.core.capabilities.catalogue import CapabilityQuery
    from mountainash.core.capabilities.declarations import CapabilityKey
    from mountainash.core.capabilities.identity import Dialect, Scope

    family = _vc_fact(FK_DT.TRUNCATE)
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, (family,))
    scope = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    key = CapabilityKey.from_fact(family)
    old = CapabilityRegistry.reader(scope)
    assert old.get_optional(key) is None
    with pytest.raises(KeyError):
        old.get(key)
    assert old.search(CapabilityQuery(operation=FK_DT.TRUNCATE)) == ()
    assert (
        CapabilityRegistry.capability_for(
            FK_DT.TRUNCATE,
            "unit",
            CONST_BACKEND.IBIS,
            "ibis-duckdb",
            "2d",
        )
        is family
    )

    dialect = _vc_fact(FK_DT.TRUNCATE, dialect="ibis-duckdb")
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, (dialect,))
    assert old.get_optional(key) is None
    current = CapabilityRegistry.reader(scope)
    assert current.get(key) is dialect
    assert current.search(CapabilityQuery(operation=FK_DT.TRUNCATE)) == (dialect,)


def test_catalogue_distinguishes_unrequested_empty_and_uncaptured_scopes():
    from mountainash.core.capabilities.catalogue import (
        CapabilityQuery,
        CatalogueQuery,
        UncapturedScopeError,
    )
    from mountainash.core.capabilities.identity import FamilyWide, Scope

    scope = Scope(CONST_BACKEND.IBIS, FamilyWide())
    capture = CapabilityRegistry.capture(scopes=frozenset({scope}))
    assert capture.search(CatalogueQuery()).capabilities is None
    assert capture.search(CatalogueQuery(capabilities=CapabilityQuery(), scopes=frozenset())).capabilities == ()
    records = capture.search(CatalogueQuery(capabilities=CapabilityQuery())).capabilities
    assert records == capture.reader(scope).search(CapabilityQuery())
    assert all(fact.backend is CONST_BACKEND.IBIS and fact.dialect is None for fact in records)
    other = Scope(CONST_BACKEND.POLARS, FamilyWide())
    with pytest.raises(UncapturedScopeError):
        capture.reader(other)
    with pytest.raises(UncapturedScopeError):
        capture.search(CatalogueQuery(capabilities=CapabilityQuery(), scopes=frozenset({other})))


def test_issue_capture_retains_old_source_and_distinguishes_missing_namespace():
    from mountainash.core.capabilities.capture import CapturedAddress
    from mountainash.core.capabilities.catalogue import IssueSnapshot, UncapturedNamespaceError
    from mountainash.core.capabilities.schema import CaptureValue

    row = {"id": "IB-STR-01", "status": "needs_filing", "affected_backends": ["ibis-duckdb"]}
    source = CapturedAddress(
        "mountainash",
        "registry/upstream-issues.yaml",
        "issues",
        artifact=b"issues: [{id: IB-STR-01, status: needs_filing, affected_backends: [ibis-duckdb]}]",
    )
    snapshot = IssueSnapshot(source, (("IB-STR-01", CaptureValue.of(row)),))
    old = CapabilityRegistry.capture(issues=snapshot)
    row["status"] = "resolved"
    row["affected_backends"].append("ibis-sqlite")
    updated = IssueSnapshot(
        CapturedAddress(
            "mountainash",
            "registry/upstream-issues.yaml",
            "issues",
            artifact=b"issues: [{id: IB-STR-01, status: resolved, affected_backends: [ibis-duckdb, ibis-sqlite]}]",
        ),
        (("IB-STR-01", CaptureValue.of(row)),),
    )
    current = CapabilityRegistry.capture(issues=updated)
    old_fields = dict(old.issue("IB-STR-01").value)
    assert old_fields["status"] == CaptureValue("text", "needs_filing")
    assert old_fields["affected_backends"] == CaptureValue("sequence", (CaptureValue("text", "ibis-duckdb"),))
    assert dict(current.issue("IB-STR-01").value)["status"] == CaptureValue("text", "resolved")
    assert old.issues.source.artifact == source.artifact
    with pytest.raises(KeyError):
        old.issue("IB-STR-99")
    with pytest.raises(UncapturedNamespaceError):
        CapabilityRegistry.capture().issue("IB-STR-01")
    empty = IssueSnapshot(
        CapturedAddress("mountainash", "registry/upstream-issues.yaml", "issues", artifact=b"issues: []"),
        (),
    )
    with pytest.raises(KeyError):
        CapabilityRegistry.capture(issues=empty).issue("IB-STR-01")


def test_issue_reference_validation_precedes_uncaptured_namespace():
    from mountainash.core.capabilities.catalogue import UncapturedNamespaceError

    capture = CapabilityRegistry.capture()
    with pytest.raises(ValueError):
        capture.issue("malformed")
    with pytest.raises(UncapturedNamespaceError):
        capture.issue("IB-STR-01")


def test_evidence_and_bindings_do_not_follow_same_key_payload_edits():
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        BindingRole,
        CapturedAddress,
        CapturedAssertion,
        Environment,
        EvidenceCapture,
        VerificationBinding,
    )
    from mountainash.core.capabilities.catalogue import (
        BindingQuery,
        CatalogueQuery,
        EvidenceQuery,
        UncapturedNamespaceError,
    )
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey
    from mountainash.core.capabilities.gaps import VerificationSnapshot
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
    from mountainash.core.capabilities.schema import Scenario

    fact = CapabilityRegistry.facts()[0]
    scope = Scope(fact.backend, FamilyWide() if fact.dialect is None else Dialect(fact.dialect))
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "test_evidence_and_bindings_do_not_follow_same_key_payload_edits",
        artifact=Path(__file__).read_bytes(),
    )
    claim = CapturedAssertion("capability", QualifiedCapabilityKey(scope, CapabilityKey.from_fact(fact)), fact, source)
    changed = replace(claim, payload=replace(fact, message="different captured claim"))
    evidence = EvidenceCapture(
        source,
        (claim,),
        None,
        Environment(),
        (source,),
        "structural",
        ("immutable claim identity",),
        (source,),
    )
    oracle = replace(source, entry="independent oracle")
    binding = VerificationBinding(
        claim,
        Scenario(),
        BindingRole.STRUCTURAL_EVIDENCE,
        source,
        scope,
        oracle,
        "compilation",
    )
    capture = CapabilityRegistry.capture(
        verification=VerificationSnapshot((), bindings=(binding,)),
        evidence=(evidence,),
    )
    original = capture.search(
        CatalogueQuery(
            evidence=EvidenceQuery(subject=claim),
            bindings=BindingQuery(captured_claim=claim),
        )
    )
    assert original.evidence == (evidence,)
    assert original.bindings == (binding,)
    edited = capture.search(
        CatalogueQuery(
            evidence=EvidenceQuery(subject=changed),
            bindings=BindingQuery(captured_claim=changed),
        )
    )
    assert edited.evidence == ()
    assert edited.bindings == ()
    with pytest.raises(UncapturedNamespaceError):
        CapabilityRegistry.capture().search(CatalogueQuery(evidence=EvidenceQuery()))
    with pytest.raises(UncapturedNamespaceError):
        CapabilityRegistry.capture(verification=VerificationSnapshot(())).search(
            CatalogueQuery(bindings=BindingQuery())
        )


def test_evidence_subject_scope_filters_apply_to_the_same_subject():
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        CapturedAddress,
        CapturedAssertion,
        Environment,
        EvidenceCapture,
    )
    from mountainash.core.capabilities.catalogue import CatalogueQuery, EvidenceQuery
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope

    facts = CapabilityRegistry.facts()
    first = facts[0]
    second = next(
        fact
        for fact in facts
        if Scope(
            fact.backend,
            FamilyWide() if fact.dialect is None else Dialect(fact.dialect),
        )
        != Scope(
            first.backend,
            FamilyWide() if first.dialect is None else Dialect(first.dialect),
        )
    )
    first_scope = Scope(first.backend, FamilyWide() if first.dialect is None else Dialect(first.dialect))
    second_scope = Scope(second.backend, FamilyWide() if second.dialect is None else Dialect(second.dialect))
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "test_evidence_subject_scope_filters_apply_to_the_same_subject",
        artifact=Path(__file__).read_bytes(),
    )
    first_claim = CapturedAssertion(
        "capability",
        QualifiedCapabilityKey(first_scope, CapabilityKey.from_fact(first)),
        first,
        replace(source, entry="first"),
    )
    second_claim = CapturedAssertion(
        "capability",
        QualifiedCapabilityKey(second_scope, CapabilityKey.from_fact(second)),
        second,
        replace(source, entry="second"),
    )
    evidence = EvidenceCapture(
        source,
        (first_claim, second_claim),
        None,
        Environment(),
        (source,),
        "structural",
        ("correlated subjects",),
        (source,),
    )
    capture = CapabilityRegistry.capture(evidence=(evidence,))

    assert (
        capture.search(
            CatalogueQuery(
                evidence=EvidenceQuery(subject=second_claim),
                scopes=frozenset({first_scope}),
            )
        ).evidence
        == ()
    )
    assert capture.search(
        CatalogueQuery(
            evidence=EvidenceQuery(subject=second_claim),
            scopes=frozenset({second_scope}),
        )
    ).evidence == (evidence,)


def test_all_family_history_requires_verification_but_capability_history_does_not():
    from mountainash.core.capabilities.catalogue import (
        CatalogueQuery,
        ChangeQuery,
        UncapturedNamespaceError,
    )

    capture = CapabilityRegistry.capture()
    with pytest.raises(UncapturedNamespaceError):
        capture.search(CatalogueQuery(changes=ChangeQuery()))
    assert isinstance(
        capture.search(CatalogueQuery(changes=ChangeQuery(family="capability"))).changes,
        tuple,
    )


def test_binding_order_uses_qualified_claim_identity_before_bundle_address():
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        BindingRole,
        CapturedAddress,
        CapturedAssertion,
        VerificationBinding,
    )
    from mountainash.core.capabilities.catalogue import BindingQuery, CatalogueQuery
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey
    from mountainash.core.capabilities.gaps import VerificationSnapshot
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
    from mountainash.core.capabilities.schema import Scenario

    facts = CapabilityRegistry.facts()

    def scope_for(fact):
        return Scope(
            fact.backend,
            FamilyWide() if fact.dialect is None else Dialect(fact.dialect),
        )

    first = next(
        fact
        for fact in facts
        if any(scope_for(other) == scope_for(fact) and other.operation_key != fact.operation_key for other in facts)
    )
    second = next(
        fact for fact in facts if scope_for(fact) == scope_for(first) and fact.operation_key != first.operation_key
    )
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "shared evidence bundle",
        artifact=Path(__file__).read_bytes(),
    )
    claims = tuple(
        CapturedAssertion(
            "capability",
            QualifiedCapabilityKey(scope_for(fact), CapabilityKey.from_fact(fact)),
            fact,
            source,
        )
        for fact in (first, second)
    )
    ordered_claims = tuple(
        sorted(
            claims,
            key=lambda claim: (
                claim.key.scope.backend.value,
                type(claim.key.scope.applicability).__name__,
                claim.key.scope.dialect or "",
                type(claim.key.local.operation).__module__,
                type(claim.key.local.operation).__qualname__,
                claim.key.local.operation.name,
            ),
        )
    )
    observer = replace(source, entry="shared observer")
    oracle = replace(source, entry="independent oracle")
    bindings = tuple(
        VerificationBinding(
            claim,
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            claim.key.scope,
            oracle,
            "compilation",
        )
        for claim in ordered_claims
    )
    capture = CapabilityRegistry.capture(
        verification=VerificationSnapshot((), bindings=tuple(reversed(bindings))),
    )

    assert capture.search(CatalogueQuery(bindings=BindingQuery())).bindings == bindings


def test_binding_order_uses_captured_claim_address_for_same_qualified_key():
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        BindingRole,
        CapturedAddress,
        CapturedAssertion,
        VerificationBinding,
    )
    from mountainash.core.capabilities.catalogue import BindingQuery, CatalogueQuery
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey
    from mountainash.core.capabilities.gaps import VerificationSnapshot
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
    from mountainash.core.capabilities.schema import Scenario

    fact = CapabilityRegistry.facts()[0]
    scope = Scope(
        fact.backend,
        FamilyWide() if fact.dialect is None else Dialect(fact.dialect),
    )
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "binding ordering fixture",
        artifact=Path(__file__).read_bytes(),
    )
    claim = CapturedAssertion(
        "capability",
        QualifiedCapabilityKey(scope, CapabilityKey.from_fact(fact)),
        fact,
        source,
    )
    older = replace(claim, address=replace(source, entry="captured-old"))
    current = replace(claim, address=replace(source, entry="captured-current"))
    observer = replace(source, entry="shared observer")
    oracle = replace(source, entry="independent oracle")
    bindings = tuple(
        VerificationBinding(
            captured_claim,
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        )
        for captured_claim in (current, older)
    )

    def ordered(records):
        return (
            CapabilityRegistry.capture(
                verification=VerificationSnapshot((), bindings=records),
            )
            .search(CatalogueQuery(bindings=BindingQuery()))
            .bindings
        )

    expected = bindings
    assert ordered(bindings) == expected
    assert ordered(tuple(reversed(bindings))) == expected


def test_binding_capture_rejects_conflicting_payloads_at_one_claim_source():
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        BindingRole,
        CapturedAddress,
        CapturedAssertion,
        VerificationBinding,
    )
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey
    from mountainash.core.capabilities.gaps import VerificationSnapshot
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
    from mountainash.core.capabilities.schema import Scenario

    fact = CapabilityRegistry.facts()[0]
    scope = Scope(
        fact.backend,
        FamilyWide() if fact.dialect is None else Dialect(fact.dialect),
    )
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "one captured assertion",
        artifact=Path(__file__).read_bytes(),
    )
    claim = CapturedAssertion(
        "capability",
        QualifiedCapabilityKey(scope, CapabilityKey.from_fact(fact)),
        fact,
        source,
    )
    conflicting = replace(claim, payload=replace(fact, message="conflicting capture"))
    observer = replace(source, entry="shared observer")
    oracle = replace(source, entry="independent oracle")
    bindings = tuple(
        VerificationBinding(
            captured_claim,
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        )
        for captured_claim in (claim, conflicting)
    )

    with pytest.raises(ValueError, match="conflicting payload"):
        CapabilityRegistry.capture(verification=VerificationSnapshot((), bindings=bindings))


def test_static_provenance_follows_collection_positions_and_keeps_capture(isolated):
    from dataclasses import replace

    from mountainash.core.capabilities.capture import CapturedAddress, RuntimeOrigin
    from mountainash.core.capabilities.declarations import (
        BoundSegment,
        CapabilityAssertion,
        CapabilityKey,
        CapabilitySegment,
        DivergenceManifestation,
        Domain,
        ManifestationKey,
        QualifiedCapabilityKey,
        QualifiedManifestationKey,
    )
    from mountainash.core.capabilities.identity import FamilyWide, Scope
    from mountainash.core.capabilities.schema import (
        CaptureValue,
        DivergenceKind,
        OperationTarget,
        Scenario,
    )
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    )

    scope = Scope(CONST_BACKEND.IBIS, FamilyWide())
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "static provenance fixture",
        artifact=b"static provenance fixture",
    )
    first = CapabilityAssertion(
        CapabilityKey(FK_STR.CENTER, "length"),
        CapabilityLevel.LITERAL_ONLY,
        "2026-09-15",
        message="first",
        probe_exempt="test",
    )
    second = CapabilityAssertion(
        CapabilityKey(FK_STR.CENTER, "character"),
        CapabilityLevel.LITERAL_ONLY,
        "2026-09-15",
        message="second",
        probe_exempt="test",
    )
    inserted = CapabilityAssertion(
        CapabilityKey(FK_STR.REPLACE, "substring"),
        CapabilityLevel.LITERAL_ONLY,
        "2026-09-15",
        message="inserted",
        probe_exempt="test",
    )

    def manifestation_for(value):
        return DivergenceManifestation(
            ManifestationKey(
                OperationTarget(FK_STR.CENTER),
                Scenario(arguments=(("input", CaptureValue.of(value)),)),
            ),
            DivergenceKind.SEMANTICS,
            CaptureValue.of("expected"),
            CaptureValue.of("observed"),
            "fixture divergence",
            "2026-09-15",
        )

    first_manifestation = manifestation_for("first")
    second_manifestation = manifestation_for("second")
    inserted_manifestation = manifestation_for("inserted")

    def segment(capabilities, manifestations, source_capture=source):
        return BoundSegment(
            "mountainash.expressions.backends.capabilities.ibis.family.substrait.string",
            scope,
            CapabilitySegment(Domain.STRING, capabilities, manifestations),
            source_capture,
        )

    CapabilityRegistry.register_segment(segment((first, second), (first_manifestation, second_manifestation)))
    first_key = QualifiedCapabilityKey(scope, first.key)
    first_manifestation_key = QualifiedManifestationKey(scope, first_manifestation.key)
    initial_origins = CapabilityRegistry.origins()
    assert initial_origins[first_key][0].entry == "capabilities[0]"
    assert initial_origins[first_key][0].captured == replace(source, entry="capabilities[0]")
    assert CapabilityRegistry.snapshot().manifestations[first_manifestation_key].origins[0] == replace(
        initial_origins[first_key][0],
        entry="manifestations[0]",
        captured=replace(source, entry="manifestations[0]"),
    )

    CapabilityRegistry.reset()
    CapabilityRegistry.register_segment(segment((inserted, first, second), (first_manifestation, second_manifestation)))
    assert CapabilityRegistry.origins()[first_key][0].entry == "capabilities[1]"
    assert CapabilityRegistry.snapshot().manifestations[first_manifestation_key].origins[0].entry == "manifestations[0]"

    CapabilityRegistry.reset()
    CapabilityRegistry.register_segment(
        segment((first, second), (inserted_manifestation, first_manifestation, second_manifestation))
    )
    assert CapabilityRegistry.origins()[first_key][0].entry == "capabilities[0]"
    assert CapabilityRegistry.snapshot().manifestations[first_manifestation_key].origins[0].entry == "manifestations[1]"

    CapabilityRegistry.reset()
    CapabilityRegistry.register_segment(segment((first,), (first_manifestation,), source_capture=None))
    assert CapabilityRegistry.origins()[first_key][0].captured is None

    CapabilityRegistry.reset()
    CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, (first.qualify(scope),))
    assert isinstance(CapabilityRegistry.origins()[first_key][0], RuntimeOrigin)


def test_published_source_origin_survives_later_file_change(tmp_path, monkeypatch):
    import importlib
    import sys
    from types import ModuleType

    from mountainash.core.capabilities import bootstrap
    from mountainash.core.capabilities.declarations import QualifiedCapabilityKey

    declared_root = "mountainash.expressions.backends.capabilities"
    segment = next(
        item
        for item in CapabilityRegistry.capture().segments
        if item.module.startswith(declared_root + ".ibis.family.") and item.segment.capabilities
    )
    assert segment.source_capture is not None
    original_source = segment.source_capture.artifact
    assert type(original_source) is bytes
    relative_module = segment.module.removeprefix(declared_root + ".").split(".")
    source_path = tmp_path.joinpath(*relative_module).with_suffix(".py")
    source_path.parent.mkdir(parents=True)
    for depth in range(1, len(relative_module)):
        (tmp_path.joinpath(*relative_module[:depth]) / "__init__.py").touch()
    (tmp_path.joinpath(*relative_module[:2]) / "_scope.py").write_text(
        "from mountainash.core.capabilities.identity import FamilyWide, Scope\n"
        "from mountainash.core.constants import CONST_BACKEND\n"
        "SCOPE = Scope(CONST_BACKEND.IBIS, FamilyWide())\n"
    )
    source_path.write_bytes(original_source)
    original_children = {name: module for name, module in sys.modules.items() if name.startswith(declared_root + ".")}
    for name in original_children:
        sys.modules.pop(name)
    root = ModuleType(declared_root)
    root.__path__ = [str(tmp_path)]
    root.__package__ = declared_root
    monkeypatch.setitem(sys.modules, declared_root, root)
    monkeypatch.setattr(bootstrap, "_ROOTS", (declared_root,))
    monkeypatch.setattr(
        bootstrap,
        "discover_declaration_modules",
        lambda: (segment.module,),
    )
    importlib.invalidate_caches()
    snapshot = CapabilityRegistry.snapshot()
    try:
        acquired = bootstrap._load_segments()[0]
        CapabilityRegistry.reset()
        CapabilityRegistry.register_segment(acquired)
        key = QualifiedCapabilityKey(acquired.scope, acquired.segment.capabilities[0].key)
        origin = CapabilityRegistry.origins()[key][0]
        source_path.write_bytes(original_source + b"\n# Later source revision\n")
        assert origin.captured.artifact == original_source
        assert bootstrap._load_segments()[0].source_capture.artifact != origin.captured.artifact
        assert CapabilityRegistry.reader(acquired.scope).get(key.local) is acquired.facts[0]
    finally:
        CapabilityRegistry.restore(snapshot)
        for name in tuple(sys.modules):
            if name.startswith(declared_root + "."):
                sys.modules.pop(name)
        sys.modules.update(original_children)


def test_family_claim_binding_retains_concrete_execution_scope():
    from dataclasses import replace
    from pathlib import Path

    from mountainash.core.capabilities.capture import (
        BindingRole,
        CapturedAddress,
        CapturedAssertion,
        VerificationBinding,
    )
    from mountainash.core.capabilities.catalogue import BindingQuery, CatalogueQuery
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey
    from mountainash.core.capabilities.gaps import VerificationSnapshot
    from mountainash.core.capabilities.identity import Dialect, FamilyWide, Scope
    from mountainash.core.capabilities.schema import Scenario

    fact = _vc_fact(FK_DT.TRUNCATE)
    family = Scope(CONST_BACKEND.IBIS, FamilyWide())
    duckdb = Scope(CONST_BACKEND.IBIS, Dialect("ibis-duckdb"))
    sqlite = Scope(CONST_BACKEND.IBIS, Dialect("ibis-sqlite"))
    source = CapturedAddress(
        "mountainash",
        "tests/core/test_capability_registry_enumeration.py",
        "family claim",
        artifact=Path(__file__).read_bytes(),
    )
    claim = CapturedAssertion(
        "capability",
        QualifiedCapabilityKey(family, CapabilityKey.from_fact(fact)),
        fact,
        source,
    )
    binding = VerificationBinding(
        claim,
        Scenario(),
        BindingRole.OPERATIONAL_CONTRACT,
        replace(source, entry="observer[ibis-duckdb]"),
        duckdb,
        replace(source, entry="independent oracle"),
        "compilation",
    )
    capture = CapabilityRegistry.capture(verification=VerificationSnapshot((), bindings=(binding,)))
    assert capture.search(
        CatalogueQuery(
            scopes=frozenset({duckdb}),
            bindings=BindingQuery(captured_claim=claim),
        )
    ).bindings == (binding,)
    assert (
        capture.search(
            CatalogueQuery(
                scopes=frozenset({sqlite}),
                bindings=BindingQuery(captured_claim=claim),
            )
        ).bindings
        == ()
    )
    exact = replace(
        claim,
        key=QualifiedCapabilityKey(duckdb, claim.key.local),
        payload=replace(fact, dialect="ibis-duckdb"),
    )
    with pytest.raises(ValueError):
        replace(binding, captured_claim=exact, scope=sqlite)
    with pytest.raises(ValueError):
        replace(binding, scope=Scope(CONST_BACKEND.POLARS, Dialect("polars")))
