"""Assertion-change history contracts."""

from __future__ import annotations

from dataclasses import replace
from enum import Enum

import pytest

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.capabilities.capture import (
    BindingRole,
    CapturedAddress,
    CapturedAssertion,
    Environment,
    EnvironmentCoordinate,
    EvidenceCapture,
    UnresolvedHistoricalValue,
    VerificationBinding,
)
from mountainash.core.capabilities.declarations import Domain, FactSource
from mountainash.core.capabilities.identity import FamilyWide, Scope
from mountainash.core.capabilities.retired import AssertionChange, ChangeDisposition
from mountainash.core.capabilities.schema import CaptureValue, Scenario
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _address(entry: str) -> CapturedAddress:
    return CapturedAddress("mountainash", "history.py", entry, artifact=b"history")


def _captured(message: str, entry: str) -> CapturedAssertion:
    fact = CapabilityFact(
        operation_key=FK_STR.CENTER,
        param="length",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS,
        message=message,
        since="2026-07-05",
        probe_exempt="test",
    )
    return CapturedAssertion("capability", fact.fact_key, fact, _address(entry))


def test_assertion_change_preserves_complete_same_key_replacement():
    prior = _captured("old limitation", "prior")
    successor = CapturedAssertion(
        "capability",
        prior.key,
        replace(prior.payload, message="corrected limitation"),
        _address("successor"),
    )
    change = AssertionChange(
        _address("change"),
        prior,
        ChangeDisposition.INCORRECT_DECLARATION,
        "2026-09-15T10:11:12",
        "correct explanatory claim",
        (successor,),
        (_address("evidence"),),
        Environment(
            (
                EnvironmentCoordinate("package", "ibis", "13.0.0"),
                EnvironmentCoordinate("engine", "duckdb", "1.2.2"),
            )
        ),
    )

    assert change.prior.payload.message == "old limitation"
    assert change.successors[0].payload.message == "corrected limitation"
    assert change.prior.key == change.successors[0].key
    assert change.evidence_refs[0].entry == "evidence"
    assert change.fixed_versions.coordinates[0].name == "duckdb"


def test_assertion_change_allows_removal_without_successor():
    change = AssertionChange(
        _address("change"),
        _captured("removed limitation", "prior"),
        ChangeDisposition.UPSTREAM_FIX,
        "2026-09-15",
        "observed upstream fix",
    )

    assert change.successors == ()
    assert change.fixed_versions is None


@pytest.mark.parametrize(
    "replacement, error",
    [
        ({"reason": ""}, ValueError),
        ({"recorded_at": "2026-99-99"}, ValueError),
        ({"successors": (_captured("changed content", "prior"),)}, ValueError),
        (
            {
                "successors": (
                    _captured("new", "successor"),
                    _captured("different new", "successor"),
                )
            },
            ValueError,
        ),
    ],
)
def test_assertion_change_rejects_invalid_history(replacement, error):
    change = AssertionChange(
        _address("change"),
        _captured("old limitation", "prior"),
        ChangeDisposition.INCORRECT_DECLARATION,
        "2026-09-15",
        "correct explanatory claim",
    )

    with pytest.raises(error):
        replace(change, **replacement)


def test_capture_environment_preserves_stack_and_rejects_conflicts():
    env = Environment(
        (
            EnvironmentCoordinate("package", "ibis", "12.0.0"),
            EnvironmentCoordinate("engine", "duckdb", "1.2.2"),
        )
    )
    assert env.coordinates[1].name == "ibis-framework"
    assert env.coordinates[1].original_label == "ibis"
    assert env != Environment(
        (
            EnvironmentCoordinate("package", "ibis-framework", "12.0.0"),
            EnvironmentCoordinate("engine", "duckdb", "1.3.0"),
        )
    )
    with pytest.raises(ValueError, match="conflicting"):
        Environment(
            (
                EnvironmentCoordinate("package", "ibis", "12.0.0"),
                EnvironmentCoordinate("package", "ibis-framework", "11.0.0"),
            )
        )


def test_evidence_requires_explicit_null_or_unavailable_history():
    claim = _captured("observed limitation", "claim")
    source = _address("evidence")

    with pytest.raises(ValueError, match="explicit"):
        EvidenceCapture(
            source,
            (claim,),
            None,
            Environment(),
            (source,),
            "structural",
            None,
            (source,),
        )

    explicit_null = EvidenceCapture(
        source,
        (claim,),
        None,
        Environment(),
        (source,),
        "structural",
        CaptureValue.of(None),
        (source,),
    )
    unavailable = EvidenceCapture(
        source,
        (claim,),
        None,
        Environment(),
        (source,),
        "historical_unknown",
        UnresolvedHistoricalValue("legacy result", source, "result was not retained"),
        (source,),
    )

    assert explicit_null.result == CaptureValue("null", "")
    assert unavailable.result.reason == "result was not retained"


def test_capture_rejects_enum_with_mutable_value():
    class MutableResult(Enum):
        VALUE = []

    with pytest.raises(TypeError, match="mutable"):
        CapturedAssertion("capability", "legacy-key", MutableResult.VALUE, _address("mutable"))


def test_verification_binding_rejects_capability_key_payload_scope_and_self_oracle():
    from mountainash.core.capabilities.declarations import CapabilityKey, QualifiedCapabilityKey

    fact = CapabilityFact(
        operation_key=FK_STR.CENTER,
        param="length",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.IBIS,
        message="observed limitation",
        since="2026-07-05",
        probe_exempt="test",
    )
    scope = Scope(CONST_BACKEND.IBIS, FamilyWide())
    claim = CapturedAssertion(
        "capability",
        QualifiedCapabilityKey(scope, CapabilityKey.from_fact(fact)),
        fact,
        _address("claim"),
    )
    observer = _address("observer")
    oracle = _address("oracle")

    binding = VerificationBinding(
        claim,
        Scenario(),
        BindingRole.STRUCTURAL_EVIDENCE,
        observer,
        scope,
        oracle,
        "compilation",
    )
    assert binding.captured_claim is claim

    with pytest.raises(ValueError, match="payload"):
        VerificationBinding(
            replace(claim, payload=replace(fact, param="unexpected")),
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        )
    with pytest.raises(ValueError, match="scope"):
        VerificationBinding(
            replace(
                claim,
                key=QualifiedCapabilityKey(
                    Scope(CONST_BACKEND.POLARS, FamilyWide()),
                    CapabilityKey.from_fact(fact),
                ),
            ),
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        )
    with pytest.raises(ValueError, match="independent"):
        VerificationBinding(
            claim,
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            observer,
            "compilation",
        )


def test_verification_binding_accepts_and_validates_manifestation_and_gap_claims():
    from mountainash.core.capabilities.capture import SourceOrigin
    from mountainash.core.capabilities.declarations import (
        DivergenceManifestation,
        ManifestationKey,
        QualifiedManifestation,
        QualifiedManifestationKey,
    )
    from mountainash.core.capabilities.gaps import GapKey, InventoryGap, InventoryWide
    from mountainash.core.capabilities.schema import (
        DivergenceKind,
        GapKind,
        KnownGap,
        OperationTarget,
    )

    source = _address("source")
    observer = _address("observer")
    oracle = _address("oracle")
    scope = Scope(CONST_BACKEND.IBIS, FamilyWide())
    local_key = ManifestationKey(OperationTarget(FK_STR.CENTER), Scenario())
    manifestation = DivergenceManifestation(
        local_key,
        DivergenceKind.SEMANTICS,
        CaptureValue.of(0),
        CaptureValue.of(1),
        "observed difference",
        "2026-09-15",
    )
    manifestation_key = QualifiedManifestationKey(scope, local_key)
    local_claim = CapturedAssertion("manifestation", manifestation_key, manifestation, source)
    qualified_claim = CapturedAssertion(
        "manifestation",
        manifestation_key,
        QualifiedManifestation(
            manifestation_key,
            manifestation,
            (SourceOrigin("test.module", scope, FactSource.SUBSTRAIT, Domain.STRING, "manifestation", source),),
        ),
        source,
    )
    for claim in (local_claim, qualified_claim):
        assert (
            VerificationBinding(
                claim,
                Scenario(),
                BindingRole.STRUCTURAL_EVIDENCE,
                observer,
                scope,
                oracle,
                "compilation",
            ).captured_claim
            is claim
        )
    with pytest.raises(ValueError, match="payload"):
        VerificationBinding(
            replace(
                local_claim,
                payload=replace(
                    manifestation,
                    key=ManifestationKey(
                        OperationTarget(FK_STR.CENTER),
                        Scenario(execution=(("mode", CaptureValue.of("different")),)),
                    ),
                ),
            ),
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        )

    gap_key = GapKey("review", OperationTarget(FK_STR.CENTER), "structural coverage", InventoryWide())
    gap = InventoryGap(
        gap_key,
        ("legacy",),
        KnownGap(GapKind.OTHER, "test-only gap", "2026-09-15"),
        (source,),
    )
    gap_claim = CapturedAssertion("gap", gap_key, gap, source)
    assert (
        VerificationBinding(
            gap_claim,
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        ).captured_claim
        is gap_claim
    )
    with pytest.raises(ValueError, match="payload"):
        VerificationBinding(
            replace(
                gap_claim,
                payload=replace(
                    gap,
                    key=GapKey("review", OperationTarget(FK_STR.CENTER), "other coverage", InventoryWide()),
                ),
            ),
            Scenario(),
            BindingRole.STRUCTURAL_EVIDENCE,
            observer,
            scope,
            oracle,
            "compilation",
        )
